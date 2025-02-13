import discord
from typing import Optional

class BotState:
    _initialized_systems = set()
    
    @classmethod
    def is_initialized(cls, system_name: str) -> bool:
        """Проверяет, была ли система уже инициализирована"""
        return system_name in cls._initialized_systems
        
    @classmethod
    def mark_initialized(cls, system_name: str):
        """Отмечает систему как инициализированную"""
        cls._initialized_systems.add(system_name)
        
    @classmethod
    def reset(cls):
        """Сбрасывает все флаги инициализации"""
        cls._initialized_systems.clear()

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