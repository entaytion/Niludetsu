import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import zipfile
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    emoji_group = app_commands.Group(name="emoji", description="Управление эмодзи")

    @emoji_group.command(name="download", description="Скачать эмодзи")
    @app_commands.describe(emoji="Эмодзи для скачивания (оставьте пустым для скачивания всех)")
    async def emoji_download(self, interaction: discord.Interaction, emoji: Optional[str] = None):
        """Скачать одно или несколько эмодзи"""
        await interaction.response.defer()

        if not emoji:  # Если эмодзи не указано, загружаем все
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
            
            embed=Embed(
                title="📥 Скачивание эмодзи",
                description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                          f"{EMOJIS['DOT']} **Количество:** `{len(interaction.guild.emojis)}`\n"
                          f"{EMOJIS['DOT']} **Формат:** ZIP-архив"
            )
            await interaction.followup.send(embed=embed, file=file)
            return

        try:
            # Пытаемся получить ID эмодзи
            emoji_id = int(emoji.split(':')[-1].rstrip('>'))
            emoji_obj = discord.utils.get(interaction.guild.emojis, id=emoji_id)
            
            if not emoji_obj:
                raise ValueError("Эмодзи не найдено")

            # Скачиваем одно эмодзи
            async with aiohttp.ClientSession() as session:
                async with session.get(str(emoji_obj.url)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        extension = '.gif' if emoji_obj.animated else '.png'
                        file = discord.File(io.BytesIO(image_data), filename=f"{emoji_obj.name}{extension}")
                        
                        embed=Embed(
                            title="📥 Скачивание эмодзи",
                            description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                                      f"{EMOJIS['DOT']} **Имя:** `{emoji_obj.name}`\n"
                                      f"{EMOJIS['DOT']} **Формат:** `{extension[1:]}`"
                        )
                        await interaction.followup.send(embed=embed, file=file)
                    else:
                        raise ValueError("Не удалось скачать эмодзи")

        except (ValueError, AttributeError) as e:
            embed=Embed(
                title="❌ Ошибка",
                description=str(e) if str(e) != "Эмодзи не найдено" else "Не удалось найти указанное эмодзи",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=embed)

    @emoji_group.command(name="pack", description="Скачать несколько эмодзи")
    @app_commands.describe(emojis="Список эмодзи через пробел")
    async def emoji_pack(self, interaction: discord.Interaction, emojis: str):
        """Скачать несколько эмодзи в ZIP-архиве"""
        await interaction.response.defer()

        emoji_list = emojis.split()
        successful_downloads = []
        failed_downloads = []
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
                                else:
                                    failed_downloads.append(emoji_obj.name)
                        else:
                            failed_downloads.append(emoji)
                    except (ValueError, AttributeError):
                        failed_downloads.append(emoji)

        if successful_downloads:
            zip_buffer.seek(0)
            file = discord.File(zip_buffer, filename="emoji_pack.zip")
            
            description = [
                f"{EMOJIS['DOT']} **Статус:** {'Частично успешно' if failed_downloads else 'Успешно'}",
                f"{EMOJIS['DOT']} **Скачано:** `{len(successful_downloads)}`",
                f"{EMOJIS['DOT']} **Успешно:** {', '.join(f'`{name}`' for name in successful_downloads)}"
            ]
            
            if failed_downloads:
                description.append(f"{EMOJIS['DOT']} **Не удалось:** {', '.join(f'`{name}`' for name in failed_downloads)}")
            
            embed=Embed(
                title="📥 Скачивание эмодзи",
                description="\n".join(description)
            )
            await interaction.followup.send(embed=embed, file=file)
        else:
            embed=Embed(
                title="❌ Ошибка",
                description="Не удалось найти или скачать указанные эмодзи",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=embed)

    @emoji_group.command(name="all", description="Скачать все эмодзи сервера")
    async def emoji_all(self, interaction: discord.Interaction):
        """Скачать все эмодзи сервера в ZIP-архиве"""
        await interaction.response.defer()

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
        
        embed=Embed(
            title="📥 Скачивание эмодзи",
            description=f"{EMOJIS['DOT']} **Статус:** Успешно\n"
                      f"{EMOJIS['DOT']} **Количество:** `{len(interaction.guild.emojis)}`\n"
                      f"{EMOJIS['DOT']} **Формат:** ZIP-архив"
        )
        await interaction.followup.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Emoji(bot))