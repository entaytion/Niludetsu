import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import re

class Partnership(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="partnership", description="Отправляет сообщение о партнёрстве в канал.")
    @app_commands.describe(user="Пользователь-партнёр", text="Сообщение о партнёрстве или ссылка на сообщение")
    async def partnership(self, interaction: discord.Interaction, user: discord.Member, text: str):
        if interaction.user.id != 636570363605680139:
            embed = create_embed(
                description="У вас нет прав для выполнения этой команды.")
            await interaction.response.send_message(embed=embed)
            return
        
        # Проверяем, является ли text ссылкой на сообщение Discord
        message_link_match = re.match(r'https://(?:ptb\.|canary\.)?discord\.com/channels/(\d+)/(\d+)/(\d+)', text)
        
        if message_link_match:
            try:
                guild_id, channel_id, message_id = map(int, message_link_match.groups())
                guild = self.client.get_guild(guild_id)
                if not guild:
                    embed = create_embed(
                        description="Бот не находится на сервере, с которого вы пытаетесь получить сообщение."
                    )
                    await interaction.response.send_message(embed=embed)
                    return
                    
                channel = guild.get_channel(channel_id)
                if not channel:
                    embed = create_embed(
                        description="Канал не найден."
                    )
                    await interaction.response.send_message(embed=embed)
                    return
                    
                message = await channel.fetch_message(message_id)
                if not message:
                    embed = create_embed(
                        description="Сообщение не найдено."
                    )
                    await interaction.response.send_message(embed=embed)
                    return
                
                # Получаем текст из сообщения
                cleaned_text = message.content
            except discord.Forbidden:
                embed = create_embed(
                    description="У бота нет прав для чтения сообщений в указанном канале."
                )
                await interaction.response.send_message(embed=embed)
                return
            except Exception as e:
                embed = create_embed(
                    description=f"Произошла ошибка при получении сообщения: {str(e)}"
                )
                await interaction.response.send_message(embed=embed)
                return
        else:
            cleaned_text = text

        # Очищаем текст от упоминаний
        cleaned_text = cleaned_text.replace("@everyone", "").replace("@here", "").replace(f"<@{interaction.user.id}>", "")
        match = re.search(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite)/[^\s]+', cleaned_text)
        
        if match:
            discord_link = match.group(0)
            cleaned_text = cleaned_text.replace(discord_link, '')
            prefix = (f"Партнёр - {user.mention}\n"
                      f"Ссылка на сервер - {discord_link}\n")
            await interaction.channel.send(prefix, allowed_mentions=discord.AllowedMentions.none())
            embed = create_embed(
                description=f"{cleaned_text}",
            )
            await interaction.response.send_message("Сообщение о партнерстве отправлено!")
            await interaction.channel.send(embed=embed)
        else:
            embed = create_embed(
                description="Не найдена ссылка на Discord сервер в сообщении."
            )
            await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Partnership(client))
