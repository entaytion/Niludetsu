import asyncio, random, re, discord
from typing import Optional, Dict, List, Union
from discord.ext import commands, tasks
from Niludetsu import Database, Embed, Emojis

class LevelSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()
        self.CATEGORY_ID = 1128436199204343828
        self.NOTIFICATION_CHANNEL_ID = 1125546970522583070
        self.ROLES = {
            5: {"remove": "1125344221986041902", "add": "1125344221986041903"},
            10: {"remove": ["1125344221986041902", "1125344221986041903"], "add": "1125344221986041904"},
            20: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904"], "add": "1125344221986041905"},
            30: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904", "1125344221986041905"], "add": "1125344222007005184"},
            50: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904", "1125344221986041905", "1125344222007005184"], "add": "1125344222007005186"},
        }
        self.emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        # Запускаем проверку голосовых каналов
        self.bot.loop.create_task(self._check_voice_channels_loop())

    def calculate_next_level_xp(self, level: int) -> int:
        """
        Рассчитывает количество опыта, необходимое для следующего уровня
        Args:
            level (int): Текущий уровень
        Returns:
            int: Количество опыта для следующего уровня
        """
        return 5 * (level ** 2) + 50 * level + 100
        
    async def _check_voice_channels_loop(self) -> None:
        """Бесконечный цикл проверки голосовых каналов"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self._check_voice_channels()
            await asyncio.sleep(120)

    async def _check_voice_channels(self) -> None:
        """Проверка пользователей в голосовых каналах и начисление опыта"""
        for guild in self.bot.guilds:
            text_channel = guild.get_channel(self.NOTIFICATION_CHANNEL_ID)
            if not text_channel:
                continue

            for voice_channel in guild.voice_channels:
                if voice_channel.category and voice_channel.category.id == self.CATEGORY_ID:
                    for member in voice_channel.members:
                        if member.bot:
                            continue
                        await self._process_voice_xp(member)

    async def _process_voice_xp(self, member: discord.Member) -> None:
        """
        Обработка опыта за голосовой канал
        Args:
            member (discord.Member): Участник для обработки
        """
        user_id = str(member.id)
        user = await self.db.get_row("users", user_id=user_id)
        if not user:
            user = await self.db.insert("users", {
                'user_id': user_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            })

        xp = user.get('xp', 0)
        level = user.get('level', 1)
        
        # Начисляем опыт за голосовой канал
        xp += 5

        # Проверяем повышение уровня
        await self._check_level_up(member, user_id, xp, level)

    async def _level_up_notification(self, member: discord.Member, level: int) -> None:
        """
        Отправка уведомления о повышении уровня
        Args:
            member (discord.Member): Участник, получивший новый уровень
            level (int): Новый уровень
        """
        notification_channel = member.guild.get_channel(self.NOTIFICATION_CHANNEL_ID)
        if not notification_channel:
            return

        embed=Embed(
            title=f"{Emojis.LEVELUP} Новый уровень!",
            description=f"🎉 Поздравляем, {member.mention}!\n"
                       f"Теперь у вас {level} уровень!",
            color="BLUE"
        )
        await notification_channel.send(embed=embed)

    async def _give_role_by_level(self, member: discord.Member, level: int) -> None:
        """
        Выдача ролей за уровень
        Args:
            member (discord.Member): Участник для выдачи роли
            level (int): Уровень участника
        """
        if level in self.ROLES:
            role_data = self.ROLES[level]
            
            # Удаление старых ролей
            role_remove = role_data["remove"]
            if isinstance(role_remove, list):
                for role_id in role_remove:
                    role = member.guild.get_role(int(role_id))
                    if role and role in member.roles:
                        await member.remove_roles(role)
            else:
                role = member.guild.get_role(int(role_remove))
                if role and role in member.roles:
                    await member.remove_roles(role)
            
            # Добавление новой роли
            role = member.guild.get_role(int(role_data["add"]))
            if role and role not in member.roles:
                await member.add_roles(role)

    async def _check_level_up(self, member: discord.Member, user_id: str, xp: int, level: int) -> None:
        """
        Проверка и обработка повышения уровня
        Args:
            member (discord.Member): Участник для проверки
            user_id (str): ID участника
            xp (int): Текущий опыт
            level (int): Текущий уровень
        """
        next_level_xp = self.calculate_next_level_xp(level)
        while xp >= next_level_xp:
            xp -= next_level_xp
            level += 1
            await self._level_up_notification(member, level)
            await self._give_role_by_level(member, level)
            next_level_xp = self.calculate_next_level_xp(level)

        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "xp": xp,
                "level": level
            }
        )

    async def process_message(self, message: discord.Message) -> None:
        """
        Обработка сообщения для начисления опыта
        Args:
            message (discord.Message): Сообщение для обработки
        """
        if message.author.bot or message.stickers:
            return

        # Проверка на сообщение только из эмодзи
        message_without_emoji = self.emoji_pattern.sub(r'', message.content)
        if message.content and not message_without_emoji.strip():
            return

        user_id = str(message.author.id)
        user = await self.db.ensure_user(user_id)

        xp = user.get('xp', 0)
        level = user.get('level', 1)

        # Начисляем опыт за сообщение
        if len(message.content) >= 7:
            xp_gain = min(len(message.content) // 7, 5)
            xp += xp_gain
            await self._check_level_up(message.author, user_id, xp, level) 