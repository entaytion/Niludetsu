import discord
from discord.ext import commands
from discord import ui
import asyncio
import yaml
import os
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.database import Database
from Niludetsu.logging.voice import VoiceLogger
import traceback
from typing import Optional, Dict, Any

def load_config():
    with open('data/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class VoiceChannelManager:
    def __init__(self):
        self.config = load_config()
        self.db = Database()
    
    async def add_channel(self, user_id: str, channel_id: int, guild_id: str, name: str):
        """Добавляет канал в базу данных"""
        try:
            await self.db.insert("temp_rooms", {
                'channel_id': str(channel_id),
                'guild_id': str(guild_id),
                'owner_id': str(user_id),
                'name': name,
                'channel_type': 2  # 2 - voice channel
            })
        except Exception as e:
            print(f"❌ Ошибка при добавлении канала: {e}")
    
    async def delete_temp_room(self, channel_id: str):
        """Удаляет канал из базы данных"""
        try:
            # Проверяем существование канала в базе
            result = await self.db.fetch_one(
                "SELECT channel_id FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
            
            if result:
                await self.db.execute(
                    "DELETE FROM temp_rooms WHERE channel_id = ?",
                    channel_id
                )
                print(f"✅ Канал {channel_id} успешно удален из базы данных")
            else:
                print(f"⚠️ Канал {channel_id} не найден в базе данных")
                
        except Exception as e:
            print(f"❌ Ошибка при удалении канала из базы данных: {e}")
            traceback.print_exc()
    
    async def get_channel(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные канала пользователя"""
        try:
            result = await self.db.fetch_one(
                """
                SELECT * 
                FROM temp_rooms 
                WHERE owner_id = ? AND channel_type = 2
                """,
                str(user_id)
            )
            return result
        except Exception as e:
            print(f"❌ Ошибка при получении канала: {e}")
            return None

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

    async def update_temp_room(self, channel_id: str, **kwargs):
        """Обновляет данные временного канала"""
        try:
            await self.db.update(
                "temp_rooms",
                where={"channel_id": str(channel_id)},
                values=kwargs
            )
        except Exception as e:
            print(f"❌ Ошибка при обновлении канала: {e}")

class VoiceChannelView(ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceCrown", id="1332417411370057781"), style=discord.ButtonStyle.gray, row=0)
    async def transfer_ownership(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Передача прав владельца"""
        await self._handle_voice_action(interaction, "transfer")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceUsers", id="1332418260435603476"), style=discord.ButtonStyle.gray, row=0)
    async def manage_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Управление доступом"""
        await self._handle_voice_action(interaction, "access")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceNumbers", id="1332418493915725854"), style=discord.ButtonStyle.gray, row=0)
    async def change_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Изменение лимита пользователей"""
        await self._handle_voice_action(interaction, "limit")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceLock", id="1332418712304615495"), style=discord.ButtonStyle.gray, row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Закрытие/открытие канала"""
        await self._handle_voice_action(interaction, "lock")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoicePencil", id="1332418910242471967"), style=discord.ButtonStyle.gray, row=0)
    async def rename_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Переименование канала"""
        await self._handle_voice_action(interaction, "rename")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceVisible", id="1332419077184163920"), style=discord.ButtonStyle.gray, row=1)
    async def toggle_visibility(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Переключение видимости канала"""
        await self._handle_voice_action(interaction, "visibility")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceKick", id="1332419383003447427"), style=discord.ButtonStyle.gray, row=1)
    async def kick_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Выгнать пользователя"""
        await self._handle_voice_action(interaction, "kick")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceMute", id="1332419509830553601"), style=discord.ButtonStyle.gray, row=1)
    async def toggle_mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Включить/выключить мут для всех"""
        await self._handle_voice_action(interaction, "mute")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceBitrate", id="1332419630672904294"), style=discord.ButtonStyle.gray, row=1)
    async def change_bitrate(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Изменить битрейт канала"""
        await self._handle_voice_action(interaction, "bitrate")

    async def _handle_voice_action(self, interaction: discord.Interaction, action: str):
        """Обработчик действий с каналом"""
        try:
            # Проверяем, является ли пользователь владельцем какого-либо канала
            channel_data = await self.manager.get_channel(str(interaction.user.id))
            if not channel_data:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="У вас нет активного голосового канала!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            channel = interaction.guild.get_channel(int(channel_data['channel_id']))
            if not channel:
                await self.manager.delete_temp_room(str(channel_data['channel_id']))
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="Канал не найден!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            if action == "transfer":
                await self._transfer_ownership(interaction, channel)
            elif action == "access":
                await self._manage_access(interaction, channel)
            elif action == "limit":
                await self._change_limit(interaction, channel)
            elif action == "lock":
                await self._toggle_lock(interaction, channel)
            elif action == "rename":
                await self._rename_channel(interaction, channel)
            elif action == "visibility":
                await self._toggle_visibility(interaction, channel)
            elif action == "kick":
                await self._kick_user(interaction, channel)
            elif action == "mute":
                await self._toggle_mute(interaction, channel)
            elif action == "bitrate":
                await self._change_bitrate(interaction, channel)

        except Exception as e:
            print(f"❌ Ошибка при обработке действия с каналом: {e}")
            traceback.print_exc()
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Произошла ошибка при выполнении действия!",
                    color="RED"
                ),
                ephemeral=True
            )

    async def _transfer_ownership(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Передача прав владельца"""
        members = [m for m in channel.members if m.id != interaction.user.id and not m.bot]
        if not members:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="В канале нет участников для передачи прав!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        options = [
            discord.SelectOption(
                label=member.display_name,
                value=str(member.id),
                description=f"ID: {member.id}"
            )
            for member in members
        ]

        select = ui.Select(
            placeholder="Выберите нового владельца",
            options=options
        )

        async def select_callback(select_interaction: discord.Interaction):
            new_owner_id = int(select.values[0])
            new_owner = select_interaction.guild.get_member(new_owner_id)

            # Обновляем права доступа
            await channel.set_permissions(new_owner, 
                manage_channels=True,
                move_members=True,
                view_channel=True,
                connect=True,
                speak=True
            )
            await channel.set_permissions(interaction.user,
                manage_channels=False,
                move_members=False,
                view_channel=True,
                connect=True,
                speak=True
            )

            # Обновляем владельца в базе данных
            await self.manager.update_temp_room(str(channel.id), owner_id=str(new_owner_id))

            await select_interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['SUCCESS']} Успешно",
                    description=f"Права на канал переданы пользователю {new_owner.mention}",
                    color="GREEN"
                ),
                ephemeral=True
            )

        select.callback = select_callback
        view = ui.View()
        view.add_item(select)
        await interaction.response.send_message(
            embed=Embed(
                title="👑 Передача прав",
                description="Выберите нового владельца канала:",
                color="BLUE"
            ),
            view=view,
            ephemeral=True
        )

    async def _manage_access(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Управление доступом к каналу"""
        modal = ui.Modal(title="Управление доступом")
        
        user_input = ui.TextInput(
            label="ID или никнейм пользователя",
            placeholder="Введите ID или никнейм пользователя",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(user_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                # Пытаемся найти пользователя по ID
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    # Если ID не найден, ищем по никнейму
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                if member.id == modal_interaction.user.id:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Вы не можете управлять своим доступом!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                if member.bot:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Вы не можете управлять доступом ботов!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                current_perms = channel.permissions_for(member)
                if current_perms.connect:
                    await channel.set_permissions(member, connect=False)
                    action = "ограничен"
                else:
                    await channel.set_permissions(member, connect=True)
                    action = "разрешен"

                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['SUCCESS']} Успешно",
                        description=f"Доступ для {member.mention} {action}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _change_limit(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Изменение лимита пользователей"""
        modal = ui.Modal(title="Изменение лимита пользователей")
        
        limit_input = ui.TextInput(
            label="Новый лимит (0-99, 0 - без лимита)",
            placeholder="Введите число от 0 до 99",
            required=True,
            min_length=1,
            max_length=2
        )
        modal.add_item(limit_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                new_limit = int(limit_input.value)
                if new_limit < 0 or new_limit > 99:
                    raise ValueError("Лимит должен быть от 0 до 99")
                
                await channel.edit(user_limit=new_limit)
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['SUCCESS']} Успешно",
                        description=f"Установлен лимит: {new_limit if new_limit > 0 else 'без лимита'}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except ValueError as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _toggle_lock(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Закрытие/открытие канала"""
        current_perms = channel.overwrites_for(interaction.guild.default_role)
        is_locked = not current_perms.connect if current_perms.connect is not None else True
        
        await channel.set_permissions(
            interaction.guild.default_role,
            connect=not is_locked
        )
        
        status = "закрыт" if is_locked else "открыт"
        await interaction.response.send_message(
            embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Успешно",
                description=f"Канал {status}",
                color="GREEN"
            ),
            ephemeral=True
        )

    async def _rename_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Переименование канала"""
        modal = ui.Modal(title="Переименование канала")
        
        name_input = ui.TextInput(
            label="Новое название",
            placeholder="Введите новое название канала",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(name_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            new_name = name_input.value
            await channel.edit(name=new_name)
            await self.manager.update_temp_room(str(channel.id), name=new_name)
            
            await modal_interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['SUCCESS']} Успешно",
                    description=f"Канал переименован в: {new_name}",
                    color="GREEN"
                ),
                ephemeral=True
            )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _toggle_visibility(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Переключение видимости канала"""
        current_perms = channel.overwrites_for(interaction.guild.default_role)
        is_visible = not current_perms.view_channel if current_perms.view_channel is not None else True
        
        await channel.set_permissions(
            interaction.guild.default_role,
            view_channel=not is_visible
        )
        
        status = "скрыт" if is_visible else "виден"
        await interaction.response.send_message(
            embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Успешно",
                description=f"Канал теперь {status}",
                color="GREEN"
            ),
            ephemeral=True
        )

    async def _kick_user(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Выгнать пользователя из канала"""
        modal = ui.Modal(title="Исключение пользователя")
        
        user_input = ui.TextInput(
            label="ID или никнейм пользователя",
            placeholder="Введите ID или никнейм пользователя",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(user_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                # Пытаемся найти пользователя по ID
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    # Если ID не найден, ищем по никнейму
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                if member.id == modal_interaction.user.id:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Вы не можете исключить себя!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                if member.bot:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Вы не можете исключить бота!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                if not member.voice or member.voice.channel != channel:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Пользователь не находится в вашем канале!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                await member.move_to(None)
                await channel.set_permissions(member, connect=False)
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['SUCCESS']} Успешно",
                        description=f"Пользователь {member.mention} исключен из канала",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _toggle_mute(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Включить/выключить мут для всех"""
        current_perms = channel.overwrites_for(interaction.guild.default_role)
        is_muted = not current_perms.speak if current_perms.speak is not None else True
        
        await channel.set_permissions(
            interaction.guild.default_role,
            speak=not is_muted
        )
        
        status = "выключен" if is_muted else "включен"
        await interaction.response.send_message(
            embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Успешно",
                description=f"Голосовой чат {status} для всех пользователей",
                color="GREEN"
            ),
            ephemeral=True
        )

    async def _change_bitrate(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Изменение битрейта канала"""
        modal = ui.Modal(title="Изменение битрейта")
        
        bitrate_input = ui.TextInput(
            label="Новый битрейт (8-96 кбит/с)",
            placeholder="Введите число от 8 до 96",
            required=True,
            min_length=1,
            max_length=2
        )
        modal.add_item(bitrate_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                new_bitrate = int(bitrate_input.value)
                if new_bitrate < 8 or new_bitrate > 96:
                    raise ValueError("Битрейт должен быть от 8 до 96 кбит/с")
                
                await channel.edit(bitrate=new_bitrate * 1000)
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['SUCCESS']} Успешно",
                        description=f"Установлен битрейт: {new_bitrate} кбит/с",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except ValueError as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

class VoiceChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = VoiceChannelManager()
        self.voice_logger = VoiceLogger(bot)
        asyncio.create_task(self._initialize())
        
    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.manager.db.init()
        # Даем боту время на загрузку каналов
        await asyncio.sleep(5)
        await self.setup_voice_channel()
        
    def create_panel_view(self):
        return VoiceChannelView(self.manager)
        
    async def setup_voice_channel(self):
        """Настройка системы временных каналов"""
        try:
            config = load_config()
            if 'temp_rooms' not in config:
                print("❌ Конфигурация временных комнат не найдена")
                return
                
            if 'voice' not in config['temp_rooms']:
                print("❌ Не найден ID канала для создания временных каналов")
                return
                
            if 'message' not in config['temp_rooms']:
                print("❌ Не найден ID сообщения управления")
                return
                
            voice_channel_id = config['temp_rooms']['voice']
            message_channel_id = config['temp_rooms']['channel']
            message_id = config['temp_rooms']['message']
            
            # Делаем несколько попыток получить каналы
            retries = 3
            voice_channel = None
            message_channel = None
            
            for _ in range(retries):
                voice_channel = self.bot.get_channel(int(voice_channel_id))
                message_channel = self.bot.get_channel(int(message_channel_id))
                
                if voice_channel and message_channel:
                    break
                    
                await asyncio.sleep(2)
            
            if not voice_channel:
                print(f"⚠️ Предупреждение: Канал для создания временных каналов не найден: {voice_channel_id}")
                # Не прерываем выполнение, так как канал может быть доступен позже
            
            if not message_channel:
                print(f"❌ Канал для сообщения управления не найден: {message_channel_id}")
                return

            if message_channel:
                try:
                    # Пытаемся получить существующее сообщение
                    message = await message_channel.fetch_message(int(message_id))
                    if message:
                        # Обновляем существующее сообщение
                        embed = Embed(
                            title="🎮 Управление временным каналом",
                            description=(
                                "Используйте кнопки ниже для управления вашим временным каналом:\n\n"
                                "👑 - Передать права владельца\n"
                                "👥 - Управление доступом\n"
                                "🔢 - Изменить лимит пользователей\n"
                                "🔒 - Закрыть/открыть канал\n"
                                "✏️ - Переименовать канал\n"
                                "👁️ - Переключить видимость канала\n"
                                "👢 - Выгнать пользователя\n"
                                "🔇 - Включить/выключить мут для всех\n"
                                "🔉 - Изменить битрейт канала"
                            ),
                            color="BLUE"
                        )
                        await message.edit(embed=embed, view=self.create_panel_view())
                        return
                except discord.NotFound:
                    print(f"❌ Сообщение управления не найдено: {message_id}")
                except Exception as e:
                    print(f"❌ Ошибка при обновлении сообщения управления: {e}")
            
        except Exception as e:
            print(f"❌ Ошибка при настройке временных каналов: {e}")
            traceback.print_exc()
            
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Обработчик изменений голосового состояния"""
        try:
            config = load_config()
            if 'temp_rooms' not in config or 'voice' not in config['temp_rooms']:
                return
                
            voice_channel_id = config['temp_rooms']['voice']
            category_id = config['temp_rooms']['category']
            
            # Если пользователь зашел в канал создания
            if after.channel and str(after.channel.id) == str(voice_channel_id):
                category = member.guild.get_channel(int(category_id))
                if not category:
                    print(f"❌ Категория {category_id} не найдена")
                    return

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
                
                # Создаем новый канал
                new_channel = await member.guild.create_voice_channel(
                    f"Канал {member.display_name}",
                    category=category,
                    overwrites=overwrites
                )
                
                # Сохраняем в базу данных
                await self.manager.db.execute(
                    """
                    INSERT INTO temp_rooms (channel_id, guild_id, owner_id, name, channel_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    str(new_channel.id), str(member.guild.id), str(member.id), new_channel.name, 2
                )
                
                # Перемещаем пользователя в новый канал
                await member.move_to(new_channel)
                print(f"✅ Создан временный канал {new_channel.id} для {member.name}")
                    
            # Если пользователь вышел из временного канала
            elif before.channel:
                result = await self.manager.db.fetch_one(
                    """
                    SELECT owner_id 
                    FROM temp_rooms 
                    WHERE channel_id = ?
                    """,
                    str(before.channel.id)
                )
                
                if result and not before.channel.members:
                    try:
                        await before.channel.delete()
                        await self.manager.delete_temp_room(str(before.channel.id))
                        print(f"✅ Удален пустой временный канал {before.channel.name}")
                    except Exception as e:
                        print(f"❌ Ошибка при удалении канала: {e}")
                        traceback.print_exc()
                    
        except Exception as e:
            print(f"❌ Ошибка при обработке голосового события: {e}")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(VoiceChannelCog(bot)) 