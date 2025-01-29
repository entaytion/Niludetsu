import discord
from discord.ext import commands
from easy_pil import Canvas, Editor, Font
from Niludetsu.utils.database import get_user, calculate_next_level_xp
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import io

class Level(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.font_path_regular = os.path.join('config', 'fonts', 'TTNormsPro-Regular.ttf')
        self.font_path_bold = os.path.join('config', 'fonts', 'TTNormsPro-Bold.ttf')

    async def load_image_async(self, url: str) -> Image:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch image: {response.status}")
                data = await response.read()
                return Image.open(BytesIO(data))

    def rounded_rectangle(self, draw, x1, y1, x2, y2, radius, fill=None, outline=None):
        """Draws a rounded rectangle, handling potential errors with small progress values."""

        diameter = radius * 2

        # Ensure x1 <= x2 and y1 <= y2
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        # Draw corners only if the radius allows it
        if diameter <= (x2 - x1) and diameter <= (y2 - y1): 
            draw.ellipse((x1, y1, x1 + diameter, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y1, x2, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x1, y2 - diameter, x1 + diameter, y2), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y2 - diameter, x2, y2), fill=fill, outline=outline)

            # Connecting lines, adjusting for corner ellipses
            draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill, outline=outline)
            draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill, outline=outline)
        else:
            # If the radius is too large, draw a regular rectangle 
            draw.rectangle((x1, y1, x2, y2), fill=fill, outline=outline)

    @discord.app_commands.command(name="level", description="Показать уровень и опыт пользователя")
    @discord.app_commands.describe(user="Пользователь, для которого показывать уровень и опыт")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            user = user or interaction.user
            
            if user.bot:
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="Вы не можете использовать эту команду на ботов.",
                        color="RED"
                    )
                )
                return

            user_id = str(user.id)
            user_data = get_user(user_id)

            if not user_data:
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="Пользователь не найден в базе данных.",
                        color="RED"
                    )
                )
                return
                
            xp = user_data.get('xp', 0)
            level = user_data.get('level', 0)
            next_level_xp = calculate_next_level_xp(level)

            background = Editor(Canvas((900, 200), color="#0f0f0f"))
            profile_image = await self.load_image_async(user.avatar.url)
            profile = Editor(profile_image).resize((150, 150)).circle_image()
            background.paste(profile.image, (25, 25))

            font_bold = ImageFont.truetype(self.font_path_bold, 40)
            font_regular = ImageFont.truetype(self.font_path_regular, 30)

            background.text((200, 20), f"{user.name}#{user.discriminator}", font=font_bold, color="white")
            background.text((200, 65), f"Уровень: {level}", font=font_regular, color="white")
            background.text((200, 100), f"Опыт: {xp}/{next_level_xp}", font=font_regular, color="white")

            progress_bar_x = 200
            progress_bar_y = 140
            progress_bar_width = 500
            progress_bar_height = 20
            progress = int((xp / next_level_xp) * progress_bar_width) if next_level_xp else 0

            draw = ImageDraw.Draw(background.image)

            # Draw the background of the progress bar first
            self.rounded_rectangle(draw,
                                progress_bar_x,
                                progress_bar_y,
                                progress_bar_x + progress_bar_width,
                                progress_bar_y + progress_bar_height,
                                10,
                                fill="#1f1f1f")

            # Draw the filled portion of the progress bar
            fill_x2 = max(progress_bar_x + progress, progress_bar_x) 
            self.rounded_rectangle(draw, 
                                  progress_bar_x,
                                  progress_bar_y,
                                  fill_x2,
                                  progress_bar_y + progress_bar_height,
                                  10,
                                  fill="#f20c3c") 

            # Конвертуємо зображення в байти і відправляємо
            with io.BytesIO() as image_binary:
                background.image.save(image_binary, 'PNG')
                image_binary.seek(0)
                await interaction.response.send_message(
                    file=discord.File(fp=image_binary, filename='level.png')
                )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description=f"Произошла ошибка: {str(e)}",
                    color="RED"
                )
            )

async def setup(client):
    await client.add_cog(Level(client))
