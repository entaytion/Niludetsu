import discord, asyncio
from discord.ext import commands
from discord import ui
from Niludetsu import Embed, Emojis, Database

class TempRoomsManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    async def setup_control_panel(self, guild_id: str):
        """Настраивает панель управления временными каналами"""
        try:
            # Получаем настройки из базы данных
            settings = await self.db.fetch_all(
                "SELECT key, value FROM settings WHERE category = 'temp_rooms' AND guild_id = ?",
                guild_id
            )
            
            settings_dict = {row['key']: row['value'] for row in settings}
            
            channel_id = settings_dict.get('control_channel')
            if not channel_id:
                raise ValueError("Канал управления не настроен")
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Канал управления не найден: {channel_id}")
                
            # Создаем сообщение с панелью управления
            embed = Embed(
                title="🎮 Управление временными каналами",
                description=(
                    "Используйте кнопки ниже для управления вашим временным каналом:\n\n"
                    f"{Emojis.VOICE_OWNER} - Передать права владельца\n"
                    f"{Emojis.VOICE_ACCESS} - Управление доступом\n"
                    f"{Emojis.VOICE_LIMIT} - Изменить лимит пользователей\n"
                    f"{Emojis.VOICE_LOCK} - Закрыть/открыть канал\n"
                    f"{Emojis.VOICE_EDIT} - Переименовать канал\n"
                    f"{Emojis.VOICE_TRUST} - Доверять пользователю\n"
                    f"{Emojis.VOICE_UNTRUST} - Не доверять пользователю\n"
                    f"{Emojis.VOICE_INVITE} - Создать приглашение\n"
                    f"{Emojis.VOICE_BAN} - Забанить пользователя\n"
                    f"{Emojis.VOICE_UNBAN} - Разбанить пользователя\n"
                    f"{Emojis.VOICE_REVOKE} - Забрать права\n"
                    f"{Emojis.VOICE_THREAD} - Создать ветку обсуждения\n"
                    f"{Emojis.VOICE_REGION} - Изменить регион\n"
                    f"{Emojis.VOICE_DELETE} - Удалить канал"
                ),
                color="BLUE"
            ).set_image(url="https://media.discordapp.net/attachments/1332296613988794450/1336455114126262422/voice.png?ex=67a3de51&is=67a28cd1&hm=61524318fecfadefce607fff7625d11d3ce2f0eae45a52d5228bc1ee0e3082e2&=&format=webp&quality=lossless&width=1920&height=640")
            
            message = await channel.send(embed=embed, view=TempRoomsView(self))
            
            # Сохраняем ID сообщения в базу данных
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value, guild_id)
                VALUES ('temp_rooms', 'control_message', ?, ?)
                """,
                (str(message.id), guild_id)
            )
            
            return message
            
        except Exception as e:
            print(f"❌ Ошибка при настройке панели управления: {e}")
            return None
            
    async def create_temp_room(self, member: discord.Member, name: str = None):
        """Создает временный голосовой канал"""
        try:
            # Получаем категорию из базы данных
            category_id = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'temp_rooms' AND key = 'category' AND guild_id = ?",
                str(member.guild.id)
            )
            
            if not category_id:
                raise ValueError("Категория для временных каналов не настроена")
                
            category = member.guild.get_channel(int(category_id))
            if not category:
                raise ValueError(f"Категория не найдена: {category_id}")
                
            # Создаем права доступа
            overwrites = {
                member: discord.PermissionOverwrite(
                    manage_channels=True,
                    move_members=True,
                    view_channel=True,
                    connect=True,
                    speak=True,
                    stream=True,
                    use_voice_activation=True
                ),
                member.guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,
                    stream=True,
                    use_voice_activation=True
                )
            }
            
            # Создаем канал
            channel_name = name or f"Канал {member.display_name}"
            channel = await member.guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                bitrate=64000,
                user_limit=0
            )
            
            # Сохраняем в базу данных
            await self.db.execute(
                """
                INSERT INTO temp_rooms (channel_id, guild_id, owner_id, name, channel_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(channel.id), str(member.guild.id), str(member.id), channel_name, 2)
            )
            
            # Перемещаем пользователя
            await member.move_to(channel)
            return channel
            
        except Exception as e:
            print(f"❌ Ошибка при создании временного канала: {e}")
            return None
            
    async def delete_temp_room(self, channel_id: str):
        """Удаляет временный канал"""
        try:
            # Получаем информацию о канале
            room = await self.db.fetch_one(
                "SELECT * FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
            
            if not room:
                return False
                
            # Удаляем тред, если есть
            if 'thread_id' in room and room['thread_id']:
                try:
                    thread = self.bot.get_channel(int(room['thread_id']))
                    if thread:
                        await thread.delete()
                except:
                    pass
                    
            # Удаляем канал
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                await channel.delete()
                
            # Удаляем из базы данных
            await self.db.execute(
                "DELETE FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при удалении временного канала: {e}")
            return False
            
    async def get_temp_room(self, channel_id: str):
        """Получает информацию о временном канале"""
        try:
            return await self.db.fetch_one(
                "SELECT * FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
        except Exception as e:
            print(f"❌ Ошибка при получении информации о канале: {e}")
            return None
            
class TempRoomsView(ui.View):
    def __init__(self, manager: TempRoomsManager):
        super().__init__(timeout=None)
        self.manager = manager 