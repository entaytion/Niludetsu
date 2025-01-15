import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS
import re

class Partnership(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="partnership", description="Отправляет сообщение о партнёрстве в канал.")
    @app_commands.describe(user="Пользователь-партнёр", text="Сообщение о партнёрстве")
    async def partnership(self, interaction: discord.Interaction, user: discord.Member, text: str):
        if interaction.user.id != 636570363605680139:
            embed = create_embed(
                description="У вас нет прав для выполнения этой команды.",
                footer=FOOTER_ERROR)
            await interaction.response.send_message(embed=embed)
            return
        
        # Очищаем текст от упоминаний
        cleaned_text = text.replace("@everyone", "").replace("@here", "").replace(f"<@{interaction.user.id}>", "")
        match = re.search(r'https://discord\.gg/[^\s]+', cleaned_text)
        if match:
            discord_link = match.group(0)
            cleaned_text = cleaned_text.replace(discord_link, '')
            prefix = (f"Партнёр - {user.mention}\n"
                      f"Ссылка на сервер - {discord_link}\n")
            await interaction.response.send_message(prefix, allowed_mentions=discord.AllowedMentions.none())
            embed = create_embed(
                description=f"{cleaned_text}",
            )
            await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Partnership(client))
