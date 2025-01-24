import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
from PIL import Image, ImageDraw
import io
import aiohttp
import asyncio

class LGBT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def download_avatar(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url)) as response:
                if response.status == 200:
                    return await response.read()
                return None

    def create_rainbow_overlay(self, size):
        # Создаем новое изображение с прозрачностью
        overlay = Image.new('RGBA', size)
        draw = ImageDraw.Draw(overlay)
        
        # Цвета радуги
        colors = [
            (255, 0, 0, 128),      # Красный
            (255, 127, 0, 128),    # Оранжевый
            (255, 255, 0, 128),    # Желтый
            (0, 255, 0, 128),      # Зеленый
            (0, 255, 255, 128),    # Голубой
            (0, 0, 255, 128),      # Синий  
            (148, 0, 211, 128)     # Фиолетовый
        ]
        
        # Вычисляем высоту каждой полосы
        stripe_height = size[1] // len(colors)
        
        # Рисуем полосы
        for i, color in enumerate(colors):
            y0 = i * stripe_height
            y1 = (i + 1) * stripe_height if i < len(colors) - 1 else size[1]
            draw.rectangle([(0, y0), (size[0], y1)], fill=color)
        
        return overlay

    @app_commands.command(name="lgbt", description="Наложить радужный эффект на аватар")
    @app_commands.describe(
        user="Пользователь, чей аватар нужно изменить"
    )
    async def lgbt(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        try:
            await interaction.response.defer()
            
            # Скачиваем аватар
            avatar_bytes = await self.download_avatar(user.display_avatar.with_size(512).url)
            if not avatar_bytes:
                return await interaction.followup.send(
                    "Не удалось загрузить аватар!"
                )
            
            # Открываем изображение
            with Image.open(io.BytesIO(avatar_bytes)) as avatar:
                # Конвертируем в RGBA если нужно
                avatar = avatar.convert('RGBA')
                
                # Создаем радужный оверлей
                rainbow = self.create_rainbow_overlay(avatar.size)
                
                # Устанавливаем прозрачность 35%
                rainbow.putalpha(int(255 * 0.35))
                
                # Накладываем эффект
                result = Image.alpha_composite(avatar, rainbow)
                
                # Сохраняем результат
                output = io.BytesIO()
                result.save(output, format='PNG')
                output.seek(0)
                
                # Создаем файл для отправки
                file = discord.File(output, filename='lgbt_avatar.png')
                
                # Создаем эмбед
                embed = create_embed(
                    title=f"🌈 LGBT аватар для {user.name}"
                )
                embed.set_image(url="attachment://lgbt_avatar.png")
                
                # Отправляем результат
                await interaction.followup.send(embed=embed, file=file)
                
        except Exception as e:
            print(f"Ошибка в команде lgbt: {str(e)}")
            await interaction.followup.send(
                "Произошла ошибка при обработке изображения."
            )

async def setup(bot):
    await bot.add_cog(LGBT(bot)) 