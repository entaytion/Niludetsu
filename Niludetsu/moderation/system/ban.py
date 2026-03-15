"""
Система бана с поддержкой софтбана (роль) и настоящего бана (Discord API).
"""
import discord
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.moderation.manager import ModerationManager
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Optional

_time = TimeService()

class BanSystem:
    """Система управления банами (софтбан через роль и настоящий бан)."""

    def __init__(self, bot):
        self.bot = bot
        self.mod_manager = ModerationManager(bot)

    async def ban(
        self,
        guild: discord.Guild,
        user: discord.Member,
        moderator: discord.Member,
        reason: str = "Не указана",
        duration: Optional[int] = None,  
        channel: Optional[discord.TextChannel] = None,
        real: bool = False
    ) -> Embed:
        """
        Выдаёт бан пользователю (софтбан или настоящий).

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        user : discord.Member
            Пользователь для бана
        moderator : discord.Member
            Модератор
        reason : str
            Причина бана
        duration : Optional[int]
            Длительность в минутах (уже распарсенная)
        channel : Optional[discord.TextChannel]
            Канал для логирования
        real : bool
            Если True - настоящий бан через Discord API
        """
        # НАСТОЯЩИЙ БАН (через Discord API)
        if real:
            try:
                # Используем guild.ban вместо user.ban для совместимости с discord.Object
                await guild.ban(
                    user,
                    reason=f"Модератор: {moderator} | Причина: {reason}",
                    delete_message_seconds=0
                )
                
                # Для discord.Object нет .mention, поэтому используем ID
                user_display = f"<@{user.id}>" if isinstance(user, discord.Object) else user.mention
                
                return Embed.success(title="Бан успешно выдан!",
                    description=f"{user_display} был забанен навсегда.\n**Причина:** {reason}"
                )
            except discord.Forbidden:
                raise ModerationError("У меня нет прав для бана этого пользователя.")
            except Exception as e:
                raise ModerationError(f"Ошибка при бане: {str(e)}")
                
        # Проверка на активный бан
        active_bans = await self.mod_manager.get_active_punishments(
            user_id=user.id,
            action_type=ActionType.BAN
        )

        if active_bans:
            ban = active_bans[0]
            expires_at = ban.get("expires_at")
            if expires_at:
                remaining_seconds, remaining_formatted = _time.format_remaining_time(expires_at)
                if remaining_seconds > 0:
                    raise ModerationError(
                        f"У пользователя уже есть активный бан до **{_time.format_datetime(expires_at)}** "
                        f"(осталось {remaining_formatted})"
                    )
            else:
                raise ModerationError("У пользователя уже есть постоянный бан!")

        result = await self.mod_manager.execute(
            action_type=ActionType.BAN,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            duration=duration,
            channel=channel
        )

        return result

    async def unban(
        self,
        guild: discord.Guild,
        user: discord.Member,
        moderator: discord.Member,
        reason: str = "Не указана",
        channel: Optional[discord.TextChannel] = None
    ) -> Embed:
        """
        Снимает бан с пользователя.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        user : discord.Member
            Пользователь для разбана
        moderator : discord.Member
            Модератор
        reason : str
            Причина разбана
        channel : Optional[discord.TextChannel]
            Канал для логирования
        """

        active_bans = await self.mod_manager.get_active_punishments(
            user_id=user.id,
            action_type=ActionType.BAN
        )

        if not active_bans:
            raise ModerationError("У пользователя нет активного бана!")

        punishment_rudiment = active_bans[0]["rudiment"]

        result = await self.mod_manager.execute(
            action_type=ActionType.UNBAN,
            guild=guild,
            target=user,
            moderator=moderator,
            reason=reason,
            channel=channel,
            punishment_rudiment=punishment_rudiment  
        )

        return result

