import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
from utils import create_embed, EMOJIS

class Demotivator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def download_image(self, url: str) -> Image.Image:
        """Скачивает изображение по URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("Не удалось загрузить изображение")
                data = await response.read()
                return Image.open(io.BytesIO(data))

    async def create_demotivator(self, image: Image.Image, title: str, subtitle: str = "") -> io.BytesIO:
        """Создает демотиватор из изображения и текста"""
        # Размеры рамок и отступов
        border = 3
        margin = 50
        bottom_text_margin = 50

        # Изменяем размер изображения, сохраняя пропорции
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Создаем черный фон
        frame_width = image.width + (margin * 2)
        frame_height = image.height + (margin * 2) + bottom_text_margin
        if subtitle:
            frame_height += 30

        background = Image.new('RGB', (frame_width, frame_height), 'black')
        draw = ImageDraw.Draw(background)

        # Добавляем белую рамку
        draw.rectangle(
            (margin - border, margin - border,
             margin + image.width + border, margin + image.height + border),
            fill='white'
        )

        # Вставляем изображение
        background.paste(image, (margin, margin))

        # Загружаем шрифт
        try:
            title_font = ImageFont.truetype("arial.ttf", 30)
            subtitle_font = ImageFont.truetype("arial.ttf", 20)
        except OSError:
            # Если шрифт не найден, используем дефолтный
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Добавляем заголовок
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (frame_width - title_width) // 2
        title_y = margin + image.height + 20
        draw.text((title_x, title_y), title, font=title_font, fill='white')

        # Добавляем подзаголовок если есть
        if subtitle:
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (frame_width - subtitle_width) // 2
            subtitle_y = title_y + 35
            draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill='white')

        # Сохраняем результат
        output = io.BytesIO()
        background.save(output, format='PNG')
        output.seek(0)
        return output

    @app_commands.command(name="demotivator", description="Создать демотиватор")
    @app_commands.describe(
        title="Заголовок демотиватора",
        subtitle="Подзаголовок (необязательно)",
        image="Изображение для демотиватора (необязательно, если отвечаете на сообщение с картинкой)"
    )
    async def demotivator(
        self,
        interaction: discord.Interaction,
        title: str,
        subtitle: str = None,
        image: discord.Attachment = None
    ):
        await interaction.response.defer()

        try:
            # Получаем изображение
            if image:
                # Используем прикрепленное изображение
                img_url = image.url
            elif interaction.message and interaction.message.reference:
                # Ищем изображение в сообщении, на которое отвечаем
                referenced_message = await interaction.channel.fetch_message(
                    interaction.message.reference.message_id
                )
                if referenced_message.attachments:
                    img_url = referenced_message.attachments[0].url
                elif referenced_message.embeds and referenced_message.embeds[0].image:
                    img_url = referenced_message.embeds[0].image.url
                else:
                    raise ValueError("В сообщении нет изображения")
            else:
                raise ValueError("Прикрепите изображение или ответьте на сообщение с изображением")

            # Скачиваем и обрабатываем изображение
            img = await self.download_image(img_url)
            result = await self.create_demotivator(img, title, subtitle)

            # Отправляем результат
            await interaction.followup.send(
                file=discord.File(result, filename="demotivator.png")
            )

        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при создании демотиватора: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Demotivator(bot)) 