from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ProfileData:
    user_id: str
    name: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    birthday: Optional[str] = None
    balance: int = 0
    deposit: int = 0
    xp: int = 0
    level: int = 1
    voice_time: int = 0
    voice_joins: int = 0
    messages_count: int = 0
    roles: list = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []

    @property
    def total_balance(self) -> int:
        return self.balance + self.deposit

    @property
    def age(self) -> Optional[int]:
        """Вычислить возраст на основе даты рождения"""
        if not self.birthday:
            return None
            
        try:
            birth_date = datetime.strptime(self.birthday, "%d.%m.%Y")
            today = datetime.now()
            age = today.year - birth_date.year
            
            # Проверяем, был ли уже день рождения в этом году
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
                
            return age
        except ValueError:
            return None

    def calculate_next_level_xp(self) -> int:
        return 5 * (self.level ** 2) + 50 * self.level + 100

    def format_voice_time(self) -> str:
        hours = self.voice_time // 3600
        minutes = (self.voice_time % 3600) // 60
        return f"{hours}ч {minutes}м" 