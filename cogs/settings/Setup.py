import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, EMOJIS
import yaml

class Setup(commands.GroupCog, name="setup"):
    def __init__(self, bot):
        self.bot = bot
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def is_owner():
        async def predicate(interaction: discord.Interaction):
            return await interaction.client.is_owner(interaction.user)
        return app_commands.check(predicate)

    async def update_role_id(self, role_id: str, role: discord.Role):
        """Обновляет ID роли в конфиге"""
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Ищем роль в конфиге и обновляем её ID
        for category in config['roles']:
            for role_name, role_data in config['roles'][category].items():
                if role_name == role_id:  # Ищем по имени роли
                    role_data['id'] = str(role.id)
                    break
        
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

    @app_commands.command(name="moderation", description="Настроить роли модерации")
    @is_owner()
    async def setup_moderation(self, interaction: discord.Interaction):
        """Настраивает роли модерации на сервере"""
        await interaction.response.defer()
        
        try:
            progress_msg = await interaction.followup.send(
                embed=create_embed(description="🔄 Настройка ролей модерации...")
            )
            
            roles_created = []
            roles_updated = []
            
            # Обрабатываем роли стаффа
            for role_id, role_data in self.config['roles']['staff'].items():
                # Проверяем существует ли роль с таким ID
                existing_role = None
                if role_data['id']:
                    existing_role = interaction.guild.get_role(int(role_data['id']))

                if existing_role:
                    # Обновляем права существующей роли
                    await existing_role.edit(
                        permissions=discord.Permissions(role_data['permissions']),
                        reason='Обновление прав роли'
                    )
                    roles_updated.append(existing_role)
                else:
                    # Создаем новую роль
                    role = await interaction.guild.create_role(
                        name=role_id.upper() if role_id == 'ae' else role_id.replace('_', ' ').title(),
                        permissions=discord.Permissions(role_data['permissions']),
                        reason='Автоматическая настройка сервера'
                    )
                    roles_created.append(role)
                    await self.update_role_id(role_id, role)

            # Обрабатываем специальные роли
            for role_id, role_data in self.config['roles'].get('special', {}).items():
                if role_id in self.config['roles']['special']:  # Проверяем существует ли роль в конфиге
                    existing_role = None
                    if role_data['id']:
                        existing_role = interaction.guild.get_role(int(role_data['id']))

                    if existing_role:
                        await existing_role.edit(
                            permissions=discord.Permissions(role_data['permissions']),
                            reason='Обновление прав роли'
                        )
                        roles_updated.append(existing_role)
                    else:
                        role = await interaction.guild.create_role(
                            name=role_id.replace('_', ' ').title(),
                            permissions=discord.Permissions(role_data['permissions']),
                            reason='Автоматическая настройка сервера'
                        )
                        roles_created.append(role)
                        await self.update_role_id(role_id, role)

            # Создаем/обновляем роль для ботов
            bot_role_data = self.config['roles'].get('bots', {})
            if bot_role_data:
                existing_bot_role = None
                if bot_role_data.get('id'):
                    existing_bot_role = interaction.guild.get_role(int(bot_role_data['id']))

                if existing_bot_role:
                    await existing_bot_role.edit(
                        permissions=discord.Permissions(bot_role_data['permissions']),
                        hoist=bot_role_data.get('hoisted', True),
                        reason='Обновление роли ботов'
                    )
                    roles_updated.append(existing_bot_role)
                else:
                    bot_role = await interaction.guild.create_role(
                        name='Bots',
                        permissions=discord.Permissions(bot_role_data['permissions']),
                        hoist=bot_role_data.get('hoisted', True),
                        reason='Автоматическая настройка сервера'
                    )
                    roles_created.append(bot_role)
                    await self.update_role_id('bots', bot_role)

                # Назначаем роль всем ботам на сервере
                for member in interaction.guild.members:
                    if member.bot:
                        role_to_assign = existing_bot_role if existing_bot_role else bot_role
                        try:
                            await member.add_roles(role_to_assign, reason='Автоматическая настройка ролей')
                        except discord.HTTPException:
                            continue

            # Настраиваем права мута во всех каналах
            muted_role = discord.utils.get(interaction.guild.roles, name='Muted')
            if muted_role:
                for channel in interaction.guild.channels:
                    try:
                        overwrites = channel.overwrites_for(muted_role)
                        overwrites.send_messages = False
                        overwrites.add_reactions = False
                        overwrites.speak = False
                        overwrites.create_instant_invite = False
                        overwrites.create_private_threads = False
                        overwrites.create_public_threads = False
                        overwrites.send_messages_in_threads = False
                        await channel.set_permissions(muted_role, overwrite=overwrites)
                    except discord.HTTPException:
                        continue

            # Формируем отчет
            description = "✅ Настройка завершена!\n\n"
            
            if roles_created:
                description += "**Созданные роли:**\n"
                for role in roles_created:
                    description += f"{EMOJIS['DOT']} {role.mention}\n"
            
            if roles_updated:
                description += "\n**Обновленные роли:**\n"
                for role in roles_updated:
                    description += f"{EMOJIS['DOT']} {role.mention}\n"
            
            await progress_msg.edit(embed=create_embed(
                title="⚙️ Настройка сервера",
                description=description
            ))

        except Exception as e:
            print(f"Error in setup_moderation: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при настройке сервера!"
                )
            )

    @app_commands.command(name="verification", description="Настроить систему верификации")
    @is_owner()
    async def setup_verification(self, interaction: discord.Interaction):
        """Настраивает систему верификации на сервере"""
        await interaction.response.defer()
        
        try:
            # Создаем канал верификации
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=False,
                    add_reactions=False
                )
            }
            
            channel = await interaction.guild.create_text_channel(
                'verification',
                overwrites=overwrites,
                reason="Автоматическая настройка верификации"
            )
            
            # Создаем роль верифицированного участника
            verified_role = await self.create_role(
                interaction.guild,
                {
                    'name': 'Verified',
                    'color': 0x2F3136,
                    'permissions': 104324673,
                    'position': 1,
                    'mentionable': False,
                    'hoist': False
                }
            )
            
            # Настраиваем права в каналах
            for ch in interaction.guild.channels:
                if ch != channel:
                    try:
                        overwrites = ch.overwrites_for(interaction.guild.default_role)
                        overwrites.read_messages = False
                        await ch.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                        
                        overwrites = ch.overwrites_for(verified_role)
                        overwrites.read_messages = True
                        await ch.set_permissions(verified_role, overwrite=overwrites)
                    except discord.HTTPException:
                        continue

            # Отправляем сообщение верификации
            embed = create_embed(
                title="✅ Верификация",
                description="Добро пожаловать на сервер!\nНажмите на кнопку ниже, чтобы получить доступ."
            )
            
            verify_button = discord.ui.Button(
                style=discord.ButtonStyle.green,
                label="Верификация",
                custom_id="verify_button"
            )
            
            view = discord.ui.View()
            view.add_item(verify_button)
            
            await channel.send(embed=embed, view=view)
            
            await interaction.followup.send(
                embed=create_embed(
                    title="⚙️ Настройка верификации",
                    description=f"✅ Настройка завершена!\n\n"
                              f"{EMOJIS['DOT']} Канал верификации: {channel.mention}\n"
                              f"{EMOJIS['DOT']} Роль верификации: {verified_role.mention}"
                )
            )

        except Exception as e:
            print(f"Error in setup_verification: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при настройке верификации!"
                )
            )

    @app_commands.command(name="channels", description="Настроить основные каналы")
    @is_owner()
    async def setup_channels(self, interaction: discord.Interaction):
        """Настраивает основные каналы сервера"""
        await interaction.response.defer()
        
        try:
            channels_created = []
            
            # Создаем категории
            info_category = await interaction.guild.create_category("📌 ИНФОРМАЦИЯ")
            community_category = await interaction.guild.create_category("🌟 ОБЩЕНИЕ")
            voice_category = await interaction.guild.create_category("🎤 ГОЛОСОВЫЕ КАНАЛЫ")
            
            # Информационные каналы
            channels_created.append(await interaction.guild.create_text_channel(
                'rules',
                category=info_category,
                topic="Правила сервера"
            ))
            
            channels_created.append(await interaction.guild.create_text_channel(
                'announcements',
                category=info_category,
                topic="Важные объявления"
            ))
            
            channels_created.append(await interaction.guild.create_text_channel(
                'roles',
                category=info_category,
                topic="Получение ролей"
            ))
            
            # Каналы общения
            channels_created.append(await interaction.guild.create_text_channel(
                'general',
                category=community_category,
                topic="Основной чат"
            ))
            
            channels_created.append(await interaction.guild.create_text_channel(
                'media',
                category=community_category,
                topic="Обмен медиафайлами"
            ))
            
            channels_created.append(await interaction.guild.create_text_channel(
                'bot-commands',
                category=community_category,
                topic="Команды бота"
            ))
            
            # Голосовые каналы
            channels_created.append(await interaction.guild.create_voice_channel(
                'Основной',
                category=voice_category,
                user_limit=0
            ))
            
            channels_created.append(await interaction.guild.create_voice_channel(
                'Музыка',
                category=voice_category,
                user_limit=0
            ))
            
            description = "✅ Каналы успешно созданы!\n\n**Созданные каналы:**\n"
            for channel in channels_created:
                description += f"{EMOJIS['DOT']} {channel.mention}\n"
            
            await interaction.followup.send(
                embed=create_embed(
                    title="⚙️ Настройка каналов",
                    description=description
                )
            )

        except Exception as e:
            print(f"Error in setup_channels: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при настройке каналов!"
                )
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Автоматически настраивает права для Muted роли в новых каналах"""
        # Проверяем, не является ли канал временным или специальным
        if hasattr(channel, 'guild') and not getattr(channel, 'is_temporary', False):
            muted_role = discord.utils.get(channel.guild.roles, name='Muted')
            if muted_role:
                try:
                    overwrites = discord.PermissionOverwrite(
                        send_messages=False,
                        add_reactions=False,
                        speak=False,
                        create_instant_invite=False,
                        create_private_threads=False,
                        create_public_threads=False,
                        send_messages_in_threads=False
                    )
                    await channel.set_permissions(muted_role, overwrite=overwrites)
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Проверяет и обновляет права Muted роли при изменении канала"""
        # Игнорируем изменения NSFW статуса
        if before.permissions_synced == after.permissions_synced and before.overwrites == after.overwrites:
            return
            
        muted_role = discord.utils.get(after.guild.roles, name='Muted')
        if muted_role:
            try:
                # Проверяем, есть ли уже права для мута
                current_overwrites = after.overwrites_for(muted_role)
                if not current_overwrites or not current_overwrites.is_empty():
                    overwrites = discord.PermissionOverwrite(
                        send_messages=False,
                        add_reactions=False,
                        speak=False,
                        create_instant_invite=False,
                        create_private_threads=False,
                        create_public_threads=False,
                        send_messages_in_threads=False
                    )
                    await after.set_permissions(muted_role, overwrite=overwrites)
            except discord.HTTPException:
                pass

    async def update_muted_permissions(self, guild):
        """Обновляет права Muted роли во всех каналах"""
        muted_role = discord.utils.get(guild.roles, name='Muted')
        if muted_role:
            for channel in guild.channels:
                try:
                    overwrites = discord.PermissionOverwrite(
                        send_messages=False,
                        add_reactions=False,
                        speak=False,
                        create_instant_invite=False,
                        create_private_threads=False,
                        create_public_threads=False,
                        send_messages_in_threads=False
                    )
                    await channel.set_permissions(muted_role, overwrite=overwrites)
                except discord.HTTPException:
                    continue

async def setup(bot):
    await bot.add_cog(Setup(bot)) 