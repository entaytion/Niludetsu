import asyncio
import time

import discord
from discord.ext import commands

from Niludetsu.config import LOG_CHANNEL_ID
from Niludetsu.development.Webhooks import Webhooks
from Niludetsu.webhooks.application import ApplicationLogger
from Niludetsu.webhooks.automod import AutoModLogger
from Niludetsu.webhooks.channel import ChannelLogger
from Niludetsu.webhooks.emoji import EmojiLogger
from Niludetsu.webhooks.event import EventLogger
from Niludetsu.webhooks.invite import InviteLogger
from Niludetsu.webhooks.member import MemberLogger
from Niludetsu.webhooks.message import MessageLogger
from Niludetsu.webhooks.poll import PollLogger
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
    Один общий Webhooks инстанс на все логгеры (единый кеш вебхуков).
    """

    def __init__(self, bot):
        self.bot = bot
        # Один инстанс Webhooks на всех — единый кеш, без дублей
        self._webhooks = Webhooks(bot)
        self.emoji_logger = EmojiLogger(bot, self._webhooks)
        self.sticker_logger = StickerLogger(bot, self._webhooks)
        self.webhook_logger = WebhookLogger(bot, self._webhooks)
        self.voice_logger = VoiceLogger(bot, self._webhooks)
        self.thread_logger = ThreadLogger(bot, self._webhooks)
        self.stage_logger = StageLogger(bot, self._webhooks)
        self.soundboard_logger = SoundboardLogger(bot, self._webhooks)
        self.server_logger = ServerLogger(bot, self._webhooks)
        self.role_logger = RoleLogger(bot, self._webhooks)
        self.message_logger = MessageLogger(bot, self._webhooks)
        self.invite_logger = InviteLogger(bot, self._webhooks)
        self.event_logger = EventLogger(bot, self._webhooks)
        self.application_logger = ApplicationLogger(bot, self._webhooks)
        self.channel_logger = ChannelLogger(bot, self._webhooks)
        self.automod_logger = AutoModLogger(bot, self._webhooks)
        self.member_logger = MemberLogger(bot, self._webhooks)
        self.reaction_logger = ReactionLogger(bot, self._webhooks)
        self.poll_logger = PollLogger(bot, self._webhooks)
        # Кеш для вебхуков и реакций
        self._webhook_cache = {}
        self._webhook_update_cooldown = {}
        self._message_cache = {}  # message_id: (message, timestamp) — LRU для реакций

    def _get_log_channel(self, guild: discord.Guild):
        """Хелпер: получить канал логов."""
        return guild.get_channel(LOG_CHANNEL_ID) if guild else None

    async def _get_cached_message(self, channel, message_id):
        """LRU кеш для fetch_message — чтобы не спамить API при реакциях."""
        now = time.time()
        cached = self._message_cache.get(message_id)
        if cached and (now - cached[1]) < 60:
            return cached[0]
        try:
            msg = await channel.fetch_message(message_id)
            self._message_cache[message_id] = (msg, now)
            # Очищаем старые записи (>100)
            if len(self._message_cache) > 100:
                oldest = sorted(
                    self._message_cache, key=lambda k: self._message_cache[k][1]
                )
                for k in oldest[:50]:
                    self._message_cache.pop(k, None)
            return msg
        except Exception:
            return None

    # ═══════════════════════════════════════════
    # EMOJIS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        before_ids = {e.id for e in before}
        after_ids = {e.id for e in after}
        # Добавленные
        for emoji in (e for e in after if e.id not in before_ids):
            await self.emoji_logger.log_emoji_create(channel, emoji)
        # Удалённые
        for emoji in (e for e in before if e.id not in after_ids):
            await self.emoji_logger.log_emoji_delete(channel, emoji)
        # Изменённые (имя или роли)
        before_map = {e.id: e for e in before}
        for a in after:
            b = before_map.get(a.id)
            if b and (b.name != a.name or set(b.roles or []) != set(a.roles or [])):
                await self.emoji_logger.log_emoji_update(channel, b, a)

    # ═══════════════════════════════════════════
    # STICKERS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        before_ids = {s.id for s in before}
        after_ids = {s.id for s in after}
        for sticker in (s for s in after if s.id not in before_ids):
            await self.sticker_logger.log_sticker_create(channel, sticker)
        for sticker in (s for s in before if s.id not in after_ids):
            await self.sticker_logger.log_sticker_delete(channel, sticker)
        before_map = {s.id: s for s in before}
        for a in after:
            b = before_map.get(a.id)
            if b and (
                getattr(b, "name", None) != getattr(a, "name", None)
                or getattr(b, "description", None) != getattr(a, "description", None)
                or getattr(b, "emoji", None) != getattr(a, "emoji", None)
            ):
                await self.sticker_logger.log_sticker_update(channel, b, a)

    # ═══════════════════════════════════════════
    # WEBHOOKS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        log_channel = self._get_log_channel(channel.guild)
        if not log_channel:
            return

        channel_id = channel.id
        current_time = time.time()

        # Cooldown — игнорируем события в течение 1 секунды
        if channel_id in self._webhook_update_cooldown:
            if current_time - self._webhook_update_cooldown[channel_id] < 1.0:
                return
        self._webhook_update_cooldown[channel_id] = current_time

        await asyncio.sleep(0.3)  # Задержка для race conditions

        before = self._webhook_cache.get(channel_id, [])
        after = await channel.webhooks()

        # Первый вызов — инициализация кеша
        if not before and channel_id not in self._webhook_cache:
            self._webhook_cache[channel_id] = list(after)
            return

        before_ids = {w.id for w in before}
        after_ids = {w.id for w in after}

        for add_id in after_ids - before_ids:
            webhook = next(w for w in after if w.id == add_id)
            await self.webhook_logger.log_webhook_create(log_channel, channel, webhook)

        for rem_id in before_ids - after_ids:
            webhook = next(w for w in before if w.id == rem_id)
            await self.webhook_logger.log_webhook_delete(log_channel, channel, webhook)

        for com_id in before_ids & after_ids:
            bw = next(w for w in before if w.id == com_id)
            aw = next(w for w in after if w.id == com_id)
            if bw.name != aw.name or bw.avatar != aw.avatar:
                await self.webhook_logger.log_webhook_update(
                    log_channel, channel, bw, aw
                )

        self._webhook_cache[channel_id] = list(after)

        # Периодическая очистка cooldown
        if not hasattr(self, "_cleanup_task") or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_webhook_cooldowns())

    async def _cleanup_webhook_cooldowns(self):
        await asyncio.sleep(60)
        current_time = time.time()
        to_remove = [
            cid
            for cid, ts in self._webhook_update_cooldown.items()
            if current_time - ts > 30
        ]
        for cid in to_remove:
            self._webhook_update_cooldown.pop(cid, None)

    # ═══════════════════════════════════════════
    # VOICE
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        log_channel = self._get_log_channel(member.guild)
        if not log_channel:
            return

        if before.channel != after.channel:
            if not before.channel and after.channel:
                await self.voice_logger.log_voice_join(
                    log_channel, member, after.channel
                )
            elif before.channel and not after.channel:
                # Проверяем — kick или сам ушел
                moderator = None
                try:
                    async for entry in member.guild.audit_logs(
                        limit=3, action=discord.AuditLogAction.member_disconnect
                    ):
                        if entry.target and entry.target.id == member.id:
                            moderator = entry.user
                            break
                except Exception:
                    pass
                if moderator and moderator.id != member.id:
                    await self.voice_logger.log_voice_disconnect(
                        log_channel, member, before.channel, moderator
                    )
                else:
                    await self.voice_logger.log_voice_leave(
                        log_channel, member, before.channel
                    )
            elif before.channel and after.channel and before.channel != after.channel:
                # Проверяем — move модератором или сам перешел
                moderator = None
                try:
                    async for entry in member.guild.audit_logs(
                        limit=3, action=discord.AuditLogAction.member_move
                    ):
                        if entry.target and entry.target.id == member.id:
                            moderator = entry.user
                            break
                except Exception:
                    pass
                if moderator and moderator.id != member.id:
                    await self.voice_logger.log_voice_move(
                        log_channel, member, before.channel, after.channel, moderator
                    )
                else:
                    await self.voice_logger.log_voice_switch(
                        log_channel, member, before.channel, after.channel
                    )
        else:
            # Изменения состояния (mute, deaf, stream, video)
            changes = {}
            for attr in (
                "deaf",
                "mute",
                "self_deaf",
                "self_mute",
                "self_stream",
                "self_video",
            ):
                b_val = getattr(before, attr)
                a_val = getattr(after, attr)
                if b_val != a_val:
                    changes[attr] = (b_val, a_val)
            if changes:
                await self.voice_logger.log_voice_state(log_channel, member, changes)

            # Stage speaker/audience detection — через suppress
            channel = after.channel or before.channel
            if channel and isinstance(channel, discord.StageChannel):
                # suppress = True → слушатель, suppress = False → спикер
                if before.suppress and not after.suppress:
                    # Стал спикером
                    await self.stage_logger.log_stage_speaker_join(
                        log_channel, member, channel
                    )
                elif not before.suppress and after.suppress:
                    # Перешел в слушатели
                    await self.stage_logger.log_stage_speaker_leave(
                        log_channel, member, channel
                    )
                # Request to speak
                if not getattr(before, "requested_to_speak_at", None) and getattr(
                    after, "requested_to_speak_at", None
                ):
                    await self.stage_logger.log_stage_request_to_speak(
                        log_channel, member, channel
                    )

    # ═══════════════════════════════════════════
    # THREADS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        log_channel = self._get_log_channel(thread.guild)
        if not log_channel:
            return
        await self.thread_logger.log_thread_create(log_channel, thread)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        log_channel = self._get_log_channel(after.guild)
        if not log_channel:
            return
        await self.thread_logger.log_thread_update(log_channel, before, after)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        log_channel = self._get_log_channel(thread.guild)
        if not log_channel:
            return
        await self.thread_logger.log_thread_delete(log_channel, thread)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member):
        thread = member.thread
        if not thread or not thread.guild:
            return
        log_channel = self._get_log_channel(thread.guild)
        if not log_channel:
            return
        await self.thread_logger.log_thread_member_join(log_channel, member)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member):
        thread = member.thread
        if not thread or not thread.guild:
            return
        log_channel = self._get_log_channel(thread.guild)
        if not log_channel:
            return
        await self.thread_logger.log_thread_member_remove(log_channel, member)

    # ═══════════════════════════════════════════
    # STAGE
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance):
        log_channel = self._get_log_channel(stage_instance.guild)
        if not log_channel:
            return
        await self.stage_logger.log_stage_create(log_channel, stage_instance)

    @commands.Cog.listener()
    async def on_stage_instance_update(self, before, after):
        log_channel = self._get_log_channel(after.guild)
        if not log_channel:
            return
        await self.stage_logger.log_stage_update(log_channel, before, after)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance):
        log_channel = self._get_log_channel(stage_instance.guild)
        if not log_channel:
            return
        await self.stage_logger.log_stage_delete(log_channel, stage_instance)

    # Спикеры и слушатели трибуны — ловим через voice_state_update
    # (discord.py не имеет отдельных событий для stage speakers,
    #  определяем по suppress/request_to_speak_at)

    # ═══════════════════════════════════════════
    # SOUNDBOARD
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_soundboard_sound_create(self, sound):
        log_channel = self._get_log_channel(sound.guild)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_create(log_channel, sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        log_channel = self._get_log_channel(sound.guild)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_delete(log_channel, sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_update(self, before, after):
        log_channel = self._get_log_channel(after.guild)
        if not log_channel:
            return
        await self.soundboard_logger.log_sound_update(log_channel, before, after)

    # ═══════════════════════════════════════════
    # SERVER
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.server_logger.log_guild_join(channel, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.server_logger.log_guild_remove(channel, guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        channel = self._get_log_channel(after)
        if not channel:
            return
        await self.server_logger.log_guild_update(channel, before, after)

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.server_logger.log_guild_integrations_update(channel, guild)

    # ═══════════════════════════════════════════
    # ROLES
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        channel = self._get_log_channel(role.guild)
        if not channel:
            return
        await self.role_logger.log_role_create(channel, role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        channel = self._get_log_channel(role.guild)
        if not channel:
            return
        await self.role_logger.log_role_delete(channel, role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        channel = self._get_log_channel(after.guild)
        if not channel:
            return
        await self.role_logger.log_role_update(channel, before, after)

    # ═══════════════════════════════════════════
    # MESSAGES
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None or message.author.bot:
            return
        channel = self._get_log_channel(message.guild)
        if not channel:
            return
        await self.message_logger.log_message_delete(channel, message)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
        guild = messages[0].guild
        if not guild:
            return
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.message_logger.log_message_bulk_delete(channel, messages)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None or before.author.bot:
            return
        channel = self._get_log_channel(before.guild)
        if not channel:
            return
        await self.message_logger.log_message_edit(channel, before, after)

    # ═══════════════════════════════════════════
    # INVITES
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        channel = (
            self._get_log_channel(invite.channel.guild)
            if invite.channel and invite.channel.guild
            else None
        )
        if not channel:
            return
        await self.invite_logger.log_invite_create(channel, invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        channel = (
            self._get_log_channel(invite.channel.guild)
            if invite.channel and invite.channel.guild
            else None
        )
        if not channel:
            return
        await self.invite_logger.log_invite_delete(channel, invite)

    # ═══════════════════════════════════════════
    # SCHEDULED EVENTS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        channel = self._get_log_channel(event.guild)
        if not channel:
            return
        await self.event_logger.log_scheduled_event_create(channel, event)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        channel = self._get_log_channel(event.guild)
        if not channel:
            return
        await self.event_logger.log_scheduled_event_delete(channel, event)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before, after):
        channel = self._get_log_channel(after.guild)
        if not channel:
            return
        await self.event_logger.log_scheduled_event_update(channel, before, after)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event, user):
        channel = self._get_log_channel(event.guild)
        if not channel:
            return
        await self.event_logger.log_scheduled_event_add(channel, event, user)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event, user):
        channel = self._get_log_channel(event.guild)
        if not channel:
            return
        await self.event_logger.log_scheduled_event_remove(channel, event, user)

    # ═══════════════════════════════════════════
    # INTEGRATIONS / APPLICATIONS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_integration_create(self, integration):
        channel = self._get_log_channel(integration.guild)
        if not channel:
            return
        await self.application_logger.log_app_add(channel, integration)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration):
        channel = self._get_log_channel(integration.guild)
        if not channel:
            return
        await self.application_logger.log_app_remove(channel, integration)

    @commands.Cog.listener()
    async def on_integration_update(self, before, after):
        channel = self._get_log_channel(after.guild)
        if not channel:
            return
        await self.application_logger.log_app_update(channel, before, after)

    # ═══════════════════════════════════════════
    # CHANNELS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = self._get_log_channel(channel.guild)
        if not log_channel:
            return
        await self.channel_logger.log_channel_create(log_channel, channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = self._get_log_channel(channel.guild)
        if not log_channel:
            return
        await self.channel_logger.log_channel_delete(log_channel, channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        log_channel = self._get_log_channel(after.guild)
        if not log_channel:
            return

        # Канал сам определяет, есть ли реальные изменения
        await self.channel_logger.log_channel_update(log_channel, before, after)

        # Сравниваем права доступа (overwrites)
        before_overwrites = {k: v for k, v in before.overwrites.items()}
        after_overwrites = {k: v for k, v in after.overwrites.items()}
        changes = []
        for target, after_ow in after_overwrites.items():
            before_ow = before_overwrites.get(target)
            if before_ow != after_ow:
                perms_diff = {}
                for perm in dir(after_ow):
                    if perm.startswith("_") or not isinstance(
                        getattr(after_ow, perm, None), (bool, type(None))
                    ):
                        continue
                    before_val = getattr(before_ow, perm, None) if before_ow else None
                    after_val = getattr(after_ow, perm, None)
                    if before_val != after_val:
                        perms_diff[perm] = {"before": before_val, "after": after_val}
                if perms_diff:
                    changes.append({"role": target, "permissions": perms_diff})
        if changes:
            moderator = after.guild.me  # fallback
            try:
                async for entry in after.guild.audit_logs(
                    limit=1, action=discord.AuditLogAction.overwrite_update
                ):
                    moderator = (
                        entry.user
                        if isinstance(entry.user, discord.Member)
                        else after.guild.get_member(entry.user.id) or after.guild.me
                    )
                    break
            except Exception:
                pass
            await self.channel_logger.log_permissions_update(
                log_channel, after, moderator, changes
            )

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        log_channel = self._get_log_channel(channel.guild)
        if not log_channel:
            return
        await self.channel_logger.log_pins_update(log_channel, last_pin)

    # ═══════════════════════════════════════════
    # AUTOMOD
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule):
        channel = self._get_log_channel(rule.guild)
        if not channel:
            return
        await self.automod_logger.log_automod_rule_create(channel, rule)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, rule):
        channel = self._get_log_channel(rule.guild)
        if not channel:
            return
        await self.automod_logger.log_automod_rule_update(channel, rule)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule):
        channel = self._get_log_channel(rule.guild)
        if not channel:
            return
        await self.automod_logger.log_automod_rule_delete(channel, rule)

    @commands.Cog.listener()
    async def on_automod_action(self, execution):
        guild = getattr(execution, "guild", None)
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.automod_logger.log_automod_action(channel, execution)

    # ═══════════════════════════════════════════
    # MEMBERS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self._get_log_channel(member.guild)
        if not channel:
            return
        await self.member_logger.log_member_join(channel, member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self._get_log_channel(member.guild)
        if not channel:
            return
        await self.member_logger.log_member_remove(channel, member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = self._get_log_channel(after.guild)
        if not channel:
            return
        await self.member_logger.log_member_update(channel, before, after)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.member_logger.log_member_ban(channel, user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = self._get_log_channel(guild)
        if not channel:
            return
        await self.member_logger.log_member_unban(channel, user)

    # ═══════════════════════════════════════════
    # REACTIONS (с кешем + clear/clear_emoji)
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        source_channel = guild.get_channel(payload.channel_id)
        log_channel = self._get_log_channel(guild)
        if (
            not source_channel
            or not log_channel
            or not hasattr(source_channel, "fetch_message")
        ):
            return
        try:
            message = await self._get_cached_message(source_channel, payload.message_id)
            if not message:
                return
            user = guild.get_member(payload.user_id) or (
                await self.bot.fetch_user(payload.user_id)
            )
            if user and not user.bot:
                await self.reaction_logger.log_reaction_add(
                    log_channel, payload, message, user
                )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        source_channel = guild.get_channel(payload.channel_id)
        log_channel = self._get_log_channel(guild)
        if (
            not source_channel
            or not log_channel
            or not hasattr(source_channel, "fetch_message")
        ):
            return
        try:
            message = await self._get_cached_message(source_channel, payload.message_id)
            if not message:
                return
            user = guild.get_member(payload.user_id) or (
                await self.bot.fetch_user(payload.user_id)
            )
            if user and not user.bot:
                await self.reaction_logger.log_reaction_remove(
                    log_channel, payload, message, user
                )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        """Sapphire: очистка всех реакций."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        await self.reaction_logger.log_reaction_clear(log_channel, payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        """Sapphire: очистка реакций конкретного эмодзи."""
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        await self.reaction_logger.log_reaction_clear_emoji(log_channel, payload)

    """
    # ═══════════════════════════════════════════
    # USER UPDATE (Sapphire: username/avatar changes)
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        # Логирование глобальных изменений пользователя (username, avatar).
        changes = []
        if before.name != after.name:
            changes.append(f"**Username:** `{before.name}` → `{after.name}`")
        
        # Это я не знаю нахуя, уже нету дискриминаторов.
        if before.discriminator != after.discriminator:
            changes.append(f"**Дискриминатор:** `{before.discriminator}` → `{after.discriminator}`")
            
        if before.avatar != after.avatar:
            before_avatar = before.avatar.url if before.avatar else None
            after_avatar = after.avatar.url if after.avatar else None
            changes.append(f"**Аватар:** `{before_avatar}` → `{after_avatar}`")

        if before.banner != after.banner:
            before_banner = before.banner.url if before.banner else None
            after_banner = after.banner.url if after.banner else None
            changes.append(f"**Баннер:** `{before_banner}` → `{after_banner}`")

        if before.global_name != after.global_name:
            changes.append(
                f"**Отображаемое имя:** `{before.global_name or 'Нет'}` → `{after.global_name or 'Нет'}`"
            )
        if not changes:
            return
        for guild in self.bot.guilds:
            member = guild.get_member(after.id)
            if not member:
                continue
            log_channel = self._get_log_channel(guild)
            if not log_channel:
                continue
            from Niludetsu import Emojis

            description = f"**Пользователь:** {after.mention} ({after.id})"
            fields = [
                {"name": "Изменение", "value": c, "inline": False} for c in changes
            ]
            await self._webhooks.send_log(
                channel=log_channel,
                title=f"{Emojis.UNKNOWN} Пользователь: обновлён",
                description=description,
                fields=fields,
                thumbnail_url=after.display_avatar.url,
                guild=guild,
            )
            break  # Логируем только в первую подходящую гильдию
    """

    # ═══════════════════════════════════════════
    # APP COMMAND PERMISSIONS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_raw_app_command_permissions_update(self, payload):
        """Логирует обновление прав доступа к slash-командам."""
        guild = (
            self.bot.get_guild(payload.guild_id)
            if hasattr(payload, "guild_id")
            else None
        )
        if not guild:
            return
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        try:
            await self.application_logger.log_app_permission_update(
                log_channel, payload
            )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    # POLLS
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_raw_poll_vote_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        await self.poll_logger.log_poll_vote_add(log_channel, payload)

    @commands.Cog.listener()
    async def on_raw_poll_vote_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if not guild:
            return
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        await self.poll_logger.log_poll_vote_remove(log_channel, payload)

    # ═══════════════════════════════════════════
    # MESSAGE PUBLISH (CROSSPOST)
    # ═══════════════════════════════════════════
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        """Ловим publish (crosspost) — когда flags добавляет CROSSPOSTED."""
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        data = payload.data or {}
        flags = data.get("flags", 0)
        # CROSSPOSTED flag = 1 << 0 = 1
        if not (flags & 1):
            return

        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return

        # Получаем сообщение
        try:
            source_channel = guild.get_channel(payload.channel_id)
            if source_channel and hasattr(source_channel, "fetch_message"):
                message = await source_channel.fetch_message(payload.message_id)
                if message and not message.author.bot:
                    await self.message_logger.log_message_publish(log_channel, message)
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(Logger(bot))
