import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
from typing import List, Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database import Database
import asyncio

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self.db.init())  # Асинхронная инициализация базы данных
        self.active_giveaways = {}
        self.check_giveaways.start()
        
    async def get_giveaway(self, message_id: int) -> Optional[dict]:
        """Получает данные розыгрыша"""
        result = await self.db.execute(
            """
            SELECT giveaway_id, channel_id, message_id, guild_id, host_id, 
                   prize, winners_count, end_time, is_ended, participants
            FROM giveaways WHERE message_id = ?
            """,
            (str(message_id),)
        )
        
        if not result:
            return None
            
        row = result[0]
        try:
            end_time = datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            end_time = datetime.utcnow()
            
        return {
            'giveaway_id': row[0],
            'channel_id': row[1],
            'message_id': row[2],
            'guild_id': row[3],
            'host_id': row[4],
            'prize': row[5],
            'winners_count': row[6],
            'end_time': end_time,
            'is_ended': bool(row[8]),
            'participants': eval(row[9])
        }

    async def update_participants(self, message_id: int, participants: List[int]):
        """Обновляет список участников в базе данных"""
        await self.db.execute(
            "UPDATE giveaways SET participants = ? WHERE message_id = ?",
            (str(participants), message_id)
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Обработчик добавления реакций"""
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != "🎉":
            return

        giveaway = await self.get_giveaway(payload.message_id)
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
            if payload.user_id == int(giveaway['host_id']):
                # Убираем реакцию организатора
                await message.remove_reaction("🎉", payload.member)
                
                try:
                    embed=Embed(
                        title="❌ Ошибка участия",
                        description="Вы не можете участвовать в своем розыгрыше!",
                        color="RED"
                    )
                    await payload.member.send(embed=embed)
                except discord.Forbidden:
                    pass
                return

            participants = giveaway['participants']
            if payload.user_id not in participants:
                participants.append(payload.user_id)
                await self.update_participants(payload.message_id, participants)

                user = self.bot.get_user(payload.user_id)
                if user:
                    try:
                        embed=Embed(
                            title="🎉 Регистрация в розыгрыше",
                            description=f"Вы успешно зарегистрировались в розыгрыше **{giveaway['prize']}**!\n"
                                      f"Результаты будут объявлены <t:{int(giveaway['end_time'].timestamp())}:R>",
                            color="GREEN"
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

        giveaway = await self.get_giveaway(payload.message_id)
        if not giveaway or giveaway['is_ended']:
            return

        participants = giveaway['participants']
        if payload.user_id in participants:
            participants.remove(payload.user_id)
            await self.update_participants(payload.message_id, participants)

            user = self.bot.get_user(payload.user_id)
            if user:
                try:
                    embed=Embed(
                        title="❌ Отмена участия в розыгрыше",
                        description=f"Вы отменили участие в розыгрыше **{giveaway['prize']}**",
                        color="RED"
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Проверяет активные розыгрыши"""
        try:
            now = datetime.utcnow()
            
            # Получаем все незавершенные розыгрыши
            expired_giveaways = await self.db.fetch_all(
                """
                SELECT channel_id, message_id 
                FROM giveaways 
                WHERE end_time <= ? AND is_ended = 0
                """,
                now.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            if not expired_giveaways:
                return
                
            # Обновляем статус розыгрышей
            await self.db.execute(
                """
                UPDATE giveaways 
                SET is_ended = 1 
                WHERE end_time <= ? AND is_ended = 0
                """,
                now.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Завершаем каждый розыгрыш
            for giveaway in expired_giveaways:
                try:
                    channel = self.bot.get_channel(int(giveaway['channel_id']))
                    if channel:
                        message = await channel.fetch_message(int(giveaway['message_id']))
                        if message:
                            await self.end_giveaway(message)
                except Exception as e:
                    print(f"Ошибка при завершении розыгрыша: {e}")
                    continue
                    
        except Exception as e:
            print(f"Ошибка в check_giveaways: {e}")

    async def end_giveaway(self, message: discord.Message):
        """Завершает розыгрыш и выбирает победителей"""
        giveaway_data = await self.get_giveaway(message.id)
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
                            win_embed=Embed(
                                title="🎊 Поздравляем!",
                                description=f"Вы выиграли в розыгрыше **{giveaway_data['prize']}**!\n"
                                          f"Организатор свяжется с вами для передачи приза.",
                                color="GOLD"
                            )
                            await user.send(embed=win_embed)
                        except discord.Forbidden:
                            pass

                winners_text = "\n".join([f"🏆 {winner.mention}" for winner in winners])
                
                embed=Embed(
                    title=f"🎉 {giveaway_data['prize']}",
                    description=f"**Розыгрыш завершен!**\n\n"
                               f"**Победители:**\n{winners_text}\n\n"
                               f"**Организатор:** <@{giveaway_data['host_id']}>",
                    color="GREEN"
                )
            else:
                # Если нет участников, удаляем все реакции
                await message.clear_reactions()
                
                embed=Embed(
                    title=f"🎉 {giveaway_data['prize']}",
                    description="**Розыгрыш завершен!**\n\n"
                               "Победителей нет - никто не участвовал 😢",
                    color="RED"
                )
            
            await message.edit(embed=embed)
            
            if winners:
                winners_mentions = ", ".join([w.mention for w in winners])
                await message.channel.send(
                    embed=Embed(
                        title="🎊 Поздравляем победителей!",
                        description=f"**Приз:** {giveaway_data['prize']}\n"
                                  f"**Победители:** {winners_mentions}",
                        color="GOLD"
                    )
                )
            
            # Уведомляем организатора
            host = self.bot.get_user(int(giveaway_data['host_id']))
            if host:
                try:
                    host_embed=Embed(
                        title="🎉 Розыгрыш завершен",
                        description=f"Ваш розыгрыш **{giveaway_data['prize']}** завершен!\n"
                                  f"Победители: {winners_mentions if winners else 'нет победителей'}",
                        color="BLUE"
                    )
                    await host.send(embed=host_embed)
                except discord.Forbidden:
                    pass
            
            await self.db.execute(
                "UPDATE giveaways SET is_ended = 1 WHERE message_id = ?",
                (str(message.id),)
            )
                
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
                embed=Embed(
                    description=f"{Emojis.ERROR} Неверный формат длительности! Используйте: 1d, 12h, 30m, 10s",
                    color="RED"
                ),
                ephemeral=True
            )
            return None

        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        embed=Embed(
            title=f"🎉 {prize}",
            description=f"Нажмите на 🎉 чтобы участвовать!\n\n"
                       f"**Призовых мест:** {winners}\n"
                       f"**Организатор:** {ctx.user.mention}\n"
                       f"**Завершится:** <t:{int(end_time.timestamp())}:R>"
        )
        
        giveaway_message = await channel.send(embed=embed)
        await giveaway_message.add_reaction("🎉")
        
        # Сохраняем в базу данных
        await self.db.execute(
            """
            INSERT INTO giveaways 
            (channel_id, message_id, guild_id, host_id, prize, winners_count, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(channel.id),
                str(giveaway_message.id),
                str(ctx.guild_id),
                str(ctx.user.id),
                prize,
                winners,
                end_time.isoformat()
            )
        )
        
        self.active_giveaways[giveaway_message.id] = {
            'end_time': end_time,
            'message': giveaway_message
        }
        
        await ctx.response.send_message(
            embed=Embed(
                description=f"{Emojis.SUCCESS} Розыгрыш успешно создан в {channel.mention}!"
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
        await self.create_giveaway(interaction, prize, winners, duration, channel)

    @giveaway.command(name="end", description="Досрочно завершить розыгрыш")
    @app_commands.describe(message_id="ID сообщения с розыгрышем")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_end(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id = int(message_id)
            giveaway = await self.get_giveaway(message_id)
            
            if not giveaway:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Розыгрыш не найден!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            if giveaway['is_ended']:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Этот розыгрыш уже завершен!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            channel = self.bot.get_channel(int(giveaway['channel_id']))
            if not channel:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Канал розыгрыша не найден!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            message = await channel.fetch_message(message_id)
            if not message:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Сообщение розыгрыша не найдено!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            await self.end_giveaway(message)
            
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{Emojis.SUCCESS} Розыгрыш успешно завершен!",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{Emojis.ERROR} Неверный формат ID сообщения!",
                    color="RED"
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{Emojis.ERROR} Произошла ошибка: {e}",
                    color="RED"
                ),
                ephemeral=True
            )

    @giveaway.command(name="reroll", description="Выбрать новых победителей")
    @app_commands.describe(message_id="ID сообщения с розыгрышем")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            message_id = int(message_id)
            giveaway = await self.get_giveaway(message_id)
            
            if not giveaway:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Розыгрыш не найден!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            if not giveaway['is_ended']:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Этот розыгрыш еще не завершен!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            channel = self.bot.get_channel(int(giveaway['channel_id']))
            if not channel:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Канал розыгрыша не найден!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            message = await channel.fetch_message(message_id)
            if not message:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Сообщение розыгрыша не найдено!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            participants = giveaway['participants']
            if not participants:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} В розыгрыше не было участников!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            # Выбираем новых победителей
            winner_count = min(giveaway['winners_count'], len(participants))
            winner_ids = random.sample(participants, winner_count)
            winners = []
            
            for winner_id in winner_ids:
                user = self.bot.get_user(winner_id)
                if user:
                    winners.append(user)
                    try:
                        win_embed=Embed(
                            title="🎊 Поздравляем!",
                            description=f"Вы выиграли в перерозыгрыше **{giveaway['prize']}**!\n"
                                      f"Организатор свяжется с вами для передачи приза.",
                            color="GOLD"
                        )
                        await user.send(embed=win_embed)
                    except discord.Forbidden:
                        pass
            
            if winners:
                winners_text = "\n".join([f"🏆 {winner.mention}" for winner in winners])
                winners_mentions = ", ".join([w.mention for w in winners])
                
                reroll_embed=Embed(
                    title="🎲 Перерозыгрыш",
                    description=f"**Приз:** {giveaway['prize']}\n"
                               f"**Новые победители:**\n{winners_text}",
                    color="BLUE"
                )
                
                await message.reply(embed=reroll_embed)
                
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.SUCCESS} Перерозыгрыш успешно проведен!",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=Embed(
                        description=f"{Emojis.ERROR} Не удалось определить победителей!",
                        color="RED"
                    ),
                    ephemeral=True
                )
            
        except ValueError:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{Emojis.ERROR} Неверный формат ID сообщения!",
                    color="RED"
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{Emojis.ERROR} Произошла ошибка: {e}",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Giveaways(bot)) 