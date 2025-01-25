import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta, time
from utils import create_embed, EMOJIS

class Streak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "config/database.db"
        self.setup_database()
        self.reset_time = time(22, 0)  # 22:00
        
    def setup_database(self):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            # Создаем таблицу для отслеживания активности
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_streaks (
                    user_id INTEGER PRIMARY KEY,
                    streak_count INTEGER DEFAULT 0,
                    last_message_date TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    highest_streak INTEGER DEFAULT 0
                )
            """)
            db.commit()

    def get_flame_emoji(self, streak_count: int) -> str:
        """Возвращает эмодзи огонька в зависимости от длины Огонька"""
        if streak_count < 3:
            return "🔥"
        elif streak_count < 7:
            return "💫"
        elif streak_count < 14:
            return "⚡"
        elif streak_count < 30:
            return "🌟"
        else:
            return "👑"

    async def update_nickname(self, member: discord.Member, streak_count: int):
        """Обновляет никнейм пользователя, добавляя или обновляя эмодзи Огонька"""
        if member.guild.owner_id == member.id:
            return  # Пропускаем владельца сервера
            
        try:
            base_name = member.display_name
            # Убираем старые эмодзи Огоньков
            for emoji in ["🔥", "💫", "⚡", "🌟", "👑"]:
                base_name = base_name.replace(emoji, "").strip()
            
            # Добавляем новый эмодзи
            if streak_count > 0:
                new_name = f"{self.get_flame_emoji(streak_count)} {base_name}"
                await member.edit(nick=new_name[:32])  # Discord ограничивает длину никнейма 32 символами
        except discord.Forbidden:
            print(f"Не удалось обновить никнейм для {member.name}. Недостаточно прав.")
        except Exception as e:
            print(f"Ошибка при обновлении никнейма: {e}")

    def is_streak_expired(self, last_message: datetime) -> tuple[bool, bool, datetime]:
        """Проверяет статус огонька и возвращает (истек ли, нужно ли уведомить, время истечения)"""
        now = datetime.now()
        
        # Если последнее сообщение было до 22:00
        if last_message.time() < self.reset_time:
            # Огонек тухнет в 22:00 того же дня
            expire_time = datetime.combine(last_message.date(), self.reset_time)
        else:
            # Огонек тухнет в 22:00 следующего дня
            expire_time = datetime.combine(last_message.date() + timedelta(days=1), self.reset_time)
            
        # Если близко к истечению (за час до), отправляем уведомление
        if not hasattr(self, '_notified_users'):
            self._notified_users = set()
            
        if now < expire_time and (expire_time - now).total_seconds() <= 3600:  # За час до истечения
            return False, True, expire_time  # Не истек, но нужно уведомить
        
        # Очищаем уведомления для пользователя если огонек истек
        if now >= expire_time:
            self._notified_users = set()
            return True, False, expire_time  # Истек, уведомлять не нужно
            
        return False, False, expire_time  # Не истек и уведомлять не нужно

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        now = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT streak_count, last_message_date FROM user_streaks WHERE user_id = ?",
                    (message.author.id,)
                )
                result = cursor.fetchone()
                
                if result:
                    streak_count, last_message = result
                    last_message = datetime.strptime(last_message, "%Y-%m-%d %H:%M:%S.%f")
                    
                    # Проверяем статус огонька
                    is_expired, should_notify, expire_time = self.is_streak_expired(last_message)
                    
                    # Отправляем уведомление если нужно
                    if should_notify and message.author.id not in self._notified_users:
                        try:
                            embed = create_embed(
                                title="🔥 Внимание! Ваш огонёк скоро потухнет!",
                                description=(
                                    f"Ваш огонёк активности скоро потухнет!\n"
                                    f"Напишите сообщение в чат до {self.reset_time.strftime('%H:%M')}, "
                                    f"чтобы сохранить огонёк ({streak_count} дней)!"
                                ),
                                color=0xFF0000
                            )
                            await message.author.send(embed=embed)
                            self._notified_users.add(message.author.id)
                        except discord.Forbidden:
                            pass  # Пользователь запретил ЛС
                    
                    if is_expired:
                        streak_count = 0  # Сбрасываем огонек
                        new_message_date = now  # Если огонек потерян, начинаем новый отсчет
                    elif last_message.date() < now.date():
                        streak_count += 1  # Увеличиваем огонек если это новый день
                        new_message_date = now  # Новый день - обновляем время
                    else:
                        new_message_date = last_message  # Оставляем старое время, если огонек активен
                else:
                    streak_count = 1  # Первое сообщение пользователя
                    new_message_date = now
                
                # Обновляем данные в БД
                cursor.execute("""
                    INSERT OR REPLACE INTO user_streaks 
                    (user_id, streak_count, last_message_date, total_messages, highest_streak) 
                    VALUES (?, ?, ?, 
                        COALESCE((SELECT total_messages FROM user_streaks WHERE user_id = ?) + 1, 1),
                        COALESCE(MAX((SELECT highest_streak FROM user_streaks WHERE user_id = ?), ?), ?)
                    )
                """, (message.author.id, streak_count, new_message_date, message.author.id, message.author.id, streak_count, streak_count))
                db.commit()

                # Обновляем никнейм
                await self.update_nickname(message.author, streak_count)

        except Exception as e:
            print(f"Ошибка при обновлении огонька: {e}")

    @app_commands.command(name="streak", description="Показать информацию о вашем огоньке общения")
    @app_commands.describe(user="Пользователь, чей огонек вы хотите посмотреть")
    async def streak(self, interaction: discord.Interaction, user: discord.User = None):
        target_user = user or interaction.user
        
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    """
                    SELECT streak_count, total_messages, highest_streak, last_message_date 
                    FROM user_streaks 
                    WHERE user_id = ?
                    """,
                    (target_user.id,)
                )
                result = cursor.fetchone()

            if not result:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} У {'вас' if target_user == interaction.user else 'пользователя'} пока нет огонька общения."
                    )
                )
                return

            streak_count, total_messages, highest_streak, last_message = result
            last_message = datetime.strptime(last_message, "%Y-%m-%d %H:%M:%S.%f")
            
            # Проверяем статус огонька
            is_expired, _, expire_time = self.is_streak_expired(last_message)
            
            if is_expired:
                streak_status = "❌ Огонёк потерян"
            else:
                now = datetime.now()
                if now.time() >= self.reset_time:
                    # После 22:00
                    streak_status = f"⚡ Огонёк в безопасности до {expire_time.strftime('%H:%M')}"
                else:
                    # До 22:00
                    hours_left = (expire_time - now).total_seconds() / 3600
                    if hours_left <= 1:
                        streak_status = f"⚠️ Огонёк погаснет через {int(hours_left * 60)} минут!"
                    else:
                        streak_status = f"✨ Огонёк в безопасности до {expire_time.strftime('%H:%M')}"

            embed = create_embed(
                title=f"{self.get_flame_emoji(streak_count)} Статистика общения",
                description=f"Статистика для {target_user.mention}",
                fields=[
                    {"name": "Текущий огонёк:", "value": f"{streak_count} дней", "inline": True},
                    {"name": "Рекордный огонёк:", "value": f"{highest_streak} дней", "inline": True},
                    {"name": "Всего сообщений:", "value": str(total_messages), "inline": True},
                    {"name": "Статус:", "value": streak_status, "inline": False}
                ],
                thumbnail_url=target_user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при получении информации о огоньке: {str(e)}"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Streak(bot)) 