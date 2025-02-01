import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.database import Database
from datetime import datetime
import asyncio
import traceback

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self.db.init())  # Асинхронная инициализация базы данных
        
    @app_commands.command(name="afk", description="Установить статус AFK")
    @app_commands.describe(reason="Причина отсутствия (необязательно)")
    async def afk(self, interaction: discord.Interaction, reason: str = "Причина не указана"):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        # Проверяем, не в AFK ли уже пользователь
        result = await self.db.fetch_one(
            """
            SELECT reason 
            FROM afk 
            WHERE user_id = ? AND guild_id = ?
            """,
            user_id, guild_id
        )
            
        if result:
            # Удаляем AFK статус
            await self.db.execute(
                """
                DELETE FROM afk 
                WHERE user_id = ? AND guild_id = ?
                """,
                user_id, guild_id
            )
                
            # Убираем [AFK] из никнейма
            try:
                current_nick = interaction.user.display_name
                if current_nick.startswith("[AFK] "):
                    await interaction.user.edit(nick=current_nick[6:])
            except discord.Forbidden:
                pass
                
            await interaction.response.send_message(
                embed=Embed(
                    title="👋 С возвращением!",
                    description="Ваш статус AFK был снят"
                )
            )
            return
            
        # Устанавливаем AFK статус
        await self.db.execute(
            """
            INSERT OR REPLACE INTO afk (user_id, guild_id, reason, timestamp) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            user_id, guild_id, reason
        )
            
        # Добавляем [AFK] к никнейму
        try:
            current_nick = interaction.user.display_name
            if not current_nick.startswith("[AFK] "):
                await interaction.user.edit(nick=f"[AFK] {current_nick}")
        except discord.Forbidden:
            pass
            
        await interaction.response.send_message(
            embed=Embed(
                title="💤 AFK статус установлен",
                description=f"**Причина:** {reason}"
            )
        )
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        try:
            # Проверяем упоминания
            for member in message.mentions:
                result = await self.db.fetch_one(
                    """
                    SELECT reason, strftime('%s', timestamp) as unix_time 
                    FROM afk 
                    WHERE user_id = ? AND guild_id = ?
                    """,
                    str(member.id), str(message.guild.id)
                )
                
                if result:
                    await message.reply(
                        embed=Embed(
                            title=f"{EMOJIS['INFO']} Пользователь AFK",
                            description=f"{member.mention} сейчас AFK\nПричина: {result['reason']}\nУшел: <t:{result['unix_time']}:R>",
                            color="YELLOW"
                        )
                    )

            # Проверяем возвращение из AFK
            result = await self.db.fetch_one(
                """
                SELECT reason, strftime('%s', timestamp) as unix_time 
                FROM afk 
                WHERE user_id = ? AND guild_id = ?
                """,
                str(message.author.id), str(message.guild.id)
            )
            
            if result:
                await self.db.execute(
                    """
                    DELETE FROM afk 
                    WHERE user_id = ? AND guild_id = ?
                    """,
                    str(message.author.id), str(message.guild.id)
                )
                
                # Убираем [AFK] из никнейма
                try:
                    current_nick = message.author.display_name
                    if current_nick.startswith("[AFK] "):
                        await message.author.edit(nick=current_nick[6:])
                except discord.Forbidden:
                    pass
                
                await message.reply(
                    embed=Embed(
                        title=f"{EMOJIS['SUCCESS']} С возвращением!",
                        description=f"Вы вернулись из AFK\nПричина была: {result['reason']}\nОтсутствовали: <t:{result['unix_time']}:R>",
                        color="GREEN"
                    )
                )
                
        except Exception as e:
            print(f"❌ Ошибка при обработке AFK: {e}")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(AFK(bot)) 