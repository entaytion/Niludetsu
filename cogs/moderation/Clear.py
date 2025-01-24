import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import json

def load_config():
    with open('config/config.json', 'r') as f:
        return json.load(f)

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
    
    @app_commands.command(name="clear", description="Очистить сообщения")
    @app_commands.describe(
        amount="Количество сообщений для удаления",
        member="Участник, чьи сообщения нужно удалить"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int, member: discord.Member = None):
        if amount > 1000:
            return await interaction.response.send_message(
                embed=create_embed(description="Нельзя удалить больше 1000 сообщений за раз!"),
                ephemeral=True
            )
        
        if amount < 1:
            return await interaction.response.send_message(
                embed=create_embed(description="Количество сообщений должно быть больше 0!"),
                ephemeral=True
            )
        
        try:
            await interaction.response.defer(thinking=True)
            
            if member:
                # Если указан пользователь, удаляем только его сообщения
                messages = []
                async for message in interaction.channel.history(limit=100):
                    if len(messages) == amount:
                        break
                    if message.author == member:
                        messages.append(message)
                
                await interaction.channel.delete_messages(messages)
                deleted = len(messages)
            else:
                # Иначе удаляем все сообщения, кроме команды
                deleted = 0
                while amount > 0:
                    to_delete = min(amount, 100)  # Discord позволяет удалять максимум 100 сообщений за раз
                    messages = [msg async for msg in interaction.channel.history(limit=to_delete) 
                              if msg.id != interaction.id]
                    if not messages:
                        break
                        
                    await interaction.channel.delete_messages(messages)
                    deleted += len(messages)
                    amount -= len(messages)
                    
                    if len(messages) < to_delete:
                        break

            # Отправляем сообщение о завершении очистки
            await interaction.followup.send(
                embed=create_embed(
                    title="🗑️ Очистка сообщений", 
                    description=f"**Модератор:** {interaction.user.mention}\n"
                              f"**Канал:** {interaction.channel.mention}\n"
                              f"**Удалено сообщений:** `{deleted}`\n"
                              f"{'**Пользователь:** ' + member.mention if member else ''}"
                )
            )

            # Логирование действия, если указана лог-комната
            log_channel_id = self.config.get('LOG_CHANNEL_ID')
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    await log_channel.send(
                        embed=create_embed(
                            title="🗑️ Очистка сообщений",
                            description=f"**Модератор:** {interaction.user.mention}\n"
                                      f"**Канал:** {interaction.channel.mention}\n"
                                      f"**Удалено сообщений:** `{deleted}`\n"
                                      f"{'**Пользователь:** ' + member.mention if member else ''}"
                        )
                    )
        
        except discord.Forbidden:
            await interaction.followup.send(
                embed=create_embed(description="У меня недостаточно прав для удаления сообщений!"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                embed=create_embed(description=f"Произошла ошибка при удалении сообщений: {str(e)}"),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Clear(bot))