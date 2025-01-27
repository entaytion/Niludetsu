import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, has_helper_role, command_cooldown
import asyncio

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="clear", description="Очистить сообщения в канале")
    @app_commands.describe(
        amount="Количество сообщений для удаления (1-100)",
        user="Удалить сообщения только от конкретного пользователя"
    )
    @has_helper_role()
    @command_cooldown()
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
        user: discord.Member = None
    ):
        if amount > 1000:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Нельзя удалить больше 1000 сообщений за раз!",
                    color='RED'
                ),
                ephemeral=True
            )
            return
        
        if amount < 1:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Количество сообщений должно быть больше 0!",
                    color='RED'
                ),
                ephemeral=True
            )
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = 0
            
            if user:
                # Если указан пользователь, удаляем только его сообщения
                messages = []
                async for message in interaction.channel.history(limit=100):
                    if len(messages) == amount:
                        break
                    if message.author == user:
                        messages.append(message)
                
                if messages:
                    await interaction.channel.delete_messages(messages)
                    deleted = len(messages)
            else:
                # Иначе удаляем все сообщения
                while amount > 0:
                    to_delete = min(amount, 100)  # Discord позволяет удалять максимум 100 сообщений за раз
                    messages = [msg async for msg in interaction.channel.history(limit=to_delete)]
                    if not messages:
                        break
                        
                    await interaction.channel.delete_messages(messages)
                    deleted += len(messages)
                    amount -= len(messages)
                    
                    if len(messages) < to_delete:
                        break

            # Отправляем сообщение о завершении очистки
            embed = create_embed(
                title="🗑️ Очистка сообщений", 
                description=f"**Модератор:** {interaction.user.mention}\n"
                          f"**Канал:** {interaction.channel.mention}\n"
                          f"**Удалено сообщений:** `{deleted}`\n"
                          f"{'**Пользователь:** ' + user.mention if user else ''}",
                color='GREEN'
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Отправляем временное сообщение в канал
            temp_msg = await interaction.channel.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await temp_msg.delete()
            except discord.NotFound:
                pass
        
        except discord.Forbidden:
            await interaction.followup.send(
                embed=create_embed(
                    description="У меня недостаточно прав для удаления сообщений!",
                    color='RED'
                ),
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Произошла ошибка при удалении сообщений: {str(e)}",
                    color='RED'
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Произошла неизвестная ошибка: {str(e)}",
                    color='RED'
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Clear(bot))