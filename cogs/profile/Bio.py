import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.database import DB_PATH, initialize_table, TABLES_SCHEMAS
import sqlite3
from datetime import datetime

class Bio(commands.GroupCog, group_name="bio"):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        
    def setup_database(self):
        initialize_table('user_profiles', TABLES_SCHEMAS['user_profiles'])

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
        if age is not None and (age < 13 or age > 100):
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Возраст должен быть от 13 до 100 лет!",
                    color="RED"
                )
            )
            return
            
        if bio and len(bio) > 1024:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Биография не может быть длиннее 1024 символов!",
                    color="RED"
                )
            )
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем текущие данные
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (interaction.user.id,))
            current_data = cursor.fetchone()
            
            if current_data:
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
                    set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
                    values = list(update_data.values())
                    values.append(interaction.user.id)
                    
                    cursor.execute(
                        f"UPDATE user_profiles SET {set_clause} WHERE user_id = ?",
                        values
                    )
            else:
                # Создаем новую запись
                cursor.execute(
                    "INSERT INTO user_profiles (user_id, name, age, country, bio) VALUES (?, ?, ?, ?, ?)",
                    (interaction.user.id, name, age, country, bio)
                )
            
            conn.commit()
            
        await interaction.response.send_message(
            embed=create_embed(
                title=f"{EMOJIS['SUCCESS']} Профиль обновлен",
                description="Информация в вашем профиле была успешно обновлена!",
                color="GREEN"
            )
        )

    @app_commands.command(name="view", description="Посмотреть профиль пользователя")
    @app_commands.describe(user="Пользователь, чей профиль вы хотите посмотреть")
    async def bio_view(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (target_user.id,))
            profile = cursor.fetchone()
            
            if not profile:
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Профиль не найден",
                        description=f"{'Ваш профиль' if target_user == interaction.user else f'Профиль {target_user.display_name}'} еще не настроен!",
                        color="RED"
                    )
                )
                return
                
            # Распаковываем данные
            user_id, name, age, country, bio, timestamp = profile
            
            # Формируем описание
            description = []
            if name:
                description.append(f"{EMOJIS['NAME']} **Имя:** {name}")
            if age:
                description.append(f"{EMOJIS['AGE']} **Возраст:** {age}")
            if country:
                description.append(f"{EMOJIS['COUNTRY']} **Страна:** {country}")
            if bio:
                description.append(f"{EMOJIS['BIO']} **О себе:** `{bio}`")
                
            embed = create_embed(
                title=f"{EMOJIS['PROFILE']} Профиль {target_user.display_name}",
                description="\n".join(description) if description else "Профиль пуст",
                color="BLUE"
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            if timestamp:
                # Обрезаем миллисекунды перед парсингом
                timestamp = timestamp.split('.')[0]
                formatted_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
                embed.set_footer(text=f"Последнее обновление: {formatted_time}")
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Очистить свой профиль")
    async def bio_clear(self, interaction: discord.Interaction):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (interaction.user.id,))
            conn.commit()
            
        await interaction.response.send_message(
            embed=create_embed(
                title=f"{EMOJIS['SUCCESS']} Профиль очищен",
                description="Вся информация из вашего профиля была удалена!",
                color="GREEN"
            )
        )

async def setup(bot):
    await bot.add_cog(Bio(bot)) 