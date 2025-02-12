import discord
from discord.ext import commands
from discord import app_commands
import yaml
import traceback
from typing import Optional
from datetime import datetime
from Niludetsu.utils.config_loader import bot_state
from Niludetsu.utils.embed import Embed
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
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
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
                        await self.log_channel.send(
                            embed=Embed(
                                title="✅ Система логирования активирована",
                                description="Канал логов успешно подключен и готов к работе.",
                                color="GREEN"
                            )
                        )
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
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            config['logging']['main_channel'] = str(channel_id)
            with open('data/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    logs_group = app_commands.Group(name="logs", description="Управление системой логирования")

    @logs_group.command(name="status", description="Показать статус и информацию о системе логирования")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_status(self, interaction: discord.Interaction):
        if not self._initialized:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Система логирования не инициализирована!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        embed=Embed(
            title="📊 Статус системы логирования",
            description=(
                f"**Статус:** {'🟢 Включена' if self.logging_enabled else '🔴 Отключена'}\n"
                f"**Канал логов:** {self.log_channel.mention if self.log_channel else 'Не установлен'}\n"
                f"**Задержка:** {self._rate_limit_delay} сек"
            )
        )
        await interaction.response.send_message(embed=embed)

    @logs_group.command(name="set", description="Установить канал для логов")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.log_channel = channel
        self.save_config(channel.id)
        
        await interaction.response.send_message(
            embed=Embed(
                description=f"✅ Канал логов установлен: {channel.mention}",
                color="GREEN"
            )
        )
        
        await channel.send(
            embed=Embed(
                title="✅ Канал логов активирован",
                description="Этот канал теперь будет использоваться для системных логов.",
                color="GREEN"
            )
        )

    @logs_group.command(name="test", description="Отправить тестовое сообщение в лог")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_test(self, interaction: discord.Interaction):
        if not self.log_channel:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Канал логов не установлен!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        await self.log_channel.send(
            embed=Embed(
                title="🧪 Тестовое сообщение",
                description="Это тестовое сообщение системы логирования.",
                footer={"text": f"Отправлено: {interaction.user}"}
            )
        )
        
        await interaction.response.send_message(
            embed=Embed(
                description="✅ Тестовое сообщение отправлено!",
                color="GREEN"
            ),
            ephemeral=True
        )

    @logs_group.command(name="disable", description="Отключить систему логирования")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_disable(self, interaction: discord.Interaction):
        if not self.logging_enabled:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Система логирования уже отключена!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        self.logging_enabled = False
        await interaction.response.send_message(
            embed=Embed(
                description="✅ Система логирования отключена",
                color="GREEN"
            )
        )

    @logs_group.command(name="enable", description="Включить систему логирования")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs_enable(self, interaction: discord.Interaction):
        if self.logging_enabled:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Система логирования уже включена!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if not self.log_channel:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Сначала установите канал для логов!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        self.logging_enabled = True
        await interaction.response.send_message(
            embed=Embed(
                description="✅ Система логирования включена",
                color="GREEN"
            )
        )

    # Event Listeners
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['server'].log_guild_update(before, after)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if self.logging_enabled and self.log_channel:
            await self.loggers['role'].log_role_create(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if self.logging_enabled and self.log_channel:
            await self.loggers['role'].log_role_delete(role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['role'].log_role_update(before, after)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['emoji'].log_emoji_update(before, after)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Логирование создания каналов"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['channel'].log_channel_create(channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Логирование удаления каналов"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['channel'].log_channel_delete(channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Логирование изменений каналов"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['channel'].log_channel_update(before, after)
            
    @commands.Cog.listener()
    async def on_guild_channel_permissions_update(self, channel, target, before, after):
        """Обработчик изменения прав канала"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['channel'].log_channel_permissions_update(channel, target, before, after)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_member_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_member_remove(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_member_update(before, after)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_user_update(before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_member_ban(guild, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if self.logging_enabled and self.log_channel:
            await self.loggers['user'].log_member_unban(guild, user)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Логирование удаления сообщений"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['message'].log_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Логирование изменения сообщений"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['message'].log_message_edit(before, after)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Логирование массового удаления сообщений"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['message'].log_bulk_message_delete(messages)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование изменений голосового состояния"""
        await self.loggers['voice'].log_voice_status_update(member, before, after)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.logging_enabled and self.log_channel:
            await self.loggers['thread'].log_thread_create(thread)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if self.logging_enabled and self.log_channel:
            await self.loggers['thread'].log_thread_delete(thread)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['thread'].log_thread_update(before, after)

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker):
        if self.logging_enabled and self.log_channel:
            await self.loggers['sticker'].log_sticker_create(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker):
        if self.logging_enabled and self.log_channel:
            await self.loggers['sticker'].log_sticker_delete(sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before, after):
        if self.logging_enabled and self.log_channel:
            await self.loggers['sticker'].log_sticker_update(before, after)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if self.logging_enabled and self.log_channel:
            await self.loggers['invite'].log_invite_create(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if self.logging_enabled and self.log_channel:
            await self.loggers['invite'].log_invite_delete(invite)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        if self.logging_enabled and self.log_channel:
            await self.loggers['webhook'].log_webhooks_update(channel)

    # Onboarding Events
    @commands.Cog.listener()
    async def on_guild_onboarding_channels_update(self, guild, before, after):
        """Обработчик изменения каналов онбординга"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['server'].log_onboarding_channels_update(before, after)

    @commands.Cog.listener()
    async def on_guild_onboarding_question_add(self, guild, question):
        """Обработчик добавления вопроса онбординга"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['server'].log_onboarding_question_add(question)

    @commands.Cog.listener()
    async def on_guild_onboarding_question_remove(self, guild, question):
        """Обработчик удаления вопроса онбординга"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['server'].log_onboarding_question_remove(question)

    @commands.Cog.listener()
    async def on_guild_onboarding_question_update(self, guild, before, after):
        """Обработчик изменения вопроса онбординга"""
        if self.logging_enabled and self.log_channel:
            await self.loggers['server'].log_onboarding_question_update(before, after)

    @commands.Cog.listener()
    async def on_guild_onboarding_update(self, guild, before, after):
        """Обработчик изменения настроек онбординга"""
        if self.logging_enabled and self.log_channel:
            if before.enabled != after.enabled:
                await self.loggers['server'].log_onboarding_toggle(after.enabled)

    async def cog_load(self):
        """Инициализация при загрузке кога"""
        try:
            for logger in self.loggers.values():
                if hasattr(logger, 'setup'):
                    await logger.setup()
        except Exception as e:
            print(f"Error initializing loggers: {e}")

async def setup(bot):
    await bot.add_cog(Logs(bot)) 