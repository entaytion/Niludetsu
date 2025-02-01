import discord
from discord.ext import commands, tasks
from Niludetsu.database import Database
from datetime import datetime, timedelta
import traceback
import asyncio

class UserStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.voice_states = {}  # {user_id: join_time}
        asyncio.create_task(self._initialize())
        self.update_voice_time.start()

    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.db.init()

    def cog_unload(self):
        self.update_voice_time.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Увеличиваем счетчик сообщений
        user_id = str(message.author.id)
        user_data = await self.db.get_row("users", user_id=user_id)
        
        if user_data:
            messages_count = user_data.get('messages_count', 0) + 1
            await self.db.update(
                "users",
                where={"user_id": user_id},
                values={"messages_count": messages_count}
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Обработка изменений голосового состояния для статистики"""
        try:
            if member.bot:
                return

            user_id = str(member.id)
            now = datetime.utcnow()
            
            # Получаем или создаем запись пользователя
            user_data = await self.db.get_row("users", user_id=user_id)
            if not user_data:
                user_data = await self.db.insert("users", {
                    "user_id": user_id,
                    "voice_time": 0,
                    "voice_joins": 0,
                    "last_voice_join": None,
                    "messages_count": 0
                })

            # Если пользователь присоединился к голосовому каналу
            if not before.channel and after.channel:
                await self.db.update(
                    "users",
                    where={"user_id": user_id},
                    values={
                        "last_voice_join": now.isoformat(),
                        "voice_joins": (user_data.get("voice_joins", 0) or 0) + 1
                    }
                )

            # Если пользователь покинул голосовой канал
            elif before.channel and not after.channel:
                last_join = user_data.get("last_voice_join")
                if last_join:
                    try:
                        if isinstance(last_join, str):
                            last_join = datetime.fromisoformat(last_join)
                        duration = int((now - last_join).total_seconds())
                        await self.db.update(
                            "users",
                            where={"user_id": user_id},
                            values={
                                "voice_time": (user_data.get("voice_time", 0) or 0) + duration,
                                "last_voice_join": None
                            }
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Ошибка при обработке времени: {e}")

        except Exception as e:
            print(f"❌ Ошибка при обработке голосовой статистики: {e}")
            traceback.print_exc()

    @tasks.loop(minutes=5.0)
    async def update_voice_time(self):
        """Обновляет время в голосовых каналалах каждые 5 минут"""
        current_time = datetime.utcnow()
        
        for user_id, join_time in list(self.voice_states.items()):
            try:
                member = await self.bot.fetch_user(int(user_id))
                if not member:
                    continue
                    
                duration = int((current_time - join_time).total_seconds())
                user_data = await self.db.get_row("users", user_id=user_id)
                
                if user_data:
                    await self.db.update(
                        "users",
                        where={"user_id": user_id},
                        values={"voice_time": user_data.get('voice_time', 0) + duration}
                    )
                    
                # Обновляем время входа
                self.voice_states[user_id] = current_time
                
            except Exception as e:
                print(f"Error updating voice time for {user_id}: {e}")

    @update_voice_time.before_loop
    async def before_update_voice_time(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(UserStats(bot)) 