import aiohttp, discord, textwrap, traceback
from discord.ext import commands
from Niludetsu.config import BUGS_CHANNEL_ID, OWNER_ID
from Niludetsu.logging import logger
from typing import Any, Optional

DEFAULT_LEVEL = "error"
ELLIPSIS = "..."
MAX_MESSAGE_LENGTH = 1900

class ContextualError(Exception):
    """Исключение с дополнительными метаданными."""

    def __init__(
        self,
        original: BaseException,
        *,
        level: str,
        context: str,
        tb_text: str,
        origin: str,
    ) -> None:
        super().__init__(str(original))
        self.original = original
        self.level = level
        self.context = context
        self.tb_text = tb_text
        self.origin = origin

class PastebinClient:
    API_URL = "https://dpaste.com/api/"

    def __init__(self) -> None:
        pass

    async def create_paste(
        self,
        *,
        title: str,
        content: str,
        expire: str = "1D",
        private: bool = True,
    ) -> str:
        timeout = aiohttp.ClientTimeout(total=30)
        payload = {
            "content": content,
            "title": title,
            "expiry_days": 1,
        }
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.API_URL,
                data=payload,
            ) as response:
                body = (await response.text()).strip()
                if not response.ok:
                    raise RuntimeError(f"Paste service error: {response.status} {body}")
                return body

