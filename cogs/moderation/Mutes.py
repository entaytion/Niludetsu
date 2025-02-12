import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
from Niludetsu.database.db import Database

class Mutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="mutes", description="Показать список мутов")
    @app_commands.describe(member="Участник для просмотра мутов")
    @has_mod_role()
    async def mutes_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._show_mutes(interaction, member)
        
    async def _show_mutes(self, ctx, member: discord.Member = None):
        """Общая логика отображения мутов"""
        # Формируем SQL запрос
        if member:
            query = """
                SELECT user_id, moderator_id, reason, created_at, expires_at 
                FROM moderation 
                WHERE guild_id = ? AND type = 'mute' AND active = TRUE AND user_id = ?
                ORDER BY created_at DESC
            """
            params = [str(ctx.guild.id), str(member.id)]
        else:
            query = """
                SELECT user_id, moderator_id, reason, created_at, expires_at 
                FROM moderation 
                WHERE guild_id = ? AND type = 'mute' AND active = TRUE
                ORDER BY created_at DESC
            """
            params = [str(ctx.guild.id)]
            
        # Получаем активные муты
        mutes = await self.db.fetch_all(query, *params)
        
        if not mutes:
            description = f"У {member.mention} нет активных мутов" if member else "На сервере нет замученных участников"
            embed = Embed(
                title=f"{Emojis.INFO} Активные муты",
                description=description,
                color="GREEN"
            )
        else:
            embed = Embed(
                title=f"{Emojis.INFO} Активные муты",
                description=f"Всего активных мутов: {len(mutes)}",
                color="YELLOW"
            )
            
            for mute in mutes:
                user = ctx.guild.get_member(int(mute[0]))
                if not user:
                    continue
                    
                moderator = ctx.guild.get_member(int(mute[1]))
                moderator_mention = moderator.mention if moderator else f"ID: {mute[1]}"
                
                created_at = int(mute[3].timestamp())
                expires_at = int(mute[4].timestamp())
                
                embed.add_field(
                    name=f"Мут {user}",
                    value=(
                        f"{Emojis.DOT} **Модератор:** {moderator_mention}\n"
                        f"{Emojis.DOT} **Причина:** {mute[2]}\n"
                        f"{Emojis.DOT} **Выдан:** <t:{created_at}:R>\n"
                        f"{Emojis.DOT} **Истекает:** <t:{expires_at}:R>"
                    ),
                    inline=False
                )
                
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Mutes(bot)) 