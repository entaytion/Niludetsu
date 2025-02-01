import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict, Any
from easy_pil import Canvas, Editor, Font, load_image_async
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import io
import json
import asyncio

def calculate_next_level_xp(level: int) -> int:
    """
    Рассчитывает количество опыта, необходимое для следующего уровня
    Args:
        level (int): Текущий уровень
    Returns:
        int: Количество опыта для следующего уровня
    """
    return 5 * (level ** 2) + 50 * level + 100

def format_voice_time(seconds: int) -> str:
    """
    Форматирует время в голосовых каналах в читаемый вид
    Args:
        seconds (int): Количество секунд
    Returns:
        str: Отформатированное время
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}ч {minutes}м"

class SellRoleButton(discord.ui.Button):
    def __init__(self, role_id: int, role_name: str, price: int):
        super().__init__(
            style=discord.ButtonStyle.red,
            label=f"Продать {role_name}",
            custom_id=f"sell_role_{role_id}"
        )
        self.role_id = role_id
        self.price = price
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        # Получаем роль
        role_data = await self.view.cog.db.get_row("shop_roles", role_id=self.role_id)

        if not role_data:
            await interaction.response.send_message(
                embed=Embed(
                    title="❌ Ошибка",
                    description="Роль не найдена в базе данных.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(int(role_data['role_id']))
        if not role:
            await interaction.response.send_message(
                embed=Embed(
                    title="❌ Ошибка",
                    description="Роль не найдена на сервере.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем, есть ли роль у пользователя
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                embed=Embed(
                    title="❌ Ошибка",
                    description="У вас нет этой роли.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        sell_price = int(self.price * 0.7)  # Возвращаем 70% от стоимости
        bot_profit = self.price - sell_price  # 30% в казну сервера

        # Получаем текущие данные пользователя
        user_id = str(interaction.user.id)
        user_data = await self.view.cog.db.get_row("users", user_id=user_id)
        
        # Получаем список ролей пользователя и удаляем продаваемую роль
        try:
            user_roles = eval(user_data['roles'])
            user_roles.remove(self.role_id)
        except:
            user_roles = []

        # Обновляем баланс и список ролей пользователя
        await self.view.cog.db.update(
            "users",
            where={"user_id": user_id},
            values={
                "balance": user_data.get('balance', 0) + sell_price,
                "roles": str(user_roles)
            }
        )

        # Обновляем баланс бота (казну сервера)
        bot_id = '1264591814208262154'  # ID бота
        bot_data = await self.view.cog.db.get_row("users", user_id=bot_id)
        await self.view.cog.db.update(
            "users",
            where={"user_id": bot_id},
            values={"balance": bot_data.get('balance', 0) + bot_profit}
        )

        # Удаляем роль у пользователя
        await interaction.user.remove_roles(role)

        # Создаем новый view для обновленного инвентаря
        new_view = InventoryView(str(interaction.user.id), interaction.user.global_name or interaction.user.name, True)
        new_view.cog = self.view.cog
        
        # Создаем embed с информацией о продаже
        sell_embed=Embed(
            title="✅ Роль продана",
            description=(
                f"Вы продали роль **{role.name}** за {sell_price:,} {EMOJIS['MONEY']}\n"
                f"Ваш новый баланс: {user_data['balance'] + sell_price:,} {EMOJIS['MONEY']}\n"
                f"С продажи роли, 30% отправляется в **казну сервера**"
            ),
            color="GREEN"
        )

        # Обновляем текущее сообщение с инвентарем
        await interaction.response.edit_message(embed=sell_embed, view=new_view)

class InventoryView(discord.ui.View):
    def __init__(self, user_id: str, user_name: str, is_self: bool):
        super().__init__()  # Убираем timeout=None
        self.user_id = user_id
        self.user_name = user_name
        self.is_self = is_self
        self.cog = None

    async def refresh_inventory(self, interaction: discord.Interaction):
        # Получаем данные пользователя
        user_data = await self.cog.db.get_row("users", user_id=self.user_id)
        if not user_data or not user_data['roles']:
            await interaction.response.send_message(
                embed=Embed(
                    title="🎒 Инвентарь",
                    description=f"У {self.user_name} нет купленных ролей.",
                    color="BLUE"
                ),
                ephemeral=True
            )
            return

        # Получаем список ID ролей
        try:
            user_roles = eval(user_data['roles'])  # Преобразуем строку в список
        except:
            user_roles = []

        if not user_roles:
            await interaction.response.send_message(
                embed=Embed(
                    title="🎒 Инвентарь",
                    description=f"У {self.user_name} нет купленных ролей.",
                    color="BLUE"
                ),
                ephemeral=True
            )
            return

        # Получаем информацию о ролях
        roles_data = []
        for role_id in user_roles:
            role_data = await self.cog.db.get_row("shop_roles", role_id=role_id)
            if role_data:
                roles_data.append(role_data)

        if not roles_data:
            await interaction.response.send_message(
                embed=Embed(
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
        
        # Очищаем старые кнопки
        self.clear_items()
        
        for role_data in roles_data:
            role = interaction.guild.get_role(int(role_data['role_id']))
            if role:
                sell_price = int(role_data['price'] * 0.7)  # Возвращаем 70% от стоимости
                roles_list.append(f"• {role.name} — {role_data['price']:,} 💰 (продажа: {sell_price:,} 💰)")
                total_value += role_data['price']
                
                # Добавляем кнопку продажи только если это инвентарь пользователя
                if self.is_self:
                    self.add_item(SellRoleButton(role_data['role_id'], role.name, role_data['price']))

        # Создаем embed с информацией
        embed=Embed(
            title=f"🎒 Инвентарь {self.user_name}",
            description="\n".join([
                "**Купленные роли:**",
                "\n".join(roles_list),
                f"\n**Общая стоимость:** {total_value:,} 💰"
            ]),
            color="BLUE"
        )

        await interaction.response.send_message(
            embed=embed,
            view=self if self.is_self else None,
            ephemeral=True
        )

class InventoryButton(discord.ui.Button):
    def __init__(self, user_id: str, user_name: str):
        super().__init__(style=discord.ButtonStyle.gray, label="Инвентарь", emoji="🎒", custom_id=f"inventory_{user_id}")
        self.user_id = user_id
        self.user_name = user_name

    async def callback(self, interaction: discord.Interaction):
        # Проверяем, свой ли инвентарь открывает пользователь
        is_self = str(interaction.user.id) == self.user_id
        
        view = InventoryView(self.user_id, self.user_name, is_self)
        view.cog = self.view.cog
        await view.refresh_inventory(interaction)

class ProfileView(discord.ui.View):
    def __init__(self, user_id: str, user_name: str):
        super().__init__(timeout=None)
        self.add_item(InventoryButton(user_id, user_name))

class Profile(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = Database()
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
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Вы не можете просмотреть профиль бота.",
                    color="RED"
                )
            )
            return

        user_id = str(user.id)
        user_data = await self.db.get_row("users", user_id=user_id)

        if not user_data:
            user_data = await self.db.insert("users", {
                'user_id': user_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            })

        # Создаем новый Canvas
        background = Editor(Image.new('RGBA', (800, 600), color=(20, 20, 30, 255)))
        
        # Создаем градиентный фон
        gradient = Image.new('RGBA', (800, 600))
        draw = ImageDraw.Draw(gradient)
        for y in range(600):
            r = int(30 * (1 - y/600))
            g = int(30 * (1 - y/600))
            b = int(40 * (1 - y/600))
            draw.line([(0, y), (800, y)], fill=(r, g, b, 255))
        
        background.image = Image.alpha_composite(background.image, gradient)
        
        # Добавляем декоративные элементы
        # Верхняя панель
        self.rounded_rectangle(ImageDraw.Draw(background.image), 20, 20, 780, 200, 20, fill=(40, 40, 55, 255))
        # Нижняя панель для статистики
        self.rounded_rectangle(ImageDraw.Draw(background.image), 20, 220, 780, 580, 20, fill=(40, 40, 55, 255))

        # Загружаем и добавляем аватар с обводкой
        profile_image = await self.load_image_async(str(user.display_avatar.url))
        profile_image = Editor(profile_image).resize((140, 140)).circle_image()
        
        # Создаем обводку для аватара
        circle_border = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
        draw = ImageDraw.Draw(circle_border)
        draw.ellipse((0, 0, 149, 149), outline=(255, 255, 255, 255), width=3)
        circle_border = Editor(circle_border)
        
        # Накладываем аватар и обводку
        background.paste(profile_image, (40, 40))
        background.paste(circle_border, (35, 35))

        # Загружаем шрифты
        font_regular = Font(self.font_path_regular, size=30)
        font_small = Font(self.font_path_regular, size=25)
        font_smaller = Font(self.font_path_regular, size=20)
        font_bold = Font(self.font_path_bold, size=40)

        # Добавляем имя пользователя
        background.text((210, 50), user.name, font=font_bold, color="white")

        # Добавляем уровень и опыт с прогресс-баром
        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        next_level_xp = calculate_next_level_xp(level)
        xp_percentage = min(xp / next_level_xp * 100, 100)

        # Рисуем прогресс-бар
        bar_width = 300
        bar_height = 20
        bar_x = 210
        bar_y = 100
        
        # Фон прогресс-бара
        self.rounded_rectangle(
            ImageDraw.Draw(background.image),
            bar_x, bar_y,
            bar_x + bar_width, bar_y + bar_height,
            10, fill=(30, 30, 40, 255)
        )
        
        # Заполненная часть прогресс-бара
        filled_width = int(bar_width * (xp_percentage / 100))
        if filled_width > 0:
            self.rounded_rectangle(
                ImageDraw.Draw(background.image),
                bar_x, bar_y,
                bar_x + filled_width, bar_y + bar_height,
                10, fill=(70, 130, 180, 255)
            )

        # Текст уровня и опыта
        background.text((210, 130), f"Уровень {level}", font=font_regular, color="white")
        background.text((400, 130), f"XP: {xp:,}/{next_level_xp:,}", font=font_small, color="#cccccc")

        # Добавляем баланс с иконками
        balance = user_data.get('balance', 0)
        deposit = user_data.get('deposit', 0)
        total = balance + deposit

        # Рисуем секции для денег
        money_section_y = 250
        self.rounded_rectangle(ImageDraw.Draw(background.image), 40, money_section_y, 380, money_section_y + 100, 15, fill=(50, 50, 65, 255))
        
        # Иконка денег и баланс
        money_icon = Editor(self.money_icon_path).resize((25, 25))
        background.paste(money_icon, (60, money_section_y + 20))
        background.text((95, money_section_y + 15), f"Баланс: {balance:,}", font=font_regular, color="white")
        background.text((95, money_section_y + 55), f"В банке: {deposit:,}", font=font_small, color="#cccccc")

        # Статистика справа
        stats_x = 420
        stats_y = 250
        self.rounded_rectangle(ImageDraw.Draw(background.image), stats_x, stats_y, 760, stats_y + 300, 15, fill=(50, 50, 65, 255))
        
        # Заголовок статистики
        background.text((stats_x + 20, stats_y + 20), "Статистика", font=font_regular, color="white")
        
        # Статистика с иконками
        stats_start_y = stats_y + 70
        line_height = 45
        
        # Время в войсе
        voice_time = user_data.get('voice_time', 0)
        formatted_voice_time = format_voice_time(voice_time)
        background.text((stats_x + 20, stats_start_y), f"🎤 Время в войсе: {formatted_voice_time}", font=font_small, color="#cccccc")
        
        # Подключения
        voice_joins = user_data.get('voice_joins', 0)
        background.text((stats_x + 20, stats_start_y + line_height), f"🔌 Подключений: {voice_joins:,}", font=font_small, color="#cccccc")
        
        # Сообщения
        messages_count = user_data.get('messages_count', 0)
        background.text((stats_x + 20, stats_start_y + line_height * 2), f"💬 Сообщений: {messages_count:,}", font=font_small, color="#cccccc")

        # Конвертируем изображение в файл
        file = discord.File(fp=background.image_bytes, filename="profile.png")

        # Создаем view с кнопкой инвентаря
        view = ProfileView(user_id, user.global_name or user.name)
        view.cog = self

        # Отправляем сообщение с изображением и кнопкой
        await interaction.response.send_message(file=file, view=view)

async def setup(client):
    await client.add_cog(Profile(client)) 