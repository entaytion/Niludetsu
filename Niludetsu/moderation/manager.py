"""
Единый менеджер для всех модерационных действий.
Заменяет actions.py, actiontype.py, punishments.py, expiresystem.py
"""
import discord
from discord.ext import tasks
from Niludetsu import database
from Niludetsu.config import NOTIFICATION_CHANNEL_ID, SERVERS
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.embed import moderationembed
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.tools.Time import TimeService
from typing import Optional, Dict, Any, List

_time = TimeService()

class ModerationManager:
    """
    Единый менеджер для работы с наказаниями.
    Использует новую таблицу user_rudiments.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.guild_id = str(SERVERS["MAIN_ID"])
        self._expire_task_started = False

    async def add_punishment(
        self,
        user_id: int,
        moderator_id: int,
        action_type: str,
        reason: str = "-",
        duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выдаёт наказание и сохраняет в БД.

        Args:
            user_id: ID пользователя
            moderator_id: ID модератора
            action_type: Тип наказания (warn, mute, ban)
            reason: Причина
            duration: Длительность в минутах (None = перманентно)
            metadata: Дополнительные данные (например, сохранённые роли)

        Returns:
            Dict с результатом операции
        """
        # Вычисляем expires_at
        expires_at = None
        if duration:
            expires_at = _time.add_duration(minutes=duration)
            expires_at = _time.to_iso(expires_at)

        # Генерируем rudiment (публичный ID)
        rudiment = await self._generate_rudiment(action_type)

        # Подготавливаем данные для вставки
        punishment_data = {
            "guild_id": self.guild_id,
            "user_id": str(user_id),
            "moderator_id": str(moderator_id),
            "type": action_type,
            "reason": reason,
            "duration": duration,
            "expires_at": expires_at,
            "metadata": metadata or {},
            "rudiment": rudiment,
            "active": True,
            "created_at": _time.now().to_iso8601_string()
        }

        # Сохраняем в БД
        punishment = await self.db.insert("user_rudiments", punishment_data)

        if not punishment:
            return {"success": False, "error": "Не удалось создать запись о наказании"}

        # Применяем Discord-действие
        await self._apply_discord_action(user_id, action_type, reason, duration, metadata)

        return {
            "success": True,
            "rudiment": rudiment,
            "expires_at": expires_at,
            "punishment": punishment
        }

    async def remove_punishment(
        self,
        user_id: int,
        action_type: str,
        rudiment: Optional[str] = None,
        moderator_id: Optional[int] = None,
        reason: str = "Снято модератором"
    ) -> Dict[str, Any]:
        """Снимает наказание (деактивирует существующую запись)."""

        # Если указан rudiment, ищем по нему
        if rudiment:
            filters = [
                {"column": "guild_id", "value": self.guild_id},
                {"column": "user_id", "value": str(user_id)},
                {"column": "rudiment", "value": rudiment},
                {"column": "type", "value": action_type},
                {"column": "active", "value": True}
            ]
        else:
            # Иначе ищем последнее активное наказание этого типа
            filters = [
                {"column": "guild_id", "value": self.guild_id},
                {"column": "user_id", "value": str(user_id)},
                {"column": "type", "value": action_type},
                {"column": "active", "value": True}
            ]

        rows = await self.db.where(
            "user_rudiments",
            filters=filters,
            order=[{"column": "id", "ascending": False}],
            limit=1
        )

        if not rows:
            return {"success": False, "error": "Наказание не найдено или уже неактивно"}

        punishment = rows[0]
        rudiment = punishment["rudiment"]                
        await self.db.update_record(
            "user_rudiments",
            {"id": punishment["id"]},
            {"active": False}
        )

        # Снимаем Discord-действие
        await self._remove_discord_action(user_id, action_type, punishment.get("metadata"))

        return {
            "success": True,
            "rudiment": rudiment,
            "punishment": punishment
        }

    async def get_active_punishments(
        self,
        user_id: int,
        action_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает активные наказания пользователя.

        Args:
            user_id: ID пользователя
            action_type: Тип наказания (если None — все типы)

        Returns:
            Список наказаний
        """
        filters = [
            {"column": "guild_id", "value": self.guild_id},
            {"column": "user_id", "value": str(user_id)},
            {"column": "active", "value": True}
        ]

        if action_type:
            filters.append({"column": "type", "value": action_type})

        return await self.db.where(
            "user_rudiments",
            filters=filters,
            order=[{"column": "created_at", "ascending": False}]
        )
    async def get_all_punishments(
        self,
        user_id: int,
        action_type: Optional[str] = None,
        include_inactive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получает все наказания пользователя (включая неактивные).

        Args:
            user_id: ID пользователя
            action_type: Тип наказания (если None — все типы)
            include_inactive: Включать ли неактивные наказания

        Returns:
            Список наказаний
        """
        filters = [
            {"column": "guild_id", "value": self.guild_id},
            {"column": "user_id", "value": str(user_id)}
        ]

        if action_type:
            filters.append({"column": "type", "value": action_type})

        if not include_inactive:
            filters.append({"column": "active", "value": True})

        return await self.db.where(
            "user_rudiments",
            filters=filters,
            order=[{"column": "created_at", "ascending": False}]
        )

    async def get_punishment_by_rudiment(self, rudiment: str) -> Optional[Dict[str, Any]]:
        """Получает наказание по публичному ID"""
        rows = await self.db.where(
            "user_rudiments",
            filters=[
                {"column": "guild_id", "value": self.guild_id},
                {"column": "rudiment", "value": rudiment}
            ],
            limit=1
        )
        return rows[0] if rows else None

    # УНИВЕРСАЛЬНЫЙ МЕТОД EXECUTE (для обратной совместимости)

    async def execute(
        self,
        action_type: str,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member,
        reason: str,
        duration: Optional[int] = None,
        channel: Optional[discord.TextChannel] = None,
        punishment_rudiment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Выполняет модераторское действие."""

        from Niludetsu.moderation.checks import check_moderation_target

        allow_bots = action_type in [ActionType.BAN, ActionType.UNBAN]

        can_moderate, error_msg = check_moderation_target(
            moderator=moderator,
            target=target,
            allow_bots_for_admin=allow_bots
        )

        if not can_moderate:
            raise ModerationError(error_msg)

        is_removal = action_type.lower().startswith("un")
        base_type = action_type[2:] if is_removal else action_type

        if metadata is None:
            metadata = {}

        # Выполняем действие
        if is_removal:
            result = await self.remove_punishment(
                user_id=target.id,
                action_type=base_type,
                rudiment=punishment_rudiment,
                moderator_id=moderator.id,
                reason=reason
            )
        else:
            result = await self.add_punishment(
                user_id=target.id,
                moderator_id=moderator.id,
                action_type=base_type,
                reason=reason,
                duration=duration,
                metadata=metadata
            )

        if not result.get("success"):
            raise ModerationError(result.get("error", "Неизвестная ошибка при выполнении действия"))

        rudiment = result.get("rudiment")

        # Эмбед для канала
        embed = moderationembed(
            punishment_type=base_type,
            target_user=target,
            moderator=moderator,
            punishment_id=rudiment,
            reason=reason,
            duration_minutes=duration,
            mode='channel',
            is_removal=is_removal
        )

        # Дублируем в канал уведомлений
        notification_message = None
        try:
            notification_channel = guild.get_channel(NOTIFICATION_CHANNEL_ID)
            if notification_channel:
                notification_message = await notification_channel.send(embed=embed)
        except Exception as e:
            print(f"[ModManager] Не удалось отправить в канал уведомлений: {e}")

        # Отправляем в ЛС
        dm_sent = False
        try:
            dm_embed = moderationembed(
                punishment_type=base_type,
                target_user=target,
                moderator=moderator,
                punishment_id=rudiment,
                reason=reason,
                duration_minutes=duration,
                mode='dm',
                is_removal=is_removal
            )
            await target.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[ModManager] Не удалось отправить в ЛС: {e}")

        return {
            "success": True,
            "embed": embed,
            "dm_sent": dm_sent,
            "notification_message": notification_message,
            "result": result,
            "punishment_id": rudiment
        }

    # СИСТЕМА ИСТЕЧЕНИЯ НАКАЗАНИЙ (бывший expiresystem.py)

    def start_expire_system(self):
        """Запускает фоновую задачу проверки истёкших наказаний"""
        if not self._expire_task_started:
            self.check_expired_punishments_task.start()
            self._expire_task_started = True

    def stop_expire_system(self):
        """Останавливает фоновую задачу"""
        if self._expire_task_started:
            self.check_expired_punishments_task.cancel()
            self._expire_task_started = False

    @tasks.loop(seconds=30)
    async def check_expired_punishments_task(self):
        """Фоновая задача проверки истёкших наказаний"""
        await self.check_expired_punishments()

    @check_expired_punishments_task.before_loop
    async def before_check_expired_punishments(self):
        """Ждём готовности бота перед запуском задачи"""
        await self.bot.wait_until_ready()

    async def check_expired_punishments(self):
        """Проверяет и обрабатывает истёкшие наказания"""
        rows = await self.db.where(
            "user_rudiments",
            filters=[
                {"column": "active", "value": True}
            ]
        )

        if not rows:
            return

        # Фильтруем только те, у которых есть expires_at и срок истёк
        expired_punishments = []
        for punishment in rows:
            expires_at = punishment.get('expires_at')
            # Проверяем: есть expires_at И время истекло
            if expires_at and _time.is_time_passed(expires_at):
                expired_punishments.append(punishment)

        # Обрабатываем каждое истёкшее наказание
        for punishment in expired_punishments:
            await self._expire_punishment(punishment)

    async def _expire_punishment(self, punishment: Dict[str, Any]):
        """
        Обрабатывает истёкшее наказание.

        Args:
            punishment: Данные наказания из БД
        """
        user_id = int(punishment['user_id'])
        action_type = punishment['type']
        rudiment = punishment.get('rudiment')

        # Снимаем наказание
        result = await self.remove_punishment(
            user_id,
            action_type,
            rudiment,
            self.bot.user.id,
            "Автоматическое снятие по истечении срока"
        )

        if not result.get('success'):
            print(f"[ExpireSystem] Не удалось снять наказание {rudiment}: {result.get('error')}")
            return

        # Получаем объекты Discord
        guild = self.bot.get_guild(SERVERS["MAIN_ID"])
        if not guild:
            return

        member = guild.get_member(user_id)
        if not member:
            return

        bot_member = guild.get_member(self.bot.user.id)

        # Определяем тип для эмбеда
        action_name_map = {
            ActionType.WARN: "warn",
            ActionType.MUTE: "mute",
            ActionType.BAN: "ban"
        }
        action_name = action_name_map.get(action_type, "warn")

        # Создаём эмбед для истечения
        embed = moderationembed(
            punishment_type=action_name,
            target_user=member,
            moderator=bot_member,
            punishment_id=rudiment,
            reason="Истёк срок",
            mode='channel',
            is_removal=True
        )

        # Отправляем в канал модерации
        try:
            mod_channel = guild.get_channel(NOTIFICATION_CHANNEL_ID)
            if mod_channel:
                await mod_channel.send(embed=embed)
        except Exception as e:
            print(f"[ExpireSystem] Не удалось отправить лог истечения: {e}")

        # Отправляем уведомление в ЛС пользователю
        try:
            dm_embed = moderationembed(
                punishment_type=action_name,
                target_user=member,
                moderator=bot_member,
                punishment_id=rudiment,
                reason="Истёк срок",
                mode='dm',
                is_removal=True
            )
            await member.send(embed=dm_embed)
            print(f"[ExpireSystem] Отправлено уведомление в ЛС пользователю {member} о снятии {action_name}")
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[ExpireSystem] Не удалось отправить ЛС пользователю {member}: {e}")

    async def _generate_rudiment(self, action_type: str) -> str:
        """
        Генерирует публичный ID для наказания.

        Формат: просто числа (1, 2, 3...) для всех типов наказаний.

        Args:
            action_type: Тип наказания (не используется, оставлен для совместимости)

        Returns:
            Публичный ID (rudiment)
        """
        rows = await self.db.where(
            "user_rudiments",
            filters=[
                {"column": "guild_id", "value": self.guild_id}
            ],
            order=[{"column": "id", "ascending": False}],
            limit=1
        )

        if rows and rows[0].get("rudiment"):
            try:
                # Пытаемся распарсить число из rudiment
                last_rudiment = rows[0]["rudiment"]

                # Если есть префикс (M-1, B-2), берём число после дефиса
                if "-" in last_rudiment:
                    last_id = int(last_rudiment.split("-")[1])
                else:
                    last_id = int(last_rudiment)

                return str(last_id + 1)
            except (ValueError, IndexError):
                pass

        return "1"

    async def _apply_discord_action(
        self,
        user_id: int,
        action_type: str,
        reason: str,
        duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Применяет действие в Discord (мут через timeout / бан через роль)."""
        guild = self.bot.get_guild(SERVERS["MAIN_ID"])
        if not guild:
            return

        member = guild.get_member(user_id)
        if not member:
            return

        if action_type == ActionType.MUTE:
            # Используем Discord timeout вместо роли
            if duration:
                timeout_until = _time.add_duration(minutes=duration)
                await member.timeout(timeout_until.in_timezone("UTC"), reason=reason)
            else:
                # Максимальный timeout Discord — 28 дней
                max_timeout = _time.add_duration(days=28)
                await member.timeout(max_timeout.in_timezone("UTC"), reason=reason)

        elif action_type == ActionType.BAN:
            from Niludetsu.config import BAN_ROLE_ID
            ban_role = guild.get_role(BAN_ROLE_ID)

            if not ban_role:
                print(f"[ModManager] Роль бана {BAN_ROLE_ID} не найдена на сервере!")
                return

            # Сохраняем роли в metadata
            if not metadata or "roles" not in metadata:
                roles_to_save = [r.id for r in member.roles if r != guild.default_role]
                if roles_to_save:
                    await self.db.update_record(
                        "user_rudiments",
                        {"user_id": str(user_id), "type": action_type, "active": True},
                        {"metadata": {"roles": roles_to_save}},
                        json_fields=["metadata"]
                    )

            # Снимаем все роли кроме @everyone
            roles_to_remove = [r for r in member.roles if r != guild.default_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Бан: {reason}")

            # Выдаём роль бана
            if ban_role not in member.roles:
                await member.add_roles(ban_role, reason=f"Бан: {reason}")

    async def _remove_discord_action(
        self,
        user_id: int,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Снимает действие в Discord (размут / разбан)."""
        guild = self.bot.get_guild(SERVERS["MAIN_ID"])
        if not guild:
            return

        member = guild.get_member(user_id)
        if not member:
            return

        if action_type == ActionType.MUTE:
            # Снимаем Discord timeout
            if member.timed_out_until:
                await member.timeout(None, reason="Снятие мута")

        elif action_type == ActionType.BAN:
            from Niludetsu.config import BAN_ROLE_ID
            ban_role = guild.get_role(BAN_ROLE_ID)

            if ban_role and ban_role in member.roles:
                await member.remove_roles(ban_role, reason="Снятие бана")

            # Восстанавливаем роли из metadata
            if metadata and "roles" in metadata:
                roles_to_restore = [guild.get_role(rid) for rid in metadata["roles"]]
                roles_to_restore = [r for r in roles_to_restore if r is not None]
                if roles_to_restore:
                    await member.add_roles(*roles_to_restore, reason="Восстановление ролей после снятия бана")

