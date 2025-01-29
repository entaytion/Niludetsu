from ..utils.logging import BaseLogger
from ..utils.emojis import EMOJIS
import discord
from typing import Optional, List
from discord.utils import format_dt

class RoleLogger(BaseLogger):
    """Логгер для ролей Discord."""
    
    async def log_role_create(self, role: discord.Role):
        """Логирование создания роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": role.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(role.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Цвет", "value": f"#{role.color.value:0>6x}" if role.color.value else "По умолчанию", "inline": True},
            {"name": f"{EMOJIS['DOT']} Отображается отдельно", "value": "Да" if role.hoist else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Упоминаемая", "value": "Да" if role.mentionable else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Позиция", "value": str(role.position), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Создана новая роль",
            description=f"Создана роль {role.mention}",
            color='GREEN',
            fields=fields,
            thumbnail_url=role.icon.url if role.icon else None
        )
        
    async def log_role_delete(self, role: discord.Role):
        """Логирование удаления роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Название", "value": role.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} ID", "value": str(role.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Цвет", "value": f"#{role.color.value:0>6x}" if role.color.value else "По умолчанию", "inline": True},
            {"name": f"{EMOJIS['DOT']} Позиция", "value": str(role.position), "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Роль удалена",
            description=f"Удалена роль {role.name}",
            color='RED',
            fields=fields,
            thumbnail_url=role.icon.url if role.icon else None
        )
        
    async def log_role_color_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения цвета роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Роль", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старый цвет", "value": f"#{before.color.value:0>6x}" if before.color.value else "По умолчанию", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новый цвет", "value": f"#{after.color.value:0>6x}" if after.color.value else "По умолчанию", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменен цвет роли",
            description=f"Обновлен цвет роли {after.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_hoist_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения отображения роли отдельно"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Роль", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое значение", "value": "Да" if before.hoist else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое значение", "value": "Да" if after.hoist else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено отображение роли",
            description=f"Обновлено отображение роли {after.mention} в списке участников",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_mentionable_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения возможности упоминания роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Роль", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое значение", "value": "Да" if before.mentionable else "Нет", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое значение", "value": "Да" if after.mentionable else "Нет", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена возможность упоминания",
            description=f"Обновлена возможность упоминания роли {after.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_name_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения названия роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} ID", "value": str(after.id), "inline": True},
            {"name": f"{EMOJIS['DOT']} Старое название", "value": before.name, "inline": True},
            {"name": f"{EMOJIS['DOT']} Новое название", "value": after.name, "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменено название роли",
            description=f"Роль переименована в {after.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_permissions_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения прав роли"""
        # Получаем разницу в правах
        added_perms = []
        removed_perms = []
        
        for perm, value in after.permissions:
            if getattr(before.permissions, perm) != value:
                if value:
                    added_perms.append(perm.replace('_', ' ').title())
                else:
                    removed_perms.append(perm.replace('_', ' ').title())
                    
        fields = [
            {"name": f"{EMOJIS['DOT']} Роль", "value": after.mention, "inline": False}
        ]
        
        if added_perms:
            fields.append({"name": f"{EMOJIS['DOT']} Добавлены права", "value": "\n".join(added_perms), "inline": True})
            
        if removed_perms:
            fields.append({"name": f"{EMOJIS['DOT']} Удалены права", "value": "\n".join(removed_perms), "inline": True})
            
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменены права роли",
            description=f"Обновлены права роли {after.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_icon_update(self, before: discord.Role, after: discord.Role):
        """Логирование изменения иконки роли"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Роль", "value": after.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Старая иконка", "value": "[Ссылка](" + before.icon.url + ")" if before.icon else "Отсутствует", "inline": True},
            {"name": f"{EMOJIS['DOT']} Новая иконка", "value": "[Ссылка](" + after.icon.url + ")" if after.icon else "Отсутствует", "inline": True}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Изменена иконка роли",
            description=f"Обновлена иконка роли {after.mention}",
            color='BLUE',
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None
        )
        
    async def log_role_update(self, before: discord.Role, after: discord.Role):
        """Общий метод для логирования изменений роли"""
        if before.name != after.name:
            await self.log_role_name_update(before, after)
        if before.color != after.color:
            await self.log_role_color_update(before, after)
        if before.hoist != after.hoist:
            await self.log_role_hoist_update(before, after)
        if before.mentionable != after.mentionable:
            await self.log_role_mentionable_update(before, after)
        if before.permissions != after.permissions:
            await self.log_role_permissions_update(before, after)
        if before.icon != after.icon:
            await self.log_role_icon_update(before, after) 