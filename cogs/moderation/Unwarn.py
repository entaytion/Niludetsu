import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu import (
    Embed,
    Emojis,
    helper_only,
    cooldown,
    Database
)

class Unwarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    @app_commands.command(name="unwarn", description="Снять предупреждение с пользователя")
    @app_commands.describe(
        user="Пользователь для снятия предупреждения",
        warn_id="ID предупреждения",
        reason="Причина снятия предупреждения"
    )
    @helper_only()
    @cooldown(seconds=3)
    async def unwarn(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        warn_id: int,
        reason: str = "Причина не указана"
    ):
        await self._unwarn_member(interaction, user, reason)
        
    async def _unwarn_member(self, ctx, member: discord.Member, reason: str):
        """Общая логика снятия предупреждения"""
        # Получаем активные предупреждения
        warnings = await self.db.fetch_all(
            """
            SELECT id FROM moderation 
            WHERE user_id = ? AND guild_id = ? AND type = 'warn' AND active = TRUE 
            ORDER BY created_at DESC LIMIT 1
            """,
            str(member.id), str(ctx.guild.id)
        )
        
        if not warnings:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description=f"У {member.mention} нет активных предупреждений",
                color="RED"
            )
        else:
            # Деактивируем последнее предупреждение
            await self.db.execute(
                """
                UPDATE moderation 
                SET active = FALSE, 
                    reason = reason || ' (Снято: ' || ? || ')'
                WHERE id = ?
                """,
                reason, warnings[0][0]
            )
            
            embed = Embed(
                title=f"{Emojis.SUCCESS} Предупреждение снято",
                description=(
                    f"{Emojis.DOT} **Участник:** {member.mention}\n"
                    f"{Emojis.DOT} **Причина снятия:** {reason}"
                ),
                color="GREEN"
            )
            
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Unwarn(bot)) 