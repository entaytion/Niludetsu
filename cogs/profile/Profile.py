import discord
from discord.ext import commands
from easy_pil import Canvas, Editor, Font
from Niludetsu.utils.database import get_user, calculate_next_level_xp, format_voice_time, get_user_roles
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import io
import sqlite3

class InventoryButton(discord.ui.Button):
    def __init__(self, user_id: str, user_name: str):
        super().__init__(style=discord.ButtonStyle.gray, label="Инвентарь", emoji="🎒", custom_id=f"inventory_{user_id}")
        self.user_id = user_id
        self.user_name = user_name

    async def callback(self, interaction: discord.Interaction):
        user_roles = get_user_roles(self.user_id)
        
        if not user_roles:
            await interaction.response.send_message(
                embed=create_embed(
                    title="🎒 Инвентарь",
                    description=f"У {self.user_name} нет купленных ролей.",
                    color="BLUE"
                ),
                ephemeral=True
            )
            return

        # Получаем информацию о ролях из базы данных
        with sqlite3.connect('config/database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role_id, name, balance FROM roles WHERE role_id IN ({})".format(
                ','.join('?' * len(user_roles))
            ), [int(role_id) for role_id in user_roles])
            roles_data = cursor.fetchall()

        if not roles_data:
            await interaction.response.send_message(
                embed=create_embed(
                    title="🎒 Инвентарь",
                    description=f"У {self.user_name} нет купленных ролей.",
                    color="BLUE"
                ),
                ephemeral=True
            )
            return

        # Формируем список ролей с их стоимостью
        roles_list = []
        total_value = 0
        for role_id, name, balance in roles_data:
            role = interaction.guild.get_role(int(role_id))
            if role:
                roles_list.append(f"• {role.name} — {balance:,} 💰")
                total_value += balance

        # Создаем embed с информацией
        embed = create_embed(
            title=f"🎒 Инвентарь {self.user_name}",
            description="\n".join([
                "**Купленные роли:**",
                "\n".join(roles_list),
                f"\n**Общая стоимость:** {total_value:,} 💰"
            ]),
            color="BLUE"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ProfileView(discord.ui.View):
    def __init__(self, user_id: str, user_name: str):
        super().__init__(timeout=None)
        self.add_item(InventoryButton(user_id, user_name))

class Profile(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.font_path_regular = os.path.join('config', 'fonts', 'TTNormsPro-Regular.ttf')
        self.font_path_bold = os.path.join('config', 'fonts', 'TTNormsPro-Bold.ttf')
        self.money_icon_path = os.path.join('config', 'images', 'profile', 'money.png')

    async def load_image_async(self, url: str) -> Image:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch image: {response.status}")
                data = await response.read()
                return Image.open(BytesIO(data))

    def format_time(self, seconds):
        """Форматирует время в формат ЧЧ:ММ:СС"""
        if seconds is None:
            return "00:00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def rounded_rectangle(self, draw, x1, y1, x2, y2, radius, fill=None, outline=None):
        """Draws a rounded rectangle"""
        diameter = radius * 2
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        if diameter <= (x2 - x1) and diameter <= (y2 - y1): 
            draw.ellipse((x1, y1, x1 + diameter, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y1, x2, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x1, y2 - diameter, x1 + diameter, y2), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y2 - diameter, x2, y2), fill=fill, outline=outline)
            draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill, outline=outline)
            draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill, outline=outline)
        else:
            draw.rectangle((x1, y1, x2, y2), fill=fill, outline=outline)

    @discord.app_commands.command(name="profile", description="Показать профиль пользователя")
    @discord.app_commands.describe(user="Пользователь, чей профиль показать")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        
        if user.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Вы не можете просмотреть профиль бота.",
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
        messages_count = user_data.get('messages_count', 0)
        voice_time = user_data.get('voice_time', 0)
        balance = user_data.get('balance', 0)
        deposit = user_data.get('deposit', 0)

        # Создаем фон
        background = Editor(Canvas((900, 300), color="#0f0f0f"))
        
        # Загружаем и добавляем аватар
        profile_image = await self.load_image_async(user.avatar.url)
        profile = Editor(profile_image).resize((150, 150)).circle_image()
        background.paste(profile.image, (25, 25))

        # Загружаем шрифты
        font_bold = ImageFont.truetype(self.font_path_bold, 40)
        font_regular = ImageFont.truetype(self.font_path_regular, 30)
        font_small = ImageFont.truetype(self.font_path_regular, 25)

        # Добавляем информацию о пользователе
        display_name = user.global_name or user.name
        background.text((200, 20), display_name, font=font_bold, color="white")
        
        # Первая колонка
        background.text((200, 80), f"Уровень: {level}", font=font_regular, color="white")
        background.text((200, 120), f"Опыт: {xp}/{next_level_xp}", font=font_regular, color="white")
        
        # Вторая колонка
        background.text((500, 80), f"Сообщений: {messages_count:,}", font=font_regular, color="white")
        background.text((500, 120), f"Время в войсе: {self.format_time(voice_time)}", font=font_regular, color="white")
        
        # Баланс с иконкой
        balance_text = f"Баланс: {balance:,}"
        background.text((200, 160), balance_text, font=font_regular, color="white")
        
        # Депозит с иконкой
        deposit_text = f"В банке: {deposit:,}"
        background.text((500, 160), deposit_text, font=font_regular, color="white")
        
        # Добавляем иконки денег
        if os.path.exists(self.money_icon_path):
            money_icon = Image.open(self.money_icon_path)
            money_icon = money_icon.resize((25, 25))  # Размер иконки
            
            # Иконка для баланса
            text_width = ImageDraw.Draw(background.image).textlength(balance_text, font=font_regular)
            money_editor = Editor(money_icon)
            background.paste(money_editor, (int(200 + text_width + 10), 160))
            
            # Иконка для депозита
            text_width_deposit = ImageDraw.Draw(background.image).textlength(deposit_text, font=font_regular)
            money_editor_deposit = Editor(money_icon)
            background.paste(money_editor_deposit, (int(500 + text_width_deposit + 10), 160))

        # Прогресс-бар опыта
        progress_bar_x = 200
        progress_bar_y = 240
        progress_bar_width = 650
        progress_bar_height = 20
        progress = int((xp / next_level_xp) * progress_bar_width) if next_level_xp else 0

        draw = ImageDraw.Draw(background.image)

        # Фон прогресс-бара
        self.rounded_rectangle(draw,
                            progress_bar_x,
                            progress_bar_y,
                            progress_bar_x + progress_bar_width,
                            progress_bar_y + progress_bar_height,
                            10,
                            fill="#1f1f1f")

        # Заполненная часть прогресс-бара
        fill_x2 = max(progress_bar_x + progress, progress_bar_x)
        self.rounded_rectangle(draw, 
                            progress_bar_x,
                            progress_bar_y,
                            fill_x2,
                            progress_bar_y + progress_bar_height,
                            10,
                            fill="#f20c3c")

        # Конвертируем изображение в байты и отправляем
        with io.BytesIO() as image_binary:
            background.image.save(image_binary, 'PNG')
            image_binary.seek(0)
            user_name = user.global_name or user.name
            await interaction.response.send_message(
                file=discord.File(fp=image_binary, filename='profile.png'),
                view=ProfileView(user_id, user_name)
            )

async def setup(client):
    await client.add_cog(Profile(client)) 