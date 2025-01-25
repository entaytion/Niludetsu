import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta, time
from utils import create_embed, DB_PATH, initialize_table, TABLES_SCHEMAS, EMOJIS

class Streak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        self.reset_time = time(22, 0)  # 22:00
        self._notified_users = set()
        
    def setup_database(self):
        initialize_table('user_streaks', TABLES_SCHEMAS['user_streaks'])

    def get_user_streak(self, user_id: int) -> dict:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_streaks WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                cursor.execute(
                    "INSERT INTO user_streaks (user_id) VALUES (?)",
                    (user_id,)
                )
                conn.commit()
                return {
                    'user_id': user_id,
                    'streak_count': 0,
                    'last_message_date': None,
                    'total_messages': 0,
                    'highest_streak': 0
                }
            
            return {
                'user_id': result[0],
                'streak_count': result[1],
                'last_message_date': datetime.fromisoformat(result[2]) if result[2] else None,
                'total_messages': result[3],
                'highest_streak': result[4]
            }

    def update_streak(self, user_id: int, streak_data: dict):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_streaks 
                SET streak_count = ?,
                    last_message_date = ?,
                    total_messages = ?,
                    highest_streak = ?
                WHERE user_id = ?
                """,
                (
                    streak_data['streak_count'],
                    streak_data['last_message_date'].isoformat() if streak_data['last_message_date'] else None,
                    streak_data['total_messages'],
                    streak_data['highest_streak'],
                    user_id
                )
            )
            conn.commit()

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
            user_id = message.author.id
            streak_data = self.get_user_streak(user_id)
            last_message = streak_data['last_message_date']
            
            # Обновляем общее количество сообщений
            streak_data['total_messages'] += 1
            
            if not last_message:
                # Первое сообщение пользователя
                streak_data['streak_count'] = 1
                streak_data['highest_streak'] = 1
                streak_data['last_message_date'] = now
            else:
                time_diff = now - last_message
                
                if time_diff < timedelta(hours=24):
                    # Сообщение в пределах 24 часов - игнорируем
                    streak_data['last_message_date'] = now
                    
                    # Проверяем, не скоро ли потухнет огонек
                    is_expired, should_notify, expire_time = self.is_streak_expired(last_message)
                    if should_notify and user_id not in self._notified_users:
                        self._notified_users.add(user_id)
                        time_left = (expire_time - now).total_seconds() / 60
                        try:
                            await message.author.send(
                                embed=create_embed(
                                    title="⚠️ Внимание!",
                                    description=f"Ваш огонек скоро потухнет! У вас осталось **{int(time_left)} минут** чтобы написать сообщение!"
                                )
                            )
                        except discord.Forbidden:
                            print(f"Не удалось отправить уведомление пользователю {message.author.name} - ЛС закрыты")
                elif time_diff < timedelta(hours=24):
                    # Сообщение в пределах 24 часов - продолжаем streak
                    streak_data['streak_count'] += 1
                    if streak_data['streak_count'] > streak_data['highest_streak']:
                        streak_data['highest_streak'] = streak_data['streak_count']
                    streak_data['last_message_date'] = now
                    
                    # Уведомляем о новом рекорде
                    if streak_data['streak_count'] == streak_data['highest_streak']:
                        try:
                            await message.author.send(
                                embed=create_embed(
                                    title=f"{EMOJIS['SUCCESS']} Новый рекорд!",
                                    description=f"Вы установили новый рекорд активности: **{streak_data['streak_count']} дней**!"
                                )
                            )
                        except discord.Forbidden:
                            print(f"Не удалось отправить уведомление о рекорде пользователю {message.author.name} - ЛС закрыты")
                else:
                    # Сообщение после 24 часов - сбрасываем streak
                    if streak_data['streak_count'] > 0:
                        try:
                            await message.author.send(
                                embed=create_embed(
                                    title="💔 Огонек потух!",
                                    description=f"Вы слишком долго не писали сообщений. Ваш огонек **{streak_data['streak_count']} дней** потух!"
                                )
                            )
                        except discord.Forbidden:
                            print(f"Не удалось отправить уведомление о потухшем огоньке пользователю {message.author.name} - ЛС закрыты")
                    streak_data['streak_count'] = 1
                    streak_data['last_message_date'] = now
            
            self.update_streak(user_id, streak_data)

            # Обновляем никнейм
            await self.update_nickname(message.author, streak_data['streak_count'])

        except Exception as e:
            print(f"Ошибка при обновлении огонька: {e}")

    @app_commands.command(name="streak", description="Показать информацию о вашем огоньке общения")
    @app_commands.describe(user="Пользователь, чей огонек вы хотите посмотреть")
    async def streak(self, interaction: discord.Interaction, user: discord.User = None):
        target_user = user or interaction.user
        
        try:
            streak_data = self.get_user_streak(target_user.id)
            last_message = streak_data['last_message_date']
            current_time = datetime.now()
            
            # Проверяем, не просрочен ли текущий streak
            if last_message and (current_time - last_message) > timedelta(hours=24):
                streak_data['streak_count'] = 0
                self.update_streak(target_user.id, streak_data)
            
            streak_count = streak_data['streak_count']
            total_messages = streak_data['total_messages']
            highest_streak = streak_data['highest_streak']
            
            # Проверяем статус огонька
            is_expired, should_notify, expire_time = self.is_streak_expired(last_message)
            
            if is_expired:
                streak_status = "❌ Огонёк потерян"
            else:
                if current_time.time() >= self.reset_time:
                    # После 22:00
                    streak_status = f"⚡ Огонёк в безопасности до {expire_time.strftime('%H:%M')}"
                else:
                    # До 22:00
                    hours_left = (expire_time - current_time).total_seconds() / 3600
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
            
            if last_message:
                time_diff = current_time - last_message
                hours_left = 24 - time_diff.total_seconds() / 3600
                
                if hours_left > 0:
                    embed.add_field(
                        name="⏰ Время до сброса",
                        value=f"**{int(hours_left)}** часов",
                        inline=False
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