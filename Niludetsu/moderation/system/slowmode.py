from ...tools.Embed import Embed
from ...tools.Time import TimeService
"""
Система управления медленным режимом (slowmode) в каналах.
"""
import discord

import Niludetsu.config as config
from Niludetsu.moderation.exceptions import ModerationError

from typing import List

_time = TimeService()

class SlowmodeSystem:
    """Система управления медленным режимом."""

    def __init__(self, bot):
        self.bot = bot

    async def set_slowmode(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channel: discord.TextChannel,
        duration: str,
        reason: str = "Не указана"
    ) -> Embed:
        """
        Устанавливает медленный режим в канале.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channel : discord.TextChannel
            Канал для установки slowmode
        duration : str
            Длительность (например: "10s", "1m", "1h", "0" или "off")
        reason : str
            Причина установки

        Returns
        -------
        Embed
            Результат операции
        """

        if duration == "0" or duration.lower() == "off":
            seconds = 0
            formatted = "отключен"
        else:
            seconds, formatted, error = _time.validate(
                duration,
                max_seconds=21600,  # Максимум 6 часов (ограничение Discord)
                min_seconds=0
            )
            if error:
                raise ModerationError(f"Ошибка в длительности: {error}")

            if seconds > 21600:
                raise ModerationError("Максимальная длительность медленного режима — 6 часов!")

        try:
            await channel.edit(
                slowmode_delay=seconds,
                reason=f"Медленный режим установлен {moderator} ({moderator.id}): {reason}"
            )
        except discord.Forbidden:
            raise ModerationError(f"У меня нет прав на управление каналом {channel.mention}!")
        except Exception as e:
            raise ModerationError(f"Ошибка при установке медленного режима: {str(e)}")

        if seconds == 0:
            description = f"{Emoji.SUCCESS} Медленный режим в канале {channel.mention} **отключен**"
        else:
            description = f"{Emoji.SUCCESS} Медленный режим в канале {channel.mention} установлен на **{formatted}**"
            if reason != "Не указана":
                description += f"**Причина:**\n```{reason}```"

        return Embed.success(description=description)

    async def set_slowmode_all(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        duration: str,
        reason: str = "Не указана"
    ) -> tuple[List[discord.TextChannel], List[discord.TextChannel]]:
        """
        Устанавливает медленный режим во всех текстовых каналах.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        duration : str
            Длительность
        reason : str
            Причина

        Returns
        -------
        tuple[List[discord.TextChannel], List[discord.TextChannel]]
            (успешные_каналы, неудачные_каналы)
        """

        if duration == "0" or duration.lower() == "off":
            seconds = 0
        else:
            seconds, formatted, error = _time.validate(
                duration,
                max_seconds=21600,
                min_seconds=0
            )
            if error:
                raise ModerationError(f"Ошибка в длительности: {error}")

            if seconds > 21600:
                raise ModerationError("Максимальная длительность медленного режима — 6 часов!")

        success_channels = []
        failed_channels = []

        for channel in guild.text_channels:
            try:
                if not channel.permissions_for(guild.me).manage_channels:
                    failed_channels.append(channel)
                    continue

                await channel.edit(
                    slowmode_delay=seconds,
                    reason=f"Медленный режим установлен {moderator} ({moderator.id}): {reason}"
                )
                success_channels.append(channel)

            except discord.Forbidden:
                failed_channels.append(channel)
            except Exception:
                failed_channels.append(channel)

        await self._log_slowmode_action(
            guild=guild,
            moderator=moderator,
            channels=success_channels,
            duration=duration,
            reason=reason,
            seconds=seconds
        )

        return success_channels, failed_channels

    async def _log_slowmode_action(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channels: List[discord.TextChannel],
        duration: str,
        reason: str,
        seconds: int
    ) -> None:
        """
        Логирует действие установки slowmode в канал модерации.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channels : List[discord.TextChannel]
            Список каналов
        duration : str
            Длительность (строка)
        reason : str
            Причина
        seconds : int
            Длительность в секундах
        """
        if not channels:
            return

        channels_str = ", ".join([ch.mention for ch in channels[:10]])  # Первые 10 каналов
        if len(channels) > 10:
            channels_str += f" и ещё {len(channels) - 10} каналов"

        if seconds == 0:
            action_text = "⏸️ Медленный режим отключён"
            duration_text = "отключен"
        else:
            action_text = "⏱️ Медленный режим установлен"
            duration_text = duration

        embed = Embed(
            title=action_text,
            description=(
                f"**Каналы:** {channels_str}\n"
                f"**Длительность:** {duration_text}\n"
                f"**Модератор:** {moderator.mention} ({moderator.id})\n"
                f"**Причина:** {reason}"
            ),
            color=0x77dd77 if seconds == 0 else 0xffa500
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        # Ищем канал для логов
        log_channel = None

        # Сначала пробуем NOTIFICATION_CHANNEL_ID из конфига
        if config.NOTIFICATION_CHANNEL_ID:
            log_channel = guild.get_channel(int(config.NOTIFICATION_CHANNEL_ID))

        # Если не нашли, ищем канал "mod-logs" или "модерация"
        if not log_channel:
            log_channel = discord.utils.get(
                guild.text_channels,
                name__in=["mod-logs", "модерация", "logs"]
            )

        # Отправляем лог
        if log_channel:
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass
            except Exception:
                pass

