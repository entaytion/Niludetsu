import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    @app_commands.command(name="warns", description="Показать предупреждения участника")
    @app_commands.describe(member="Участник для просмотра предупреждений")
    async def warns_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        await self._show_warns(interaction, member)
        
    async def _show_warns(self, ctx, member: discord.Member):
        """Общая логика отображения предупреждений"""
        # Получаем активные предупреждения
        warnings = await self.db.fetch_all(
            """
            SELECT moderator_id, reason, created_at 
            FROM moderation 
            WHERE user_id = ? AND guild_id = ? AND type = 'warn' AND active = TRUE 
            ORDER BY created_at DESC
            """,
            str(member.id), str(ctx.guild.id)
        )
        
        if not warnings:
            embed = Embed(
                title=f"{Emojis.WARNING} Предупреждения",
                description=f"У {member.mention} нет активных предупреждений",
                color="GREEN"
            )
        else:
            embed = Embed(
                title=f"{Emojis.WARNING} Предупреждения {member}",
                description=f"Всего активных предупреждений: {len(warnings)}",
                color="YELLOW"
            )
            
            for i, warn in enumerate(warnings, 1):
                moderator = ctx.guild.get_member(int(warn[0]))
                moderator_mention = moderator.mention if moderator else f"ID: {warn[0]}"
                
                embed.add_field(
                    name=f"Предупреждение #{i}",
                    value=(
                        f"{Emojis.DOT} **Модератор:** {moderator_mention}\n"
                        f"{Emojis.DOT} **Причина:** {warn[1]}\n"
                        f"{Emojis.DOT} **Дата:** <t:{int(warn[2].timestamp())}:R>"
                    ),
                    inline=False
                )
                
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Warns(bot))