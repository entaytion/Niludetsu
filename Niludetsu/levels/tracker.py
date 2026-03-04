"""
Трекер уровней — начисляет опыт за активность
"""
import random
from Niludetsu.achievements.manager import AchievementsManager
from Niludetsu.levels.manager import LevelManager
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Dict, Optional

_time = TimeService()

class LevelTracker:
    """Отслеживает активность и начисляет опыт"""

    LEVEL_ACHIEVEMENTS = (
        "level_five",
        "level_ten",
        "level_twenty",
        "level_fifty",
    )

    VOICE_ACHIEVEMENTS = (
        "voice_hour",
        "voice_ten_hours",
        "voice_hundred_hours",
    )

    # Диапазон опыта за сообщение (рандом)
    XP_MESSAGE_MIN = 10
    XP_MESSAGE_MAX = 25

    # Опыт за голосовой канал (за минуту)
    XP_PER_VOICE_MINUTE = 5

    # Кулдаун между начислениями опыта (60 секунд)
    MESSAGE_COOLDOWN = 60

    # Исключённые категории (где XP не начисляется)
    EXCLUDED_CATEGORIES = [
        1363075274018914354,  # Партнёрки
    ]

    def __init__(self, main_guild_id: Optional[int] = None):
        self.manager = LevelManager()
        self.main_guild_id = main_guild_id

        # Кеш последних начислений {user_id: timestamp}
        self._message_cooldowns: Dict[str, any] = {}

        # Кеш уведомлений о повышении уровня {user_id: timestamp}
        self._notification_cooldowns: Dict[str, any] = {}

        self.achievements_manager = AchievementsManager()

    async def track_message_xp(
        self,
        guild_id: str,
        user_id: str,
        channel
    ) -> Optional[Dict]:
        """
        Начисляет опыт за сообщение (с кулдауном и рандомом)

        Args:
            guild_id: ID гильдии
            user_id: ID пользователя
            channel: Канал Discord

        Returns:
            Профиль и флаг leveled_up, если был повышен уровень
        """
        if self.main_guild_id and int(guild_id) != self.main_guild_id:
            return None

        if self._is_excluded_channel(channel):
            return None

        if not hasattr(channel, 'guild') or not channel.guild:
            return None

        now = _time.now()
        last_xp = self._message_cooldowns.get(user_id)

        if last_xp and (now - last_xp).total_seconds() < self.MESSAGE_COOLDOWN:
            return None

        self._message_cooldowns[user_id] = now

        xp_amount = random.randint(self.XP_MESSAGE_MIN, self.XP_MESSAGE_MAX)

        profile, leveled_up = await self.manager.add_experience(
            guild_id,
            user_id,
            xp_amount
        )

        if leveled_up:
            await self._send_levelup_notification(channel, user_id, profile["level"], is_voice=False)

            await self._check_level_achievements(guild_id, user_id, profile, channel)

        return {"profile": profile, "leveled_up": leveled_up}

    async def track_voice_xp(
        self,
        guild_id: str,
        user_id: str,
        minutes: int,
        channel
    ) -> Optional[Dict]:
        """
        Начисляет опыт за время в голосовом канале

        Args:
            guild_id: ID гильдии
            user_id: ID пользователя
            minutes: Количество минут в канале
            channel: Голосовой канал

        Returns:
            Профиль и флаг leveled_up, если был повышен уровень
        """
        if minutes <= 0:
            return None

        if self.main_guild_id and int(guild_id) != self.main_guild_id:
            return None

        xp_amount = minutes * self.XP_PER_VOICE_MINUTE
        profile, leveled_up = await self.manager.add_experience(
            guild_id,
            user_id,
            xp_amount
        )

        if leveled_up:
            await self._send_levelup_notification(channel, user_id, profile["level"], is_voice=True)

            await self._check_level_achievements(guild_id, user_id, profile, channel)

        await self._check_voice_achievements(guild_id, user_id, channel)

        return {"profile": profile, "leveled_up": leveled_up}

    def _is_excluded_channel(self, channel) -> bool:
        """
        Проверяет, исключён ли канал из начисления XP

        Args:
            channel: Канал Discord

        Returns:
            True если канал исключён
        """
        # ЛС всегда исключены
        if not hasattr(channel, 'guild') or not channel.guild:
            return True

        # Проверяем категорию канала
        if hasattr(channel, 'category') and channel.category:
            if channel.category.id in self.EXCLUDED_CATEGORIES:
                return True

        return False

    async def _send_levelup_notification(
        self,
        channel,
        user_id: str,
        new_level: int,
        is_voice: bool = False
    ):
        """
        Отправляет уведомление о повышении уровня

        Args:
            channel: Канал для отправки
            user_id: ID пользователя
            new_level: Новый уровень
            is_voice: True если повышение за голосовой канал
        """
        now = _time.now()
        last_notification = self._notification_cooldowns.get(user_id)

        if last_notification and (now - last_notification).total_seconds() < 60:
            return

        self._notification_cooldowns[user_id] = now

        if is_voice:
            description = (
                f"<@{user_id}>, у вас теперь **{new_level}** уровень за общение в голосовом канале!\n"
                "Продолжайте общение в голосовых каналах!"
            )
        else:
            description = (
                f"<@{user_id}>, у вас теперь **{new_level}** уровень!\n"
                "Продолжайте общение в чате!"
            )

        embed = Embed.default(description=description)

        try:
            if hasattr(channel, 'guild'):
                member = channel.guild.get_member(int(user_id))
                if member:
                    embed.set_thumbnail(url=member.display_avatar.url)
        except Exception:
            pass

        try:
            # Для голосовых каналов отправляем в специальный канал
            if is_voice and hasattr(channel, 'guild'):
                notification_channel_id = 1125546968517726228
                notification_channel = channel.guild.get_channel(notification_channel_id)
                if notification_channel:
                    await notification_channel.send(embed=embed)
                    return

            # Для текстовых каналов отправляем в тот же канал
            await channel.send(embed=embed)

        except Exception as e:
            print(f"[LevelTracker] Ошибка отправки уведомления: {e}")

    async def _check_level_achievements(
        self,
        guild_id: str,
        user_id: str,
        profile,
        channel
    ):
        """Проверяет и выдаёт достижения за достижение определённого уровня"""
        unlocked = await self.achievements_manager.evaluate_requirements(
            guild_id,
            user_id,
            channel=channel,
            profile=profile,
            achievement_ids=self.LEVEL_ACHIEVEMENTS,
        )

        if unlocked:
            print(
                f"🎯 [Achievements] user={user_id}, level={profile.get('level')}, unlocked={','.join(unlocked)}"
            )

    async def _check_voice_achievements(
        self,
        guild_id: str,
        user_id: str,
        channel
    ):
        """Проверяет и выдаёт достижения за время в голосовых каналах"""
        # Получаем статистику из analytics
        from Niludetsu.analytics.manager import AnalyticsManager
        analytics = AnalyticsManager()
        stats = await analytics.get_user_stats(guild_id, user_id)

        total_seconds = stats["voice"]["total_seconds"]
        total_hours = total_seconds / 3600

        unlocked = await self.achievements_manager.evaluate_requirements(
            guild_id,
            user_id,
            channel=channel,
            stats=stats,
            achievement_ids=self.VOICE_ACHIEVEMENTS,
        )

        if unlocked:
            print(
                f"🎯 [Achievements] user={user_id}, voice_hours={total_hours:.2f}, unlocked={','.join(unlocked)}"
            )