class BugReportLogger:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self._pastebin_client: Optional[PastebinClient] = None

    async def log_command_error(self, channel: discord.TextChannel, ctx: commands.Context, error: ContextualError) -> None:
        await self._send_paste_report(
            channel,
            title=f"Command error: {ctx.command.qualified_name if getattr(ctx, 'command', None) else 'unknown'}",
            message_header=f"Ошибка команды `{_safe_name(getattr(ctx.command, 'qualified_name', 'unknown'))}`",
            user=getattr(ctx, "author", None),
            content=_format_command_error(ctx, error),
            raw_error=error.original,
        )

    async def log_app_command_error(self, channel: discord.TextChannel, interaction: discord.Interaction, error: ContextualError) -> None:
        command_name = getattr(getattr(interaction, "command", None), "qualified_name", "unknown")
        await self._send_paste_report(
            channel,
            title=f"Interaction error: {command_name}",
            message_header=f"Ошибка слеш-команды `{_safe_name(command_name)}`",
            user=getattr(interaction, "user", None),
            content=_format_interaction_error(interaction, error),
            raw_error=error.original,
        )

    async def _send_paste_report(
        self,
        channel: discord.TextChannel,
        *,
        title: str,
        message_header: str,
        user: Optional[discord.abc.User],
        content: str,
        raw_error: BaseException,
    ) -> None:
        paste_url = await self._create_paste(title=title, content=content)
        await self._send_channel_message(
            channel,
            header=message_header,
            user=user,
            extra=paste_url,
            raw_error=raw_error,
        )

    async def _create_paste(self, *, title: str, content: str) -> Optional[str]:
        if not content:
            content = "(пустой отчёт)"

        client = self._pastebin_client or PastebinClient()
        self._pastebin_client = client

        try:
            return await client.create_paste(title=title, content=content, expire="1D", private=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Не удалось создать пасту для ошибки: {exc}", exc=exc)
            return None

    async def resolve_channel(self, guild: Optional[discord.Guild]) -> Optional[discord.TextChannel]:
        async def _resolve(target: discord.Guild) -> Optional[discord.TextChannel]:
            try:
                channel_id = int(BUGS_CHANNEL_ID)
            except (TypeError, ValueError):
                return None

            channel = target.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await target.fetch_channel(channel_id)
                except Exception:  # noqa: BLE001
                    return None

            return channel if isinstance(channel, discord.TextChannel) else None

        if guild is not None:
            return await _resolve(guild)

        for candidate in getattr(self.bot, "guilds", []):
            channel = await _resolve(candidate)
            if channel is not None:
                return channel
        return None

    async def _send_channel_message(
        self,
        channel: discord.TextChannel,
        *,
        header: str,
        user: Optional[discord.abc.User],
        extra: Optional[str],
        raw_error: BaseException,
    ) -> None:
        summary = _summarize_error(raw_error)
        user_info = f"Пользователь: {user.mention} ({user.id})" if user else "Пользователь: —"
        paste_line = f"Paste: {extra}" if extra else "Paste: не удалось создать ссылку"
        lines = [f"<@{OWNER_ID}> ⚠️ {header}", user_info, paste_line, f"Сводка: {summary}"]
        message = "\n".join(lines)
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[: MAX_MESSAGE_LENGTH - len(ELLIPSIS)] + ELLIPSIS
        try:
            await channel.send(message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Не удалось отправить сообщение об ошибке: {exc}", exc=exc)

    def ensure_contextual(
        self,
        error: Exception,
        *,
        context_label: str,
        origin_hint: Optional[Any] = None,
        level: str = DEFAULT_LEVEL,
    ) -> ContextualError:
        return _ensure_contextual(
            error,
            context_label=context_label,
            origin_hint=origin_hint,
            level=level,
        )

    async def log_background_error(self, bot: discord.Client, source: str, error: BaseException) -> None:
        channel = await self.resolve_channel(None)
        paste_url = await self._create_paste(
            title=f"Background error: {source}",
            content=_format_background_error(bot, source, error),
        )
        if channel is None:
            logger.exception("Фоновая ошибка без канала: %s", source, exc_info=error)
            return
        await self._send_channel_message(
            channel,
            header=f"Ошибка фоновой задачи `{_safe_name(source)}`",
            user=None,
            extra=paste_url,
            raw_error=error,
        )

async def setup_error_handling(bot: commands.Bot, *, enable_test_command: bool = False) -> None:
    if not hasattr(bot, "bug_report_logger"):
        bot.bug_report_logger = BugReportLogger(bot)

def _ensure_contextual(
    error: Exception,
    *,
    context_label: str,
    origin_hint: Optional[Any] = None,
    level: str = DEFAULT_LEVEL,
) -> ContextualError:
    if isinstance(error, ContextualError):
        return error

    raw = error
    if isinstance(raw, commands.CommandInvokeError) and getattr(raw, "original", None):
        raw = raw.original

    tb = traceback.extract_tb(raw.__traceback__)
    origin = f"{tb[-1].filename}:{tb[-1].lineno}" if tb else str(origin_hint or type(raw).__name__)
    tb_text = "".join(traceback.format_exception(type(raw), raw, raw.__traceback__))

    return ContextualError(
        raw,
        level=level,
        context=context_label,
        tb_text=tb_text,
        origin=origin,
    )

def _format_command_error(ctx: commands.Context, error: ContextualError) -> str:
    guild = getattr(ctx, "guild", None)
    channel = getattr(ctx, "channel", None)
    author = getattr(ctx, "author", None)
    command = getattr(getattr(ctx, "command", None), "qualified_name", "-")
    message = getattr(getattr(ctx, "message", None), "content", "-")

    template = textwrap.dedent(
        f"""
        === COMMAND ERROR REPORT ===
        Guild: {getattr(guild, 'name', '-') if guild else '-'} (ID: {getattr(guild, 'id', '-')})
        Channel: {getattr(channel, 'name', '-') if channel else '-'} (ID: {getattr(channel, 'id', '-')})
        User: {getattr(author, 'name', '-') if author else '-'} (ID: {getattr(author, 'id', '-')})
        Command: {command}
        Message: {message}

        Context: {error.context}
        Origin: {error.origin}
        Level: {error.level}
        Exception: {type(error.original).__name__}: {error.original}

        Traceback:
        {error.tb_text}
        """
    ).strip()

    return template

def _format_interaction_error(interaction: discord.Interaction, error: ContextualError) -> str:
    guild = getattr(interaction, "guild", None)
    channel = getattr(interaction, "channel", None)
    user = getattr(interaction, "user", None)
    command = getattr(getattr(interaction, "command", None), "qualified_name", "-")
    options = _format_interaction_options(interaction)

    template = textwrap.dedent(
        f"""
        === INTERACTION ERROR REPORT ===
        Guild: {getattr(guild, 'name', '-') if guild else '-'} (ID: {getattr(guild, 'id', '-')})
        Channel: {getattr(channel, 'name', '-') if channel else '-'} (ID: {getattr(channel, 'id', '-')})
        User: {getattr(user, 'name', '-') if user else '-'} (ID: {getattr(user, 'id', '-')})
        Command: {command}
        Options: {options}

        Context: {error.context}
        Origin: {error.origin}
        Level: {error.level}
        Exception: {type(error.original).__name__}: {error.original}

        Traceback:
        {error.tb_text}
        """
    ).strip()

    return template

def _format_interaction_options(interaction: discord.Interaction) -> str:
    data = getattr(interaction, "data", {}) or {}
    options = data.get("options", [])
    if not options:
        return "-"

    def walk(items):
        parts = []
        for opt in items:
            name = opt.get("name", "<unknown>")
            if "options" in opt:
                parts.append(f"{name}: ({', '.join(walk(opt['options']))})")
            else:
                parts.append(f"{name}={opt.get('value', '-')}")
        return parts

    return ", ".join(walk(options)) or "-"

def _summarize_error(error: BaseException) -> str:
    summary = f"{type(error).__name__}: {error}"
    if len(summary) > 120:
        summary = summary[: 117] + ELLIPSIS
    return summary

def _safe_name(value: str) -> str:
    if len(value) <= 60:
        return value
    return value[:57] + ELLIPSIS

def _format_background_error(bot: discord.Client, source: str, error: BaseException) -> str:
    tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    template = textwrap.dedent(
        f"""
        === BACKGROUND ERROR REPORT ===
        Bot: {getattr(bot.user, 'name', '-') if getattr(bot, 'user', None) else '-'} (ID: {getattr(bot.user, 'id', '-') if getattr(bot, 'user', None) else '-'})
        Source: {source}
        Exception: {type(error).__name__}: {error}

        Traceback:
        {tb_text}
        """
    ).strip()
    return template

__all__ = ("BugReportLogger", "ContextualError", "setup_error_handling")

