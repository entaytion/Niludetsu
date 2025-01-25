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
                "SELECT user_id, streak_count, last_message_date, total_messages, highest_streak, reference_time, is_active FROM user_streaks WHERE user_id = ?",
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
                    'highest_streak': 0,
                    'reference_time': None,
                    'is_active': 1
                }
            
            return {
                'user_id': result[0],
                'streak_count': result[1],
                'last_message_date': datetime.fromisoformat(result[2]) if result[2] else None,
                'total_messages': result[3],
                'highest_streak': result[4],
                'reference_time': datetime.fromisoformat(result[5]) if result[5] else None,
                'is_active': result[6]
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
                    highest_streak = ?,
                    reference_time = ?,
                    is_active = ?
                WHERE user_id = ?
                """,
                (
                    streak_data['streak_count'],
                    streak_data['last_message_date'].isoformat() if streak_data['last_message_date'] else None,
                    streak_data['total_messages'],
                    streak_data['highest_streak'],
                    streak_data['reference_time'].isoformat() if streak_data['reference_time'] else None,
                    streak_data['is_active'],
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

    def is_streak_expired(self, last_message: datetime, reference_time: datetime) -> tuple[bool, bool, datetime]:
        """Проверяет статус огонька и возвращает (истек ли, нужно ли уведомить, время истечения)"""
        if not last_message or not reference_time:
            return True, False, datetime.now()
            
        now = datetime.now()
        
        # Вычисляем следующее время истечения на основе reference_time
        next_expiry = datetime.combine(now.date(), reference_time.time())
        if now.time() < reference_time.time():
            next_expiry -= timedelta(days=1)
        next_expiry += timedelta(days=1)
            
        # Если последнее сообщение было более 24 часов назад
        if (now - last_message) > timedelta(hours=24):
            return True, False, next_expiry
            
        # Если близко к истечению (за час до)
        time_until_expiry = (next_expiry - now).total_seconds()
        if time_until_expiry <= 3600:  # За час до истечения
            return False, True, next_expiry
            
        return False, False, next_expiry

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        now = datetime.now()
        
        try:
            user_id = message.author.id
            streak_data = self.get_user_streak(user_id)
            last_message = streak_data['last_message_date']
            reference_time = streak_data['reference_time']
            
            # Обновляем общее количество сообщений
            streak_data['total_messages'] += 1
            
            if not last_message or not reference_time:
                # Первое сообщение пользователя или нет reference_time
                streak_data['streak_count'] = 1
                streak_data['highest_streak'] = 1
                streak_data['last_message_date'] = now
                streak_data['reference_time'] = now
                streak_data['is_active'] = 1
            else:
                # Проверяем время последнего сброса (22:00)
                last_reset = datetime.combine(now.date(), self.reset_time)
                if now.time() < self.reset_time:
                    last_reset -= timedelta(days=1)

                # Проверяем, прошло ли больше 24 часов с последнего сообщения
                time_since_last = now - last_message
                if time_since_last > timedelta(hours=24):
                    if streak_data['streak_count'] > 0:
                        try:
                            await message.author.send(
                                embed=create_embed(
                                    title=f"{EMOJIS['ERROR']} Огонек потух!",
                                    description=f"Вы слишком долго не писали сообщений. Ваш огонек **{streak_data['streak_count']} дней** потух!"
                                )
                            )
                        except discord.Forbidden:
                            print(f"Не удалось отправить уведомление о потухшем огоньке пользователю {message.author.name} - ЛС закрыты")
                    streak_data['streak_count'] = 0
                    streak_data['reference_time'] = now
                    streak_data['is_active'] = 1
                else:
                    # Если сейчас после 22:00 и огонек активен
                    if now.time() >= self.reset_time and streak_data['is_active']:
                        streak_data['is_active'] = 0

                    # Если огонек неактивен и сейчас после 22:00, и последнее сообщение было до 22:00
                    if not streak_data['is_active'] and now > last_reset and last_message < last_reset:
                        streak_data['streak_count'] += 1
                        streak_data['is_active'] = 1
                        if streak_data['streak_count'] > streak_data['highest_streak']:
                            streak_data['highest_streak'] = streak_data['streak_count']
                            try:
                                await message.author.send(
                                    embed=create_embed(
                                        title=f"{EMOJIS['SUCCESS']} Новый рекорд!",
                                        description=f"Вы установили новый рекорд активности: **{streak_data['streak_count']} дней**!"
                                    )
                                )
                            except discord.Forbidden:
                                print(f"Не удалось отправить уведомление о рекорде пользователю {message.author.name} - ЛС закрыты")

                streak_data['last_message_date'] = now

            self.update_streak(user_id, streak_data)
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
            reference_time = streak_data['reference_time']
            current_time = datetime.now()
            
            streak_count = streak_data['streak_count']
            total_messages = streak_data['total_messages']
            highest_streak = streak_data['highest_streak']
            is_active = streak_data['is_active']
            
            # Проверяем время последнего сброса (22:00)
            last_reset = datetime.combine(current_time.date(), self.reset_time)
            if current_time.time() < self.reset_time:
                last_reset -= timedelta(days=1)
            
            # Проверяем, не истек ли огонек (24 часа)
            if not last_message:
                streak_status = f"{EMOJIS['INFO']} Нет активности"
            elif (current_time - last_message) > timedelta(hours=24):
                streak_status = f"{EMOJIS['ERROR']} Огонёк потух! Прошло более 24 часов с последнего сообщения"
            elif not is_active:
                if current_time.time() >= self.reset_time:
                    streak_status = f"{EMOJIS['WARNING']} Напишите сообщение, чтобы продолжить огонёк!"
                else:
                    next_reset = datetime.combine(current_time.date(), self.reset_time)
                    hours_left = (next_reset - current_time).total_seconds() / 3600
                    streak_status = f"{EMOJIS['WARNING']} Огонёк станет неактивным в {next_reset.strftime('%H:%M')} (через {int(hours_left * 60)} минут)"
            else:
                next_reset = datetime.combine(current_time.date(), self.reset_time)
                if current_time.time() >= self.reset_time:
                    next_reset += timedelta(days=1)
                
                hours_left = (next_reset - current_time).total_seconds() / 3600
                if hours_left <= 1:
                    streak_status = f"{EMOJIS['WARNING']} Огонёк станет неактивным через {int(hours_left * 60)} минут!"
                else:
                    streak_status = f"{EMOJIS['SUCCESS']} Огонёк активен до {next_reset.strftime('%H:%M')} (через {int(hours_left * 60)} минут)"

            embed = create_embed(
                title=f"{self.get_flame_emoji(streak_count)} Статистика общения",
                description=f"Статистика для {target_user.mention}",
                fields=[
                    {"name": f"{EMOJIS['FLAME']} Текущий огонёк:", "value": f"{streak_count} дней", "inline": True},
                    {"name": f"{EMOJIS['CROWN']} Рекордный огонёк:", "value": f"{highest_streak} дней", "inline": True},
                    {"name": f"{EMOJIS['MESSAGE']} Всего сообщений:", "value": str(total_messages), "inline": True},
                    {"name": f"{EMOJIS['STATUS']} Статус:", "value": streak_status, "inline": False}
                ],
                thumbnail_url=target_user.display_avatar.url
            )
            
            if reference_time:
                embed.add_field(
                    name=f"{EMOJIS['CALENDAR']} Начало общения",
                    value=f"**{reference_time.strftime('%d.%m.%Y %H:%M')}**",
                    inline=True
                )
            
            if last_message:
                time_since = current_time - last_message
                hours_since = int(time_since.total_seconds() / 3600)
                minutes_since = int((time_since.total_seconds() % 3600) / 60)
                time_ago = f" (прошло {hours_since}ч {minutes_since}м)" if hours_since > 0 or minutes_since > 0 else ""
                
                embed.add_field(
                    name=f"{EMOJIS['CLOCK']} Последнее сообщение",
                    value=f"**{last_message.strftime('%d.%m.%Y %H:%M')}**{time_ago}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при получении информации о огоньке: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Streak(bot)) 