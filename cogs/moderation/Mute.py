import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import json
import datetime

def load_config():
    with open('config/config.json', 'r') as f:
        return json.load(f)

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
    
    @app_commands.command(name="mute", description="Замутить участника")
    @app_commands.describe(
        member="Участник, которого нужно замутить",
        duration="Длительность мута (s - секунды, m - минуты, h - часы, d - дни)",
        reason="Причина мута"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: str = None, reason: str = "Причина не указана"):
        # Проверяем, может ли бот мутить участников
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=create_embed(description="У меня нет прав на мут участников!")
            )
        
        # Проверяем, не пытается ли замутить администратора
        if member.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=create_embed(description="Я не могу замутить администратора!")
            )
        
        # Проверяем, не пытается ли замутить бота
        if member.bot:
            return await interaction.response.send_message(
                embed=create_embed(description="Я не могу замутить бота!")
            )
        
        # Проверяем, не пытается ли замутить себя
        if member == interaction.user:
            return await interaction.response.send_message(
                embed=create_embed(description="Вы не можете замутить себя!")
            )
        
        # Парсим время
        if duration:
            time_units = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400
            }
            
            try:
                time = int(duration[:-1])
                unit = duration[-1].lower()
                
                if unit not in time_units:
                    return await interaction.response.send_message(
                        embed=create_embed(description="Неверный формат времени! Используйте s/m/h/d")
                    )
                
                seconds = time * time_units[unit]
                duration = datetime.timedelta(seconds=seconds)
            except ValueError:
                return await interaction.response.send_message(
                    embed=create_embed(description="Неверный формат времени!")
                )
        else:
            duration = None
        
        try:
            # Мутим участника
            await member.timeout(duration, reason=reason)
            
            # Отправляем сообщение
            await interaction.response.send_message(
                embed=create_embed(
                    title="🔇 Мут",
                    description=f"**Модератор:** {interaction.user.mention}\n"
                              f"**Нарушитель:** {member.mention}\n"
                              f"**Причина:** {reason}\n"
                              f"**Длительность:** {'Бессрочно' if not duration else str(duration)}"
                )
            )
            
            # Логируем действие если указан канал логов
            log_channel_id = self.config.get('LOG_CHANNEL_ID')
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    await log_channel.send(
                        embed=create_embed(
                            title="🔇 Мут",
                            description=f"**Модератор:** {interaction.user.mention}\n"
                                      f"**Нарушитель:** {member.mention}\n"
                                      f"**Причина:** {reason}\n"
                                      f"**Длительность:** {'Бессрочно' if not duration else str(duration)}"
                        )
                    )
        
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(description="У меня недостаточно прав для мута этого участника!")
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(description=f"Произошла ошибка: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(Mute(bot))