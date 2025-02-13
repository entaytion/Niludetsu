import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from Niludetsu import (
    Embed,
    Emojis,
    mod_only,
    cooldown,
    Database,
    Tables
)

class Mutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="mutes", description="Показать список замученных пользователей")
    @app_commands.describe(
        page="Номер страницы"
    )
    @mod_only()
    @cooldown(seconds=3)
    async def mutes(
        self,
        interaction: discord.Interaction,
        page: int = 1
    ):
        if page < 1:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Номер страницы не может быть меньше 1!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Получаем список мутов
        mutes = await self.db.fetch_all(
            f"""
            SELECT * FROM {Tables.MODERATION}
            WHERE guild_id = ? AND type = 'mute' AND active = TRUE
            ORDER BY created_at DESC
            LIMIT 10 OFFSET ?
            """,
            str(interaction.guild_id), (page - 1) * 10
        )

        if not mutes:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.INFO} Список мутов",
                    description="На сервере нет замученных пользователей!",
                    color="BLUE"
                )
            )

        # Создаем эмбед
        mutes_embed = Embed(
            title=f"{Emojis.MUTE} Список замученных пользователей",
            description=f"Страница {page}",
            color="BLUE"
        )

        for mute in mutes:
            try:
                user = await self.bot.fetch_user(int(mute['user_id']))
                moderator = await self.bot.fetch_user(int(mute['moderator_id']))
                
                value = (
                    f"{Emojis.DOT} **Модератор:** {moderator.mention}\n"
                    f"{Emojis.DOT} **Причина:** {mute['reason']}\n"
                )
                
                if mute['expires_at']:
                    value += f"{Emojis.DOT} **Истекает:** <t:{int(datetime.fromisoformat(mute['expires_at']).timestamp())}:R>"
                else:
                    value += f"{Emojis.DOT} **Длительность:** Навсегда"
                
                mutes_embed.add_field(
                    name=f"{user} (ID: {user.id})",
                    value=value,
                    inline=False
                )
            except discord.NotFound:
                continue

        await interaction.response.send_message(embed=mutes_embed)

async def setup(bot):
    await bot.add_cog(Mutes(bot)) 