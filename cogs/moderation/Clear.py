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
                embed=create_embed(description="Нельзя удалить больше 1000 сообщений за раз!")
            )
        
        if amount < 1:
            return await interaction.response.send_message(
                embed=create_embed(description="Количество сообщений должно быть больше 0!")
            )
        
        try:
            # Сначала отправляем отложенный ответ
            await interaction.response.defer()
            
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
                # Иначе удаляем все сообщения
                deleted = 0
                while amount > 0:
                    # Discord позволяет удалять максимум 100 сообщений за раз
                    to_delete = min(amount, 100)
                    messages = await interaction.channel.purge(limit=to_delete)
                    deleted += len(messages)
                    amount -= to_delete
                    
                    # Если вернулось меньше сообщений чем запрошено, значит больше нет сообщений
                    if len(messages) < to_delete:
                        break
            
            # Отправляем сообщение об успешном удалении
            await interaction.followup.send(
                embed=create_embed(
                    title="🗑️ Очистка сообщений",
                    description=f"**Модератор:** {interaction.user.mention}\n"
                              f"**Канал:** {interaction.channel.mention}\n"
                              f"**Удалено сообщений:** `{deleted}`\n"
                              f"{'**Пользователь:** ' + member.mention if member else ''}"
                )
            )
            
            # Логируем действие если указан канал логов
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
                embed=create_embed(description="У меня недостаточно прав для удаления сообщений!")
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                embed=create_embed(description=f"Произошла ошибка при удалении сообщений: {str(e)}")
            )

async def setup(bot):
    await bot.add_cog(Clear(bot))