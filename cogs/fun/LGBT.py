import discord
from discord.ext import commands
import random
from Niludetsu.utils.embed import create_embed
from PIL import Image, ImageDraw
import io
import aiohttp

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
        overlay = Image.new('RGBA', size)
        draw = ImageDraw.Draw(overlay)
        
        colors = [
            (255, 0, 0, 128),      # Красный
            (255, 127, 0, 128),    # Оранжевый
            (255, 255, 0, 128),    # Желтый
            (0, 255, 0, 128),      # Зеленый
            (0, 255, 255, 128),    # Голубой
            (0, 0, 255, 128),      # Синий  
            (148, 0, 211, 128)     # Фиолетовый
        ]
        
        stripe_height = size[1] // len(colors)
        
        for i, color in enumerate(colors):
            y0 = i * stripe_height
            y1 = (i + 1) * stripe_height if i < len(colors) - 1 else size[1]
            draw.rectangle([(0, y0), (size[0], y1)], fill=color)
        
        return overlay

    @discord.app_commands.command(name="lgbt", description="Наложить радужный эффект на аватар")
    @discord.app_commands.describe(user="Пользователь, чей аватар нужно изменить")
    async def lgbt(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        
        user = user or interaction.user
        
        try:
            # Скачиваем аватар
            avatar_bytes = await self.download_avatar(user.display_avatar.with_size(512).url)
            if not avatar_bytes:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Не удалось загрузить аватар!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
            
            # Открываем изображение
            with Image.open(io.BytesIO(avatar_bytes)) as avatar:
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
                
                await interaction.followup.send(
                    embed=create_embed(
                        title=f"🌈 LGBT аватар для {user.name}",
                        image="attachment://lgbt_avatar.png",
                        color="RANDOM"
                    ),
                    file=file
                )
                
        except Exception as e:
            print(f"Ошибка в команде lgbt: {str(e)}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при обработке изображения.",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(LGBT(bot)) 