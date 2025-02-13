"""
Система модерации Niludetsu
Включает декораторы для проверки прав доступа и управления кулдаунами команд
"""

from .permissions import (
    ModPermissions,
    has_permission,
    cooldown,
    admin_only,
    mod_only,
    helper_only
)

__all__ = [
    # Основной класс
    'ModPermissions',
    
    # Декораторы проверки прав
    'has_permission',
    'admin_only',
    'mod_only',
    'helper_only',
    
    # Управление кулдаунами
    'cooldown'
] 