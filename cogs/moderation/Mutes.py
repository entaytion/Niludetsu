import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import json
from datetime import datetime

def load_config():
    with open('config/config.json', 'r') as f:
        return json.load(f)

class Mutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
    
    @app_commands.command(name="mutes", description="Показать список замученных участников")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute_list(self, interaction: discord.Interaction):
        # Получаем роль мута из конфига
        mute_role_id = self.config.get('MUTE_ROLE_ID')
        if not mute_role_id:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не настроена в конфигурации!"),
                ephemeral=True
            )

        mute_role = interaction.guild.get_role(int(mute_role_id))
        if not mute_role:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не найдена на сервере!"),
                ephemeral=True
            )

        # Получаем список замученных участников
        muted_members = []
        for member in mute_role.members:
            if member.is_timed_out():
                # Получаем оставшееся время мута
                time_remaining = member.timed_out_until - datetime.now(member.timed_out_until.tzinfo)
                days = time_remaining.days
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # Форматируем время
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days}д")
                if hours > 0:
                    time_parts.append(f"{hours}ч")
                if minutes > 0:
                    time_parts.append(f"{minutes}м")
                if seconds > 0:
                    time_parts.append(f"{seconds}с")
                
                duration = " ".join(time_parts) if time_parts else "< 1с"
                muted_members.append(f"• {member.mention} - осталось: **{duration}**")
            else:
                # Если у участника есть роль мута, но нет таймаута - значит мут навсегда
                muted_members.append(f"• {member.mention} - **Навсегда**")

        if not muted_members:
            embed = create_embed(
                title="📋 Список замученных",
                description="На данный момент нет замученных участников",
                color=0x2F3136
            )
        else:
            embed = create_embed(
                title="📋 Список замученных",
                description="\n".join(muted_members),
                color=0xFF0000
            )
            embed.set_footer(text=f"Всего замучено: {len(muted_members)}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Mutes(bot)) 