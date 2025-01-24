import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import zipfile
from utils import create_embed, EMOJIS

class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="emoji", description="Управление эмодзи")
    async def emoji(self, interaction: discord.Interaction, *emojis: str):
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
                                # Сохраняем с расширением .png или .gif
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

        # Если указано несколько эмодзи, создаем архив
        if len(emojis) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                async with aiohttp.ClientSession() as session:
                    for emoji_str in emojis:
                        try:
                            emoji_id = int(emoji_str.split(':')[-1].rstrip('>'))
                            emoji_obj = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                            
                            if emoji_obj:
                                async with session.get(str(emoji_obj.url)) as response:
                                    if response.status == 200:
                                        image_data = await response.read()
                                        extension = '.gif' if emoji_obj.animated else '.png'
                                        zip_file.writestr(f"{emoji_obj.name}{extension}", image_data)
                        except (ValueError, AttributeError):
                            continue

            zip_buffer.seek(0)
            file = discord.File(zip_buffer, filename="selected_emojis.zip")
            
            embed = create_embed(
                title="📥 Скачивание эмодзи",
                description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                          f"{EMOJIS['DOT']} **Количество:** `{len(emojis)}`\n"
                          f"{EMOJIS['DOT']} **Формат:** ZIP-архив"
            )
            await interaction.followup.send(embed=embed, file=file)
            return

        # Загрузка одного эмодзи
        try:
            emoji_id = int(emojis[0].split(':')[-1].rstrip('>'))
            emoji_obj = discord.utils.get(interaction.guild.emojis, id=emoji_id)
            
            if emoji_obj:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(emoji_obj.url)) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            extension = '.gif' if emoji_obj.animated else '.png'
                            file = discord.File(io.BytesIO(image_data), filename=f"{emoji_obj.name}{extension}")
                            
                            embed = create_embed(
                                title="📥 Скачивание эмодзи",
                                description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                                          f"{EMOJIS['DOT']} **Название:** `{emoji_obj.name}`\n"
                                          f"{EMOJIS['DOT']} **Анимированный:** `{'Да' if emoji_obj.animated else 'Нет'}`"
                            )
                            await interaction.followup.send(embed=embed, file=file)
                            return

        except (ValueError, AttributeError):
            pass

        # Если что-то пошло не так
        embed = create_embed(
            title="❌ Ошибка",
            description="Не удалось найти или скачать указанный эмодзи"
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Emoji(bot))