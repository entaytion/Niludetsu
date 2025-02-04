import discord
from discord.ext import commands
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
import asyncio

POSITIVE_TRIGGERS = ['плюс', 'согл', 'спс', 'спасибо', 'сяп', 'сенкс', 'thanks', 'thx', '👍', '❤️']
NEGATIVE_TRIGGERS = ['минус', 'не согл', 'нет', 'неа', '👎'] 

class Reputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self._initialize())
        
    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.db.init()
        await self.initialize_reputation_column()
        
    async def initialize_reputation_column(self):
        """Инициализация колонки репутации"""
        # Проверяем наличие колонки reputation
        result = await self.db.fetch_all("PRAGMA table_info(users)")
        if not result:
            return
            
        columns = [row['name'] for row in result]
        if 'reputation' not in columns:
            await self.db.execute('ALTER TABLE users ADD COLUMN reputation INTEGER DEFAULT 0')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.reference:
            return

        try:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == message.author:
                await message.channel.send("Вы не можете изменять свою репутацию!")
                return
                
            if referenced_message.author.bot:
                await message.channel.send("Ботам нельзя повышать репутацию!")
                return

            content = message.content.lower()
            
            # Проверка на + или -
            is_positive = any(trigger in content for trigger in POSITIVE_TRIGGERS) or content.strip('+').strip() == ''
            is_negative = any(trigger in content for trigger in NEGATIVE_TRIGGERS) or content.strip('-').strip() == ''

            if not is_positive and not is_negative:
                return

            # Получаем данные пользователя
            target_user_id = str(referenced_message.author.id)
            user_data = await self.db.get_row("users", user_id=target_user_id)
            
            if user_data is None:
                # Создаем запись для пользователя если её нет
                user_data = await self.db.insert("users", {
                    'user_id': target_user_id,
                    'reputation': 0,
                    'balance': 0,
                    'deposit': 0,
                    'xp': 0,
                    'level': 1
                })
            
            # Обновляем репутацию
            if is_positive:
                await self.db.execute(
                    "UPDATE users SET reputation = reputation + 1 WHERE user_id = ?",
                    str(target_user_id)
                )
                await message.add_reaction('⬆️')
                
                result = await self.db.fetch_one(
                    "SELECT reputation FROM users WHERE user_id = ?", 
                    str(target_user_id)
                )
                new_rep = result['reputation'] if result else 0
                
                embed=Embed(
                    description=f"{message.author.mention} повысил репутацию {referenced_message.author.mention}\nРепутация: {new_rep}",
                    image_url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6ZWF1Y2E3OGE4MWF2NmF1NXJ5Y2RxbWF4Z2t0bG95aWsyeGpmbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dMsh6gRYJDymXSIatd/giphy.gif"
                )
            elif is_negative:
                await self.db.execute(
                    "UPDATE users SET reputation = reputation - 1 WHERE user_id = ?",
                    str(target_user_id)
                )
                await message.add_reaction('⬇️')
                
                result = await self.db.fetch_one(
                    "SELECT reputation FROM users WHERE user_id = ?",
                    str(target_user_id)
                )
                new_rep = result['reputation'] if result else 0
                
                embed=Embed(
                    description=f"{message.author.mention} понизил репутацию {referenced_message.author.mention}\nРепутация: {new_rep}",
                    image_url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmZ5ZWN0Y2RqbWd2bXd1NXBxYnBxaWQ2aHdqbDV1ZWx1ZWxqd2JxdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oEjHAUOqG3lSS0f1C/giphy.gif"
                )
                
            await message.channel.send(embed=embed)

        except Exception as e:
            print(f"Error in reputation system: {e}")

async def setup(bot):
    await bot.add_cog(Reputation(bot))