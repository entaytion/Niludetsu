import discord
from discord.ext import commands
from discord import ui
import asyncio
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database
from Niludetsu.logging.voice import VoiceLogger
import traceback
from typing import Optional, Dict, Any

class VoiceChannelManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    async def add_channel(self, channel_id: str, user_id: str, guild_id: str, name: str):
        """Добавляет временный канал в базу данных"""
        try:
            values = [str(channel_id), str(guild_id), str(user_id), str(name), 2, "[]", "[]"]
            await self.db.execute(
                """
                INSERT INTO temp_rooms (channel_id, guild_id, owner_id, name, channel_type, trusted_users, banned_users)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                values
            )
            # Проверяем, что канал добавлен
            room = await self.get_temp_room(channel_id)
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении канала в базу данных: {e}")
            traceback.print_exc()
    
    async def delete_temp_room(self, channel_id: str):
        """Удаляет канал из базы данных"""
        try:
            await self.db.execute(
                "DELETE FROM temp_rooms WHERE channel_id = ?",
                channel_id
            )
        except Exception as e:
            print(f"❌ Ошибка при удалении канала: {e}")
            traceback.print_exc()
    
    async def get_temp_room(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Получает данные временного канала"""
        try:
            result = await self.db.fetch_one(
                "SELECT * FROM temp_rooms WHERE channel_id = ?",
                str(channel_id)
            )
            return result
        except Exception as e:
            print(f"❌ Ошибка при получении данных канала: {e}")
            return None

    async def update_temp_room(self, channel_id: str, **kwargs):
        """Обновляет данные временного канала"""
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                values.append(value)
            values.append(channel_id)
            
            query = f"""
                UPDATE temp_rooms 
                SET {', '.join(updates)}
                WHERE channel_id = ?
            """
            await self.db.execute(query, values)
        except Exception as e:
            print(f"❌ Ошибка при обновлении данных канала: {e}")

    async def is_globally_banned(self, user_id: str, owner_id: str) -> bool:
        """Проверяет, находится ли пользователь в глобальном бане"""
        try:
            result = await self.db.fetch_one(
                "SELECT id FROM global_bans WHERE banned_user_id = ? AND owner_id = ?",
                user_id, owner_id
            )
            return bool(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке глобального бана: {e}")
            return False

    async def is_banned(self, channel_id: str, user_id: str) -> bool:
        """Проверяет, забанен ли пользователь в канале"""
        try:
            room = await self.get_temp_room(channel_id)
            if room and 'banned_users' in room:
                banned_users = eval(room['banned_users'])
                return user_id in banned_users
            return False
        except Exception as e:
            print(f"❌ Ошибка при проверке бана: {e}")
            return False

    async def is_trusted(self, channel_id: str, user_id: str) -> bool:
        """Проверяет, является ли пользователь доверенным"""
        try:
            room = await self.get_temp_room(channel_id)
            if room and 'trusted_users' in room:
                trusted_users = eval(room['trusted_users'])
                return user_id in trusted_users
            return False
        except Exception as e:
            print(f"❌ Ошибка при проверке доверенного пользователя: {e}")
            return False

class VoiceChannelView(ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager
        self.bot = manager.bot

    @discord.ui.button(emoji=Emojis.VOICE_OWNER, style=discord.ButtonStyle.gray, row=0)
    async def transfer_ownership(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Передача прав владельца"""
        await self._handle_voice_action(interaction, "transfer")

    @discord.ui.button(emoji=Emojis.VOICE_ACCESS, style=discord.ButtonStyle.gray, row=0)
    async def manage_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Управление доступом"""
        await self._handle_voice_action(interaction, "access")

    @discord.ui.button(emoji=Emojis.VOICE_LIMIT, style=discord.ButtonStyle.gray, row=0)
    async def change_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Изменение лимита пользователей"""
        await self._handle_voice_action(interaction, "limit")

    @discord.ui.button(emoji=Emojis.VOICE_LOCK, style=discord.ButtonStyle.gray, row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Закрытие/открытие канала"""
        await self._handle_voice_action(interaction, "lock")

    @discord.ui.button(emoji=Emojis.VOICE_EDIT, style=discord.ButtonStyle.gray, row=0)
    async def rename_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Переименование канала"""
        await self._handle_voice_action(interaction, "rename")

    @discord.ui.button(emoji=Emojis.VOICE_TRUST, style=discord.ButtonStyle.gray, row=1)
    async def trust_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Доверить пользователя"""
        await self._handle_voice_action(interaction, "trust")

    @discord.ui.button(emoji=Emojis.VOICE_UNTRUST, style=discord.ButtonStyle.gray, row=1)
    async def untrust_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Убрать доверие у пользователя"""
        await self._handle_voice_action(interaction, "untrust")

    @discord.ui.button(emoji=Emojis.VOICE_INVITE, style=discord.ButtonStyle.gray, row=1)
    async def create_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Создать приглашение"""
        await self._handle_voice_action(interaction, "invite")

    @discord.ui.button(emoji=Emojis.VOICE_BAN, style=discord.ButtonStyle.gray, row=1)
    async def ban_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Забанить пользователя"""
        await self._handle_voice_action(interaction, "ban")

    @discord.ui.button(emoji=Emojis.VOICE_UNBAN, style=discord.ButtonStyle.gray, row=1)
    async def unban_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Разбанить пользователя"""
        await self._handle_voice_action(interaction, "unban")

    @discord.ui.button(emoji=Emojis.VOICE_REVOKE, style=discord.ButtonStyle.gray, row=2)
    async def revoke_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Забрать права"""
        await self._handle_voice_action(interaction, "revoke")

    @discord.ui.button(emoji=Emojis.VOICE_THREAD, style=discord.ButtonStyle.gray, row=2)
    async def create_thread(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Создать ветку обсуждения"""
        await self._handle_voice_action(interaction, "thread")

    @discord.ui.button(emoji=Emojis.VOICE_REGION, style=discord.ButtonStyle.gray, row=2)
    async def change_region(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Изменить регион"""
        await self._handle_voice_action(interaction, "region")

    @discord.ui.button(emoji=Emojis.VOICE_DELETE, style=discord.ButtonStyle.gray, row=2)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Удалить канал"""
        await self._handle_voice_action(interaction, "delete")

    async def _handle_voice_action(self, interaction: discord.Interaction, action: str):
        """Обработчик действий с голосовым каналом"""
        try:
            # Получаем голосовой канал пользователя
            if not interaction.user.voice:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Вы должны находиться в голосовом канале!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            channel = interaction.user.voice.channel
            if not channel:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Вы должны находиться в голосовом канале!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            # Проверяем, является ли пользователь владельцем канала
            room = await self.manager.get_temp_room(str(channel.id))
            
            if not room:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Ваш текущий канал не является временным!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            if str(interaction.user.id) != room['owner_id']:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Вы не являетесь владельцем этого канала!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            # Обрабатываем действие
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
            elif action == "trust":
                await self._trust_user(interaction, channel)
            elif action == "untrust":
                await self._untrust_user(interaction, channel)
            elif action == "invite":
                await self._create_invite(interaction, channel)
            elif action == "ban":
                await self._ban_user(interaction, channel)
            elif action == "unban":
                await self._unban_user(interaction, channel)
            elif action == "revoke":
                await self._revoke_access(interaction, channel)
            elif action == "thread":
                await self._create_thread(interaction, channel)
            elif action == "region":
                await self._change_region(interaction, channel)
            elif action == "delete":
                await self._delete_channel(interaction, channel)

        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
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
                    title=f"{Emojis.ERROR} Ошибка",
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
                    title=f"{Emojis.SUCCESS} Успешно",
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
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
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Доступ для {member.mention} {action}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
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
                await self.manager.update_temp_room(str(channel.id), user_limit=new_limit)
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Установлен лимит: {new_limit if new_limit > 0 else 'без лимита'}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except ValueError as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _toggle_lock(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Закрытие/открытие канала"""
        room = await self.manager.get_temp_room(str(channel.id))
        is_locked = not room.get('is_locked', False)
        
        await channel.set_permissions(
            interaction.guild.default_role,
            connect=not is_locked
        )
        
        await self.manager.update_temp_room(str(channel.id), is_locked=is_locked)
        
        status = "закрыт" if is_locked else "открыт"
        await interaction.response.send_message(
            embed=Embed(
                title=f"{Emojis.SUCCESS} Успешно",
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
                    title=f"{Emojis.SUCCESS} Успешно",
                    description=f"Канал переименован в: {new_name}",
                    color="GREEN"
                ),
                ephemeral=True
            )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _trust_user(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Доверить пользователя"""
        modal = ui.Modal(title="Доверить пользователя")
        
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                await self.manager.add_trusted_user(str(channel.id), str(member.id))
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Пользователь {member.mention} добавлен в доверенные",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _untrust_user(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Убрать доверие у пользователя"""
        modal = ui.Modal(title="Убрать доверие у пользователя")
        
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                await self.manager.remove_trusted_user(str(channel.id), str(member.id))
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Пользователь {member.mention} удален из доверенных",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _create_invite(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Создать приглашение"""
        modal = ui.Modal(title="Создать приглашение")
        
        user_input = ui.TextInput(
            label="Никнейм пользователя",
            placeholder="Введите никнейм пользователя",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(user_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                # Ищем пользователя по никнейму
                member = discord.utils.find(
                    lambda m: user_input.value.lower() in m.display_name.lower() or 
                            user_input.value.lower() in m.name.lower(),
                    modal_interaction.guild.members
                )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return
                
                # Создаем приглашение на 24 часа
                invite = await channel.create_invite(max_age=86400)
                
                try:
                    # Создаем кнопку для приглашения
                    class InviteView(discord.ui.View):
                        def __init__(self):
                            super().__init__(timeout=None)
                            self.add_item(discord.ui.Button(
                                label="Присоединиться", 
                                url=str(invite),
                                style=discord.ButtonStyle.link
                            ))

                    # Отправляем приглашение в личные сообщения
                    await member.send(
                        embed=Embed( 
                            title="🎮 Приглашение в голосовой канал",
                            description=f"Вас приглашают в голосовой канал **{channel.name}**",
                            color="BLUE"
                        ),
                        view=InviteView()
                    )
                    
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.SUCCESS} Успешно",
                            description=f"Приглашение отправлено пользователю {member.mention}",
                            color="GREEN"
                        ),
                        ephemeral=True
                    )
                except discord.Forbidden:
                    # Создаем view с кнопкой для владельца канала
                    view = InviteView()
                    await modal_interaction.response.send_message(
                        content=f"❌ Не удалось отправить приглашение пользователю {member.mention}.\nВозможно, у него закрыты личные сообщения.",
                        view=view,
                        ephemeral=True
                    )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _ban_user(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Забанить пользователя"""
        modal = ui.Modal(title="Забанить пользователя")
        
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                # Добавляем в глобальный бан-лист
                await self.manager.add_to_global_banlist(str(member.id), str(modal_interaction.user.id))
                
                # Добавляем также в локальный бан текущего канала
                await self.manager.add_banned_user(str(channel.id), str(member.id))
                
                # Кикаем пользователя если он в канале
                if member.voice and member.voice.channel == channel:
                    await member.move_to(None)
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Пользователь {member.mention} добавлен в черный список.\nТеперь он не сможет присоединяться к вашим каналам.",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _unban_user(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Разбанить пользователя"""
        modal = ui.Modal(title="Разбанить пользователя")
        
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                # Удаляем из глобального бан-листа
                await self.manager.remove_from_global_banlist(str(member.id), str(modal_interaction.user.id))
                
                # Удаляем также из локального бана текущего канала
                await self.manager.remove_banned_user(str(channel.id), str(member.id))
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Пользователь {member.mention} удален из черного списка.\nТеперь он может присоединяться к вашим каналам.",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _revoke_access(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Забрать права"""
        modal = ui.Modal(title="Забрать права")
        
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
                user_id = ''.join(filter(str.isdigit, user_input.value))
                if user_id:
                    member = modal_interaction.guild.get_member(int(user_id))
                else:
                    member = discord.utils.find(
                        lambda m: user_input.value.lower() in m.display_name.lower() or 
                                user_input.value.lower() in m.name.lower(),
                        modal_interaction.guild.members
                    )

                if not member:
                    await modal_interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Пользователь не найден!",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                    return

                await member.move_to(None)
                await channel.set_permissions(member, connect=False)
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Права пользователя {member.mention} забраты",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _create_thread(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Создать ветку обсуждения"""
        modal = ui.Modal(title="Создать ветку обсуждения")
        
        name_input = ui.TextInput(
            label="Название ветки",
            placeholder="Введите название ветки",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(name_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                name = name_input.value
                config = await self.manager.db.fetch(
                    "SELECT value FROM settings WHERE category = 'temp_rooms' AND key = 'control_channel'"
                )
                
                if not config:
                    raise ValueError("Канал управления не настроен")

                control_channel_id = config[0]['value']
                control_channel = self.bot.get_channel(int(control_channel_id))
                
                if not control_channel:
                    raise ValueError("Канал управления не найден")

                # Создаем приватный тред
                thread = await control_channel.create_thread(
                    name=name,
                    type=discord.ChannelType.private_thread,
                    invitable=False
                )
                
                # Добавляем владельца канала в тред
                await thread.add_user(modal_interaction.user)
                
                # Обновляем информацию о треде в базе данных
                await self.manager.update_temp_room(str(channel.id), thread_id=str(thread.id))
                
                # Отправляем сообщение о создании
                await thread.send("!")

                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Ветка создана: {thread.mention}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _change_region(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Изменить регион"""
        modal = ui.Modal(title="Изменить регион")
        
        region_input = ui.TextInput(
            label="Новый регион",
            placeholder="Введите новый регион",
            required=True,
            min_length=1,
            max_length=100
        )
        modal.add_item(region_input)

        async def modal_callback(modal_interaction: discord.Interaction):
            try:
                new_region = region_input.value
                await channel.edit(rtc_region=new_region)
                await self.manager.update_temp_room(str(channel.id), region=new_region)
                
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Успешно",
                        description=f"Регион канала изменен на: {new_region}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )
            except Exception as e:
                await modal_interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description=str(e),
                        color="RED"
                    ),
                    ephemeral=True
                )

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def _delete_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Удалить канал"""
        await channel.delete()
        await self.manager.delete_temp_room(str(channel.id))
        await interaction.response.send_message(
            embed=Embed(
                title=f"{Emojis.SUCCESS} Успешно",
                description=f"Канал {channel.name} успешно удален",
                color="GREEN"
            ),
            ephemeral=True
        )

class VoiceChannelCog(commands.Cog):
    def __init__(self, bot, manager):
        self.bot = bot
        self.manager = manager
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
            # Получаем настройки из базы данных
            settings = await self.manager.db.fetch_all(
                "SELECT key, value FROM settings WHERE category = 'temp_rooms'"
            )
            
            settings_dict = {row['key']: row['value'] for row in settings}
            
            voice_channel_id = settings_dict.get('voice')
            message_channel_id = settings_dict.get('channel')
            message_id = settings_dict.get('message')
            
            if not all([voice_channel_id, message_channel_id, message_id]):
                print("❌ Не все настройки временных комнат найдены в базе данных")
                return
            
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
        """Обработчик изменения голосового состояния"""
        try:
            result = await self.manager.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'temp_rooms' AND key = 'voice'"
            )
            voice_channel_id = result['value'] if result else None
            
            if not voice_channel_id:
                return
            
            # Если пользователь зашел в канал создания
            if after.channel and str(after.channel.id) == str(voice_channel_id):
                await self.create_temp_channel(member)
                return
            
            # Если пользователь покинул канал
            if before.channel:
                # Проверяем, является ли канал временным
                room = await self.manager.get_temp_room(str(before.channel.id))
                if room:
                    # Если есть тред, удаляем пользователя из него
                    if 'thread_id' in room and room['thread_id']:
                        try:
                            thread = self.bot.get_channel(int(room['thread_id']))
                            if thread:
                                await thread.remove_user(member)
                        except Exception as e:
                            traceback.print_exc()

                    # Если канал пустой, удаляем его и связанный тред
                    if len(before.channel.members) == 0:
                        if 'thread_id' in room and room['thread_id']:
                            try:
                                thread = self.bot.get_channel(int(room['thread_id']))
                                if thread:
                                    await thread.delete()
                            except Exception as e:
                                traceback.print_exc()
                            
                        await before.channel.delete()
                        await self.manager.delete_temp_room(str(before.channel.id))
            
            # Если пользователь присоединился к каналу
            if after.channel:
                # Проверяем, является ли канал временным
                room = await self.manager.get_temp_room(str(after.channel.id))
                if room:
                    # Проверяем глобальный бан
                    if await self.manager.is_globally_banned(str(member.id), str(room['owner_id'])):
                        await member.move_to(None)
                        await member.send(
                            embed=Embed(
                                title=f"{Emojis.ERROR} Ошибка",
                                description="Вы находитесь в черном списке владельца канала!",
                                color="RED"
                            )
                        )
                        return

                    # Проверяем, не забанен ли пользователь в этом канале
                    if await self.manager.is_banned(str(after.channel.id), str(member.id)):
                        await member.move_to(None)
                        await member.send(
                            embed=Embed(
                                title=f"{Emojis.ERROR} Ошибка",
                                description="Вы забанены в этом канале!",
                                color="RED"
                            )
                        )
                        return
                        
                    # Проверяем, не заблокирован ли канал
                    if room.get('is_locked', False) and not await self.manager.is_trusted(str(after.channel.id), str(member.id)):
                        await member.move_to(None)
                        await member.send(
                            embed=Embed(
                                title=f"{Emojis.ERROR} Ошибка",
                                description="Этот канал заблокирован!",
                                color="RED"
                            )
                        )
                        return
                        
                    # Проверяем лимит пользователей
                    if room.get('user_limit', 0) > 0 and len(after.channel.members) > room['user_limit']:
                        await member.move_to(None)
                        await member.send(
                            embed=Embed(
                                title=f"{Emojis.ERROR} Ошибка",
                                description="В канале достигнут лимит пользователей!",
                                color="RED"
                            )
                        )
                        return

                    # Если есть тред, добавляем пользователя
                    if 'thread_id' in room and room['thread_id']:
                        try:
                            thread = self.bot.get_channel(int(room['thread_id']))
                            if thread:
                                await thread.add_user(member)
                        except Exception as e:
                            traceback.print_exc()
                            
        except Exception as e:
            traceback.print_exc()

    async def create_temp_channel(self, member: discord.Member) -> Optional[discord.VoiceChannel]:
        """Создает временный голосовой канал"""
        try:
            result = await self.manager.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'temp_rooms' AND key = 'category'"
            )
            category_id = result['value'] if result else None
            
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
            
            # Создаем новый канал
            new_channel = await member.guild.create_voice_channel(
                f"Канал {member.display_name}",
                category=category,
                overwrites=overwrites,
                bitrate=64000,
                user_limit=0
            )
            
            # Добавляем канал в базу данных
            await self.manager.add_channel(
                channel_id=str(new_channel.id),
                user_id=str(member.id),
                guild_id=str(member.guild.id),
                name=new_channel.name
            )
            
            # Перемещаем пользователя в новый канал
            await member.move_to(new_channel)
            return new_channel
                
        except Exception as e:
            traceback.print_exc()
            return None

async def setup(bot):
    """Регистрация компонентов"""
    manager = VoiceChannelManager(bot)
    await manager.db.init()
    await bot.add_cog(VoiceChannelCog(bot, manager)) 