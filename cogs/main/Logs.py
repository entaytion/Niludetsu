import discord
from discord.ext import commands
from discord import app_commands
import yaml
import traceback
from typing import Optional
from datetime import datetime

from Niludetsu.logging.users import UserLogger
from Niludetsu.logging.errors import ErrorLogger
from Niludetsu.logging.messages import MessageLogger
from Niludetsu.logging.channels import ChannelLogger
from Niludetsu.logging.server import ServerLogger
from Niludetsu.logging.applications import ApplicationLogger
from Niludetsu.logging.emojis import EmojiLogger
from Niludetsu.logging.events import EventLogger
from Niludetsu.logging.invites import InviteLogger
from Niludetsu.logging.roles import RoleLogger
from Niludetsu.logging.webhooks import WebhookLogger
from Niludetsu.logging.stickers import StickerLogger
from Niludetsu.logging.soundboards import SoundboardLogger
from Niludetsu.logging.threads import ThreadLogger
from Niludetsu.logging.voice import VoiceLogger

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None
        self.owner_id = "636570363605680139"
        self.logging_enabled = True
        bot.loop.create_task(self.initialize_logs())
        
        # Инициализация логгеров
        self.user_logger = UserLogger(bot)
        self.error_logger = ErrorLogger(bot)
        self.message_logger = MessageLogger(bot)
        self.channel_logger = ChannelLogger(bot)
        self.server_logger = ServerLogger(bot)
        self.application_logger = ApplicationLogger(bot)
        self.emoji_logger = EmojiLogger(bot)
        self.event_logger = EventLogger(bot)
        self.invite_logger = InviteLogger(bot)
        self.role_logger = RoleLogger(bot)
        self.webhook_logger = WebhookLogger(bot)
        self.sticker_logger = StickerLogger(bot)
        self.soundboard_logger = SoundboardLogger(bot)
        self.thread_logger = ThreadLogger(bot)
        self.voice_logger = VoiceLogger(bot)

    async def initialize_logs(self):
        """Инициализация канала логов"""
        await self.bot.wait_until_ready()
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' in config and 'main_channel' in config['logging']:
                    channel_id = int(config['logging']['main_channel'])
                    self.log_channel = self.bot.get_channel(channel_id)
                    if not self.log_channel:
                        print(f"❌ Канал логов не найден! ID: {channel_id}")
                        try:
                            self.log_channel = await self.bot.fetch_channel(channel_id)
                            print(f"✅ Канал логов успешно получен: {self.log_channel.name}")
                        except Exception as e:
                            print(f"❌ Не удалось получить канал: {e}")
                    else:
                        print(f"✅ Канал логов успешно установлен: {self.log_channel.name}")
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")

    def save_config(self, channel_id):
        """Сохранение конфигурации"""
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            config['logging']['main_channel'] = str(channel_id)
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    logs_group = app_commands.Group(name="logs", description="Управление системой логирования")

    @logs_group.command(name="show", description="Показать текущий канал логов")
    @commands.has_permissions(administrator=True)
    async def logs_show(self, interaction: discord.Interaction):
        """Показывает информацию о текущем канале логов"""
        try:
            if self.log_channel:
                embed = discord.Embed(
                    title="📝 Информация о логах",
                    description=f"Текущий канал логов: {self.log_channel.mention}\n"
                              f"ID канала: `{self.log_channel.id}`",
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title="❌ Канал логов не настроен",
                    description="Проверьте настройки в файле config.yaml",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    @logs_group.command(name="set", description="Установить канал для логов")
    @commands.has_permissions(administrator=True)
    async def logs_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Установка нового канала для логов"""
        try:
            self.log_channel = channel
            self.save_config(channel.id)
            
            embed = discord.Embed(
                title="✅ Канал логов установлен",
                description=f"Новый канал логов: {channel.mention}\n"
                          f"ID канала: `{channel.id}`",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
            # Отправляем тестовое сообщение в новый канал
            test_embed = discord.Embed(
                title="✅ Система логирования активирована",
                description="Канал логов успешно подключен и готов к работе.",
                color=discord.Color.green()
            )
            await channel.send(embed=test_embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    @logs_group.command(name="test", description="Отправить тестовое сообщение в лог")
    @commands.has_permissions(administrator=True)
    async def logs_test(self, interaction: discord.Interaction):
        """Отправка тестового сообщения в лог"""
        try:
            if not self.log_channel:
                raise Exception("Канал логов не настроен")

            test_embed = discord.Embed(
                title="📝 Тестовое сообщение",
                description="Это тестовое сообщение для проверки работы системы логирования",
                color=discord.Color.blue()
            )
            test_embed.add_field(name="Инициатор", value=interaction.user.mention, inline=True)
            test_embed.add_field(name="Канал", value=self.log_channel.mention, inline=True)
            
            await self.log_channel.send(embed=test_embed)
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Тестовое сообщение отправлено",
                    description="Проверьте канал логов",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    @logs_group.command(name="disable", description="Отключить систему логирования")
    @commands.has_permissions(administrator=True)
    async def logs_disable(self, interaction: discord.Interaction):
        """Отключение системы логирования"""
        try:
            self.logging_enabled = False
            
            if self.log_channel:
                await self.log_channel.send(
                    embed=discord.Embed(
                        title="⚠️ Система логирования отключена",
                        description=f"Администратор {interaction.user.mention} отключил систему логирования",
                        color=discord.Color.yellow()
                    )
                )
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Система логирования отключена",
                    description="Логирование событий приостановлено",
                    color=discord.Color.yellow()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    @logs_group.command(name="enable", description="Включить систему логирования")
    @commands.has_permissions(administrator=True)
    async def logs_enable(self, interaction: discord.Interaction):
        """Включение системы логирования"""
        try:
            self.logging_enabled = True
            
            if self.log_channel:
                await self.log_channel.send(
                    embed=discord.Embed(
                        title="✅ Система логирования включена",
                        description=f"Администратор {interaction.user.mention} включил систему логирования",
                        color=discord.Color.green()
                    )
                )
            
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Система логирования включена",
                    description="Логирование событий возобновлено",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    @logs_group.command(name="status", description="Показать статус системы логирования")
    @commands.has_permissions(administrator=True)
    async def logs_status(self, interaction: discord.Interaction):
        """Показ статуса системы логирования"""
        try:
            status = "Включено" if self.logging_enabled else "Отключено"
            color = discord.Color.green() if self.logging_enabled else discord.Color.red()
            emoji = "✅" if self.logging_enabled else "❌"
            
            embed = discord.Embed(
                title=f"{emoji} Статус системы логирования",
                description="Информация о текущем состоянии системы логирования",
                color=color
            )
            
            embed.add_field(name="Статус", value=status, inline=True)
            embed.add_field(name="Канал", value=self.log_channel.mention if self.log_channel else "Не установлен", inline=True)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    # Логирование команд и ошибок
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Логирование использования команд"""
        await self.event_logger.log_command_use(
            command=ctx.command.qualified_name,
            user=ctx.author,
            channel=ctx.channel,
            guild=ctx.guild
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Логирование ошибок команд"""
        error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        if isinstance(ctx, discord.Interaction):
            command_name = f"/{ctx.command.qualified_name}"
        else:
            command_name = ctx.message.content

        await self.error_logger.log_command_error(
            command=command_name,
            error=error,
            error_trace=error_trace,
            user=ctx.author if not isinstance(ctx, discord.Interaction) else ctx.user,
            channel=ctx.channel
        )

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Перенаправление ошибок slash-команд в основной обработчик"""
        await self.on_command_error(interaction, error)

    # События сервера
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Логирование изменений сервера"""
        await self.server_logger.log_guild_update(before, after)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Логирование создания роли"""
        if self.logging_enabled:
            await self.role_logger.log_role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Логирование удаления роли"""
        if self.logging_enabled:
            await self.role_logger.log_role_delete(role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Логирование изменений роли"""
        if self.logging_enabled:
            await self.role_logger.log_role_update(before, after)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Логирование изменений эмодзи"""
        if self.logging_enabled:
            # Находим измененные эмодзи
            for emoji in before:
                if emoji not in after:  # Удален
                    await self.emoji_logger.log_emoji_delete(emoji)
            
            for emoji in after:
                if emoji not in before:  # Создан
                    await self.emoji_logger.log_emoji_create(emoji)
                else:  # Изменен
                    old_emoji = discord.utils.get(before, id=emoji.id)
                    if old_emoji:
                        await self.emoji_logger.log_emoji_update(old_emoji, emoji)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Логирование создания канала"""
        if self.logging_enabled:
            await self.channel_logger.log_channel_create(channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Логирование удаления канала"""
        if self.logging_enabled:
            await self.channel_logger.log_channel_delete(channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Логирование изменений канала"""
        if self.logging_enabled:
            await self.channel_logger.log_channel_update(before, after)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        if self.logging_enabled:
            await self.channel_logger.log_channel_pins_update(channel, last_pin)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Логирование присоединения участника"""
        await self.event_logger.log_member_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Логирование выхода участника"""
        await self.event_logger.log_member_remove(member)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Логирование бана участника"""
        if self.logging_enabled:
            await self.server_logger.log_ban_add(guild, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Логирование разбана участника"""
        if self.logging_enabled:
            await self.server_logger.log_ban_remove(guild, user)

    # События пользователей
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Логирование изменений участника"""
        if self.logging_enabled:
            if before.display_name != after.display_name:
                await self.user_logger.log_user_name_update(before, after)
            if before.roles != after.roles:
                await self.user_logger.log_user_roles_update(before, after)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar != after.avatar:
            await self.user_logger.log_user_avatar_update(before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if isinstance(user, discord.Member):
            await self.user_logger.log_user_timeout(user, user.timed_out_until)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if isinstance(user, discord.Member):
            await self.user_logger.log_user_timeout_remove(user)

    # События сообщений
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await self.message_logger.log_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.message_logger.log_message_edit(before, after)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        await self.message_logger.log_bulk_message_delete(messages)

    # События голосовых каналов
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование изменений голосового состояния"""
        if self.logging_enabled:
            await self.voice_logger.log_voice_status_update(member, before.channel if before else None, after.channel if after else None)

    # События вебхуков
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        """Логирование обновления вебхуков в канале"""
        if self.logging_enabled:
            await self.webhook_logger.log_webhook_channel_update(channel)

    @commands.Cog.listener()
    async def on_guild_channel_webhooks_update(self, channel: discord.TextChannel):
        """Логирование обновления вебхуков в канале"""
        if self.logging_enabled:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                if webhook.id not in self._webhook_cache.get(channel.id, {}):
                    # Новый вебхук
                    await self.webhook_logger.log_webhook_create(webhook)
                    self._webhook_cache.setdefault(channel.id, {})[webhook.id] = webhook
                else:
                    # Проверяем изменения
                    old_webhook = self._webhook_cache[channel.id][webhook.id]
                    if old_webhook.name != webhook.name:
                        await self.webhook_logger.log_webhook_name_update(old_webhook, webhook)
                    if old_webhook.avatar != webhook.avatar:
                        await self.webhook_logger.log_webhook_avatar_update(old_webhook, webhook)
                    if old_webhook.channel != webhook.channel:
                        await self.webhook_logger.log_webhook_channel_update(old_webhook, webhook)
                    self._webhook_cache[channel.id][webhook.id] = webhook

            # Проверяем удаленные вебхуки
            if channel.id in self._webhook_cache:
                for webhook_id, webhook in list(self._webhook_cache[channel.id].items()):
                    if not any(w.id == webhook_id for w in webhooks):
                        await self.webhook_logger.log_webhook_delete(webhook)
                        del self._webhook_cache[channel.id][webhook_id]

    async def cog_load(self):
        """Инициализация кэша вебхуков при загрузке кога"""
        self._webhook_cache = {}
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                try:
                    webhooks = await channel.webhooks()
                    self._webhook_cache[channel.id] = {webhook.id: webhook for webhook in webhooks}
                except discord.Forbidden:
                    continue

    # События тредов
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        await self.thread_logger.log_thread_create(thread)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        await self.thread_logger.log_thread_delete(thread)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        if before.name != after.name:
            await self.thread_logger.log_thread_name_update(before, after)
        if before.slowmode_delay != after.slowmode_delay:
            await self.thread_logger.log_thread_slowmode_update(before, after)
        if before.auto_archive_duration != after.auto_archive_duration:
            await self.thread_logger.log_thread_archive_duration_update(before, after)
        if not before.archived and after.archived:
            await self.thread_logger.log_thread_archive(after)
        if before.archived and not after.archived:
            await self.thread_logger.log_thread_unarchive(after)
        if not before.locked and after.locked:
            await self.thread_logger.log_thread_lock(after)
        if before.locked and not after.locked:
            await self.thread_logger.log_thread_unlock(after)

    # События стикеров
    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker):
        await self.sticker_logger.log_sticker_create(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker):
        await self.sticker_logger.log_sticker_delete(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before, after):
        if before.name != after.name:
            await self.sticker_logger.log_sticker_name_update(before, after)
        if before.description != after.description:
            await self.sticker_logger.log_sticker_description_update(before, after)
        if before.emoji != after.emoji:
            await self.sticker_logger.log_sticker_emoji_update(before, after)

    # События звуков
    @commands.Cog.listener()
    async def on_soundboard_sound_create(self, guild: discord.Guild, sound: discord.SoundboardSound):
        """Логирование создания звука"""
        if self.logging_enabled:
            data = {
                'id': sound.id,
                'name': sound.name,
                'emoji': str(sound.emoji) if sound.emoji else None,
                'volume': sound.volume,
                'user': sound.user,
                'guild': sound.guild
            }
            await self.soundboard_logger.log_soundboard_create(data)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, guild: discord.Guild, sound: discord.SoundboardSound):
        """Логирование удаления звука"""
        if self.logging_enabled:
            data = {
                'id': sound.id,
                'name': sound.name,
                'emoji': str(sound.emoji) if sound.emoji else None,
                'volume': sound.volume,
                'user': sound.user,
                'guild': sound.guild
            }
            await self.soundboard_logger.log_soundboard_delete(data)

    @commands.Cog.listener()
    async def on_soundboard_sound_update(self, guild: discord.Guild, before: discord.SoundboardSound, after: discord.SoundboardSound):
        """Логирование обновления звука"""
        if self.logging_enabled:
            before_data = {
                'id': before.id,
                'name': before.name,
                'emoji': str(before.emoji) if before.emoji else None,
                'volume': before.volume,
                'user': before.user,
                'guild': before.guild
            }
            after_data = {
                'id': after.id,
                'name': after.name,
                'emoji': str(after.emoji) if after.emoji else None,
                'volume': after.volume,
                'user': after.user,
                'guild': after.guild
            }
            
            if before.name != after.name:
                await self.soundboard_logger.log_soundboard_name_update(before_data, after_data)
            if before.volume != after.volume:
                await self.soundboard_logger.log_soundboard_volume_update(before_data, after_data)
            if str(before.emoji) != str(after.emoji):
                await self.soundboard_logger.log_soundboard_emoji_update(before_data, after_data)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Логирование создания приглашения"""
        if self.logging_enabled and self.log_channel:
            await self.invite_logger.log_invite_create(invite)
            
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Логирование удаления приглашения"""
        if self.logging_enabled and self.log_channel:
            await self.invite_logger.log_invite_delete(invite)

async def setup(bot):
    await bot.add_cog(Logs(bot)) 