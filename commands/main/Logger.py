from Niludetsu import Webhooks, config
import asyncio, time, discord
from discord.ext import commands

class Logger(commands.Cog):
    """Централизованный логгер с ленивой загрузкой модулей для экономии RAM."""

    def __init__(self, bot):
        self.bot = bot
        self._webhooks = Webhooks(bot)
        self._loggers = {}
        self._message_cache = {}
        self._webhook_cache = {}
        self._webhook_cooldown = {}

    def _get_logger(self, name):
        """Динамически импортирует и возвращает нужный логгер."""
        if name not in self._loggers:
            try:
                module = __import__(f"Niludetsu.webhooks.{name}", fromlist=[f"{name.capitalize()}Logger"])
                logger_cls = getattr(module, f"{name.capitalize()}Logger")
                self._loggers[name] = logger_cls(self.bot, self._webhooks)
            except Exception as e:
                print(f"Ошибка загрузки логгера {name}: {e}")
                return None
        return self._loggers[name]

    def _get_log_channel(self, guild):
        return guild.get_channel(config.LOG_CHANNEL_ID) if guild else None

    async def _get_cached_message(self, channel, message_id):
        now = time.time()
        if message_id in self._message_cache:
            m, ts = self._message_cache[message_id]
            if now - ts < 60: return m
        try:
            msg = await channel.fetch_message(message_id)
            self._message_cache[message_id] = (msg, now)
            if len(self._message_cache) > 100:
                for k in list(self._message_cache.keys())[:50]: self._message_cache.pop(k)
            return msg
        except: return None

    # --- Групповые слушатели ---

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, b, a):
        ch = self._get_log_channel(guild)
        log = self._get_logger("emoji")
        if not ch or not log: return
        b_ids = {e.id for e in b}
        a_ids = {e.id for e in a}
        for e in a:
            if e.id not in b_ids: await log.log_emoji_create(ch, e)
        for e in b:
            if e.id not in a_ids: await log.log_emoji_delete(ch, e)
        b_map = {e.id: e for e in b}
        for ex in a:
            old = b_map.get(ex.id)
            if old and (old.name != ex.name or set(old.roles) != set(ex.roles)):
                await log.log_emoji_update(ch, old, ex)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, b, a):
        ch = self._get_log_channel(guild)
        log = self._get_logger("sticker")
        if not ch or not log: return
        b_ids = {s.id for s in b}
        a_ids = {s.id for s in a}
        for s in a:
            if s.id not in b_ids: await log.log_sticker_create(ch, s)
        for s in b:
            if s.id not in a_ids: await log.log_sticker_delete(ch, s)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, b, a):
        ch = self._get_log_channel(member.guild)
        log = self._get_logger("voice")
        if not ch or not log: return
        if b.channel != a.channel:
            if not b.channel: await log.log_voice_join(ch, member, a.channel)
            elif not a.channel: await log.log_voice_leave(ch, member, b.channel)
            else: await log.log_voice_switch(ch, member, b.channel, a.channel)
        else:
            diff = {attr: (getattr(b, attr), getattr(a, attr)) for attr in ("mute", "deaf", "self_stream", "self_video") if getattr(b, attr) != getattr(a, attr)}
            if diff: await log.log_voice_state(ch, member, diff)

    @commands.Cog.listener()
    async def on_message_delete(self, m):
        if m.guild and not m.author.bot:
            ch = self._get_log_channel(m.guild)
            log = self._get_logger("message")
            if ch and log: await log.log_message_delete(ch, m)

    @commands.Cog.listener()
    async def on_message_edit(self, b, a):
        if b.guild and not b.author.bot and b.content != a.content:
            ch = self._get_log_channel(b.guild)
            log = self._get_logger("message")
            if ch and log: await log.log_message_edit(ch, b, a)

    @commands.Cog.listener()
    async def on_member_join(self, m):
        ch = self._get_log_channel(m.guild)
        log = self._get_logger("member")
        if ch and log: await log.log_member_join(ch, m)

    @commands.Cog.listener()
    async def on_member_remove(self, m):
        ch = self._get_log_channel(m.guild)
        log = self._get_logger("member")
        if ch and log: await log.log_member_remove(ch, m)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, c):
        ch = self._get_log_channel(c.guild)
        log = self._get_logger("channel")
        if ch and log: await log.log_channel_create(ch, c)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, c):
        ch = self._get_log_channel(c.guild)
        log = self._get_logger("channel")
        if ch and log: await log.log_channel_delete(ch, c)

    @commands.Cog.listener()
    async def on_guild_role_create(self, r):
        ch = self._get_log_channel(r.guild)
        log = self._get_logger("role")
        if ch and log: await log.log_role_create(ch, r)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, r):
        ch = self._get_log_channel(r.guild)
        log = self._get_logger("role")
        if ch and log: await log.log_role_delete(ch, r)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, p):
        guild = self.bot.get_guild(p.guild_id)
        log_ch = self._get_log_channel(guild)
        log = self._get_logger("reaction")
        if not guild or not log_ch or not log: return
        msg = await self._get_cached_message(guild.get_channel(p.channel_id), p.message_id)
        user = guild.get_member(p.user_id) or await self.bot.fetch_user(p.user_id)
        if msg and user and not user.bot:
            await log.log_reaction_add(log_ch, p, msg, user)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        log_ch = self._get_log_channel(channel.guild)
        log = self._get_logger("webhook")
        if not log_ch or not log: return
        cid = channel.id
        now = time.time()
        if now - self._webhook_cooldown.get(cid, 0) < 2.0: return
        self._webhook_cooldown[cid] = now
        await asyncio.sleep(0.5)
        before = self._webhook_cache.get(cid, [])
        after = await channel.webhooks()
        self._webhook_cache[cid] = list(after)
        if not before: return
        b_ids, a_ids = {w.id for w in before}, {w.id for w in after}
        for wid in a_ids - b_ids: await log.log_webhook_create(log_ch, channel, next(w for w in after if w.id == wid))
        for wid in b_ids - a_ids: await log.log_webhook_delete(log_ch, channel, next(w for w in before if w.id == wid))

async def setup(bot): await bot.add_cog(Logger(bot))
