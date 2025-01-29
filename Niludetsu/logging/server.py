from ..utils.logging import BaseLogger
from ..core.base import EMOJIS
import discord
from typing import Optional, List, Dict, Any
from discord.utils import format_dt

class ServerLogger(BaseLogger):
    """Логгер для сервера Discord."""
    
    # --- Модерация ---
    async def log_ban_add(self, guild: discord.Guild, user: discord.User, reason: Optional[str] = None):
        """Логирование бана пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": f"{user.mention} (`{user.id}`)", "inline": True},
            {"name": f"{EMOJIS['DOT']} Причина", "value": reason or "Не указана", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Пользователь забанен",
            description=f"Пользователь {user} был забанен на сервере",
            color='RED',
            fields=fields,
            thumbnail_url=user.display_avatar.url
        )
        
    async def log_ban_remove(self, guild: discord.Guild, user: discord.User):
        """Логирование разбана пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": f"{user.mention} (`{user.id}`)", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Пользователь разбанен",
            description=f"С пользователя {user} снят бан на сервере",
            color='GREEN',
            fields=fields,
            thumbnail_url=user.display_avatar.url
        )
        
    async def log_user_join(self, member: discord.Member):
        """Логирование присоединения пользователя"""
        account_age = discord.utils.utcnow() - member.created_at
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": f"{member.mention} (`{member.id}`)", "inline": True},
            {"name": f"{EMOJIS['DOT']} Создан", "value": format_dt(member.created_at), "inline": True},
            {"name": f"{EMOJIS['DOT']} Возраст аккаунта", "value": f"{account_age.days} дней", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Новый участник",
            description=f"Пользователь {member} присоединился к серверу",
            color='GREEN',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_user_leave(self, member: discord.Member):
        """Логирование выхода пользователя"""
        joined_at = format_dt(member.joined_at) if member.joined_at else "Неизвестно"
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": f"{member.mention} (`{member.id}`)", "inline": True},
            {"name": f"{EMOJIS['DOT']} Присоединился", "value": joined_at, "inline": True},
            {"name": f"{EMOJIS['DOT']} Роли", "value": ", ".join(role.mention for role in member.roles[1:]) or "Нет", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Участник покинул сервер",
            description=f"Пользователь {member} покинул сервер",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_user_kick(self, member: discord.Member, reason: Optional[str] = None):
        """Логирование кика пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": f"{member.mention} (`{member.id}`)", "inline": True},
            {"name": f"{EMOJIS['DOT']} Причина", "value": reason or "Не указана", "inline": True},
            {"name": f"{EMOJIS['DOT']} Роли", "value": ", ".join(role.mention for role in member.roles[1:]) or "Нет", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Участник кикнут",
            description=f"Пользователь {member} был кикнут с сервера",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_member_prune(self, guild: discord.Guild, days: int, pruned: int):
        """Логирование очистки неактивных участников"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Дней неактивности", "value": str(days), "inline": True},
            {"name": f"{EMOJIS['DOT']} Удалено участников", "value": str(pruned), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['WARNING']} Очистка участников",
            description=f"Проведена очистка неактивных участников",
            color='YELLOW',
            fields=fields
        )
        
    # --- Настройки сервера ---
    async def log_afk_channel_update(self, before: Optional[discord.VoiceChannel], after: Optional[discord.VoiceChannel]):
        """Логирование изменения AFK канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый канал", "value": before.mention if before else "Не установлен", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention if after else "Не установлен", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен AFK канал",
            description="Обновлен канал для AFK пользователей",
            color='BLUE',
            fields=fields
        )
        
    async def log_afk_timeout_update(self, before: int, after: int):
        """Логирование изменения времени до AFK"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старое значение", "value": f"{before} секунд", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое значение", "value": f"{after} секунд", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено время до AFK",
            description="Обновлено время неактивности до перемещения в AFK",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_banner_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения баннера сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Статус", "value": "Обновлен" if after else "Удален", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен баннер сервера",
            description="Обновлен баннер сервера",
            color='BLUE',
            fields=fields,
            image_url=after if after else None
        )
        
    async def log_message_notifications_update(self, before: discord.NotificationLevel, after: discord.NotificationLevel):
        """Логирование изменения настроек уведомлений"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старое значение", "value": str(before), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое значение", "value": str(after), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены настройки уведомлений",
            description="Обновлены настройки уведомлений по умолчанию",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_discovery_splash_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения баннера поиска сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Статус", "value": "Обновлен" if after else "Удален", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен баннер поиска",
            description="Обновлен баннер поиска сервера",
            color='BLUE',
            fields=fields,
            image_url=after if after else None
        )
        
    async def log_server_content_filter_update(self, before: discord.ContentFilter, after: discord.ContentFilter):
        """Логирование изменения фильтра контента"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый уровень", "value": str(before), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый уровень", "value": str(after), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен фильтр контента",
            description="Обновлен уровень фильтрации контента",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_features_update(self, before: List[str], after: List[str]):
        """Логирование изменения функций сервера"""
        added = set(after) - set(before)
        removed = set(before) - set(after)
        
        fields = []
        if added:
            fields.append({"name": f"{EMOJIS['DOT']} Добавлены функции", "value": "\n".join(added), "inline": True})
        if removed:
            fields.append({"name": f"{EMOJIS['DOT']} Удалены функции", "value": "\n".join(removed), "inline": True})
            
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены функции сервера",
            description="Обновлен список доступных функций сервера",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_icon_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения иконки сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Статус", "value": "Обновлена" if after else "Удалена", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена иконка сервера",
            description="Обновлена иконка сервера",
            color='BLUE',
            fields=fields,
            thumbnail_url=after if after else None
        )
        
    async def log_mfa_level_update(self, before: discord.MFALevel, after: discord.MFALevel):
        """Логирование изменения требований 2FA"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старое значение", "value": str(before), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое значение", "value": str(after), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены требования 2FA",
            description="Обновлены требования двухфакторной аутентификации для модерации",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_name_update(self, before: str, after: str):
        """Логирование изменения названия сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старое название", "value": before, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое название", "value": after, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено название сервера",
            description="Сервер был переименован",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_description_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения описания сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старое описание", "value": before or "Нет описания", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое описание", "value": after or "Нет описания", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено описание сервера",
            description="Обновлено описание сервера",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_owner_update(self, before: discord.Member, after: discord.Member):
        """Логирование изменения владельца сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый владелец", "value": before.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый владелец", "value": after.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['WARNING']} Изменен владелец сервера",
            description="Права владельца сервера были переданы",
            color='YELLOW',
            fields=fields
        )
        
    async def log_partnered_update(self, is_partnered: bool):
        """Логирование изменения статуса партнерства"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен статус партнерства",
            description=f"Сервер {'стал партнером' if is_partnered else 'больше не является партнером'} Discord",
            color='BLUE'
        )
        
    async def log_boost_level_update(self, before: int, after: int):
        """Логирование изменения уровня буста"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый уровень", "value": str(before), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый уровень", "value": str(after), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен уровень буста",
            description="Обновлен уровень буста сервера",
            color='BLUE',
            fields=fields
        )
        
    async def log_boost_progress_bar_update(self, enabled: bool):
        """Логирование изменения отображения прогресса буста"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено отображение прогресса буста",
            description=f"Прогресс буста {'теперь отображается' if enabled else 'больше не отображается'}",
            color='BLUE'
        )
        
    async def log_public_updates_channel_update(self, before: Optional[discord.TextChannel], after: Optional[discord.TextChannel]):
        """Логирование изменения канала публичных обновлений"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый канал", "value": before.mention if before else "Не установлен", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention if after else "Не установлен", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен канал публичных обновлений",
            description="Обновлен канал для публичных обновлений сервера",
            color='BLUE',
            fields=fields
        )
        
    async def log_rules_channel_update(self, before: Optional[discord.TextChannel], after: Optional[discord.TextChannel]):
        """Логирование изменения канала правил"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый канал", "value": before.mention if before else "Не установлен", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention if after else "Не установлен", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен канал правил",
            description="Обновлен канал с правилами сервера",
            color='BLUE',
            fields=fields
        )
        
    async def log_server_splash_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения сплэш-экрана сервера"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Статус", "value": "Обновлен" if after else "Удален", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен сплэш-экран",
            description="Обновлен сплэш-экран сервера",
            color='BLUE',
            fields=fields,
            image_url=after if after else None
        )
        
    async def log_system_channel_update(self, before: Optional[discord.TextChannel], after: Optional[discord.TextChannel]):
        """Логирование изменения системного канала"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый канал", "value": before.mention if before else "Не установлен", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый канал", "value": after.mention if after else "Не установлен", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен системный канал",
            description="Обновлен канал для системных сообщений",
            color='BLUE',
            fields=fields
        )
        
    async def log_vanity_url_update(self, before: Optional[str], after: Optional[str]):
        """Логирование изменения пользовательской ссылки"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старая ссылка", "value": f"discord.gg/{before}" if before else "Отсутствует", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новая ссылка", "value": f"discord.gg/{after}" if after else "Отсутствует", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена пользовательская ссылка",
            description="Обновлена пользовательская ссылка-приглашение",
            color='BLUE',
            fields=fields
        )
        
    async def log_verification_level_update(self, before: discord.VerificationLevel, after: discord.VerificationLevel):
        """Логирование изменения уровня проверки"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый уровень", "value": str(before), "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый уровень", "value": str(after), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен уровень проверки",
            description="Обновлен уровень проверки пользователей",
            color='BLUE',
            fields=fields
        )
        
    async def log_verified_update(self, is_verified: bool):
        """Логирование изменения статуса верификации"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен статус верификации",
            description=f"Сервер {'теперь верифицирован' if is_verified else 'больше не верифицирован'}",
            color='BLUE'
        )
        
    async def log_widget_update(self, enabled: bool):
        """Логирование изменения виджета сервера"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен виджет сервера",
            description=f"Виджет сервера {'включен' if enabled else 'выключен'}",
            color='BLUE'
        )
        
    async def log_preferred_locale_update(self, before: str, after: str):
        """Логирование изменения основного языка"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый язык", "value": before, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый язык", "value": after, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен основной язык",
            description="Обновлен основной язык сервера",
            color='BLUE',
            fields=fields
        )
        
    # --- Onboarding ---
    async def log_onboarding_toggle(self, enabled: bool):
        """Логирование включения/выключения онбординга"""
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен статус онбординга",
            description=f"Онбординг {'включен' if enabled else 'выключен'}",
            color='BLUE'
        )
        
    async def log_onboarding_channels_update(self, before: List[discord.abc.GuildChannel], after: List[discord.abc.GuildChannel]):
        """Логирование изменения каналов онбординга"""
        before_channels = ", ".join(channel.mention for channel in before) or "Нет"
        after_channels = ", ".join(channel.mention for channel in after) or "Нет"
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Старые каналы", "value": before_channels, "inline": False},
            {"name": f"{EMOJIS['DOT']} Новые каналы", "value": after_channels, "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены каналы онбординга",
            description="Обновлен список каналов для онбординга",
            color='BLUE',
            fields=fields
        )
        
    async def log_onboarding_question_add(self, question: Dict[str, Any]):
        """Логирование добавления вопроса онбординга"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Вопрос", "value": question.get('title', 'Неизвестно'), "inline": False},
            {"name": f"{EMOJIS['DOT']} Варианты ответов", "value": "\n".join(question.get('options', [])) or "Нет", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Добавлен вопрос онбординга",
            description="В онбординг добавлен новый вопрос",
            color='GREEN',
            fields=fields
        )
        
    async def log_onboarding_question_remove(self, question: Dict[str, Any]):
        """Логирование удаления вопроса онбординга"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Вопрос", "value": question.get('title', 'Неизвестно'), "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Удален вопрос онбординга",
            description="Из онбординга удален вопрос",
            color='RED',
            fields=fields
        )
        
    async def log_onboarding_question_update(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Логирование изменения вопроса онбординга"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Старый вопрос", "value": before.get('title', 'Неизвестно'), "inline": False},
            {"name": f"{EMOJIS['DOT']} Новый вопрос", "value": after.get('title', 'Неизвестно'), "inline": False},
            {"name": f"{EMOJIS['DOT']} Старые варианты", "value": "\n".join(before.get('options', [])) or "Нет", "inline": False},
            {"name": f"{EMOJIS['DOT']} Новые варианты", "value": "\n".join(after.get('options', [])) or "Нет", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен вопрос онбординга",
            description="Обновлен вопрос в онбординге",
            color='BLUE',
            fields=fields
        )
        
    async def log_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Логирование всех изменений сервера"""
        if before.name != after.name:
            await self.log_server_name_update(before.name, after.name)
            
        if before.description != after.description:
            await self.log_server_description_update(before.description, after.description)
            
        if before.icon != after.icon:
            await self.log_server_icon_update(
                before.icon.url if before.icon else None,
                after.icon.url if after.icon else None
            )
            
        if before.banner != after.banner:
            await self.log_server_banner_update(
                before.banner.url if before.banner else None,
                after.banner.url if after.banner else None
            )
            
        if before.features != after.features:
            await self.log_server_features_update(before.features, after.features)
            
        if before.mfa_level != after.mfa_level:
            await self.log_mfa_level_update(before.mfa_level, after.mfa_level)
            
        if before.default_notifications != after.default_notifications:
            await self.log_message_notifications_update(before.default_notifications, after.default_notifications)
            
        if before.explicit_content_filter != after.explicit_content_filter:
            await self.log_server_content_filter_update(before.explicit_content_filter, after.explicit_content_filter)
            
        if before.afk_channel != after.afk_channel:
            await self.log_afk_channel_update(before.afk_channel, after.afk_channel)
            
        if before.afk_timeout != after.afk_timeout:
            await self.log_afk_timeout_update(before.afk_timeout, after.afk_timeout) 