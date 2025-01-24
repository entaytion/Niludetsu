import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import json

def load_config():
    with open('config/config.json', 'r') as f:
        return json.load(f)

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
    
    @app_commands.command(name="unmute", description="Размутить участника")
    @app_commands.describe(
        member="Участник, которого нужно размутить",
        reason="Причина размута"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Причина не указана"):
        # Проверяем, может ли бот размутить участников
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=create_embed(description="У меня нет прав на размут участников!")
            )
        
        # Проверяем, замучен ли участник
        if not member.is_timed_out():
            return await interaction.response.send_message(
                embed=create_embed(description="Этот участник не замучен!")
            )
        
        try:
            # Размучиваем участника
            await member.timeout(None, reason=reason)
            
            # Отправляем сообщение
            await interaction.response.send_message(
                embed=create_embed(
                    title="🔊 Размут",
                    description=f"**Модератор:** {interaction.user.mention}\n"
                              f"**Участник:** {member.mention}\n"
                              f"**Причина:** `{reason}`"
                )
            )
            
            # Логируем действие если указан канал логов
            log_channel_id = self.config.get('LOG_CHANNEL_ID')
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    await log_channel.send(
                        embed=create_embed(
                            title="🔊 Размут",
                            description=f"**Модератор:** {interaction.user.mention}\n"
                                      f"**Участник:** {member.mention}\n"
                                      f"**Причина:** `{reason}`"
                        )
                    )
        
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(description="У меня недостаточно прав для размута этого участника!")
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(description=f"Произошла ошибка: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(Unmute(bot))