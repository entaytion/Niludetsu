import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import os

class Demotivator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.font_path = "config/fonts/Times New Roman.ttf"

    async def download_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None

    def create_demotivator(self, image_bytes, top_text, bottom_text=None):
        img = Image.open(io.BytesIO(image_bytes))
        
        max_size = (400, 400)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        width = img.width + 100
        height = img.height + 150
        if bottom_text:
            height += 50
            
        background = Image.new('RGB', (width, height), 'black')
        
        border = Image.new('RGB', (img.width + 4, img.height + 4), 'white')
        background.paste(border, ((width - border.width) // 2, 20))
        
        background.paste(img, ((width - img.width) // 2, 22))
        
        draw = ImageDraw.Draw(background)
        font_size = 35
        font = ImageFont.truetype(self.font_path, font_size)
        
        text_width = draw.textlength(top_text, font=font)
        x = (width - text_width) / 2
        y = img.height + 40
        draw.text((x, y), top_text, font=font, fill='white')
        
        if bottom_text:
            font_size = 25
            font = ImageFont.truetype(self.font_path, font_size)
            text_width = draw.textlength(bottom_text, font=font)
            x = (width - text_width) / 2
            y = img.height + 90
            draw.text((x, y), bottom_text, font=font, fill='white')
        
        output = io.BytesIO()
        background.save(output, format='PNG')
        output.seek(0)
        return output

    @discord.app_commands.command(name="demotivator", description="Создать демотиватор")
    @discord.app_commands.describe(
        image="Изображение для демотиватора",
        top_text="Верхний текст",
        bottom_text="Нижний текст (необязательно)"
    )
    async def demotivator(
        self,
        interaction: discord.Interaction,
        image: discord.Attachment,
        top_text: str,
        bottom_text: str = None
    ):
        await interaction.response.defer()

        if not image.content_type.startswith('image/'):
            await interaction.followup.send(
                embed=Embed(
                    description="Пожалуйста, загрузите изображение!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        image_bytes = await self.download_image(image.url)
        if not image_bytes:
            await interaction.followup.send(
                embed=Embed(
                    description="Не удалось загрузить изображение!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        result = self.create_demotivator(image_bytes, top_text, bottom_text)
        file = discord.File(result, filename='demotivator.png')
        
        embed=Embed(
            title="Демотиватор создан!",
            color="GREEN"
        )
        embed.set_image(url="attachment://demotivator.png")
        
        await interaction.followup.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Demotivator(bot)) 