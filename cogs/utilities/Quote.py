import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
import textwrap
import os

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.font_path = 'config/fonts/TTNormsPro-Regular.ttf'

    async def download_avatar(self, avatar_url):
        """Завантаження та обробка аватарки"""
        async with aiohttp.ClientSession() as session:
            async with session.get(str(avatar_url)) as response:
                if response.status == 200:
                    avatar_data = io.BytesIO(await response.read())
                    avatar = Image.open(avatar_data)
                    
                    # Конвертуємо в RGBA якщо потрібно
                    if avatar.mode != 'RGBA':
                        avatar = avatar.convert('RGBA')
                    
                    # Створюємо маску для круглої аватарки
                    mask = Image.new('L', avatar.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + avatar.size, fill=255)
                    
                    # Застосовуємо маску
                    output = Image.new('RGBA', avatar.size, (0, 0, 0, 0))
                    output.paste(avatar, (0, 0))
                    output.putalpha(mask)
                    
                    return output
        return None

    def create_quote_image(self, text, author_name, avatar):
        """Створення зображення з цитатою"""
        # Розміри зображення
        width = 800
        height = 400
        padding = 40
        
        # Створюємо нове зображення
        image = Image.new('RGB', (width, height), color='#2C2F33')
        draw = ImageDraw.Draw(image)
        
        # Завантажуємо шрифти
        quote_font = ImageFont.truetype(self.font_path, 32)
        author_font = ImageFont.truetype(self.font_path, 24)
        
        # Обробляємо текст (розбиваємо на рядки)
        max_chars_per_line = 50
        wrapped_text = textwrap.fill(text, width=max_chars_per_line)
        
        # Додаємо лапки до тексту
        quote_text = f"«{wrapped_text}»"
        
        # Малюємо текст цитати
        text_y = padding
        draw.text((padding, text_y), quote_text, font=quote_font, fill='#FFFFFF')
        
        # Вставляємо аватар
        if avatar:
            avatar_size = 64
            avatar = avatar.resize((avatar_size, avatar_size))
            avatar_position = (padding, height - padding - avatar_size)
            image.paste(avatar, avatar_position, avatar)
            
            # Малюємо ім'я автора справа від аватара
            author_x = padding + avatar_size + 20
            author_y = height - padding - (avatar_size // 2) - 12
            draw.text((author_x, author_y), f"— {author_name}", font=author_font, fill='#FFFFFF')
        
        return image

    @discord.app_commands.command(name="quote", description="Создать цитату из сообщения")
    @discord.app_commands.describe(message="ID сообщения для цитирования (необязательно)")
    async def quote(self, interaction: discord.Interaction, message: str = None):
        await interaction.response.defer()

        if message:
            # Якщо передано ID повідомлення
            try:
                message_id = int(message)
                quoted_message = await interaction.channel.fetch_message(message_id)
            except:
                await interaction.followup.send(
                    embed=Embed(
                        description="Не удалось найти сообщение с указанным ID!"
                    )
                )
                return
        else:
            # Перевіряємо, чи є це відповіддю на повідомлення
            reference_message = None
            async for msg in interaction.channel.history(limit=1, before=interaction.created_at):
                reference_message = msg
            
            if not reference_message:
                await interaction.followup.send(
                    embed=Embed(
                        description="Используйте команду сразу после сообщения, которое хотите процитировать, или укажите ID сообщения!"
                    )
                )
                return
            quoted_message = reference_message

        # Завантажуємо аватарку автора
        avatar = await self.download_avatar(quoted_message.author.display_avatar.url)
        
        # Створюємо зображення з цитатою
        quote_image = self.create_quote_image(
            quoted_message.content,
            quoted_message.author.display_name,
            avatar
        )
        
        # Конвертуємо зображення в байти
        with io.BytesIO() as image_binary:
            quote_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            # Відправляємо зображення
            await interaction.followup.send(
                file=discord.File(fp=image_binary, filename='quote.png')
            )

async def setup(bot):
    await bot.add_cog(Quote(bot)) 