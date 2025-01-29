import discord
from discord.ext import commands, tasks
from Niludetsu.utils.database import get_user, save_user
from datetime import datetime, timedelta

class UserStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}  # {user_id: join_time}
        self.update_voice_time.start()

    def cog_unload(self):
        self.update_voice_time.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Увеличиваем счетчик сообщений
        user_id = str(message.author.id)
        user_data = get_user(user_id)
        
        if user_data:
            user_data['messages_count'] = user_data.get('messages_count', 0) + 1
            save_user(user_id, user_data)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = str(member.id)
        
        # Пользователь присоединился к голосовому каналу
        if before.channel is None and after.channel is not None:
            self.voice_states[user_id] = datetime.utcnow()
            
        # Пользователь покинул голосовой канал
        elif before.channel is not None and after.channel is None:
            join_time = self.voice_states.pop(user_id, None)
            if join_time:
                duration = int((datetime.utcnow() - join_time).total_seconds())
                user_data = get_user(user_id)
                if user_data:
                    user_data['voice_time'] = user_data.get('voice_time', 0) + duration
                    save_user(user_id, user_data)

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
                user_data = get_user(user_id)
                
                if user_data:
                    user_data['voice_time'] = user_data.get('voice_time', 0) + duration
                    save_user(user_id, user_data)
                    
                # Обновляем время входа
                self.voice_states[user_id] = current_time
                
            except Exception as e:
                print(f"Error updating voice time for {user_id}: {e}")

    @update_voice_time.before_loop
    async def before_update_voice_time(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(UserStats(bot)) 