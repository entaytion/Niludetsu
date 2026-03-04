"""
Исключения для системы модерации
"""

class ModerationError(Exception):
    """
    Базовое исключение для ошибок модерации.
    Используется для предотвращения применения кулдауна при ошибках.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)