import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import zipfile
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

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
                description=f"{Emojis.DOT} **Статус:** Успешно\n"
                          f"{Emojis.DOT} **Количество:** `{len(interaction.guild.emojis)}`\n"
                          f"{Emojis.DOT} **Формат:** ZIP-архив"
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
                            description=f"{Emojis.DOT} **Статус:** Успешно\n"
                                      f"{Emojis.DOT} **Имя:** `{emoji_obj.name}`\n"
                                      f"{Emojis.DOT} **Формат:** `{extension[1:]}`"
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
                f"{Emojis.DOT} **Статус:** {'Частично успешно' if failed_downloads else 'Успешно'}",
                f"{Emojis.DOT} **Скачано:** `{len(successful_downloads)}`",
                f"{Emojis.DOT} **Успешно:** {', '.join(f'`{name}`' for name in successful_downloads)}"
            ]
            
            if failed_downloads:
                description.append(f"{Emojis.DOT} **Не удалось:** {', '.join(f'`{name}`' for name in failed_downloads)}")
            
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
            description=f"{Emojis.DOT} **Статус:** Успешно\n"
                      f"{Emojis.DOT} **Количество:** `{len(interaction.guild.emojis)}`\n"
                      f"{Emojis.DOT} **Формат:** ZIP-архив"
        )
        await interaction.followup.send(embed=embed, file=file)

    @commands.command(
        name="addemoji",
        description="Добавить эмодзи на сервер",
        aliases=['adde']
    )
    @commands.is_owner()
    async def add_emoji(self, ctx, *, emoji_text: str):
        """Добавить эмодзи на сервер из ссылки в тексте
        
        Параметры:
        ---------------
        emoji_text: Текст, содержащий название и ссылку на эмодзи в формате [name](url)
        """
        try:
            # Извлекаем имя и URL из текста формата [name](url)
            import re
            match = re.match(r'\[(.+?)\]\((.+?)\)', emoji_text)
            if not match:
                raise ValueError("Неверный формат. Используйте: [name](url)")
            
            name, url = match.groups()
            
            # Очищаем имя от недопустимых символов
            name = re.sub(r'[^a-zA-Z0-9_]', '', name)
            
            # Проверяем валидность имени
            if not name:
                raise ValueError("Имя эмодзи должно содержать буквы, цифры или подчеркивания")
            if len(name) < 2:
                raise ValueError("Имя эмодзи должно быть не менее 2 символов")
            if len(name) > 32:
                raise ValueError("Имя эмодзи должно быть не более 32 символов")
            if name[0].isdigit():
                name = f"emoji_{name}"  # Добавляем префикс, если имя начинается с цифры
            
            # Проверяем, является ли URL ссылкой на Discord CDN
            if not url.startswith(('https://cdn.discordapp.com/', 'http://cdn.discordapp.com/')):
                raise ValueError("Ссылка должна быть с cdn.discordapp.com")
            
            # Скачиваем эмодзи
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ValueError("Не удалось скачать эмодзи")
                    image_data = await response.read()
            
            # Определяем, анимированное ли эмодзи
            is_animated = url.endswith('.gif')
            
            # Создаем эмодзи на сервере
            emoji = await ctx.guild.create_custom_emoji(
                name=name,
                image=image_data,
                reason=f"Добавлено {ctx.author}"
            )
            
            embed = Embed(
                title="✅ Эмодзи добавлено",
                description=f"{Emojis.DOT} **Имя:** `{name}`\n"
                          f"{Emojis.DOT} **Тип:** {'Анимированное' if is_animated else 'Статичное'}\n"
                          f"{Emojis.DOT} **ID:** `{emoji.id}`\n"
                          f"{Emojis.DOT} **Использование:** `<{'a' if is_animated else ''}:{name}:{emoji.id}>`"
            )
            await ctx.send(embed=embed)
            
        except ValueError as e:
            embed = Embed(
                title="❌ Ошибка",
                description=str(e),
                color=0xe74c3c
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = Embed(
                title="❌ Ошибка",
                description="У бота нет прав на добавление эмодзи",
                color=0xe74c3c
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = Embed(
                title="❌ Ошибка",
                description=f"Не удалось добавить эмодзи: {str(e)}",
                color=0xe74c3c
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Emoji(bot))