import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, DB_PATH, initialize_table, TABLES_SCHEMAS
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
                    description="Возраст должен быть от 13 до 100 лет!"
                )
            )
            return
            
        if bio and len(bio) > 1024:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Биография не может быть длиннее 1024 символов!"
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
                title="✅ Профиль обновлен",
                description="Информация в вашем профиле была успешно обновлена!"
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
                        description=f"{'Ваш профиль' if target_user == interaction.user else f'Профиль {target_user.display_name}'} еще не настроен!"
                    )
                )
                return
                
            # Распаковываем данные
            user_id, name, age, country, bio, timestamp = profile
            
            # Формируем описание
            description = []
            if name:
                description.append(f"**Имя:** {name}")
            if age:
                description.append(f"**Возраст:** {age}")
            if country:
                description.append(f"**Страна:** {country}")
            if bio:
                description.append(f"**О себе:** `{bio}`")
                
            embed = create_embed(
                title=f"Профиль {target_user.display_name}",
                description="\n".join(description) if description else "Профиль пуст"
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            if timestamp:
                try:
                    # Обрезаем миллисекунды перед парсингом
                    timestamp = timestamp.split('.')[0]
                    formatted_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
                    embed.set_footer(text=f"Последнее обновление: {formatted_time}")
                except Exception as e:
                    print(f"Ошибка форматирования времени: {e}")
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Очистить свой профиль")
    async def bio_clear(self, interaction: discord.Interaction):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (interaction.user.id,))
            conn.commit()
            
        await interaction.response.send_message(
            embed=create_embed(
                title="✅ Профиль очищен",
                description="Вся информация из вашего профиля была удалена!"
            )
        )

async def setup(bot):
    await bot.add_cog(Bio(bot)) 