import discord
from discord.ext import commands
from discord import ui
import asyncio
import yaml
import os
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class VoiceChannelManager:
    def __init__(self):
        self.voice_channels = {}
        self.load_channels()
        self.config = load_config()
    
    def load_channels(self):
        if os.path.exists('config/voice_channels.yaml'):
            with open('config/voice_channels.yaml', 'r', encoding='utf-8') as f:
                self.voice_channels = yaml.safe_load(f)
    
    def save_channels(self):
        with open('config/voice_channels.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.voice_channels, f)
    
    def add_channel(self, user_id: str, channel_id: int):
        self.voice_channels[str(user_id)] = channel_id
        self.save_channels()
    
    def remove_channel(self, user_id: str):
        if str(user_id) in self.voice_channels:
            del self.voice_channels[str(user_id)]
            self.save_channels()
    
    def get_channel(self, user_id: str) -> int:
        return self.voice_channels.get(str(user_id))

class VoiceChannelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Загружаем ID эмодзи из конфига
        self.config = load_config()
        
        # Если в конфиге нет эмодзи, используем стандартные
        self.emojis = {
            'crown': self.config.get('EMOJI_CROWN', '👑'),
            'users': self.config.get('EMOJI_USERS', '👥'),
            'numbers': self.config.get('EMOJI_NUMBERS', '🔢'),
            'lock': self.config.get('EMOJI_LOCK', '🔒'),
            'pencil': self.config.get('EMOJI_PENCIL', '✏️'),
            'eye': self.config.get('EMOJI_EYE', '👁'),
            'ban': self.config.get('EMOJI_BAN', '🚫'),
            'mute': self.config.get('EMOJI_MUTE', '🔇'),
            'music': self.config.get('EMOJI_MUSIC', '🎵')
        }
        
        # Конвертируем ID в объекты эмодзи если они указаны как ID
        for key, value in self.emojis.items():
            if isinstance(value, str) and value.isdigit():
                self.emojis[key] = f"<:custom_{key}:{value}>"

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceCrown", id="1332417411370057781"), style=discord.ButtonStyle.gray, row=0)
    async def transfer_ownership(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "transfer")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceUsers", id="1332418260435603476"), style=discord.ButtonStyle.gray, row=0)
    async def manage_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "access")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceNumbers", id="1332418493915725854"), style=discord.ButtonStyle.gray, row=0)
    async def change_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "limit")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceLock", id="1332418712304615495"), style=discord.ButtonStyle.gray, row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "lock")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoicePencil", id="1332418910242471967"), style=discord.ButtonStyle.gray, row=1)
    async def rename_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "rename")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceVisible", id="1332419077184163920"), style=discord.ButtonStyle.gray, row=1)
    async def toggle_visibility(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "visibility")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceKick", id="1332419383003447427"), style=discord.ButtonStyle.gray, row=1)
    async def kick_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "kick")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceMute", id="1332419509830553601"), style=discord.ButtonStyle.gray, row=1)
    async def toggle_mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "mute")

    @discord.ui.button(emoji=discord.PartialEmoji(name="VoiceBitrate", id="1332419630672904294"), style=discord.ButtonStyle.gray, row=2)
    async def change_bitrate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_voice_action(interaction, "bitrate")

    async def handle_voice_action(self, interaction: discord.Interaction, action: str):
        # Получаем менеджер из кога
        manager = interaction.client.get_cog("VoiceChannelCog").manager
        channel_id = manager.get_channel(str(interaction.user.id))
        
        if not channel_id:
            await interaction.response.send_message(
                "У вас нет активного голосового канала!",
                ephemeral=True
            )
            return
            
        voice_channel = interaction.guild.get_channel(channel_id)
        if not voice_channel:
            manager.remove_channel(str(interaction.user.id))
            await interaction.response.send_message(
                "Канал не найден!",
                ephemeral=True
            )
            return

        if action == "transfer":
            members = voice_channel.members
            if not members:
                await interaction.response.send_message("В канале нет участников для передачи прав", ephemeral=True)
                return
            
            options = [
                discord.SelectOption(label=member.name, value=str(member.id))
                for member in members if member.id != interaction.user.id
            ]
            
            if not options:
                await interaction.response.send_message("Нет доступных участников для передачи прав", ephemeral=True)
                return
            
            class OwnerSelect(ui.Select):
                def __init__(self):
                    super().__init__(
                        placeholder="Выберите нового владельца",
                        options=options
                    )
                
                async def callback(self, i: discord.Interaction):
                    new_owner_id = int(self.values[0])
                    new_owner = i.guild.get_member(new_owner_id)
                    
                    await voice_channel.set_permissions(new_owner,
                        manage_channels=True,
                        move_members=True,
                        view_channel=True,
                        connect=True,
                        speak=True
                    )
                    
                    await voice_channel.set_permissions(interaction.user,
                        manage_channels=False,
                        move_members=False,
                        view_channel=True,
                        connect=True,
                        speak=True
                    )
                    
                    manager.remove_channel(str(interaction.user.id))
                    manager.add_channel(str(new_owner_id), voice_channel.id)
                    
                    await i.response.send_message(
                        f"Права на канал переданы пользователю {new_owner.mention}",
                        ephemeral=True
                    )
            
            await interaction.response.send_message(
                "Выберите нового владельца канала:",
                view=discord.ui.View().add_item(OwnerSelect()),
                ephemeral=True
            )

        elif action == "access":
            class AccessView(ui.View):
                def __init__(self):
                    super().__init__(timeout=300)
                    
                    # Получаем список всех участников сервера
                    members = interaction.guild.members
                    
                    # Создаем список опций, исключая владельца канала и ботов
                    options = []
                    for member in members:
                        if member.id != interaction.user.id and not member.bot:
                            # Проверяем текущие права
                            perms = voice_channel.permissions_for(member)
                            explicit_perms = voice_channel.overwrites_for(member)
                            
                            # Определяем текущий статус доступа
                            has_access = explicit_perms.connect if explicit_perms.connect is not None else perms.connect
                            
                            options.append(
                                discord.SelectOption(
                                    label=member.name,
                                    value=str(member.id),
                                    description=f"{'✅ Есть доступ' if has_access else '❌ Нет доступа'}"
                                )
                            )
                    
                    # Разбиваем список на части по 25 опций (лимит Discord)
                    self.all_options = [options[i:i + 25] for i in range(0, len(options), 25)]
                    self.current_page = 0
                    
                    # Добавляем первый селект
                    if self.all_options:
                        self.add_item(self.create_select())
                    
                        # Добавляем кнопки навигации если есть больше одной страницы
                        if len(self.all_options) > 1:
                            self.add_item(ui.Button(label="⬅️", custom_id="prev", disabled=True))
                            self.add_item(ui.Button(label="➡️", custom_id="next"))
                    
                def create_select(self):
                    select = ui.Select(
                        placeholder="Выберите участника",
                        options=self.all_options[self.current_page]
                    )
                    
                    async def select_callback(interaction: discord.Interaction):
                        member_id = int(select.values[0])
                        member = interaction.guild.get_member(member_id)
                        
                        # Проверяем текущие права
                        explicit_perms = voice_channel.overwrites_for(member)
                        has_access = explicit_perms.connect if explicit_perms.connect is not None else False
                        
                        if has_access:
                            # Забираем доступ
                            await voice_channel.set_permissions(member, 
                                connect=False,
                                speak=False,
                                view_channel=True
                            )
                            # Если пользователь в канале - выкидываем его
                            if member in voice_channel.members:
                                await member.move_to(None)
                            await interaction.response.send_message(
                                f"Доступ для {member.mention} ограничен",
                                ephemeral=True
                            )
                        else:
                            # Выдаем доступ
                            await voice_channel.set_permissions(member,
                                connect=True,
                                speak=True,
                                view_channel=True
                            )
                            await interaction.response.send_message(
                                f"Доступ для {member.mention} выдан",
                                ephemeral=True
                            )
                    
                    select.callback = select_callback
                    return select
                
                @ui.button(label="⬅️", custom_id="prev")
                async def prev_page(self, interaction: discord.Interaction, button: ui.Button):
                    self.current_page = max(0, self.current_page - 1)
                    await self.update_view(interaction)
                
                @ui.button(label="➡️", custom_id="next")
                async def next_page(self, interaction: discord.Interaction, button: ui.Button):
                    self.current_page = min(len(self.all_options) - 1, self.current_page + 1)
                    await self.update_view(interaction)
                
                async def update_view(self, interaction: discord.Interaction):
                    # Обновляем селект
                    self.clear_items()
                    self.add_item(self.create_select())
                    
                    # Обновляем кнопки навигации
                    if len(self.all_options) > 1:
                        self.add_item(ui.Button(
                            label="⬅️",
                            custom_id="prev",
                            disabled=self.current_page == 0
                        ))
                        self.add_item(ui.Button(
                            label="➡️",
                            custom_id="next",
                            disabled=self.current_page == len(self.all_options) - 1
                        ))
                    
                    await interaction.response.edit_message(view=self)
            
            await interaction.response.send_message(
                "Выберите участника для управления доступом:",
                view=AccessView(),
                ephemeral=True
            )

        elif action == "limit":
            class LimitModal(ui.Modal, title="Изменение лимита"):
                def __init__(self):
                    super().__init__()
                
                limit = ui.TextInput(
                    label="Новый лимит",
                    placeholder="Введите число (0 - без лимита)",
                    required=True
                )
                
                async def on_submit(self, i: discord.Interaction):
                    try:
                        new_limit = int(self.limit.value)
                        await voice_channel.edit(user_limit=new_limit)
                        await i.response.send_message(
                            f"Установлен лимит: {new_limit if new_limit > 0 else 'без лимита'}",
                            ephemeral=True
                        )
                    except ValueError:
                        await i.response.send_message("Введите корректное число", ephemeral=True)
            
            await interaction.response.send_modal(LimitModal())

        elif action == "lock":
            is_locked = voice_channel.permissions_for(interaction.guild.default_role).connect
            if is_locked:
                await voice_channel.set_permissions(interaction.guild.default_role, connect=False)
                await interaction.response.send_message("Канал закрыт", ephemeral=True)
            else:
                await voice_channel.set_permissions(interaction.guild.default_role, connect=True)
                await interaction.response.send_message("Канал открыт", ephemeral=True)

        elif action == "rename":
            class RenameModal(ui.Modal, title="Изменение названия"):
                def __init__(self):
                    super().__init__()
                
                name = ui.TextInput(
                    label="Новое название",
                    placeholder="Введите новое название канала",
                    required=True
                )
                
                async def on_submit(self, i: discord.Interaction):
                    await voice_channel.edit(name=self.name.value)
                    await i.response.send_message(f"Название канала изменено на: {self.name.value}", ephemeral=True)
            
            await interaction.response.send_modal(RenameModal())

        elif action == "visibility":
            is_visible = voice_channel.permissions_for(interaction.guild.default_role).view_channel
            if is_visible:
                await voice_channel.set_permissions(interaction.guild.default_role, view_channel=False)
                await interaction.response.send_message("Канал скрыт", ephemeral=True)
            else:
                await voice_channel.set_permissions(interaction.guild.default_role, view_channel=True)
                await interaction.response.send_message("Канал виден всем", ephemeral=True)

        elif action == "kick":
            members = voice_channel.members
            if not members:
                await interaction.response.send_message("В канале нет участников", ephemeral=True)
                return
            
            options = [
                discord.SelectOption(label=member.name, value=str(member.id))
                for member in members if member.id != interaction.user.id
            ]
            
            class KickSelect(ui.Select):
                def __init__(self):
                    super().__init__(
                        placeholder="Выберите участника для кика",
                        options=options
                    )
                
                async def callback(self, i: discord.Interaction):
                    member_id = int(self.values[0])
                    member = i.guild.get_member(member_id)
                    if member in voice_channel.members:
                        await member.move_to(None)
                        await i.response.send_message(f"Участник {member.mention} выгнан из канала", ephemeral=True)
                    else:
                        await i.response.send_message("Участник уже не находится в канале", ephemeral=True)
            
            await interaction.response.send_message(
                "Выберите участника для кика:",
                view=discord.ui.View().add_item(KickSelect()),
                ephemeral=True
            )

        elif action == "mute":
            members = voice_channel.members
            if not members:
                await interaction.response.send_message("В канале нет участников", ephemeral=True)
                return
            
            options = [
                discord.SelectOption(label=member.name, value=str(member.id))
                for member in members if member.id != interaction.user.id
            ]
            
            class MuteSelect(ui.Select):
                def __init__(self):
                    super().__init__(
                        placeholder="Выберите участника",
                        options=options
                    )
                
                async def callback(self, i: discord.Interaction):
                    member_id = int(self.values[0])
                    member = i.guild.get_member(member_id)
                    
                    if member in voice_channel.members:
                        current_mute = member.voice.mute
                        await member.edit(mute=not current_mute)
                        status = "замучен" if not current_mute else "размучен"
                        await i.response.send_message(f"Участник {member.mention} {status}", ephemeral=True)
                    else:
                        await i.response.send_message("Участник уже не находится в канале", ephemeral=True)
            
            await interaction.response.send_message(
                "Выберите участника:",
                view=discord.ui.View().add_item(MuteSelect()),
                ephemeral=True
            )

        elif action == "bitrate":
            class BitrateModal(ui.Modal, title="Изменение битрейта"):
                def __init__(self):
                    super().__init__()
                
                bitrate = ui.TextInput(
                    label="Новый битрейт",
                    placeholder="Введите значение от 8 до 96 (кбит/с)",
                    required=True,
                    default=str(voice_channel.bitrate // 1000)
                )
                
                async def on_submit(self, i: discord.Interaction):
                    try:
                        new_bitrate = int(self.bitrate.value)
                        if 8 <= new_bitrate <= 96:
                            await voice_channel.edit(bitrate=new_bitrate * 1000)
                            await i.response.send_message(
                                f"Битрейт канала изменен на: {new_bitrate} кбит/с",
                                ephemeral=True
                            )
                        else:
                            await i.response.send_message(
                                "Ошибка: битрейт должен быть от 8 до 96 кбит/с",
                                ephemeral=True
                            )
                    except ValueError:
                        await i.response.send_message(
                            "Ошибка: введите корректное число",
                            ephemeral=True
                        )
            
            await interaction.response.send_modal(BitrateModal())

class VoiceChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = VoiceChannelManager()
        self.config = load_config()
        bot.loop.create_task(self.setup_voice_channel())
    
    async def setup_voice_channel(self):
        await self.bot.wait_until_ready()
        
        # Получаем ID каналов из конфига
        channel_id = self.config.get('voice', {}).get('chat_channel')
        message_id = self.config.get('voice', {}).get('message_channel')
        
        if not channel_id or not message_id:
            print("❌ Не настроены ID каналов для голосовых комнат")
            return
            
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            print(f"❌ Канал с ID {channel_id} не найден")
            return
            
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            message = await channel.send("Создание панели управления...")
            print(f"✅ Создано новое сообщение для панели управления: {message.id}")
        
        # Создаем эмбед
        embed = create_embed(
            title="⚙️ Приватные комнаты",
            description=(
                "Измените конфигурацию вашей комнаты с помощью панели управления.\n\n"
                f"{EMOJIS['VoiceCrown']} — назначить нового создателя комнаты\n"
                f"{EMOJIS['VoiceUsers']} — ограничить/выдать доступ к комнате\n"
                f"{EMOJIS['VoiceNumbers']} — задать новый лимит участников\n"
                f"{EMOJIS['VoiceLock']} — закрыть/открыть комнату\n"
                f"{EMOJIS['VoiceEdit']} — изменить название комнаты\n"
                f"{EMOJIS['VoiceVisible']} — скрыть/открыть комнату\n"
                f"{EMOJIS['VoiceKick']} — выгнать участника из комнаты\n"
                f"{EMOJIS['VoiceMute']} — ограничить/выдать право говорить\n"
                f"{EMOJIS['VoiceBitrate']} — изменить битрейт канала"
            )
        )
        
        await message.edit(content=None, embed=embed, view=VoiceChannelView())
        print("✅ Панель управления голосовыми комнатами обновлена")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Получаем ID канала создания из конфига
        voice_channel_id = self.config.get('voice', {}).get('main_channel')
        
        if not voice_channel_id:
            return
            
        # Если пользователь зашел в канал создания
        if after.channel and str(after.channel.id) == str(voice_channel_id):
            try:
                # Создаем новый канал
                new_channel = await after.channel.guild.create_voice_channel(
                    name=f"🎮 Канал {member.name}",
                    category=after.channel.category,
                    bitrate=64000  # Устанавливаем стандартный битрейт
                )
                
                # Выдаем права создателю
                await new_channel.set_permissions(member,
                    manage_channels=True,
                    move_members=True,
                    view_channel=True,
                    connect=True,
                    speak=True
                )
                
                # Устанавливаем права по умолчанию
                await new_channel.set_permissions(member.guild.default_role,
                    connect=True,
                    view_channel=True
                )
                
                # Перемещаем пользователя
                await member.move_to(new_channel)
                
                # Сохраняем информацию о канале
                self.manager.add_channel(str(member.id), new_channel.id)
                print(f"✅ Создан новый голосовой канал для {member.name} (ID: {new_channel.id})")
                
            except Exception as e:
                print(f"❌ Ошибка при создании канала: {e}")
        
        # Проверяем, не покинул ли кто-то канал
        if before.channel:
            # Проверяем все приватные каналы
            for user_id, channel_id in list(self.manager.voice_channels.items()):
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Если это тот канал, который покинули
                    if channel.id == before.channel.id:
                        # Если в канале никого не осталось
                        if len(channel.members) == 0:
                            try:
                                await channel.delete()
                                self.manager.remove_channel(user_id)
                                print(f"✅ Удален пустой голосовой канал (ID: {channel_id})")
                            except Exception as e:
                                print(f"❌ Ошибка при удалении канала: {e}")
                            break

async def setup(bot):
    await bot.add_cog(VoiceChannelCog(bot)) 