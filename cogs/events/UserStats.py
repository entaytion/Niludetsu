import discord
from discord.ext import commands, tasks
from Niludetsu.utils.database import get_user, save_user
from datetime import datetime, timedelta
import traceback

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
        """Обработка изменений голосового состояния для статистики"""
        try:
            if member.bot:
                return

            user_id = str(member.id)
            user_data = get_user(user_id)
            
            # Создаем базовые данные, если их нет
            if not user_data:
                user_data = {
                    'user_id': user_id,
                    'voice_time': 0,
                    'voice_joins': 0,
                    'last_voice_join': None,
                    'messages_count': 0
                }
                save_user(user_id, user_data)
            else:
                # Убеждаемся, что все необходимые поля существуют и инициализированы
                if 'voice_time' not in user_data or user_data['voice_time'] is None:
                    user_data['voice_time'] = 0
                if 'voice_joins' not in user_data or user_data['voice_joins'] is None:
                    user_data['voice_joins'] = 0
                if 'last_voice_join' not in user_data:
                    user_data['last_voice_join'] = None
                save_user(user_id, user_data)

            # Если пользователь присоединился к голосовому каналу
            if not before.channel and after.channel:
                user_data['last_voice_join'] = datetime.utcnow().timestamp()
                user_data['voice_joins'] = int(user_data['voice_joins']) + 1
                save_user(user_id, user_data)

            # Если пользователь покинул голосовой канал
            elif before.channel and not after.channel:
                if user_data.get('last_voice_join'):
                    duration = int(datetime.utcnow().timestamp() - float(user_data['last_voice_join']))
                    user_data['voice_time'] = int(user_data['voice_time']) + duration
                    user_data['last_voice_join'] = None
                    save_user(user_id, user_data)

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