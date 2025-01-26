import discord
from discord import app_commands
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime, timedelta
import random
from typing import List, Optional
from utils import create_embed, DB_PATH, initialize_table, TABLES_SCHEMAS, EMOJIS

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        self.active_giveaways = {}
        self.check_giveaways.start()
        
    def setup_database(self):
        initialize_table('giveaways', TABLES_SCHEMAS['giveaways'])

    def get_giveaway(self, message_id: int) -> Optional[dict]:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT giveaway_id, channel_id, message_id, guild_id, host_id, 
                       prize, winners_count, end_time, is_ended, participants
                FROM giveaways WHERE message_id = ?
                """,
                (message_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return None
                
            return {
                'giveaway_id': result[0],
                'channel_id': result[1],
                'message_id': result[2],
                'guild_id': result[3],
                'host_id': result[4],
                'prize': result[5],
                'winners_count': result[6],
                'end_time': datetime.fromisoformat(result[7]),
                'is_ended': bool(result[8]),
                'participants': eval(result[9])
            }

    def update_participants(self, message_id: int, participants: List[int]):
        """Обновляет список участников в базе данных"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE giveaways SET participants = ? WHERE message_id = ?",
                (str(participants), message_id)
            )
            conn.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Обработчик добавления реакций"""
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != "🎉":
            return

        giveaway = self.get_giveaway(payload.message_id)
        if not giveaway or giveaway['is_ended']:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
            if not message:
                return

            # Проверяем, не является ли пользователь организатором
            if payload.user_id == giveaway['host_id']:
                # Убираем реакцию организатора
                await message.remove_reaction("🎉", payload.member)
                
                try:
                    embed = create_embed(
                        title="❌ Ошибка участия",
                        description="Вы не можете участвовать в своем розыгрыше!",
                        color=0xe74c3c
                    )
                    await payload.member.send(embed=embed)
                except discord.Forbidden:
                    pass
                return

            participants = giveaway['participants']
            if payload.user_id not in participants:
                participants.append(payload.user_id)
                self.update_participants(payload.message_id, participants)

                user = self.bot.get_user(payload.user_id)
                if user:
                    try:
                        embed = create_embed(
                            title="🎉 Регистрация в розыгрыше",
                            description=f"Вы успешно зарегистрировались в розыгрыше **{giveaway['prize']}**!\n"
                                      f"Результаты будут объявлены <t:{int(giveaway['end_time'].timestamp())}:R>",
                            color=0x2ecc71
                        )
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        pass

        except Exception as e:
            print(f"Ошибка при обработке реакции: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Обработчик удаления реакций"""
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != "🎉":
            return

        giveaway = self.get_giveaway(payload.message_id)
        if not giveaway or giveaway['is_ended']:
            return

        participants = giveaway['participants']
        if payload.user_id in participants:
            participants.remove(payload.user_id)
            self.update_participants(payload.message_id, participants)

            user = self.bot.get_user(payload.user_id)
            if user:
                try:
                    embed = create_embed(
                        title="❌ Отмена участия в розыгрыше",
                        description=f"Вы отменили участие в розыгрыше **{giveaway['prize']}**",
                        color=0xe74c3c  # Красный
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    @tasks.loop(seconds=5)  # Уменьшаем интервал проверки до 5 секунд
    async def check_giveaways(self):
        """Проверяет и завершает розыгрыши"""
        now = datetime.now()
        ended_giveaways = []
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Получаем все активные розыгрыши
            cursor.execute("""
                SELECT message_id, channel_id, end_time 
                FROM giveaways 
                WHERE is_ended = 0 AND end_time <= ?
            """, (now.isoformat(),))
            
            for row in cursor.fetchall():
                message_id, channel_id, end_time = row
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        message = await channel.fetch_message(message_id)
                        if message:
                            ended_giveaways.append(message_id)
                            await self.end_giveaway(message)
                    except:
                        continue

        # Удаляем завершенные розыгрыши из активных
        for message_id in ended_giveaways:
            if message_id in self.active_giveaways:
                del self.active_giveaways[message_id]

    async def end_giveaway(self, message: discord.Message):
        """Завершает розыгрыш и выбирает победителей"""
        giveaway_data = self.get_giveaway(message.id)
        if not giveaway_data or giveaway_data['is_ended']:
            return
            
        try:
            participants = giveaway_data['participants']
            winners = []
            
            if participants:
                # Выбираем победителей из списка участников
                winner_count = min(giveaway_data['winners_count'], len(participants))
                winner_ids = random.sample(participants, winner_count)
                
                for winner_id in winner_ids:
                    user = self.bot.get_user(winner_id)
                    if user:
                        winners.append(user)
                        try:
                            win_embed = create_embed(
                                title="🎊 Поздравляем!",
                                description=f"Вы выиграли в розыгрыше **{giveaway_data['prize']}**!\n"
                                          f"Организатор свяжется с вами для передачи приза.",
                                color=0xf1c40f
                            )
                            await user.send(embed=win_embed)
                        except discord.Forbidden:
                            pass

                winners_text = "\n".join([f"🏆 {winner.mention}" for winner in winners])
                
                embed = create_embed(
                    title=f"🎉 {giveaway_data['prize']}",
                    description=f"**Розыгрыш завершен!**\n\n"
                               f"**Победители:**\n{winners_text}\n\n"
                               f"**Организатор:** <@{giveaway_data['host_id']}>",
                    color=0x2ecc71
                )
            else:
                # Если нет участников, удаляем все реакции
                await message.clear_reactions()
                
                embed = create_embed(
                    title=f"🎉 {giveaway_data['prize']}",
                    description="**Розыгрыш завершен!**\n\n"
                               "Победителей нет - никто не участвовал 😢",
                    color=0xe74c3c
                )
            
            await message.edit(embed=embed)
            
            if winners:
                winners_mentions = ", ".join([w.mention for w in winners])
                await message.channel.send(
                    embed=create_embed(
                        title="🎊 Поздравляем победителей!",
                        description=f"**Приз:** {giveaway_data['prize']}\n"
                                  f"**Победители:** {winners_mentions}",
                        color=0xf1c40f
                    )
                )
            
            # Уведомляем организатора
            host = self.bot.get_user(giveaway_data['host_id'])
            if host:
                try:
                    host_embed = create_embed(
                        title="🎉 Розыгрыш завершен",
                        description=f"Ваш розыгрыш **{giveaway_data['prize']}** завершен!\n"
                                  f"Победители: {winners_mentions if winners else 'нет победителей'}",
                        color=0x3498db  # Синий
                    )
                    await host.send(embed=host_embed)
                except discord.Forbidden:
                    pass
            
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE giveaways SET is_ended = 1 WHERE message_id = ?",
                    (message.id,)
                )
                conn.commit()
                
        except Exception as e:
            print(f"Ошибка при завершении розыгрыша: {e}")

    async def create_giveaway(
        self,
        ctx: discord.Interaction,
        prize: str,
        winners: int,
        duration: str,
        channel: Optional[discord.TextChannel] = None
    ) -> Optional[discord.Message]:
        """Создает новый розыгрыш"""
        channel = channel or ctx.channel
        
        # Парсим длительность
        duration_seconds = 0
        time_units = {
            'd': 86400,
            'h': 3600,
            'm': 60,
            's': 1
        }
        
        try:
            value = int(duration[:-1])
            unit = duration[-1].lower()
            if unit not in time_units:
                raise ValueError
            duration_seconds = value * time_units[unit]
        except ValueError:
            await ctx.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Неверный формат длительности! Используйте: 1d, 12h, 30m, 10s",
                    color=0xe74c3c  # Красный
                ),
                ephemeral=True
            )
            return None

        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        embed = create_embed(
            title=f"🎉 {prize}",
            description=f"Нажмите на 🎉 чтобы участвовать!\n\n"
                       f"**Призовых мест:** {winners}\n"
                       f"**Организатор:** {ctx.user.mention}\n"
                       f"**Завершится:** <t:{int(end_time.timestamp())}:R>"
        )
        
        giveaway_message = await channel.send(embed=embed)
        await giveaway_message.add_reaction("🎉")
        
        # Сохраняем в базу данных
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO giveaways 
                (channel_id, message_id, guild_id, host_id, prize, winners_count, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel.id,
                    giveaway_message.id,
                    ctx.guild_id,
                    ctx.user.id,
                    prize,
                    winners,
                    end_time.isoformat()
                )
            )
            conn.commit()
        
        self.active_giveaways[giveaway_message.id] = {
            'end_time': end_time,
            'message': giveaway_message
        }
        
        await ctx.response.send_message(
            embed=create_embed(
                description=f"{EMOJIS['SUCCESS']} Розыгрыш успешно создан в {channel.mention}!"
            ),
            ephemeral=True
        )
        
        return giveaway_message

    giveaway = app_commands.Group(name="giveaway", description="Управление розыгрышами")

    @giveaway.command(name="create", description="Начать новый розыгрыш")
    @app_commands.describe(
        prize="Что разыгрываем",
        winners="Количество победителей",
        duration="Длительность (например: 1d, 12h, 30m)",
        channel="Канал для розыгрыша (по умолчанию - текущий)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        prize: str,
        winners: int,
        duration: str,
        channel: Optional[discord.TextChannel] = None
    ):
        """Создать новый розыгрыш"""
        await self.create_giveaway(interaction, prize, winners, duration, channel)

    @giveaway.command(name="end", description="Досрочно завершить розыгрыш")
    @app_commands.describe(message_id="ID сообщения с розыгрышем")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_end(self, interaction: discord.Interaction, message_id: str):
        """Досрочно завершить розыгрыш"""
        try:
            message_id = int(message_id)
            giveaway_data = self.get_giveaway(message_id)
            
            if not giveaway_data:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Розыгрыш не найден!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            if giveaway_data['is_ended']:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Этот розыгрыш уже завершен!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            channel = interaction.guild.get_channel(giveaway_data['channel_id'])
            if not channel:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Канал розыгрыша не найден!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            message = await channel.fetch_message(message_id)
            if not message:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Сообщение розыгрыша не найдено!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            await self.end_giveaway(message)
            
            if message_id in self.active_giveaways:
                del self.active_giveaways[message_id]
                
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} Розыгрыш успешно завершен!"
                ),
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Неверный формат ID сообщения!",
                    color=0xe74c3c  # Красный
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка: {str(e)}",
                    color=0xe74c3c  # Красный
                ),
                ephemeral=True
            )

    @giveaway.command(name="reroll", description="Выбрать новых победителей")
    @app_commands.describe(message_id="ID сообщения с розыгрышем")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        """Выбрать новых победителей"""
        try:
            message_id = int(message_id)
            giveaway_data = self.get_giveaway(message_id)
            
            if not giveaway_data:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Розыгрыш не найден!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            if not giveaway_data['is_ended']:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Этот розыгрыш еще не завершен!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            channel = interaction.guild.get_channel(giveaway_data['channel_id'])
            if not channel:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Канал розыгрыша не найден!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            message = await channel.fetch_message(message_id)
            if not message:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Сообщение розыгрыша не найдено!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Реакции не найдены!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            users = [user async for user in reaction.users() if not user.bot]
            
            if not users:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Нет участников для выбора!",
                        color=0xe74c3c  # Красный
                    ),
                    ephemeral=True
                )
                return
                
            winner_count = min(giveaway_data['winners_count'], len(users))
            winners = random.sample(users, winner_count)
            winners_text = "\n".join([f"🏆 {winner.mention}" for winner in winners])
            
            embed = create_embed(
                title=f"🎉 {giveaway_data['prize']} (Повторный розыгрыш)",
                description=f"**Новые победители:**\n{winners_text}\n\n"
                           f"**Организатор:** <@{giveaway_data['host_id']}>",
                color=0x2ecc71  # Зеленый
            )
            
            await message.edit(embed=embed)
            
            winners_mentions = ", ".join([w.mention for w in winners])
            await message.channel.send(
                embed=create_embed(
                    title="🎊 Поздравляем новых победителей!",
                    description=f"**Приз:** {giveaway_data['prize']}\n"
                              f"**Победители:** {winners_mentions}",
                    color=0xf1c40f  # Золотой
                )
            )
            
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} Новые победители успешно выбраны!",
                    color=0x2ecc71  # Зеленый
                ),
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Неверный формат ID сообщения!",
                    color=0xe74c3c  # Красный
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка: {str(e)}",
                    color=0xe74c3c  # Красный
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Giveaways(bot)) 