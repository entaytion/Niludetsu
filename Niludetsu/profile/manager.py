from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import ProfileData
from Niludetsu.database import Database

class ProfileManager:
    def __init__(self, database: Database):
        self.db = database

    async def get_profile(self, user_id: str) -> ProfileData:
        """Получить профиль пользователя"""
        user_data = await self.db.get_row("users", user_id=user_id)

        if not user_data:
            user_data = await self.db.insert("users", {
                'user_id': user_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'voice_time': 0,
                'voice_joins': 0,
                'messages_count': 0,
                'name': None,
                'country': None,
                'bio': None,
                'birthday': None
            })

        return ProfileData(
            user_id=user_id,
            name=user_data.get('name'),
            country=user_data.get('country'),
            bio=user_data.get('bio'),
            birthday=user_data.get('birthday'),
            balance=user_data.get('balance', 0),
            deposit=user_data.get('deposit', 0),
            xp=user_data.get('xp', 0),
            level=user_data.get('level', 1),
            voice_time=user_data.get('voice_time', 0),
            voice_joins=user_data.get('voice_joins', 0),
            messages_count=user_data.get('messages_count', 0),
            roles=user_data.get('roles', [])
        )

    async def update_profile(self, user_id: str, **kwargs) -> None:
        """Обновить профиль пользователя"""
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values=kwargs
        )

    async def clear_profile(self, user_id: str) -> None:
        """Очистить профиль пользователя"""
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "name": None,
                "country": None,
                "bio": None,
                "birthday": None
            }
        )

    async def check_birthdays(self) -> List[ProfileData]:
        """Проверить у кого сегодня день рождения"""
        today = datetime.now()
        today_str = today.strftime("%d.%m")
        
        # Получаем всех пользователей с днем рождения
        users = await self.db.fetch_all(
            "SELECT * FROM users WHERE birthday IS NOT NULL"
        )
        
        birthday_users = []
        for user_data in users:
            try:
                # Проверяем совпадает ли день и месяц
                if user_data['birthday']:
                    birth_date = datetime.strptime(user_data['birthday'], "%d.%m.%Y")
                    if birth_date.strftime("%d.%m") == today_str:
                        profile = ProfileData(
                            user_id=user_data['user_id'],
                            name=user_data.get('name'),
                            country=user_data.get('country'),
                            bio=user_data.get('bio'),
                            birthday=user_data.get('birthday'),
                            balance=user_data.get('balance', 0),
                            deposit=user_data.get('deposit', 0),
                            xp=user_data.get('xp', 0),
                            level=user_data.get('level', 1),
                            voice_time=user_data.get('voice_time', 0),
                            voice_joins=user_data.get('voice_joins', 0),
                            messages_count=user_data.get('messages_count', 0),
                            roles=user_data.get('roles', [])
                        )
                        birthday_users.append(profile)
            except (ValueError, TypeError):
                continue
                
        return birthday_users 