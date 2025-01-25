import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, DB_PATH, initialize_table, TABLES_SCHEMAS
import sqlite3
from datetime import datetime
import asyncio

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        
    def setup_database(self):
        initialize_table('afk', TABLES_SCHEMAS['afk'])

    @app_commands.command(name="afk", description="Установить статус AFK")
    @app_commands.describe(reason="Причина отсутствия (необязательно)")
    async def afk(self, interaction: discord.Interaction, reason: str = "Причина не указана"):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Проверяем, не в AFK ли уже пользователь
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reason FROM afk WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            existing = cursor.fetchone()
            
            if existing:
                # Удаляем AFK статус
                cursor.execute("DELETE FROM afk WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
                conn.commit()
                
                # Убираем [AFK] из никнейма
                try:
                    current_nick = interaction.user.display_name
                    if current_nick.startswith("[AFK] "):
                        await interaction.user.edit(nick=current_nick[6:])
                except discord.Forbidden:
                    pass
                
                await interaction.response.send_message(
                    embed=create_embed(
                        title="👋 С возвращением!",
                        description="Ваш статус AFK был снят"
                    ),
                    ephemeral=True
                )
                return
            
            # Устанавливаем AFK статус
            cursor.execute(
                "INSERT OR REPLACE INTO afk (user_id, guild_id, reason, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, reason, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            
            # Добавляем [AFK] к никнейму
            try:
                current_nick = interaction.user.display_name
                if not current_nick.startswith("[AFK] "):
                    await interaction.user.edit(nick=f"[AFK] {current_nick}")
            except discord.Forbidden:
                pass
            
            await interaction.response.send_message(
                embed=create_embed(
                    title="💤 AFK статус установлен",
                    description=f"**Причина:** {reason}"
                ),
                ephemeral=True
            )
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Проверяем упоминания в сообщении
        mentioned_users = message.mentions
        if mentioned_users:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                for user in mentioned_users:
                    cursor.execute(
                        "SELECT reason, timestamp FROM afk WHERE user_id = ? AND guild_id = ?",
                        (user.id, message.guild.id)
                    )
                    afk_data = cursor.fetchone()
                    
                    if afk_data:
                        reason, timestamp = afk_data
                        afk_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        time_passed = datetime.now() - afk_time
                        
                        # Форматируем время отсутствия
                        hours = time_passed.seconds // 3600
                        minutes = (time_passed.seconds % 3600) // 60
                        time_str = ""
                        if time_passed.days > 0:
                            time_str += f"{time_passed.days}д "
                        if hours > 0:
                            time_str += f"{hours}ч "
                        time_str += f"{minutes}м"
                        
                        await message.reply(
                            embed=create_embed(
                                title="💤 Пользователь AFK",
                                description=f"{user.mention} сейчас отсутствует\n"
                                          f"**Причина:** {reason}\n"
                                          f"**Отсутствует:** {time_str}"
                            ),
                            delete_after=10
                        )
        
        # Проверяем, не вернулся ли AFK пользователь
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT reason FROM afk WHERE user_id = ? AND guild_id = ?", 
                (message.author.id, message.guild.id)
            )
            afk_data = cursor.fetchone()
            
            if afk_data:
                # Удаляем AFK статус при любой активности
                cursor.execute(
                    "DELETE FROM afk WHERE user_id = ? AND guild_id = ?", 
                    (message.author.id, message.guild.id)
                )
                conn.commit()
                
                # Убираем [AFK] из никнейма
                try:
                    current_nick = message.author.display_name
                    if current_nick.startswith("[AFK] "):
                        await message.author.edit(nick=current_nick[6:])
                except discord.Forbidden:
                    pass
                
                welcome_msg = await message.channel.send(
                    embed=create_embed(
                        title="👋 С возвращением!",
                        description=f"{message.author.mention}, ваш статус AFK был автоматически снят"
                    )
                )
                await asyncio.sleep(5)
                try:
                    await welcome_msg.delete()
                except:
                    pass

async def setup(bot):
    await bot.add_cog(AFK(bot)) 