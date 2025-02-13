"""
Модуль для проверки прав доступа к модераторским командам
"""
import discord
from discord import app_commands
from functools import wraps
from typing import Callable, Any, Optional, List, Union
from datetime import datetime, timedelta
from ..database.db import Database
from ..database.tables import Tables

class ModPermissions:
    """Класс для работы с правами модерации"""
    
    def __init__(self, db: Database):
        self.db = db
        
    async def _get_staff_roles(self, guild_id: str) -> dict:
        """Получение ролей персонала из базы данных"""
        roles = {}
        async for role in await self.db.get_rows(Tables.SETTINGS, category="roles", guild_id=guild_id):
            if role["key"].startswith("staff."):
                role_name = role["key"].split(".")[1]
                roles[role_name] = {"id": role["value"]}
        return roles
        
    @staticmethod
    def _has_any_role(member_roles: List[int], required_roles: List[int]) -> bool:
        """Проверка наличия хотя бы одной роли из списка"""
        return any(role_id in member_roles for role_id in required_roles)
        
    async def check_cooldown(
        self,
        user_id: Union[str, int],
        guild_id: Union[str, int],
        command: str,
        cooldown_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Проверка кулдауна команды
        
        Args:
            user_id: ID пользователя
            guild_id: ID сервера
            command: Название команды
            cooldown_seconds: Время кулдауна в секундах
            
        Returns:
            tuple[bool, Optional[int]]: (можно_использовать, оставшееся_время)
        """
        current_time = datetime.utcnow()
        
        # Проверяем существующий кулдаун
        cooldown = await self.db.get_row(
            Tables.COOLDOWNS,
            user_id=str(user_id),
            guild_id=str(guild_id),
            command=command
        )
        
        if cooldown:
            expires_at = datetime.fromisoformat(cooldown["expires_at"])
            if current_time < expires_at:
                remaining = int((expires_at - current_time).total_seconds())
                return False, remaining
                
            # Удаляем истекший кулдаун
            await self.db.execute(
                f"DELETE FROM {Tables.COOLDOWNS} WHERE id = ?",
                (cooldown["id"],)
            )
        
        # Создаем новый кулдаун
        expires_at = current_time + timedelta(seconds=cooldown_seconds)
        await self.db.insert(
            Tables.COOLDOWNS,
            {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "command": command,
                "expires_at": expires_at.isoformat()
            }
        )
        return True, None

def has_permission(*required_roles: str) -> Callable[[discord.Interaction], Any]:
    """
    Декоратор для проверки прав доступа к командам
    
    Args:
        *required_roles: Список требуемых ролей ('admin', 'moderator', 'helper')
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        db = Database()  # В реальном коде нужно передавать существующий экземпляр
        await db.init()
        
        mod_perms = ModPermissions(db)
        staff_roles = await mod_perms._get_staff_roles(str(interaction.guild_id))
        required_role_ids = []
        
        for role_name in required_roles:
            if role_name in staff_roles:
                role_id = int(staff_roles[role_name]["id"])
                required_role_ids.append(role_id)
        
        if not required_role_ids:
            return False
            
        member_role_ids = [role.id for role in interaction.user.roles]
        has_permission = mod_perms._has_any_role(member_role_ids, required_role_ids)
        
        if not has_permission:
            await interaction.response.send_message(
                "❌ У вас недостаточно прав для использования этой команды.",
                ephemeral=True
            )
            return False
            
        return True
        
    return app_commands.check(predicate)

def cooldown(seconds: int = 3):
    """
    Декоратор для установки кулдауна на команду
    
    Args:
        seconds: Время кулдауна в секундах
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            db = Database()  # В реальном коде нужно передавать существующий экземпляр
            await db.init()
            
            mod_perms = ModPermissions(db)
            
            # Проверяем, есть ли у пользователя роли, освобождающие от кулдауна
            staff_roles = await mod_perms._get_staff_roles(str(interaction.guild_id))
            user_roles = [role.id for role in interaction.user.roles]
            
            admin_role = staff_roles.get("admin", {}).get("id")
            mod_role = staff_roles.get("moderator", {}).get("id")
            
            if admin_role and mod_role:
                if mod_perms._has_any_role(user_roles, [int(admin_role), int(mod_role)]):
                    return await func(interaction, *args, **kwargs)
            
            # Проверяем кулдаун
            can_use, remaining = await mod_perms.check_cooldown(
                interaction.user.id,
                interaction.guild_id,
                interaction.command.name,
                seconds
            )
            
            if not can_use:
                await interaction.response.send_message(
                    f"⏳ Подождите еще {remaining} секунд перед использованием этой команды.",
                    ephemeral=True
                )
                return False
            
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

# Предопределенные декораторы для удобства
def admin_only() -> Callable[[discord.Interaction], Any]:
    """Декоратор для команд, требующих права администратора"""
    return has_permission("admin")

def mod_only() -> Callable[[discord.Interaction], Any]:
    """Декоратор для команд, требующих права модератора или выше"""
    return has_permission("admin", "moderator")

def helper_only() -> Callable[[discord.Interaction], Any]:
    """Декоратор для команд, требующих права помощника или выше"""
    return has_permission("admin", "moderator", "helper") 