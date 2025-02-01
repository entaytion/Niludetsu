import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.database import Database
from datetime import datetime
import asyncio

class Bio(commands.GroupCog, group_name="bio"):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self.db.init())  # Асинхронная инициализация базы данных
        
    @app_commands.command(name="set", description="Установить информацию в профиле")
    @app_commands.describe(
        name="Ваше имя",
        age="Ваш возраст",
        country="Страна проживания",
        bio="О себе"
    )
    async def bio_set(
        self, 
        interaction: discord.Interaction, 
        name: str = None,
        age: int = None,
        country: str = None,
        bio: str = None
    ):
        if not any([name, age, country, bio]):
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Укажите хотя бы одно поле для обновления!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if age is not None and (age < 13 or age > 100):
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Возраст должен быть от 13 до 100 лет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        if bio and len(bio) > 1024:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Биография не может быть длиннее 1024 символов!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем текущие данные
        result = await self.db.get_row("user_profiles", user_id=str(interaction.user.id))
            
        if result:
            # Обновляем только предоставленные данные
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if age is not None:
                update_data['age'] = age
            if country is not None:
                update_data['country'] = country
            if bio is not None:
                update_data['bio'] = bio
                    
            if update_data:
                await self.db.update(
                    "user_profiles",
                    where={"user_id": str(interaction.user.id)},
                    values=update_data
                )
        else:
            # Создаем новую запись
            await self.db.insert(
                "user_profiles",
                {
                    "user_id": str(interaction.user.id),
                    "name": name,
                    "age": age,
                    "country": country,
                    "bio": bio
                }
            )
            
        await interaction.response.send_message(
            embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Профиль обновлен",
                description="Информация в вашем профиле была успешно обновлена!",
                color="GREEN"
            )
        )

    @app_commands.command(name="view", description="Посмотреть профиль пользователя")
    @app_commands.describe(user="Пользователь, чей профиль вы хотите посмотреть")
    async def bio_view(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        # Получаем профиль пользователя
        result = await self.db.get_row("user_profiles", user_id=str(target_user.id))
        
        # Если профиля нет, создаем пустой
        if not result:
            result = await self.db.insert(
                "user_profiles",
                {
                    "user_id": str(target_user.id),
                    "name": None,
                    "age": None,
                    "country": None,
                    "bio": None
                }
            )
            
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['INFO']} Профиль создан",
                    description=(
                        f"Профиль {'был создан для вас' if target_user == interaction.user else f'пользователя {target_user.display_name} был создан'}!\n"
                        f"Используйте команду `/bio set`, чтобы заполнить информацию."
                    ),
                    color="BLUE"
                )
            )
            return
            
        embed = Embed(
            title=f"{EMOJIS['USER']} Профиль {target_user.display_name}",
            color="BLUE"
        )
        
        # Добавляем поля только если они не пустые
        if result['name']:
            embed.add_field(name="Имя", value=result['name'], inline=True)
        if result['age']:
            embed.add_field(name="Возраст", value=str(result['age']), inline=True)
        if result['country']:
            embed.add_field(name="Страна", value=result['country'], inline=True)
        if result['bio']:
            embed.add_field(name="О себе", value=result['bio'], inline=False)
            
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Очистить свой профиль")
    async def bio_clear(self, interaction: discord.Interaction):
        await self.db.execute(
            "DELETE FROM user_profiles WHERE user_id = ?",
            (str(interaction.user.id),)
        )
            
        await interaction.response.send_message(
            embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Профиль очищен",
                description="Вся информация из вашего профиля была удалена!",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Bio(bot)) 