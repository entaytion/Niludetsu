import discord
from discord.ext import commands
from utils import get_user, save_user, create_embed
import sqlite3
from utils import DB_PATH

POSITIVE_TRIGGERS = ['плюс', 'согл', 'спс', 'спасибо', 'сяп', 'сенкс', 'thanks', 'thx', '👍', '❤️']
NEGATIVE_TRIGGERS = ['минус', 'не согл', 'нет', 'неа', '👎'] 

class Reputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initialize_reputation_column()
        
    def initialize_reputation_column(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'reputation' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN reputation INTEGER DEFAULT 0')
                conn.commit()

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

            target_user = get_user(self.bot, str(referenced_message.author.id))
            if target_user is None:
                return
            
            # Обновление репутации в БД напрямую
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                if is_positive:
                    cursor.execute(
                        "UPDATE users SET reputation = reputation + 1 WHERE user_id = ?",
                        (str(referenced_message.author.id),)
                    )
                    await message.add_reaction('⬆️')
                    cursor.execute("SELECT reputation FROM users WHERE user_id = ?", 
                                 (str(referenced_message.author.id),))
                    new_rep = cursor.fetchone()[0]
                    embed = create_embed(
                        description=f"{message.author.mention} повысил репутацию {referenced_message.author.mention}\nРепутация: {new_rep}",
                        image_url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6ZWF1Y2E3OGE4MWF2NmF1NXJ5Y2RxbWF4Z2t0bG95aWsyeGpmbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dMsh6gRYJDymXSIatd/giphy.gif"
                    )
                elif is_negative:
                    cursor.execute(
                        "UPDATE users SET reputation = reputation - 1 WHERE user_id = ?",
                        (str(referenced_message.author.id),)
                    )
                    await message.add_reaction('⬇️')
                    cursor.execute("SELECT reputation FROM users WHERE user_id = ?",
                                 (str(referenced_message.author.id),))
                    new_rep = cursor.fetchone()[0]
                    embed = create_embed(
                        description=f"{message.author.mention} понизил репутацию {referenced_message.author.mention}\nРепутация: {new_rep}",
                        image_url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmZ5ZWN0Y2RqbWd2bXd1NXBxYnBxaWQ2aHdqbDV1ZWx1ZWxqd2JxdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oEjHAUOqG3lSS0f1C/giphy.gif"
                    )
                conn.commit()
                await message.channel.send(embed=embed)

        except Exception as e:
            print(f"Error in reputation system: {e}")

async def setup(bot):
    await bot.add_cog(Reputation(bot))