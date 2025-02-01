import discord
from discord import app_commands
from functools import wraps
import yaml
from datetime import datetime, timedelta
from typing import Callable, Any

def load_config():
    """Загрузка конфигурации из файла"""
    with open('data/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def has_admin_role() -> Callable[[discord.Interaction], Any]:
    """Декоратор для проверки наличия роли администратора"""
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        admin_role_id = int(config['roles']['staff']['admin']['id'])
        return any(role.id == admin_role_id for role in interaction.user.roles)
    return app_commands.check(predicate)

def has_mod_role() -> Callable[[discord.Interaction], Any]:
    """Декоратор для проверки наличия роли модератора или выше"""
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        admin_role_id = int(config['roles']['staff']['admin']['id'])
        mod_role_id = int(config['roles']['staff']['moderator']['id'])
        user_roles = [role.id for role in interaction.user.roles]
        return any(role_id in user_roles for role_id in [admin_role_id, mod_role_id])
    return app_commands.check(predicate)

def has_helper_role() -> Callable[[discord.Interaction], Any]:
    """Декоратор для проверки наличия роли помощника или выше"""
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        admin_role_id = int(config['roles']['staff']['admin']['id'])
        mod_role_id = int(config['roles']['staff']['moderator']['id'])
        helper_role_id = int(config['roles']['staff']['helper']['id'])
        user_roles = [role.id for role in interaction.user.roles]
        return any(role_id in user_roles for role_id in [admin_role_id, mod_role_id, helper_role_id])
    return app_commands.check(predicate)

def command_cooldown() -> Callable[[discord.Interaction], Any]:
    """Декоратор для проверки кулдауна команды"""
    cooldowns = {}
    
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        
        # Получаем ID ролей из конфига
        admin_role_id = int(config['roles']['staff']['admin']['id'])
        mod_role_id = int(config['roles']['staff']['moderator']['id'])
        helper_role_id = int(config['roles']['staff']['helper']['id'])
        
        # Проверяем, есть ли у пользователя роли, освобождающие от кулдауна
        user_roles = [role.id for role in interaction.user.roles]
        if any(role_id in user_roles for role_id in [admin_role_id, mod_role_id, helper_role_id]):
            return True
            
        # Получаем время кулдауна из конфига
        cooldown_time = config.get('cooldowns', {}).get('default', 3)  # По умолчанию 3 секунды
        
        # Проверяем кулдаун
        user_id = interaction.user.id
        command_name = interaction.command.name
        
        key = f"{user_id}:{command_name}"
        if key in cooldowns:
            remaining = (cooldowns[key] + timedelta(seconds=cooldown_time)) - datetime.utcnow()
            if remaining.total_seconds() > 0:
                await interaction.response.send_message(
                    f"⏳ Подождите еще {int(remaining.total_seconds())} секунд перед использованием этой команды.",
                    ephemeral=True
                )
                return False
                
        cooldowns[key] = datetime.utcnow()
        return True
        
    return app_commands.check(predicate) 