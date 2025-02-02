import discord
from discord import app_commands
from discord.ext import commands
import yaml
import os
from datetime import datetime
import typing
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

def format_permission(perm_name: str) -> str:
    """Форматирует название права для красивого отображения"""
    return perm_name.replace('_', ' ').title()

def get_permission_details(permissions: discord.Permissions) -> typing.Dict[str, bool]:
    """Получает детальную информацию о правах"""
    all_perms = {}
    for perm, value in permissions:
        all_perms[format_permission(perm)] = value
    return all_perms

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    backup_group = app_commands.Group(name="backup", description="Команды для управления резервными копиями")
    
    @backup_group.command(name="info", description="Показать информацию о сервере")
    @app_commands.default_permissions(administrator=True)
    async def backup_info(self, interaction: discord.Interaction):
        """Показывает детальную информацию о сервере"""
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Эту команду может использовать только владелец сервера!")
            return
            
        await interaction.response.defer()
        
        # Создаем эмбед с основной информацией
        embed=Embed(
            title=f"📊 Информация о сервере {interaction.guild.name}",
            fields=[
                {
                    "name": "🔧 Основное",
                    "value": f"ID: {interaction.guild.id}\n"
                            f"Владелец: {interaction.guild.owner.mention} (ID: {interaction.guild.owner.id})\n"
                            f"Создан: {discord.utils.format_dt(interaction.guild.created_at, 'D')}\n"
                            f"Уровень проверки: {interaction.guild.verification_level}\n"
                            f"Буст уровень: {interaction.guild.premium_tier}",
                    "inline": False
                },
                {
                    "name": "📈 Статистика",
                    "value": f"Участников: {interaction.guild.member_count}\n"
                            f"Ролей: {len(interaction.guild.roles)}\n"
                            f"Каналов: {len(interaction.guild.channels)} (ID системного канала: {interaction.guild.system_channel.id if interaction.guild.system_channel else 'Нет'})\n"
                            f"Эмодзи: {len(interaction.guild.emojis)}\n"
                            f"Стикеров: {len(interaction.guild.stickers)}",
                    "inline": False
                }
            ],
            color="BLUE"
        )
        
        await interaction.followup.send(embed=embed)
        
        # Отправляем информацию о каналах
        channels_embed = Embed(
            title="📚 Информация о каналах",
            fields=[],
            color="BLUE"
        )
        
        for category in interaction.guild.categories:
            channel_list = [f"• {channel.name} (ID: {channel.id})" for channel in category.channels]
            channels_embed.fields.append({
                "name": f"📁 {category.name} (ID: {category.id})",
                "value": "\n".join(channel_list) if channel_list else "Пусто",
                "inline": False
            })
            
        # Каналы без категории
        no_category_channels = [c for c in interaction.guild.channels if not c.category]
        if no_category_channels:
            channel_list = [f"• {channel.name} (ID: {channel.id})" for channel in no_category_channels]
            channels_embed.fields.append({
                "name": "🗂️ Без категории",
                "value": "\n".join(channel_list),
                "inline": False
            })
            
        await interaction.followup.send(embed=channels_embed)
        
        # Отправляем информацию о ролях
        roles_info = []
        for role in reversed(interaction.guild.roles[1:]):  # Пропускаем @everyone
            perms = get_permission_details(role.permissions)
            enabled_perms = [k for k, v in perms.items() if v]
            
            fields = [
                {
                    "name": "🔧 Основное",
                    "value": f"ID: {role.id}\n"
                            f"Цвет: {str(role.color)}\n"
                            f"Позиция: {role.position}\n"
                            f"Отображается отдельно: {role.hoist}\n"
                            f"Упоминаемая: {role.mentionable}\n"
                            f"Управляемая: {role.managed}",
                    "inline": False
                }
            ]
            
            # Разделяем права на группы для лучшей читаемости
            general_perms = []
            text_perms = []
            voice_perms = []
            admin_perms = []
            
            for perm in enabled_perms:
                if perm in ["Administrator", "Manage Server", "Manage Roles", "Manage Channels"]:
                    admin_perms.append(perm)
                elif perm in ["Send Messages", "Read Messages", "Manage Messages", "Embed Links", "Attach Files"]:
                    text_perms.append(perm)
                elif perm in ["Connect", "Speak", "Mute Members", "Deafen Members", "Move Members"]:
                    voice_perms.append(perm)
                else:
                    general_perms.append(perm)
            
            if admin_perms:
                fields.append({"name": "⚡ Админ права", "value": "\n".join(admin_perms), "inline": False})
            if text_perms:
                fields.append({"name": "💬 Текстовые права", "value": "\n".join(text_perms), "inline": False})
            if voice_perms:
                fields.append({"name": "🔊 Голосовые права", "value": "\n".join(voice_perms), "inline": False})
            if general_perms:
                fields.append({"name": "🔧 Общие права", "value": "\n".join(general_perms), "inline": False})
                
            # Добавляем информацию о пользователях с этой ролью
            members_with_role = [f"{member.name}#{member.discriminator} (ID: {member.id})" for member in role.members[:10]]
            if members_with_role:
                members_text = "\n".join(members_with_role)
                if len(role.members) > 10:
                    members_text += f"\n... и еще {len(role.members) - 10} пользователей"
                fields.append({"name": "👥 Пользователи с ролью", "value": members_text, "inline": False})
            
            role_embed=Embed(
                title=f"👑 Роль: {role.name}",
                fields=fields,
                color=str(role.color)
            )
                
            roles_info.append(role_embed)
            
        # Отправляем эмбеды с информацией о ролях
        for embed in roles_info:
            await interaction.followup.send(embed=embed)
        
    @backup_group.command(name="create", description="Создать резервную копию сервера")
    @app_commands.default_permissions(administrator=True)
    async def backup_create(self, interaction: discord.Interaction):
        # Проверяем, является ли пользователь владельцем сервера
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Эту команду может использовать только владелец сервера!")
            return
            
        await interaction.response.defer()
        
        backup_data = {
            # Основная информация о сервере
            "server_name": interaction.guild.name,
            "server_icon": str(interaction.guild.icon.url) if interaction.guild.icon else None,
            "server_banner": str(interaction.guild.banner.url) if interaction.guild.banner else None,
            "server_splash": str(interaction.guild.splash.url) if interaction.guild.splash else None,
            "server_description": interaction.guild.description,
            "server_region": str(interaction.guild.region) if hasattr(interaction.guild, 'region') else None,
            "server_verification_level": str(interaction.guild.verification_level),
            "server_explicit_content_filter": str(interaction.guild.explicit_content_filter),
            "server_default_notifications": str(interaction.guild.default_notifications),
            "server_features": list(interaction.guild.features),
            "server_premium_tier": interaction.guild.premium_tier,
            "server_preferred_locale": str(interaction.guild.preferred_locale),
            "server_system_channel_flags": interaction.guild.system_channel_flags.value if interaction.guild.system_channel_flags else None,
            "server_mfa_level": str(interaction.guild.mfa_level),
            "server_max_members": interaction.guild.max_members,
            "server_max_presences": interaction.guild.max_presences,
            "server_filesize_limit": interaction.guild.filesize_limit,
            "server_bitrate_limit": interaction.guild.bitrate_limit,
            "server_emoji_limit": interaction.guild.emoji_limit,
            "server_sticker_limit": interaction.guild.sticker_limit,
            
            # Специальные каналы
            "system_channel_id": interaction.guild.system_channel.id if interaction.guild.system_channel else None,
            "rules_channel_id": interaction.guild.rules_channel.id if interaction.guild.rules_channel else None,
            "public_updates_channel_id": interaction.guild.public_updates_channel.id if interaction.guild.public_updates_channel else None,
            "afk_channel_id": interaction.guild.afk_channel.id if interaction.guild.afk_channel else None,
            "afk_timeout": interaction.guild.afk_timeout,
            
            # Эмодзи и стикеры
            "emojis": [{
                "name": emoji.name,
                "url": str(emoji.url),
                "animated": emoji.animated,
                "available": emoji.available,
                "managed": emoji.managed,
                "require_colons": emoji.require_colons,
                "roles": [role.id for role in emoji.roles] if emoji.roles else None
            } for emoji in interaction.guild.emojis],
            
            "stickers": [{
                "name": sticker.name,
                "description": sticker.description,
                "url": str(sticker.url) if hasattr(sticker, 'url') else None,
                "format": str(sticker.format),
                "available": sticker.available,
                "tags": sticker.tags if hasattr(sticker, 'tags') else None
            } for sticker in interaction.guild.stickers],
            
            # Роли, категории и каналы
            "roles": [],
            "categories": [],
            "channels_without_category": [],
            
            # Метаданные бэкапа
            "backup_version": "2.1",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backup_creator_id": interaction.user.id,
            "guild_id": interaction.guild.id,
            "member_count": interaction.guild.member_count,
            "premium_subscription_count": interaction.guild.premium_subscription_count
        }
        
        # Сохраняем роли с расширенной информацией
        for role in interaction.guild.roles:
            if role.name != "@everyone":
                role_data = {
                    "name": role.name,
                    "permissions": role.permissions.value,
                    "permissions_detailed": get_permission_details(role.permissions),
                    "color": role.color.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position,
                    "managed": role.managed,
                    "tags": str(role.tags) if role.tags else None,
                    "icon": str(role.icon.url) if role.icon else None,
                    "unicode_emoji": role.unicode_emoji,
                    "members_count": len(role.members),
                    "is_bot_managed": role.is_bot_managed(),
                    "is_premium_subscriber": role.is_premium_subscriber(),
                    "is_integration": role.is_integration(),
                }
                backup_data["roles"].append(role_data)
        
        # Сохраняем @everyone роль отдельно
        everyone_role = interaction.guild.default_role
        backup_data["everyone_role"] = {
            "permissions": everyone_role.permissions.value,
            "permissions_detailed": get_permission_details(everyone_role.permissions),
            "mentionable": everyone_role.mentionable,
            "color": everyone_role.color.value
        }
        
        # Сохраняем каналы без категории
        for channel in interaction.guild.channels:
            if not channel.category:
                channel_data = await self._create_channel_data(channel)
                backup_data["channels_without_category"].append(channel_data)
        
        # Сохраняем категории и их каналы
        for category in interaction.guild.categories:
            category_data = {
                "name": category.name,
                "position": category.position,
                "nsfw": category.nsfw if hasattr(category, 'nsfw') else False,
                "overwrites": await self._create_overwrites_data(category),
                "channels": []
            }
            
            for channel in category.channels:
                channel_data = await self._create_channel_data(channel)
                category_data["channels"].append(channel_data)
            
            backup_data["categories"].append(category_data)
        
        # Создаем папку для бэкапов если её нет
        if not os.path.exists('backups'):
            os.makedirs('backups')
            
        # Сохраняем бэкап в файл
        backup_filename = f'backups/backup_{interaction.guild.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            yaml.dump(backup_data, f, allow_unicode=True, sort_keys=False)
        
        # Создаем эмбед с информацией о бэкапе
        embed=Embed(
            title="✅ Резервная копия создана",
            description=f"Файл: `{backup_filename}`",
            fields=[
                {
                    "name": "📊 Статистика бэкапа",
                    "value": f"Роли: {len(backup_data['roles'])}\n"
                            f"Категории: {len(backup_data['categories'])}\n"
                            f"Каналы без категории: {len(backup_data['channels_without_category'])}\n"
                            f"Эмодзи: {len(backup_data['emojis'])}\n"
                            f"Стикеры: {len(backup_data['stickers'])}",
                    "inline": False
                }
            ],
            color="GREEN"
        )
        
        await interaction.followup.send(embed=embed)

    async def _create_channel_data(self, channel):
        """Создает данные о канале в зависимости от его типа"""
        base_data = {
            "name": channel.name,
            "type": str(channel.type),
            "position": channel.position,
            "overwrites": await self._create_overwrites_data(channel),
            "created_at": channel.created_at.isoformat() if hasattr(channel, 'created_at') else None,
            "permissions_synced": channel.permissions_synced if hasattr(channel, 'permissions_synced') else None
        }
        
        if isinstance(channel, discord.TextChannel):
            base_data.update({
                "topic": channel.topic,
                "nsfw": channel.nsfw,
                "slowmode_delay": channel.slowmode_delay,
                "news": channel.is_news(),
                "default_auto_archive_duration": channel.default_auto_archive_duration,
                "default_thread_slowmode_delay": channel.default_thread_slowmode_delay if hasattr(channel, 'default_thread_slowmode_delay') else None,
                "last_message_id": str(channel.last_message_id) if channel.last_message_id else None,
                "webhooks": [{
                    "name": webhook.name,
                    "avatar": str(webhook.avatar.url) if webhook.avatar else None,
                    "channel_id": str(webhook.channel_id),
                    "created_at": webhook.created_at.isoformat() if hasattr(webhook, 'created_at') else None
                } for webhook in await channel.webhooks()],
                "threads": [{
                    "name": thread.name,
                    "archived": thread.archived,
                    "auto_archive_duration": thread.auto_archive_duration,
                    "slowmode_delay": thread.slowmode_delay,
                    "message_count": thread.message_count if hasattr(thread, 'message_count') else None,
                    "member_count": thread.member_count if hasattr(thread, 'member_count') else None,
                    "created_at": thread.created_at.isoformat() if hasattr(thread, 'created_at') else None
                } for thread in channel.threads]
            })
            
        elif isinstance(channel, discord.VoiceChannel):
            base_data.update({
                "bitrate": channel.bitrate,
                "user_limit": channel.user_limit,
                "rtc_region": str(channel.rtc_region) if channel.rtc_region else None,
                "video_quality_mode": str(channel.video_quality_mode) if hasattr(channel, 'video_quality_mode') else None,
                "members": [member.id for member in channel.members]
            })
            
        elif isinstance(channel, discord.StageChannel):
            base_data.update({
                "topic": channel.topic if hasattr(channel, 'topic') else None,
                "bitrate": channel.bitrate,
                "user_limit": channel.user_limit,
                "rtc_region": str(channel.rtc_region) if channel.rtc_region else None,
                "requesting_to_speak": [member.id for member in channel.requesting_to_speak] if hasattr(channel, 'requesting_to_speak') else []
            })
            
        elif isinstance(channel, discord.ForumChannel):
            base_data.update({
                "topic": channel.topic if hasattr(channel, 'topic') else None,
                "slowmode_delay": channel.slowmode_delay if hasattr(channel, 'slowmode_delay') else None,
                "nsfw": channel.nsfw if hasattr(channel, 'nsfw') else False,
                "available_tags": [{
                    "name": tag.name,
                    "moderated": tag.moderated,
                    "emoji_id": str(tag.emoji_id) if tag.emoji_id else None,
                    "emoji_name": tag.emoji_name
                } for tag in channel.available_tags] if hasattr(channel, 'available_tags') else [],
                "default_reaction_emoji": str(channel.default_reaction_emoji) if hasattr(channel, 'default_reaction_emoji') and channel.default_reaction_emoji else None,
                "default_thread_slowmode_delay": channel.default_thread_slowmode_delay if hasattr(channel, 'default_thread_slowmode_delay') else None
            })
            
        return base_data

    async def _create_overwrites_data(self, channel):
        """Создает данные о правах доступа канала"""
        overwrites_data = []
        for target, overwrite in channel.overwrites.items():
            permissions_data = {}
            for perm, value in overwrite._values.items():
                if value is not None:  # Сохраняем только установленные права
                    permissions_data[perm] = value
                    
            overwrite_data = {
                "target_name": target.name,
                "target_type": "role" if isinstance(target, discord.Role) else "member",
                "target_id": str(target.id),
                "permissions": permissions_data,
                "permissions_detailed": {format_permission(perm): value for perm, value in permissions_data.items()}
            }
            overwrites_data.append(overwrite_data)
        return overwrites_data

    @backup_group.command(name="restore", description="Восстановить сервер из резервной копии")
    @app_commands.default_permissions(administrator=True)
    async def backup_restore(self, interaction: discord.Interaction, file: discord.Attachment):
        # Проверяем, является ли пользователь владельцем сервера
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Эту команду может использовать только владелец сервера!")
            return
            
        await interaction.response.defer()
        
        if not file.filename.endswith('.yaml'):
            await interaction.followup.send("❌ Пожалуйста, загрузите файл резервной копии в формате YAML!")
            return
            
        backup_content = await file.read()
        backup_data = yaml.safe_load(backup_content)
        
        # Проверяем версию бэкапа
        if "backup_version" not in backup_data:
            await interaction.followup.send("❌ Неверный формат файла бэкапа!")
            return
        
        # Обновляем основные настройки сервера
        await interaction.guild.edit(
            name=backup_data["server_name"],
            description=backup_data.get("server_description"),
            verification_level=discord.VerificationLevel[backup_data["server_verification_level"]],
            explicit_content_filter=discord.ContentFilter[backup_data["server_explicit_content_filter"]],
            preferred_locale=backup_data["server_preferred_locale"],
            afk_timeout=backup_data["afk_timeout"]
        )
        
        # Восстанавливаем @everyone роль
        await interaction.guild.default_role.edit(
            permissions=discord.Permissions(backup_data["everyone_role"]["permissions"]),
            mentionable=backup_data["everyone_role"]["mentionable"]
        )
        
        # Восстанавливаем роли
        existing_roles = {role.name: role for role in interaction.guild.roles}
        for role_data in backup_data["roles"]:
            if role_data["name"] not in existing_roles:
                await interaction.guild.create_role(
                    name=role_data["name"],
                    permissions=discord.Permissions(role_data["permissions"]),
                    color=discord.Color(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
            else:
                role = existing_roles[role_data["name"]]
                await role.edit(
                    permissions=discord.Permissions(role_data["permissions"]),
                    color=discord.Color(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
        
        # Восстанавливаем эмодзи
        for emoji_data in backup_data.get("emojis", []):
            if not discord.utils.get(interaction.guild.emojis, name=emoji_data["name"]):
                async with self.bot.session.get(emoji_data["url"]) as resp:
                    if resp.status == 200:
                        emoji_image = await resp.read()
                        await interaction.guild.create_custom_emoji(
                            name=emoji_data["name"],
                            image=emoji_image
                        )
        
        # Восстанавливаем каналы без категории
        for channel_data in backup_data.get("channels_without_category", []):
            await self._restore_channel(interaction.guild, channel_data)
        
        # Восстанавливаем категории и их каналы
        for category_data in backup_data["categories"]:
            # Создаем или получаем категорию
            category = discord.utils.get(interaction.guild.categories, name=category_data["name"])
            if not category:
                overwrites = await self._create_overwrites(interaction.guild, category_data["overwrites"])
                category = await interaction.guild.create_category(
                    name=category_data["name"],
                    position=category_data["position"],
                    overwrites=overwrites
                )
            
            # Восстанавливаем каналы в категории
            for channel_data in category_data["channels"]:
                await self._restore_channel(interaction.guild, channel_data, category)
            
        await interaction.followup.send("✅ Сервер успешно восстановлен из резервной копии!")

    async def _restore_channel(self, guild, channel_data, category=None):
        """Восстанавливает канал определенного типа"""
        existing_channel = discord.utils.get(guild.channels, name=channel_data["name"])
        if existing_channel:
            return existing_channel
            
        overwrites = await self._create_overwrites(guild, channel_data["overwrites"])
        channel_type = channel_data["type"].split('.')[-1]
        
        if channel_type == "text":
            channel = await guild.create_text_channel(
                name=channel_data["name"],
                category=category,
                topic=channel_data.get("topic"),
                nsfw=channel_data.get("nsfw", False),
                slowmode_delay=channel_data.get("slowmode_delay", 0),
                position=channel_data["position"],
                overwrites=overwrites
            )
            
            # Восстанавливаем вебхуки
            for webhook_data in channel_data.get("webhooks", []):
                await channel.create_webhook(
                    name=webhook_data["name"],
                    avatar=webhook_data.get("avatar")
                )
                    
        elif channel_type == "voice":
            await guild.create_voice_channel(
                name=channel_data["name"],
                category=category,
                bitrate=channel_data.get("bitrate", 64000),
                user_limit=channel_data.get("user_limit", 0),
                position=channel_data["position"],
                overwrites=overwrites,
                rtc_region=channel_data.get("rtc_region")
            )
            
        elif channel_type == "stage":
            await guild.create_stage_channel(
                name=channel_data["name"],
                category=category,
                topic=channel_data.get("topic"),
                position=channel_data["position"],
                overwrites=overwrites
            )
            
        elif channel_type == "forum":
            channel = await guild.create_forum_channel(
                name=channel_data["name"],
                category=category,
                topic=channel_data.get("topic"),
                position=channel_data["position"],
                overwrites=overwrites,
                nsfw=channel_data.get("nsfw", False)
            )
            
            # Восстанавливаем теги форума
            if hasattr(channel, 'edit'):
                tags = []
                for tag_data in channel_data.get("available_tags", []):
                    tags.append(discord.ForumTag(
                        name=tag_data["name"],
                        moderated=tag_data.get("moderated", False),
                        emoji_id=int(tag_data["emoji_id"]) if tag_data.get("emoji_id") else None,
                        emoji_name=tag_data.get("emoji_name")
                    ))
                await channel.edit(available_tags=tags)

    async def _create_overwrites(self, guild, overwrites_data):
        """Создает словарь пермишенов для канала"""
        overwrites = {}
        for overwrite_data in overwrites_data:
            target = None
            if overwrite_data["target_type"] == "role":
                target = discord.utils.get(guild.roles, name=overwrite_data["target_name"])
            else:
                target = guild.get_member(int(overwrite_data["target_id"]))
                
            if target:
                overwrites[target] = discord.PermissionOverwrite(**overwrite_data["permissions"])
        return overwrites

async def setup(bot):
    await bot.add_cog(Backup(bot))