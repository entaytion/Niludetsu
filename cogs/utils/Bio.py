import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime
from utils import create_embed, EMOJIS

class Bio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "config/database.db"
        self.setup_database()

    def setup_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    country TEXT,
                    bio TEXT
                )
            """)
            db.commit()

    bio_group = app_commands.Group(name="bio", description="Команды для управления профилем")

    @bio_group.command(name="set", description="Установить данные профиля")
    @app_commands.describe(
        name="Ваше имя (макс. 32 символа)",
        age="Ваш возраст (13-99)",
        country="Страна (макс. 32 символа)",
        bio="Ваша биография (макс. 1000 символов)"
    )
    async def bio_set(self, interaction: discord.Interaction, name: str = None, age: int = None, country: str = None, bio: str = None):
        if not any([name, age, country, bio]):
            await interaction.response.send_message(
                embed=create_embed(description=f"{EMOJIS['ERROR']} Укажите хотя бы один параметр для изменения!"),
                ephemeral=True
            )
            return

        if name and len(name) > 32:
            await interaction.response.send_message(
                embed=create_embed(description=f"{EMOJIS['ERROR']} Имя не должно превышать 32 символа!"),
                ephemeral=True
            )
            return

        if age and (age < 13 or age > 99):
            await interaction.response.send_message(
                embed=create_embed(description=f"{EMOJIS['ERROR']} Возраст должен быть от 13 до 99 лет!"),
                ephemeral=True
            )
            return

        if country and len(country) > 32:
            await interaction.response.send_message(
                embed=create_embed(description=f"{EMOJIS['ERROR']} Название страны не должно превышать 32 символа!"),
                ephemeral=True
            )
            return

        if bio and len(bio) > 1000:
            await interaction.response.send_message(
                embed=create_embed(description=f"{EMOJIS['ERROR']} Биография не должна превышать 1000 символов!"),
                ephemeral=True
            )
            return

        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles 
                    (user_id, name, age, country, bio) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (interaction.user.id, name, age, country, bio or "")
                )
                db.commit()

            embed = create_embed(
                title="✏️ Профиль обновлён",
                description=f"{EMOJIS['SUCCESS']} Ваш профиль был успешно обновлён!",
                fields=[
                    {"name": "Имя:", "value": name, "inline": True},
                    {"name": "Возраст:", "value": f"{age} лет", "inline": True},
                    {"name": "Страна:", "value": country, "inline": True}
                ]
            )
            
            if bio:
                embed.add_field(name="О себе:", value=f"```{bio}```", inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при обновлении профиля: {str(e)}"
                ),
                ephemeral=True
            )

    @bio_group.command(name="view", description="Посмотреть профиль пользователя")
    @app_commands.describe(user="Пользователь, чей профиль вы хотите посмотреть")
    async def bio_view(self, interaction: discord.Interaction, user: discord.User = None):
        target_user = user or interaction.user

        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    """
                    SELECT name, age, country, bio
                    FROM user_profiles
                    WHERE user_id = ?
                    """,
                    (target_user.id,)
                )
                result = cursor.fetchone()

            if not result:
                if target_user == interaction.user:
                    message = f"{EMOJIS['ERROR']} У вас ещё нет профиля. Используйте `/bio set`, чтобы создать его!"
                else:
                    message = f"{EMOJIS['ERROR']} У пользователя {target_user.mention} нет профиля."
                
                await interaction.response.send_message(embed=create_embed(description=message))
                return

            name, age, country, bio = result

            fields = []
            if name:
                fields.append({"name": "Имя:", "value": name, "inline": True})
            if age:
                fields.append({"name": "Возраст:", "value": f"{age} лет", "inline": True})
            if country:
                fields.append({"name": "Страна:", "value": country, "inline": True})
            if bio:
                fields.append({"name": "О себе:", "value": bio, "inline": False})

            embed = create_embed(
                title=f"👤 Профиль {target_user.name}",
                fields=fields,
                thumbnail_url=target_user.display_avatar.url,
                footer={"text": f"Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M')}"}
            )
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при получении профиля: {str(e)}"
                ),
                ephemeral=True
            )

    @bio_group.command(name="clear", description="Удалить свой профиль")
    async def bio_clear(self, interaction: discord.Interaction):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(
                    "DELETE FROM user_profiles WHERE user_id = ?",
                    (interaction.user.id,)
                )
                db.commit()

            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} Ваш профиль был успешно удалён!"
                )
            )

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при удалении профиля: {str(e)}"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Bio(bot)) 