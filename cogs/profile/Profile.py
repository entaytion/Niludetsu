import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict, Any
from easy_pil import Canvas, Editor, Font, load_image_async
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.profile import ProfileManager, ProfileImage
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from discord.ext import tasks

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
                f"Вы продали роль **{role.name}** за {sell_price:,} {Emojis.MONEY}\n"
                f"Ваш новый баланс: {user_data['balance'] + sell_price:,} {Emojis.MONEY}\n"
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

class Profile(commands.GroupCog, group_name="profile"):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.profile_manager = ProfileManager(self.db)
        self.profile_image = ProfileImage()
        self.font_path_regular = os.path.join('config', 'fonts', 'TTNormsPro-Regular.ttf')
        self.font_path_bold = os.path.join('config', 'fonts', 'TTNormsPro-Bold.ttf')

    async def check_birthdays(self) -> None:
        """Проверить у кого сегодня день рождения"""
        try:
            birthday_users = await self.profile_manager.check_birthdays()
            
            if not birthday_users:
                return
                
            for profile in birthday_users:
                user = await self.bot.fetch_user(int(profile.user_id))
                if user:
                    age = profile.age
                    age_text = f", исполнилось {age} лет" if age else ""
                    
                    # Отправляем поздравление в личные сообщения
                    try:
                        await user.send(
                            embed=Embed(
                                title="🎂 С Днем Рождения!",
                                description=f"Поздравляем с днем рождения{age_text}! Желаем счастья, здоровья и всего самого наилучшего!",
                                color="YELLOW"
                            )
                        )
                    except discord.Forbidden:
                        pass  # Пользователь запретил личные сообщения
                        
        except Exception as e:
            print(f"Ошибка при проверке дней рождения: {e}")

    @tasks.loop(hours=24)
    async def birthday_check(self):
        """Ежедневная проверка дней рождения"""
        await self.check_birthdays()

    async def cog_load(self) -> None:
        """Инициализация при загрузке кога"""
        await self.db.connect()
        self.birthday_check.start()

    async def cog_unload(self) -> None:
        """Очистка при выгрузке кога"""
        self.birthday_check.cancel()
        await self.db.close()

    @app_commands.command(name="view", description="Показать профиль пользователя")
    @app_commands.describe(user="Пользователь, чей профиль показать")
    async def profile_view(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        
        if user.bot:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Вы не можете просмотреть профиль бота.",
                    color="RED"
                )
            )
            return

        # Получаем данные профиля через ProfileManager
        profile_data = await self.profile_manager.get_profile(str(user.id))
        
        # Создаем изображение профиля
        image_bytes = await self.profile_image.create_profile_image(
            profile_data,
            user.global_name or user.name,
            str(user.display_avatar.url)
        )

        # Создаем view с кнопкой инвентаря
        view = ProfileView(str(user.id), user.global_name or user.name)
        view.cog = self

        # Отправляем сообщение с изображением и кнопкой
        file = discord.File(fp=image_bytes, filename="profile.png")
        await interaction.response.send_message(file=file, view=view)

    @app_commands.command(name="set", description="Установить информацию в профиле")
    @app_commands.describe(
        name="Ваше имя",
        country="Страна проживания",
        bio="О себе",
        birthday="Дата рождения (например: 01.01.2000)"
    )
    async def profile_set(
        self, 
        interaction: discord.Interaction, 
        name: str = None,
        country: str = None,
        bio: str = None,
        birthday: str = None
    ):
        if not any([name, country, bio, birthday]):
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Укажите хотя бы одно поле для обновления!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем длину биографии
        if bio and len(bio) > 1024:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Биография не может быть длиннее 1024 символов!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем формат даты рождения
        if birthday:
            try:
                day, month, year = map(int, birthday.split('.'))
                if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2024):
                    raise ValueError
            except ValueError:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Неверный формат даты рождения. Используйте формат ДД.ММ.ГГГГ (например: 01.01.2000)",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

        # Обновляем профиль через ProfileManager
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if country is not None:
            update_data["country"] = country
        if bio is not None:
            update_data["bio"] = bio
        if birthday is not None:
            update_data["birthday"] = birthday

        await self.profile_manager.update_profile(str(interaction.user.id), **update_data)

        # Формируем сообщение об обновлении
        updated_fields = []
        if name is not None:
            updated_fields.append(f"Имя: {name}")
        if country is not None:
            updated_fields.append(f"Страна: {country}")
        if bio is not None:
            updated_fields.append(f"О себе: {bio}")
        if birthday is not None:
            updated_fields.append(f"День рождения: {birthday}")

        await interaction.response.send_message(
            embed=Embed(
                title=f"{Emojis.SUCCESS} Профиль обновлен",
                description="\n".join(updated_fields),
                color="GREEN"
            ),
            ephemeral=True
        )

    @app_commands.command(name="clear", description="Очистить свой профиль")
    async def profile_clear(self, interaction: discord.Interaction):
        # Очищаем профиль через ProfileManager
        await self.profile_manager.clear_profile(str(interaction.user.id))
            
        await interaction.response.send_message(
            embed=Embed(
                title=f"{Emojis.SUCCESS} Профиль очищен",
                description="Вся информация из вашего профиля была удалена!",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Profile(bot)) 