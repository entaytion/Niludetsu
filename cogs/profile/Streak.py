import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta, time
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.database import DB_PATH, initialize_table, TABLES_SCHEMAS
from discord.ext import tasks

class Streak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        self.reset_time = time(22, 0)  # 22:00
        self._notified_users = set()
        self.check_streaks.start()  # Запускаем периодическую проверку
        
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
            
            # Добавляем новый эмодзи только если есть активный огонек
            if streak_count > 0:
                new_name = f"{self.get_flame_emoji(streak_count)} {base_name}"
            else:
                new_name = base_name

            # Обновляем никнейм только если он изменился
            if new_name != member.display_name:
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
        
        # Расчет следующего дедлайна
        next_expiry = datetime.combine(now.date(), reference_time.time())
        if now.time() < reference_time.time():
            next_expiry -= timedelta(days=1)
        next_expiry += timedelta(days=1)
            
        # Проверка, было ли последнее сообщение более 24 часов назад
        time_since_last_message = now - last_message
        if time_since_last_message > timedelta(hours=24):
            return True, False, next_expiry
            
        # Близость к дедлайну (уведомление)
        time_until_expiry = (next_expiry - now).total_seconds()
        if time_until_expiry <= 3600:  # за 1 час
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
                # Первое сообщение пользователя
                streak_data['streak_count'] = 1
                streak_data['highest_streak'] = 1
                streak_data['last_message_date'] = now
                streak_data['reference_time'] = now
                streak_data['is_active'] = 1
            else:
                # Проверяем, прошли ли сутки с последнего сообщения
                time_since_last = now - last_message
                
                if time_since_last > timedelta(hours=24):
                    # Если прошло больше 24 часов - обнуляем
                    streak_data['streak_count'] = 1
                    streak_data['reference_time'] = now
                    streak_data['is_active'] = 1
                elif time_since_last > timedelta(hours=20):  # Даем 4 часа форы до обнуления
                    # Просто обновляем время последнего сообщения
                    streak_data['last_message_date'] = now
                    streak_data['is_active'] = 1
                elif last_message.date() < now.date():
                    # Если сообщение в новый день и не прошло 24 часа - увеличиваем огонек
                    streak_data['streak_count'] += 1
                    streak_data['last_message_date'] = now
                    streak_data['is_active'] = 1

                # Проверяем рекорд
                if streak_data['streak_count'] > streak_data['highest_streak']:
                    streak_data['highest_streak'] = streak_data['streak_count']
                    try:
                        await message.author.send(
                            embed=create_embed(
                                title=f"{EMOJIS['TROPHY']} Новый рекорд!",
                                description=f"{EMOJIS['FIRE']} Вы установили новый рекорд активности: **{streak_data['streak_count']} дней**!",
                                color="GOLD"
                            )
                        )
                    except discord.Forbidden:
                        print(f"Не удалось отправить уведомление о рекорде пользователю {message.author.name} - ЛС закрыты")

            self.update_streak(user_id, streak_data)
            await self.update_nickname(message.author, streak_data['streak_count'])

        except Exception as e:
            print(f"Ошибка при обновлении огонька: {e}")

    def check_streak_status(self, streak_data: dict) -> tuple[bool, int, datetime]:
        """Проверяет актуальность огонька и возвращает (is_active, current_streak, next_reset)"""
        current_time = datetime.now()
        last_message = streak_data['last_message_date']
        reference_time = streak_data['reference_time']
        
        if not last_message or not reference_time:
            return False, 0, current_time

        # Вычисляем следующий дедлайн
        next_deadline = datetime.combine(current_time.date(), reference_time.time())
        if current_time.time() < reference_time.time():
            next_deadline -= timedelta(days=1)
        next_deadline += timedelta(days=1)

        # Огонек активен если не пропущен дедлайн
        is_active = current_time <= next_deadline and streak_data['is_active'] == 1
        return is_active, streak_data['streak_count'], next_deadline

    @app_commands.command(name="streak", description="Показать информацию о вашем огоньке общения")
    @app_commands.describe(user="Пользователь, чей огонек вы хотите посмотреть")
    async def streak(self, interaction: discord.Interaction, user: discord.User = None):
        target_user = user or interaction.user
        
        try:
            streak_data = self.get_user_streak(target_user.id)
            last_message = streak_data['last_message_date']
            
            if not last_message:
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Нет огонька",
                        description=f"У {target_user.mention} пока нет огонька. Начните общаться, чтобы получить огонек!",
                        color="RED"
                    )
                )
                return
            
            # Проверяем актуальный статус огонька
            is_active, current_streak, next_reset = self.check_streak_status(streak_data)
            
            if not is_active:
                status = f"{EMOJIS['ERROR']} Огонёк потух! Напишите сообщение, чтобы начать новый."
                color = "RED"
            else:
                time_left = int((next_reset - datetime.now()).total_seconds())
                hours_left, minutes_left = divmod(time_left // 60, 60)
                status = f"{EMOJIS['SUCCESS']} Огонёк активен ещё {hours_left}ч {minutes_left}м."
                color = "GREEN"

            # Создаем эмбед с информацией об огоньке
            embed = create_embed(
                title=f"{self.get_flame_emoji(streak_data['streak_count'])} Огонёк {target_user.name}",
                description=status,
                color=color
            )

            # Добавляем поля с информацией
            embed.add_field(
                name=f"{EMOJIS['STREAK']} Текущий огонёк",
                value=f"**{streak_data['streak_count']}** дней",
                inline=True
            )
            embed.add_field(
                name=f"{EMOJIS['TROPHY']} Рекорд",
                value=f"**{streak_data['highest_streak']}** дней",
                inline=True
            )
            embed.add_field(
                name=f"{EMOJIS['MESSAGES']} Всего сообщений",
                value=f"**{streak_data['total_messages']}**",
                inline=True
            )

            # Добавляем информацию о последнем сообщении
            last_message_str = last_message.strftime("%d.%m.%Y %H:%M")
            embed.add_field(
                name=f"{EMOJIS['TIME']} Последнее сообщение",
                value=f"**{last_message_str}**",
                inline=False
            )

            embed.set_thumbnail(url=target_user.display_avatar.url)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при получении информации о огоньке: {str(e)}"
                )
            )

    def cog_unload(self):
        self.check_streaks.cancel()  # Останавливаем задачу при выгрузке кога

    @tasks.loop(minutes=5)  # Проверяем каждые 5 минут
    async def check_streaks(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # Получаем всех пользователей с активными огоньками
                cursor.execute("SELECT user_id, last_message_date FROM user_streaks WHERE is_active = 1")
                active_users = cursor.fetchall()

                now = datetime.now()
                for user_id, last_message_str in active_users:
                    if last_message_str:
                        last_message = datetime.fromisoformat(last_message_str)
                        # Если прошло больше 24 часов
                        if (now - last_message) > timedelta(hours=24):
                            # Сбрасываем огонек
                            cursor.execute("""
                                UPDATE user_streaks 
                                SET streak_count = 0,
                                    is_active = 0
                                WHERE user_id = ?
                            """, (user_id,))
                            
                            # Пытаемся обновить никнейм пользователя
                            try:
                                for guild in self.bot.guilds:
                                    member = guild.get_member(user_id)
                                    if member:
                                        await self.update_nickname(member, 0)
                                        break
                            except:
                                pass
                conn.commit()
        except Exception as e:
            print(f"Ошибка при проверке огоньков: {e}")

    @check_streaks.before_loop
    async def before_check_streaks(self):
        await self.bot.wait_until_ready()  # Ждем готовности бота

async def setup(bot):
    await bot.add_cog(Streak(bot)) 