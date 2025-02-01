import discord
from typing import Optional
from Niludetsu.database.db import Database
import yaml
import traceback

class TempRoomsManager:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.db = Database()
        self._config = None
        
    def load_config(self) -> dict:
        """Загрузка конфигурации из файла"""
        try:
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self._config = config.get('temp_rooms', {})
                return self._config
        except Exception as e:
            print(f"❌ Ошибка при загрузке конфигурации: {e}")
            return {}

    async def setup_control_panel(self):
        """Настройка панели управления временными комнатами"""
        try:
            config = self.load_config()
            if not config:
                print("❌ Конфигурация временных комнат не найдена")
                return False

            message_channel_id = config.get('message')
            if not message_channel_id:
                print("❌ ID канала для сообщения не указан")
                return False

            channel = self.bot.get_channel(int(message_channel_id))
            if not channel:
                print(f"❌ Канал {message_channel_id} не найден")
                return False

            # Создаем сообщение с кнопками управления
            embed = discord.Embed(
                title="🎮 Управление временным каналом",
                description=(
                    "Используйте кнопки ниже для управления вашим временным каналом:\n\n"
                    "👑 - Передать права владельца\n"
                    "👥 - Управление доступом\n"
                    "🔢 - Изменить лимит пользователей\n"
                    "🔒 - Закрыть/открыть канал\n"
                    "✏️ - Переименовать канал\n"
                    "👁 - Скрыть/показать канал\n"
                    "🚫 - Забанить пользователя\n"
                    "🔇 - Замутить пользователя\n"
                    "🎵 - Включить/выключить режим музыки"
                ),
                color=discord.Color.blurple()
            )

            # Проверяем существующие сообщения
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and message.embeds:
                    if message.embeds[0].title == "🎮 Управление временным каналом":
                        return True

            await channel.send(embed=embed, view=None)  # view будет добавлен в коге
            return True

        except Exception as e:
            print(f"❌ Ошибка при настройке панели управления: {e}")
            traceback.print_exc()
            return False

    async def create_temp_room(self, member: discord.Member) -> Optional[discord.VoiceChannel]:
        """Создает временный голосовой канал"""
        try:
            config = self.load_config()
            if not config:
                return None

            category_id = config.get('category')
            if not category_id:
                return None

            category = member.guild.get_channel(int(category_id))
            if not category:
                return None

            # Создаем права доступа для канала
            overwrites = {
                member: discord.PermissionOverwrite(
                    manage_channels=True,
                    move_members=True,
                    view_channel=True,
                    connect=True,
                    speak=True
                ),
                member.guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True
                )
            }
            
            # Создаем канал
            channel = await member.guild.create_voice_channel(
                f"Канал {member.display_name}",
                category=category,
                overwrites=overwrites
            )
            
            # Сохраняем в базу данных
            await self.db.execute(
                """
                INSERT INTO temp_rooms (channel_id, guild_id, owner_id, name, channel_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                str(channel.id), str(member.guild.id), str(member.id), channel.name, 2
            )
            
            print(f"✅ Создан временный канал {channel.id} для {member.name}")
            return channel
            
        except Exception as e:
            print(f"❌ Ошибка при создании временного канала: {e}")
            traceback.print_exc()
            return None

    async def update_temp_room(self, channel_id: str, **kwargs) -> bool:
        """Обновляет параметры временного канала"""
        try:
            await self.db.execute(
                """
                UPDATE temp_rooms 
                SET name = COALESCE(?, name)
                WHERE channel_id = ?
                """,
                kwargs.get('name'), channel_id
            )
            return True
        except Exception as e:
            print(f"❌ Ошибка при обновлении канала: {e}")
            return False

    async def delete_temp_room(self, channel_id: str) -> bool:
        """Удаляет временный канал"""
        try:
            await self.db.execute(
                "DELETE FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
            print(f"✅ Удален временный канал {channel_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при удалении временного канала: {e}")
            return False

    async def is_temp_room_owner(self, user_id: str, channel_id: str) -> bool:
        """Проверяет, является ли пользователь владельцем временного канала"""
        try:
            result = await self.db.fetch_one(
                """
                SELECT owner_id 
                FROM temp_rooms 
                WHERE channel_id = ? AND owner_id = ?
                """,
                str(channel_id), str(user_id)
            )
            return bool(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке владельца канала: {e}")
            return False

    async def get_temp_room(self, channel_id: str) -> Optional[dict]:
        """Получает информацию о временном канале"""
        try:
            result = await self.db.fetch_one(
                """
                SELECT channel_id, guild_id, owner_id, name, channel_type
                FROM temp_rooms 
                WHERE channel_id = ?
                """,
                str(channel_id)
            )
            return result if result else None
        except Exception as e:
            print(f"❌ Ошибка при получении информации о канале: {e}")
            return None 