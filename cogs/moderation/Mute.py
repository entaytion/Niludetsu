import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import yaml
import datetime

def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
    
    @app_commands.command(name="mute", description="Замутить участника")
    @app_commands.describe(
        member="Участник, которого нужно замутить",
        reason="Причина мута",
        duration="Длительность мута (s - секунды, m - минуты, h - часы, d - дни). Если не указано - мут навсегда"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Причина не указана", duration: str = None):
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

        # Получаем роль мута из конфига
        mute_role_id = self.config.get('moderation', {}).get('mute_role')
        if not mute_role_id:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не настроена в конфигурации!")
            )

        mute_role = interaction.guild.get_role(int(mute_role_id))
        if not mute_role:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не найдена на сервере!")
            )
        
        try:
            timeout_duration = None
            # Если указана длительность, парсим время и устанавливаем таймаут
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
                    timeout_duration = datetime.timedelta(seconds=seconds)
                    await member.timeout(timeout_duration, reason=reason)
                except ValueError:
                    return await interaction.response.send_message(
                        embed=create_embed(description="Неверный формат времени!")
                    )
            
            # Выдаем роль мута в любом случае
            await member.add_roles(mute_role, reason=reason)
            
            # Отправляем сообщение
            await interaction.response.send_message(
                embed=create_embed(
                    title="🔇 Мут",
                    description=f"**Модератор:** {interaction.user.mention}\n"
                              f"**Нарушитель:** {member.mention}\n"
                              f"**Причина:** {reason}\n"
                              f"**Длительность:** {'Навсегда' if not duration else f'{timeout_duration}'}"
                )
            )
            
            # Отправляем уведомление пользователю в ЛС
            try:
                await member.send(
                    embed=create_embed(
                        title="🔇 Вы были замучены",
                        description=f"**Сервер:** {interaction.guild.name}\n"
                                  f"**Модератор:** {interaction.user}\n"
                                  f"**Причина:** {reason}\n"
                                  f"**Длительность:** {'Навсегда' if not duration else f'{timeout_duration}'}"
                    )
                )
            except discord.Forbidden:
                pass  # Если у пользователя закрыты ЛС, игнорируем ошибку
            
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
                                      f"**Длительность:** {'Навсегда' if not duration else f'{timeout_duration}'}"
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