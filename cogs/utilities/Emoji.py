import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import zipfile
from typing import Optional
from utils import create_embed, EMOJIS

class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="emoji", description="Управление эмодзи")
    async def emoji(self, interaction: discord.Interaction, *, emojis: Optional[str] = None):
        await interaction.response.defer()

        if not emojis:  # Если эмодзи не указаны, загружаем все
            # Создаем ZIP архив со всеми эмодзи
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                async with aiohttp.ClientSession() as session:
                    for guild_emoji in interaction.guild.emojis:
                        emoji_url = guild_emoji.url
                        async with session.get(str(emoji_url)) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                extension = '.gif' if guild_emoji.animated else '.png'
                                zip_file.writestr(f"{guild_emoji.name}{extension}", image_data)

            zip_buffer.seek(0)
            file = discord.File(zip_buffer, filename=f"all_emojis.zip")
            
            embed = create_embed(
                title="📥 Скачивание эмодзи",
                description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                          f"{EMOJIS['DOT']} **Количество:** `{len(interaction.guild.emojis)}`\n"
                          f"{EMOJIS['DOT']} **Формат:** ZIP-архив"
            )
            await interaction.followup.send(embed=embed, file=file)
            return

        # Загрузка нескольких эмодзи
        emoji_list = emojis.split()
        successful_downloads = []
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            async with aiohttp.ClientSession() as session:
                for emoji in emoji_list:
                    try:
                        emoji_id = int(emoji.split(':')[-1].rstrip('>'))
                        emoji_obj = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                        
                        if emoji_obj:
                            async with session.get(str(emoji_obj.url)) as response:
                                if response.status == 200:
                                    image_data = await response.read()
                                    extension = '.gif' if emoji_obj.animated else '.png'
                                    zip_file.writestr(f"{emoji_obj.name}{extension}", image_data)
                                    successful_downloads.append(emoji_obj.name)
                    except (ValueError, AttributeError):
                        continue

        if successful_downloads:
            zip_buffer.seek(0)
            file = discord.File(zip_buffer, filename="selected_emojis.zip")
            
            embed = create_embed(
                title="📥 Скачивание эмодзи",
                description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                          f"{EMOJIS['DOT']} **Скачано:** `{len(successful_downloads)}`\n"
                          f"{EMOJIS['DOT']} **Эмодзи:** {', '.join(f'`{name}`' for name in successful_downloads)}"
            )
            await interaction.followup.send(embed=embed, file=file)
        else:
            embed = create_embed(
                title="❌ Ошибка",
                description="Не удалось найти или скачать указанные эмодзи"
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Emoji(bot))