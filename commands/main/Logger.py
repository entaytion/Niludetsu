import asyncio, discord, time
from discord.ext import commands
from Niludetsu.config import LOG_CHANNEL_ID
from Niludetsu.webhooks.application import ApplicationLogger
from Niludetsu.webhooks.automod import AutoModLogger
from Niludetsu.webhooks.channel import ChannelLogger
from Niludetsu.webhooks.emoji import EmojiLogger
from Niludetsu.webhooks.event import EventLogger
from Niludetsu.webhooks.invite import InviteLogger
from Niludetsu.webhooks.member import MemberLogger
from Niludetsu.webhooks.message import MessageLogger
from Niludetsu.webhooks.reaction import ReactionLogger
from Niludetsu.webhooks.role import RoleLogger
from Niludetsu.webhooks.server import ServerLogger
from Niludetsu.webhooks.soundboard import SoundboardLogger
from Niludetsu.webhooks.stage import StageLogger
from Niludetsu.webhooks.sticker import StickerLogger
from Niludetsu.webhooks.thread import ThreadLogger
from Niludetsu.webhooks.voice import VoiceLogger
from Niludetsu.webhooks.webhook import WebhookLogger

class Logger(commands.Cog):
    """
    Централизованный логгер для всех событий.
    Переписанный с нуля, чтобы было удобнее и быстрее. И без мазохизма с созданием конченной системы, которую даже я осилить не смог. Но, выглядит ублюдочно при использовании.
    """
    def __init__(self, bot):
        self.bot = bot
        self.emoji_logger = EmojiLogger(bot)
        self.sticker_logger = StickerLogger(bot)
        self.webhook_logger = WebhookLogger(bot)
        self.voice_logger = VoiceLogger(bot)
        self.thread_logger = ThreadLogger(bot)
        self.stage_logger = StageLogger(bot)
        self.soundboard_logger = SoundboardLogger(bot)
        self.server_logger = ServerLogger(bot)
        self.role_logger = RoleLogger(bot)
        self.message_logger = MessageLogger(bot)
        self.invite_logger = InviteLogger(bot)
        self.event_logger = EventLogger(bot)
        self.application_logger = ApplicationLogger(bot)
        self.channel_logger = ChannelLogger(bot)
        self.automod_logger = AutoModLogger(bot)
        self.member_logger = MemberLogger(bot)
        self.reaction_logger = ReactionLogger(bot)
        self._webhook_cache = {}  # channel_id: [webhooks]
        self._webhook_update_cooldown = {}  # channel_id: timestamp

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        # Добавленные эмодзи
        added = [e for e in after if e not in before]
        for emoji in added:
            await self.emoji_logger.log_emoji_create(channel, emoji)
        # Удалённые эмодзи
        removed = [e for e in before if e not in after]
        for emoji in removed:
            await self.emoji_logger.log_emoji_delete(channel, emoji)
        # Изменённые эмодзи (по id, но имя изменилось)
        for b in before:
            for a in after:
                if b.id == a.id and b.name != a.name:
                    await self.emoji_logger.log_emoji_update(channel, b, a)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        # Добавленные стикеры
        added = [s for s in after if s not in before]
        for sticker in added:
            await self.sticker_logger.log_sticker_create(channel, sticker)
        # Удалённые стикеры
        removed = [s for s in before if s not in after]
        for sticker in removed:
            await self.sticker_logger.log_sticker_delete(channel, sticker)
        # Изменённые стикеры (по id, но изменились поля)
        for b in before:
            for a in after:
                if b.id == a.id and (
                    getattr(b, "name", None) != getattr(a, "name", None) or
                    getattr(b, "description", None) != getattr(a, "description", None) or
                    getattr(b, "tags", None) != getattr(a, "tags", None)
                ):
                    await self.sticker_logger.log_sticker_update(channel, b, a)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        log_channel = channel.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        channel_id = channel.id
        current_time = time.time()

        # Проверка на дублирование событий - игнорируем события в течение 1 секунды
        if channel_id in self._webhook_update_cooldown:
            if current_time - self._webhook_update_cooldown[channel_id] < 1.0:
                return  # Игнорируем слишком частые обновления

        # Обновляем временную метку
        self._webhook_update_cooldown[channel_id] = current_time

        # Небольшая задержка для устранения race conditions
        await asyncio.sleep(0.3)

        before = self._webhook_cache.get(channel_id, [])
        after = await channel.webhooks()

        # Если кеш пуст для этого канала и это первый вызов - просто инициализируем кеш
        if not before and channel_id not in self._webhook_cache:
            self._webhook_cache[channel_id] = list(after)
            return

        # Основная логика сравнения и логирования осталась прежней
        before_ids = {w.id for w in before}
        after_ids = {w.id for w in after}

        # Добавленные
        added_ids = after_ids - before_ids
        for add_id in added_ids:
            webhook = next(w for w in after if w.id == add_id)
            await self.webhook_logger.log_webhook_create(log_channel, channel, webhook)

        # Удалённые
        removed_ids = before_ids - after_ids
        for rem_id in removed_ids:
            webhook = next(w for w in before if w.id == rem_id)
            await self.webhook_logger.log_webhook_delete(log_channel, channel, webhook)

        # Обновлённые
        common_ids = before_ids & after_ids
        for com_id in common_ids:
            before_webhook = next(w for w in before if w.id == com_id)
            after_webhook = next(w for w in after if w.id == com_id)
            if (before_webhook.name != after_webhook.name or
                (before_webhook.avatar != after_webhook.avatar)):
                await self.webhook_logger.log_webhook_update(log_channel, channel, before_webhook, after_webhook)

        # Обновляем кэш
        self._webhook_cache[channel_id] = list(after)

        # Периодически очищаем старые записи cooldown
        if hasattr(self, '_cleanup_task') and not self._cleanup_task.done():
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_webhook_cooldowns())

    async def _cleanup_webhook_cooldowns(self):
        """Очищаем старые записи в cooldown словаре"""
        await asyncio.sleep(60)  # Запускаем очистку раз в минуту
        current_time = time.time()
        to_remove = []

        for channel_id, timestamp in self._webhook_update_cooldown.items():
            if current_time - timestamp > 30:  # Удаляем записи старше 30 секунд
                to_remove.append(channel_id)

        for channel_id in to_remove:
            self._webhook_update_cooldown.pop(channel_id, None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        log_channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        # Изменение состояния (mute, deaf, stream, video и т.д.)
        changes = {}
        if before.channel != after.channel:
            # Переход между каналами
            if not before.channel and after.channel:
                await self.voice_logger.log_voice_join(log_channel, member, after.channel)
            elif before.channel and not after.channel:
                await self.voice_logger.log_voice_leave(log_channel, member, before.channel)
            elif before.channel and after.channel and before.channel != after.channel:
                await self.voice_logger.log_voice_switch(log_channel, member, before.channel, after.channel)
        else:
            # Проверяем изменения состояния
            if before.deaf != after.deaf:
                changes['deaf'] = (before.deaf, after.deaf)
            if before.mute != after.mute:
                changes['mute'] = (before.mute, after.mute)
            if before.self_deaf != after.self_deaf:
                changes['self_deaf'] = (before.self_deaf, after.self_deaf)
            if before.self_mute != after.self_mute:
                changes['self_mute'] = (before.self_mute, after.self_mute)
            if before.self_stream != after.self_stream:
                changes['self_stream'] = (before.self_stream, after.self_stream)
            if before.self_video != after.self_video:
                changes['self_video'] = (before.self_video, after.self_video)
            if changes:
                await self.voice_logger.log_voice_state(log_channel, member, changes)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        log_channel = thread.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.thread_logger.log_thread_create(log_channel, thread)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        log_channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.thread_logger.log_thread_update(log_channel, before, after)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        log_channel = thread.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.thread_logger.log_thread_delete(log_channel, thread)

    # Soundboard события
    @commands.Cog.listener()
    async def on_soundboard_sound_create(self, sound):
        log_channel = sound.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_create(log_channel, sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        log_channel = sound.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_delete(log_channel, sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_update(self, before, after):
        log_channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_update(log_channel, before, after)

    @commands.Cog.listener()
    async def on_soundboard_sound_play(self, sound, member):
        log_channel = sound.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_play(log_channel, sound, member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_join(channel, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_remove(channel, guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        channel = after.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_update(channel, before, after)

    # закомментировал, потому что это бесполезная хуета.
    """ @commands.Cog.listener()
    async def on_guild_available(self, guild):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_available(channel, guild)

    @commands.Cog.listener()
    async def on_guild_unavailable(self, guild):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_unavailable(channel, guild) """

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.server_logger.log_guild_integrations_update(channel, guild)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        channel = role.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.role_logger.log_role_create(channel, role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        channel = role.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.role_logger.log_role_delete(channel, role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.role_logger.log_role_update(channel, before, after)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return
        channel = message.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.message_logger.log_message_delete(channel, message)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
        guild = messages[0].guild if messages[0].guild else None
        if not guild:
            return
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.message_logger.log_message_bulk_delete(channel, messages)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None:
            return
        channel = before.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.message_logger.log_message_edit(channel, before, after)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        channel = invite.channel.guild.get_channel(LOG_CHANNEL_ID) if invite.channel and invite.channel.guild else None
        if not channel:
            return
        await self.invite_logger.log_invite_create(channel, invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        channel = invite.channel.guild.get_channel(LOG_CHANNEL_ID) if invite.channel and invite.channel.guild else None
        if not channel:
            return
        await self.invite_logger.log_invite_delete(channel, invite)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        channel = event.guild.get_channel(LOG_CHANNEL_ID) if event.guild else None
        if not channel:
            return
        await self.event_logger.log_scheduled_event_create(channel, event)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        channel = event.guild.get_channel(LOG_CHANNEL_ID) if event.guild else None
        if not channel:
            return
        await self.event_logger.log_scheduled_event_delete(channel, event)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before, after):
        channel = after.guild.get_channel(LOG_CHANNEL_ID) if after.guild else None
        if not channel:
            return
        await self.event_logger.log_scheduled_event_update(channel, before, after)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event, user):
        channel = event.guild.get_channel(LOG_CHANNEL_ID) if event.guild else None
        if not channel:
            return
        await self.event_logger.log_scheduled_event_add(channel, event, user)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event, user):
        channel = event.guild.get_channel(LOG_CHANNEL_ID) if event.guild else None
        if not channel:
            return
        await self.event_logger.log_scheduled_event_remove(channel, event, user)

    @commands.Cog.listener()
    async def on_integration_create(self, integration):
        channel = integration.guild.get_channel(LOG_CHANNEL_ID) if integration.guild else None
        if not channel:
            return
        await self.application_logger.log_app_add(channel, integration)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration):
        channel = integration.guild.get_channel(LOG_CHANNEL_ID) if integration.guild else None
        if not channel:
            return
        # remover можно получить из audit log, если нужно
        await self.application_logger.log_app_remove(channel, integration)

    @commands.Cog.listener()
    async def on_integration_update(self, before, after):
        channel = after.guild.get_channel(LOG_CHANNEL_ID) if after.guild else None
        if not channel:
            return
        # updater можно получить из audit log, если нужно
        await self.application_logger.log_app_update(channel, before, after)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = channel.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.channel_logger.log_channel_create(log_channel, channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = channel.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.channel_logger.log_channel_delete(log_channel, channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        log_channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        # Проверяем, изменилась ли только позиция канала (игнорируем такие изменения)
        position_only_change = (
            before.name == after.name and
            before.category == after.category and
            getattr(before, 'topic', None) == getattr(after, 'topic', None) and
            getattr(before, 'slowmode_delay', None) == getattr(after, 'slowmode_delay', None) and
            getattr(before, 'nsfw', None) == getattr(after, 'nsfw', None) and
            getattr(before, 'bitrate', None) == getattr(after, 'bitrate', None) and
            getattr(before, 'user_limit', None) == getattr(after, 'user_limit', None)
        )

        # Если изменилась только позиция, игнорируем лог
        if position_only_change:
            return

        # Определяем изменения в канале
        changes = []

        # Проверяем изменение названия
        if before.name != after.name:
            changes.append(f"**Название:** `{before.name}` → `{after.name}`")

        # Проверяем изменение темы (для текстовых каналов)
        if hasattr(before, 'topic') and hasattr(after, 'topic'):
            if before.topic != after.topic:
                before_topic = before.topic or "Не установлена"
                after_topic = after.topic or "Не установлена"
                changes.append(f"**Тема:** `{before_topic}` → `{after_topic}`")

        # Проверяем изменение slowmode (медленный режим)
        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay'):
            if before.slowmode_delay != after.slowmode_delay:
                def format_slowmode(seconds):
                    if seconds == 0:
                        return "Отключен"
                    elif seconds < 60:
                        return f"{seconds}с"
                    elif seconds < 3600:
                        return f"{seconds // 60}м {seconds % 60}с" if seconds % 60 else f"{seconds // 60}м"
                    else:
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        return f"{hours}ч {minutes}м" if minutes else f"{hours}ч"

                before_slowmode = format_slowmode(before.slowmode_delay)
                after_slowmode = format_slowmode(after.slowmode_delay)
                changes.append(f"**Медленный режим:** `{before_slowmode}` → `{after_slowmode}`")

        # Проверяем изменение NSFW статуса
        if hasattr(before, 'nsfw') and hasattr(after, 'nsfw'):
            if before.nsfw != after.nsfw:
                nsfw_status = "Включен" if after.nsfw else "Отключен"
                changes.append(f"**NSFW:** `{nsfw_status}`")

        # Проверяем изменение категории
        if before.category != after.category:
            before_cat = before.category.name if before.category else "Без категории"
            after_cat = after.category.name if after.category else "Без категории"
            changes.append(f"**Категория:** `{before_cat}` → `{after_cat}`")

        # Проверяем изменение битрейта (для голосовых каналов)
        if hasattr(before, 'bitrate') and hasattr(after, 'bitrate'):
            if before.bitrate != after.bitrate:
                changes.append(f"**Битрейт:** `{before.bitrate // 1000}kbps` → `{after.bitrate // 1000}kbps`")

        # Проверяем изменение лимита пользователей (для голосовых каналов)
        if hasattr(before, 'user_limit') and hasattr(after, 'user_limit'):
            if before.user_limit != after.user_limit:
                before_limit = "Без ограничений" if before.user_limit == 0 else str(before.user_limit)
                after_limit = "Без ограничений" if after.user_limit == 0 else str(after.user_limit)
                changes.append(f"**Лимит пользователей:** `{before_limit}` → `{after_limit}`")

        # Получаем модератора из audit log
        updater = None
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                if entry.target.id == after.id:
                    updater = entry.user
                    break
        except:
            pass

        await self.channel_logger.log_channel_update(log_channel, before, after, updater, changes)

        # Сравниваем overwrites (права доступа)
        def get_overwrites_dict(channel):
            return {k: v for k, v in channel.overwrites.items()}

        before_overwrites = get_overwrites_dict(before)
        after_overwrites = get_overwrites_dict(after)
        changes = []
        for target, after_ow in after_overwrites.items():
            before_ow = before_overwrites.get(target)
            if before_ow != after_ow:
                perms_diff = {}
                for perm in dir(after_ow):
                    if perm.startswith('_') or not isinstance(getattr(after_ow, perm, None), (bool, type(None))):
                        continue
                    before_val = getattr(before_ow, perm, None) if before_ow else None
                    after_val = getattr(after_ow, perm, None)
                    if before_val != after_val:
                        perms_diff[perm] = {"before": before_val, "after": after_val}
                if perms_diff:
                    changes.append({"role": target, "permissions": perms_diff})
        if changes:
            # Получаем модератора из audit log
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.overwrite_update):
                moderator = entry.user if isinstance(entry.user, discord.Member) else after.guild.get_member(entry.user.id)
                break
            else:
                moderator = after.guild.me  # fallback
            await self.channel_logger.log_permissions_update(log_channel, after, moderator, changes)

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule):
        channel = rule.guild.get_channel(LOG_CHANNEL_ID) if rule.guild else None
        if not channel:
            return
        await self.automod_logger.log_automod_rule_create(channel, rule)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, rule):
        channel = rule.guild.get_channel(LOG_CHANNEL_ID) if rule.guild else None
        if not channel:
            return
        await self.automod_logger.log_automod_rule_update(channel, rule)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule):
        channel = rule.guild.get_channel(LOG_CHANNEL_ID) if rule.guild else None
        if not channel:
            return
        await self.automod_logger.log_automod_rule_delete(channel, rule)

    @commands.Cog.listener()
    async def on_automod_action(self, execution):
        guild = getattr(execution, 'guild', None)
        channel = guild.get_channel(LOG_CHANNEL_ID) if guild else None
        if not channel:
            return
        await self.automod_logger.log_automod_action(channel, execution)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.member_logger.log_member_join(channel, member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.member_logger.log_member_remove(channel, member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.member_logger.log_member_update(channel, before, after)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        log_channel = channel.guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return
        await self.channel_logger.log_pins_update(log_channel, last_pin)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.member_logger.log_member_ban(channel, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        await self.member_logger.log_member_unban(channel, user)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        # Получаем канал, где была реакция
        source_channel = guild.get_channel(payload.channel_id)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if not source_channel or not log_channel or not hasattr(source_channel, 'fetch_message'):
            return
        try:
            message = await source_channel.fetch_message(payload.message_id)
            user = guild.get_member(payload.user_id) or (await self.bot.fetch_user(payload.user_id))
            if user and not user.bot:
                await self.reaction_logger.log_reaction_add(log_channel, payload, message, user)
        except Exception as e:
            print(f"[Logger] Ошибка логгирования добавления реакции: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        source_channel = guild.get_channel(payload.channel_id)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if not source_channel or not log_channel or not hasattr(source_channel, 'fetch_message'):
            return
        try:
            message = await source_channel.fetch_message(payload.message_id)
            user = guild.get_member(payload.user_id) or (await self.bot.fetch_user(payload.user_id))
            if user and not user.bot:
                await self.reaction_logger.log_reaction_remove(log_channel, payload, message, user)
        except Exception as e:
            print(f"[Logger] Ошибка логгирования удаления реакции: {e}")

async def setup(bot):
    await bot.add_cog(Logger(bot)) 

