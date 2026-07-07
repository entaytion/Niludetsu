import discord
from Niludetsu import ModerationError, Embed, Emojis, config
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu.locale import _, DEFAULT_LOCALE

from typing import Optional

class ClearCog(commands.Cog):
    """Команда очистки сообщений в канале."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        aliases=["очистить", "purge"],
        description="Очистить сообщения в канале"
    )
    @app_commands.describe(
        amount="🔢 Количество сообщений для удаления (1-100)",
        target="👤 Пользователь, чьи сообщения нужно удалить (опционально)"
    )
    @moderationcommand(required_level=2, cooldown=60)
    async def clear(
        self,
        ctx: commands.Context,
        amount: str,
        target: Optional[discord.Member] = None
    ):
        t = _(ctx=ctx)
        is_interaction = ctx.interaction is not None

        if not target and not is_interaction:
            if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
                target = ctx.message.reference.resolved.author

        if not amount.isdigit():
            raise ModerationError(t("moderation", "clear_invalid_count"))

        num = int(amount)

        if num < 1:
            raise ModerationError(t("moderation", "clear_negative"))

        if num > 100:
            raise ModerationError(t("moderation", "clear_too_many"))

        bot_permissions = ctx.channel.permissions_for(ctx.guild.me)

        if not bot_permissions.manage_messages:
            raise ModerationError(t("moderation", "clear_no_perms_manage", channel=ctx.channel.mention))

        if not bot_permissions.read_message_history:
            raise ModerationError(t("moderation", "clear_no_perms_history", channel=ctx.channel.mention))

        if is_interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            try:
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        messages_to_delete = []

        history_limit = num if not target else min(500, num * 10)

        try:
            async for msg in ctx.channel.history(limit=history_limit):
                if target and msg.author != target:
                    continue
                messages_to_delete.append(msg)
                if len(messages_to_delete) >= num:
                    break

        except discord.Forbidden:
            raise ModerationError(t("moderation", "clear_no_perms_history_short"))
        except discord.HTTPException as e:
            raise ModerationError(t("moderation", "clear_fetch_error", error=str(e)))

        if not messages_to_delete:
            if target:
                raise ModerationError(t("moderation", "clear_no_messages_target", target=target.mention))
            raise ModerationError(t("moderation", "clear_no_messages"))

        try:
            await ctx.channel.delete_messages(messages_to_delete)
            deleted_count = len(messages_to_delete)

        except discord.Forbidden:
            raise ModerationError(t("moderation", "clear_no_delete_perms"))
        except discord.HTTPException as e:
            deleted_count = 0
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                    deleted_count += 1
                except:
                    pass

        if target:
            description = t("moderation", "clear_success_target", count=deleted_count, target=target.mention)
        else:
            description = t("moderation", "clear_success", count=deleted_count)

        result_embed = Embed.success(description=description)
        thumb_url = (target or ctx.author).display_avatar.url
        result_embed.set_thumbnail(url=thumb_url)

        if is_interaction:
            await ctx.interaction.followup.send(embed=result_embed, ephemeral=True)
        else:
            result_msg = await ctx.send(embed=result_embed)
            await result_msg.delete(delay=5.0)

        await self._log_clear_action(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=ctx.channel,
            deleted_count=deleted_count,
            target=target
        )

    async def _log_clear_action(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channel: discord.TextChannel,
        deleted_count: int,
        target: Optional[discord.Member] = None
    ) -> None:
        desc = (
            f"{DEFAULT_LOCALE.get('moderation', {}).get('clear_log_field_channel', '**Канал:** {channel}').format(channel=channel.mention)}\n"
            f"{DEFAULT_LOCALE.get('moderation', {}).get('clear_log_field_moderator', '**Модератор:** {moderator} ({mod_id})').format(moderator=moderator.mention, mod_id=moderator.id)}\n"
            f"{DEFAULT_LOCALE.get('moderation', {}).get('clear_log_field_deleted', '**Удалено сообщений:** {count}').format(count=deleted_count)}"
        )
        if target:
            desc += "\n" + DEFAULT_LOCALE.get('moderation', {}).get('clear_log_field_target', '**Цель:** {target} ({target_id})').format(target=target.mention, target_id=target.id)

        embed = Embed(
            title=DEFAULT_LOCALE.get("moderation", {}).get("clear_log_title", "Очистка сообщений"),
            description=desc,
            color=0xffa500
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        log_channel = None
        if config.NOTIFICATION_CHANNEL_ID:
            log_channel = guild.get_channel(int(config.NOTIFICATION_CHANNEL_ID))
        if not log_channel:
            log_channel = discord.utils.get(
                guild.text_channels,
                name__in=["mod-logs", "модерация", "logs"]
            )
        if log_channel:
            try:
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

async def setup(bot):
    """Загрузка расширения."""
    await bot.add_cog(ClearCog(bot))

