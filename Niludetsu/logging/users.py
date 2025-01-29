from ..utils.logging import BaseLogger
from ..utils.emojis import EMOJIS
from ..utils.embed import create_embed
import discord
from typing import Optional, List
from datetime import datetime

class UserLogger(BaseLogger):
    """Логгер для пользователей Discord."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def log_user_name_update(self, before: discord.Member, after: discord.Member):
        """Логирование изменения никнейма пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старый никнейм", "value": before.display_name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый никнейм", "value": after.display_name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен никнейм пользователя",
            description=f"Пользователь изменил свой никнейм на сервере",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.display_avatar.url
        )
        
    async def log_user_roles_update(self, before: discord.Member, after: discord.Member):
        """Логирование изменения ролей пользователя"""
        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Добавлены роли", "value": ", ".join([role.mention for role in added_roles]) or "Нет", "inline": False},
            {"name": f"{EMOJIS['DOT']} Удалены роли", "value": ", ".join([role.mention for role in removed_roles]) or "Нет", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены роли пользователя",
            description=f"Обновлены роли пользователя на сервере",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.display_avatar.url
        )
        
    async def log_user_roles_add(self, member: discord.Member, role: discord.Role):
        """Логирование добавления роли пользователю"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Добавлена роль", "value": role.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Добавлена роль пользователю",
            description=f"Пользователю была выдана новая роль",
            color='GREEN',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_user_roles_remove(self, member: discord.Member, role: discord.Role):
        """Логирование удаления роли у пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Удалена роль", "value": role.mention, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Удалена роль у пользователя",
            description=f"У пользователя была удалена роль",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_user_avatar_update(self, before: discord.Member, after: discord.Member):
        """Логирование изменения аватара пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен аватар пользователя",
            description=f"Пользователь обновил свой аватар",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.display_avatar.url,
            image_url=before.display_avatar.url
        )
        
    async def log_user_timeout(self, member: discord.Member, until: datetime, reason: Optional[str] = None):
        """Логирование тайм-аута пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(member.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} До", "value": f"<t:{int(until.timestamp())}:F>", "inline": True},
            {"name": f"{EMOJIS['DOT']} Причина", "value": reason or "Не указана", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Пользователь получил тайм-аут",
            description=f"Пользователь был временно ограничен в правах",
            color='RED',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )
        
    async def log_user_timeout_remove(self, member: discord.Member):
        """Логирование снятия тайм-аута с пользователя"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": member.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(member.id), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Снят тайм-аут с пользователя",
            description=f"С пользователя были сняты временные ограничения",
            color='GREEN',
            fields=fields,
            thumbnail_url=member.display_avatar.url
        )

    async def log_member_update(self, before, after):
        """Логирование изменений участника"""
        # Игнорируем изменения статуса и активности
        if before.status != after.status or before.activities != after.activities:
            return

        changes = []

        # Проверяем изменение никнейма
        if before.nick != after.nick:
            changes.append(f"**Никнейм:** {before.nick or 'Нет'} ➜ {after.nick or 'Нет'}")

        # Проверяем изменение ролей
        if before.roles != after.roles:
            removed_roles = set(before.roles) - set(after.roles)
            added_roles = set(after.roles) - set(before.roles)

            if removed_roles:
                roles_text = ", ".join(role.mention for role in removed_roles)
                changes.append(f"**Удалены роли:** {roles_text}")

            if added_roles:
                roles_text = ", ".join(role.mention for role in added_roles)
                changes.append(f"**Добавлены роли:** {roles_text}")

        # Проверяем изменение таймаута
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                changes.append(f"**Таймаут до:** {after.timed_out_until.strftime('%d.%m.%Y %H:%M:%S')}")
            else:
                changes.append("**Таймаут снят**")

        # Если есть изменения, отправляем лог
        if changes:
            await self.log_event(
                title="👤 Обновление участника",
                description="\n".join(changes),
                color="BLUE",
                fields=[
                    {"name": "Пользователь", "value": after.mention, "inline": True},
                    {"name": "ID", "value": str(after.id), "inline": True}
                ],
                thumbnail_url=after.display_avatar.url
            ) 