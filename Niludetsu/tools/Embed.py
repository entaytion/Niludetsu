import discord
from dataclasses import dataclass
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Time import TimeService
from typing import Optional, Sequence

@dataclass(frozen=True)
class Colors:
    PRIMARY: int = 0x000001
    ERROR: int = 0xF20C3C
    WARNING: int = 0xF2F20C
    SUCCESS: int = 0x0CF232
    INFO: int = 0x820CF2
_time = TimeService()
UserTarget = discord.Member | discord.User

def _normalize_timestamp(value: Optional[object]) -> Optional[discord.utils.snowflake_time]:
    if value is True:
        return _time.now()
    if value in (None, False):
        return None
    return _time.ensure_datetime(value)


def _user_text(user: UserTarget, text: str, *, mention: bool, preserve_blocks: bool) -> str:
    formatted = text.strip()
    if not mention:
        return formatted
    if preserve_blocks and (text.startswith("```") or text.startswith("\n")):
        return f"{user.mention}\n{formatted}"
    return f"{user.mention}, {formatted}" if formatted else user.mention

class Embed(discord.Embed):
    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[Sequence[dict]] = None,
        footer: Optional[dict] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[object] = None,
        emoji: Optional[str] = None,
        inline_fields: bool = False,
        **kwargs,
    ) -> None:
        thumbnail = thumbnail or kwargs.pop("thumbnail_url", None)
        image = image or kwargs.pop("image_url", None)
        
        color = Colors.PRIMARY if color is None else color
        if emoji:
            title = f"{emoji} {title}" if title else emoji

        super().__init__(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=_normalize_timestamp(timestamp),
            **kwargs,
        )

        if fields:
            for field in fields:
                payload = dict(field)
                if inline_fields:
                    payload["inline"] = True
                self.add_field(**payload)

        if footer:
            self.set_footer(**footer)
        if thumbnail:
            self.set_thumbnail(url=thumbnail)
        if image:
            self.set_image(url=image)
        if author:
            self.set_author(**author)

    @classmethod
    def _base(cls, *, emoji: Optional[str], color: Optional[int], **kwargs) -> "Embed":
        override_color = kwargs.pop("color", None)
        resolved_color = override_color if override_color is not None else color
        return cls(emoji=emoji, color=resolved_color, **kwargs)

    @classmethod
    def default(cls, **kwargs) -> "Embed":
        color = kwargs.pop("color", Colors.PRIMARY)
        return cls._base(emoji=None, color=color, **kwargs)

    @classmethod
    def user(
        cls,
        *,
        user: UserTarget,
        title: Optional[str] = None,
        title_prefix: Optional[str] = None,
        description: Optional[str] = None,
        text: Optional[str] = None,
        color: Optional[int] = None,
        mention: bool = False,
        preserve_blocks: bool = True,
        **kwargs,
    ) -> "Embed":
        if title is None and title_prefix is not None:
            title = f"{title_prefix} — {user.display_name}"
        if description is None and text is not None:
            description = _user_text(
                user,
                text,
                mention=mention,
                preserve_blocks=preserve_blocks,
            )
        kwargs.setdefault("thumbnail", user.display_avatar.url)
        return cls(title=title, description=description, color=color, **kwargs)

    @classmethod
    def user_action(
        cls,
        *,
        action: str,
        user: UserTarget,
        text: str,
        color: Optional[int] = None,
        mention: bool = True,
        preserve_blocks: bool = True,
        **kwargs,
    ) -> "Embed":
        return cls.user(
            user=user,
            title_prefix=action,
            text=text,
            color=color,
            mention=mention,
            preserve_blocks=preserve_blocks,
            **kwargs,
        )

    @classmethod
    def success(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Успешно!", emoji=Emojis.SUCCESS, color=Colors.SUCCESS, **kwargs)
    @classmethod
    def exception(
        cls,
        *,
        error: Exception,
        user: Optional[UserTarget] = None,
        title: Optional[str] = None,
        color: Optional[int] = None,
        **kwargs,
    ) -> "Embed":
        from Niludetsu.Exceptions import NiludetsuException
        import discord
        from discord.ext import commands

        match error:
            case NiludetsuException():
                desc = getattr(error, "message", str(error))
                title = title or "Ошибка валидации"
                if type(error).__name__ in ("ActiveGameExists", "NotEnoughMoney", "BetTooLow"):
                    title = title or "Ошибка экономики"
            case commands.CommandOnCooldown():
                title = title or "Подождите"
                desc = f"Команда на перезарядке. Попробуйте снова через {error.retry_after:.2f} сек."
            case commands.MissingPermissions():
                title = title or "Недостаточно прав"
                desc = f"Необходимые права: {', '.join(error.missing_permissions)}"
            case commands.BotMissingPermissions():
                title = title or "Ошибка бота"
                desc = f"Боту не хватает прав: {', '.join(error.missing_permissions)}"
            case discord.Forbidden():
                title = title or "Нет доступа"
                desc = "Боту не хватает прав для выполнения этого действия, либо у пользователя закрыта личка."
            case _:
                title = title or "Произошла ошибка!"
                desc = str(error)

        color = color or Colors.ERROR
        emoji = kwargs.pop("emoji", Emojis.ERROR)

        embed = cls._base(title=title, description=desc, emoji=emoji, color=color, **kwargs)
        if user:
            embed.set_thumbnail(url=user.display_avatar.url)

        return embed



    @classmethod
    def error(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Ошибка!", emoji=Emojis.ERROR, color=Colors.ERROR, **kwargs)

    @classmethod
    def warning(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Предупреждение!", emoji=Emojis.WARNING, color=Colors.WARNING, **kwargs)

    @classmethod
    def info(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Информация!", emoji=Emojis.UNKNOWN, color=Colors.INFO, **kwargs)
