"""
Система блокировки/разблокировки каналов.
"""
import discord
from Niludetsu.config import NOTIFICATION_CHANNEL_ID
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.tools.Embed import Embed
from typing import List, Optional, Tuple

class LockSystem:
    """Система управления блокировкой каналов."""

    def __init__(self, bot):
        self.bot = bot

    async def lock_channel(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channel: Optional[discord.TextChannel] = None,
        reason: str = "Не указана",
        for_all: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Блокирует канал(ы) для отправки сообщений.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channel : Optional[discord.TextChannel]
            Канал для блокировки (если None и for_all=False, не блокирует ничего)
        reason : str
            Причина блокировки
        for_all : bool
            Заблокировать все текстовые каналы

        Returns
        -------
        List[Tuple[int, int]]
            Список (channel_id, message_id) для сообщений-уведомлений
        """

        channels_to_lock = []

        if for_all:
            # Блокируем все текстовые каналы, где есть права
            channels_to_lock = [
                c for c in guild.text_channels
                if c.permissions_for(guild.me).manage_channels
            ]
            if not channels_to_lock:
                raise ModerationError("Нет доступных каналов для блокировки!")
        elif channel:
            # Блокируем конкретный канал
            if not channel.permissions_for(guild.me).manage_channels:
                raise ModerationError(f"У меня нет прав на управление каналом {channel.mention}!")
            channels_to_lock = [channel]
        else:
            raise ModerationError("Укажите канал или используйте флаг `--all` для блокировки всех каналов!")

        lock_message_ids = []
        everyone_role = guild.default_role

        for ch in channels_to_lock:
            try:
                # Убираем право отправки сообщений для @everyone
                await ch.set_permissions(
                    everyone_role,
                    send_messages=False,
                    reason=f"Канал заблокирован {moderator} ({moderator.id}): {reason}"
                )

                # Отправляем сообщение-уведомление
                lock_embed = Embed(
                    title="🔒 Канал заблокирован",
                    description=(
                        f"Этот канал был закрыт по решению модератора {moderator.mention}\n"
                        f"**Причина:**\n```{reason}```"
                    ),
                    color=0xff6b6b
                )
                lock_msg = await ch.send(embed=lock_embed)
                lock_message_ids.append((ch.id, lock_msg.id))

            except discord.Forbidden:
                # Пропускаем каналы без прав
                continue
            except Exception as e:
                print(f"Ошибка блокировки канала {ch.name}: {e}")
                continue

        await self._log_lock_action(
            guild=guild,
            moderator=moderator,
            channels=channels_to_lock,
            reason=reason,
            action="lock"
        )

        return lock_message_ids

    async def unlock_channel(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channel: Optional[discord.TextChannel] = None,
        reason: str = "Не указана",
        for_all: bool = False,
        lock_message_ids: Optional[List[Tuple[int, int]]] = None
    ) -> bool:
        """
        Разблокирует канал(ы) для отправки сообщений.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channel : Optional[discord.TextChannel]
            Канал для разблокировки
        reason : str
            Причина разблокировки
        for_all : bool
            Разблокировать все текстовые каналы
        lock_message_ids : Optional[List[Tuple[int, int]]]
            Список (channel_id, message_id) для удаления сообщений-уведомлений

        Returns
        -------
        bool
            True если успешно
        """

        channels_to_unlock = []

        if for_all:
            # Разблокируем все текстовые каналы
            channels_to_unlock = [
                c for c in guild.text_channels
                if c.permissions_for(guild.me).manage_channels
            ]
            if not channels_to_unlock:
                raise ModerationError("Нет доступных каналов для разблокировки!")
        elif channel:
            # Разблокируем конкретный канал
            if not channel.permissions_for(guild.me).manage_channels:
                raise ModerationError(f"У меня нет прав на управление каналом {channel.mention}!")
            channels_to_unlock = [channel]
        else:
            raise ModerationError("Укажите канал или используйте флаг `--all` для разблокировки всех каналов!")

        everyone_role = guild.default_role

        for ch in channels_to_unlock:
            try:
                # Восстанавливаем право отправки сообщений для @everyone
                await ch.set_permissions(
                    everyone_role,
                    send_messages=None,  # None = сбрасываем override
                    reason=f"Канал разблокирован {moderator} ({moderator.id}): {reason}"
                )
            except discord.Forbidden:
                continue
            except Exception as e:
                print(f"Ошибка разблокировки канала {ch.name}: {e}")
                continue

        if lock_message_ids:
            for ch_id, msg_id in lock_message_ids:
                ch = guild.get_channel(ch_id)
                if ch:
                    try:
                        msg = await ch.fetch_message(msg_id)
                        await msg.delete()
                    except discord.NotFound:
                        pass  # Сообщение уже удалено
                    except discord.Forbidden:
                        pass  # Нет прав на удаление
                    except Exception:
                        pass  # Игнорируем другие ошибки

        await self._log_lock_action(
            guild=guild,
            moderator=moderator,
            channels=channels_to_unlock,
            reason=reason,
            action="unlock"
        )

        return True

    async def _log_lock_action(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channels: List[discord.TextChannel],
        reason: str,
        action: str
    ) -> None:
        """
        Логирует действие блокировки/разблокировки в канал модерации.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channels : List[discord.TextChannel]
            Список каналов
        reason : str
            Причина
        action : str
            "lock" или "unlock"
        """
        channels_str = ", ".join([ch.mention for ch in channels])
        action_text = "🔒 Каналы заблокированы" if action == "lock" else "🔓 Каналы разблокированы"

        embed = Embed(
            title=action_text,
            description=(
                f"**Каналы:** {channels_str}\n"
                f"**Модератор:** {moderator.mention} ({moderator.id})\n"
                f"**Причина:** {reason}"
            ),
            color=0xff6b6b if action == "lock" else 0x77dd77
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        # Ищем канал для логов
        log_channel = None

        # Сначала пробуем NOTIFICATION_CHANNEL_ID из конфига
        if NOTIFICATION_CHANNEL_ID:
            log_channel = guild.get_channel(int(NOTIFICATION_CHANNEL_ID))

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
                pass  # Нет прав на отправку
            except Exception:
                pass  # Игнорируем ошибки

