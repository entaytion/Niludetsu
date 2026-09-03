import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, Embed
from Niludetsu.moderation.system.lock import LockSystem as NiludetsuLockSystem
from Niludetsu.locale import _

class LockSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.lock_system = NiludetsuLockSystem(bot)
        self.locked_messages = {}

    @commands.hybrid_command(
        name="lock",
        description="Закрыть канал(ы) для отправки сообщений"
    )
    @app_commands.describe(
        channel="#️⃣ Канал для блокировки (по умолчанию — текущий)",
        reason="💬 Причина блокировки"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def lock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        *,
        reason: str = None
    ):
        t = _(ctx=ctx)
        is_interaction = getattr(ctx, 'interaction', None) is not None
        lock_all = False

        if is_interaction:
            if reason is None:
                reason = t("moderation", "reason_default")
            if channel is None:
                channel = ctx.channel
        else:
            content = ctx.message.content.partition(' ')[2].strip()
            if '--all' in content:
                lock_all = True
                content = content.replace('--all', '').strip()
            if channel is None and not lock_all:
                channel = ctx.channel
            if reason is None:
                reason = content if content else t("moderation", "reason_default")

        lock_ids = await self.lock_system.lock_channel(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=channel,
            reason=reason,
            for_all=lock_all
        )

        if lock_ids:
            self.locked_messages.setdefault(ctx.guild.id, []).extend(lock_ids)

        if lock_all:
            description = t("moderation", "lock_success_all", count=len(lock_ids))
        else:
            description = t("moderation", "lock_success_one", channel=channel.mention)

        embed = Embed.success(description=description)
        await send(ctx, embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="unlock",
        description="Открыть канал(ы) для отправки сообщений"
    )
    @app_commands.describe(
        channel="#️⃣ Канал для разблокировки (по умолчанию — текущий)",
        reason="💬 Причина разблокировки"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def unlock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        *,
        reason: str = None
    ):
        t = _(ctx=ctx)
        is_interaction = getattr(ctx, 'interaction', None) is not None
        unlock_all = False

        if is_interaction:
            if reason is None:
                reason = t("moderation", "reason_default")
            if channel is None:
                channel = ctx.channel
        else:
            content = ctx.message.content.partition(' ')[2].strip()
            if '--all' in content:
                unlock_all = True
                content = content.replace('--all', '').strip()
            if channel is None and not unlock_all:
                channel = ctx.channel
            if reason is None:
                reason = content if content else t("moderation", "reason_default")

        lock_ids = self.locked_messages.get(ctx.guild.id, [])

        await self.lock_system.unlock_channel(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=channel,
            reason=reason,
            for_all=unlock_all,
            lock_message_ids=lock_ids
        )

        self.locked_messages[ctx.guild.id] = []

        if unlock_all:
            description = t("moderation", "unlock_success_all")
        else:
            description = t("moderation", "unlock_success_one", channel=channel.mention)

        embed = Embed.success(description=description)
        await send(ctx, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LockSystem(bot))

