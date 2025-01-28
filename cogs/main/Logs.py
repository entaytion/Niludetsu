import discord
from discord.ext import commands
from discord import app_commands
import yaml
import traceback
from typing import Optional
from datetime import datetime
from Niludetsu.utils.config_loader import bot_state
import asyncio

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
        self._initialized = False
        self._webhook_cache = {}
        self._rate_limit_delay = 1.5  # Минимальная задержка между сообщениями
        self._last_log_time = None
        
        # Инициализация логгеров
        self.loggers = {
            'user': UserLogger(bot),
            'error': ErrorLogger(bot),
            'message': MessageLogger(bot),
            'channel': ChannelLogger(bot),
            'server': ServerLogger(bot),
            'application': ApplicationLogger(bot),
            'emoji': EmojiLogger(bot),
            'event': EventLogger(bot),
            'invite': InviteLogger(bot),
            'role': RoleLogger(bot),
            'webhook': WebhookLogger(bot),
            'sticker': StickerLogger(bot),
            'soundboard': SoundboardLogger(bot),
            'thread': ThreadLogger(bot),
            'voice': VoiceLogger(bot)
        }
        
        bot.loop.create_task(self.initialize_logs())

    async def initialize_logs(self):
        """Инициализация канала логов"""
        await self.bot.wait_until_ready()
        if self._initialized:
            return
            
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' in config and 'main_channel' in config['logging']:
                    channel_id = int(config['logging']['main_channel'])
                    self.log_channel = self.bot.get_channel(channel_id)
                    
                    if not self.log_channel:
                        try:
                            self.log_channel = await self.bot.fetch_channel(channel_id)
                        except Exception as e:
                            print(f"❌ Не удалось получить канал логов: {e}")
                            return
                    
                    if not bot_state.is_initialized('logging_system'):
                        test_embed = discord.Embed(
                            title="✅ Система логирования активирована",
                            description="Канал логов успешно подключен и готов к работе.",
                            color=discord.Color.green()
                        )
                        await self.log_channel.send(embed=test_embed)
                        bot_state.mark_initialized('logging_system')
                    
                    self._initialized = True
                    
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")

    async def _check_rate_limit(self):
        """Проверка и соблюдение ограничений отправки сообщений"""
        if self._last_log_time:
            current_time = datetime.utcnow()
            time_diff = (current_time - self._last_log_time).total_seconds()
            if time_diff < self._rate_limit_delay:
                await asyncio.sleep(self._rate_limit_delay - time_diff)
        self._last_log_time = datetime.utcnow()

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
            
            # Отправляем тестовое сообщение в новый канал только при смене канала
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
            # Если система уже включена, не делаем ничего
            if self.logging_enabled:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="⚠️ Система уже активна",
                        description="Система логирования уже включена",
                        color=discord.Color.yellow()
                    )
                )
                return

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

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Логирование использования команд"""
        if self.logging_enabled and self._initialized:
            await self.loggers['message'].log_command(ctx, ctx.command.name)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Логирование изменений сервера"""
        if self.logging_enabled and self._initialized:
            await self.loggers['server'].log_guild_update(before, after)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Логирование создания роли"""
        if self.logging_enabled and self._initialized:
            await self.loggers['role'].log_role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Логирование удаления роли"""
        if self.logging_enabled and self._initialized:
            await self.loggers['role'].log_role_delete(role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Логирование обновления роли"""
        if self.logging_enabled and self._initialized:
            await self.loggers['role'].log_role_update(before, after)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Логирование изменений эмодзи"""
        if self.logging_enabled and self._initialized:
            # Определяем добавленные и удаленные эмодзи
            added = [emoji for emoji in after if emoji not in before]
            removed = [emoji for emoji in before if emoji not in after]
            updated = [emoji for emoji in after if emoji in before and emoji != before[before.index(emoji)]]
            
            for emoji in added:
                await self.loggers['emoji'].log_emoji_create(emoji)
            for emoji in removed:
                await self.loggers['emoji'].log_emoji_delete(emoji)
            for emoji in updated:
                old_emoji = before[before.index(emoji)]
                await self.loggers['emoji'].log_emoji_update(old_emoji, emoji)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Логирование создания канала"""
        if self.logging_enabled and self._initialized:
            await self.loggers['channel'].log_channel_create(channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Логирование удаления канала"""
        if self.logging_enabled and self._initialized:
            await self.loggers['channel'].log_channel_delete(channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Логирование обновления канала"""
        if self.logging_enabled and self._initialized:
            await self.loggers['channel'].log_channel_update(before, after)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        if self.logging_enabled and self._initialized:
            await self.loggers['channel'].log_channel_pins_update(channel, last_pin)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Логирование входа участника"""
        if self.logging_enabled and self._initialized:
            await self.loggers['server'].log_user_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Логирование выхода участника"""
        if self.logging_enabled and self._initialized:
            await self.loggers['server'].log_user_leave(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Логирование обновления участника"""
        if self.logging_enabled and self._initialized:
            if before.display_name != after.display_name:
                await self.loggers['user'].log_user_name_update(before, after)
            if before.roles != after.roles:
                await self.loggers['user'].log_user_roles_update(before, after)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Логирование обновления пользователя"""
        if self.logging_enabled and self._initialized:
            if before.avatar != after.avatar:
                await self.loggers['user'].log_user_avatar_update(before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Логирование бана участника"""
        if self.logging_enabled and self._initialized:
            await self.loggers['server'].log_ban_add(guild, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Логирование разбана участника"""
        if self.logging_enabled and self._initialized:
            await self.loggers['server'].log_ban_remove(guild, user)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Логирование удаления сообщения"""
        if self.logging_enabled and not message.author.bot:
            await self.loggers['message'].log_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Логирование редактирования сообщения"""
        if self.logging_enabled and not before.author.bot:
            if before.content != after.content:
                await self.loggers['message'].log_message_edit(before, after)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Логирование массового удаления сообщений"""
        if self.logging_enabled:
            await self.loggers['message'].log_bulk_message_delete(messages)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование изменений голосового состояния"""
        if self.logging_enabled and self._initialized:
            await self.loggers['voice'].log_voice_status_update(member, before.channel if before else None, after.channel if after else None)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """Логирование создания ветки"""
        if self.logging_enabled and self._initialized:
            await self.loggers['thread'].log_thread_create(thread)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        """Логирование удаления ветки"""
        if self.logging_enabled and self._initialized:
            await self.loggers['thread'].log_thread_delete(thread)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        """Логирование обновления ветки"""
        if self.logging_enabled and self._initialized:
            await self.loggers['thread'].log_thread_update(before, after)

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker):
        """Логирование создания стикера"""
        if self.logging_enabled and self._initialized:
            await self.loggers['sticker'].log_sticker_create(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker):
        """Логирование удаления стикера"""
        if self.logging_enabled and self._initialized:
            await self.loggers['sticker'].log_sticker_delete(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before, after):
        """Логирование обновления стикера"""
        if self.logging_enabled and self._initialized:
            await self.loggers['sticker'].log_sticker_update(before, after)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Логирование создания приглашения"""
        if self.logging_enabled and self._initialized:
            await self.loggers['invite'].log_invite_create(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Логирование удаления приглашения"""
        if self.logging_enabled and self._initialized:
            await self.loggers['invite'].log_invite_delete(invite)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Логирование изменений эмодзи"""
        if self.logging_enabled:
            await self.loggers['emoji'].log_emoji_update(guild, before, after)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        """Логирование изменений стикеров"""
        if self.logging_enabled:
            await self.loggers['sticker'].log_sticker_update(guild, before, after)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Логирование изменений сервера"""
        if self.logging_enabled:
            await self.loggers['server'].log_guild_update(before, after)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        """Логирование изменений вебхуков"""
        if self.logging_enabled:
            await self.loggers['webhook'].log_webhook_update(channel)

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

async def setup(bot):
    await bot.add_cog(Logs(bot)) 