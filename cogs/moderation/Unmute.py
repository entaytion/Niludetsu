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

        # Получаем роль мута из конфига
        mute_role_id = self.config.get('MUTE_ROLE_ID')
        if not mute_role_id:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не настроена в конфигурации!")
            )

        mute_role = interaction.guild.get_role(int(mute_role_id))
        if not mute_role:
            return await interaction.response.send_message(
                embed=create_embed(description="Роль мута не найдена на сервере!")
            )

        # Проверяем, есть ли у участника роль мута или таймаут
        has_mute_role = mute_role in member.roles
        is_timed_out = member.is_timed_out()

        if not has_mute_role and not is_timed_out:
            return await interaction.response.send_message(
                embed=create_embed(description="Этот участник не замучен!")
            )

        try:
            # Снимаем роль мута, если она есть
            if has_mute_role:
                await member.remove_roles(mute_role, reason=reason)

            # Снимаем таймаут, если он есть
            if is_timed_out:
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
            
            # Отправляем сообщение участнику в ЛС
            try:
                await member.send(
                    embed=create_embed(
                        title="🔊 Вы были размучены",
                        description=f"**Сервер:** {interaction.guild.name}\n"
                                  f"**Модератор:** {interaction.user}\n"
                                  f"**Причина:** `{reason}`"
                    )
                )
            except discord.Forbidden:
                pass  # Если у пользователя закрыты ЛС, просто пропускаем
            
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