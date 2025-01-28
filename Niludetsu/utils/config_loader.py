import discord
from typing import Optional

class BotState:
    def __init__(self):
        self._initialized_systems = set()
        
    def is_initialized(self, system_name: str) -> bool:
        """Проверяет, была ли система уже инициализирована"""
        return system_name in self._initialized_systems
        
    def mark_initialized(self, system_name: str):
        """Отмечает систему как инициализированную"""
        self._initialized_systems.add(system_name)
        
    def reset(self):
        """Сбрасывает все флаги инициализации"""
        self._initialized_systems.clear()

class LoggingState:
    """Состояние системы логирования"""
    initialized: bool = False
    log_channel: Optional[discord.TextChannel] = None
    
    @classmethod
    def reset(cls):
        """Сброс состояния логирования"""
        cls.initialized = False
        cls.log_channel = None
        
    @classmethod
    def initialize(cls, channel: discord.TextChannel):
        """Инициализация состояния логирования"""
        cls.log_channel = channel
        cls.initialized = True
        print(f"✅ LoggingState инициализирован с каналом {channel.name}")

# Глобальный экземпляр для использования во всем приложении
bot_state = BotState() 