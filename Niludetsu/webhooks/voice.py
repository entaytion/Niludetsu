import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class VoiceLogger(BaseLogger):

    async def log_voice_join(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {channel.mention} (`{channel.id}`)\n"
            f"**{t('audit_log', 'field_category')}:** `{channel.category.name if channel.category else t('audit_log', 'none')}`\n"
            f"**{t('audit_log', 'field_members_in_channel')}:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.SUCCESS} {t('audit_log', 'voice_join_title')}",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_leave(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {channel.mention} (`{channel.id}`)\n"
            f"**{t('audit_log', 'field_category')}:** `{channel.category.name if channel.category else t('audit_log', 'none')}`\n"
            f"**{t('audit_log', 'field_members_in_channel')}:** `{len(channel.members)}/{channel.user_limit if channel.user_limit else '∞'}`"
        )
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} {t('audit_log', 'voice_leave_title')}",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_switch(self, log_channel: discord.TextChannel, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {before.mention if before else f'`{t("audit_log", "none")}`'} ➜ {after.mention if after else f'`{t("audit_log", "none")}`'}\n"
            f"**{t('audit_log', 'field_category')}:** `{before.category.name if before and before.category else t('audit_log', 'none')}` ➜ `{after.category.name if after and after.category else t('audit_log', 'none')}`"
        )
        fields = []
        if before and after:
            fields.append({
                "name": f"> {t('audit_log', 'field_voice_changes')}:",
                "value": (
                    f"**{t('audit_log', 'field_voice_old')}:** `{len(before.members)}/{before.user_limit if before.user_limit else '∞'}`\n"
                    f"**{t('audit_log', 'field_voice_new')}:** `{len(after.members)}/{after.user_limit if after.user_limit else '∞'}`"
                ),
                "inline": False,
            })
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} {t('audit_log', 'voice_switch_title')}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_move(self, log_channel: discord.TextChannel, member: discord.Member, before: discord.VoiceChannel, after: discord.VoiceChannel, moderator: discord.User = None):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {before.mention} ➜ {after.mention}"
        )
        if moderator:
            description += f"\n**{t('audit_log', 'moderator')}** {moderator.mention} (`{moderator.id}`)"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} {t('audit_log', 'voice_move_title')}",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_disconnect(self, log_channel: discord.TextChannel, member: discord.Member, channel: discord.VoiceChannel, moderator: discord.User = None):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {channel.mention} (`{channel.id}`)"
        )
        if moderator:
            description += f"\n**{t('audit_log', 'moderator')}** {moderator.mention} (`{moderator.id}`)"
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.ERROR} {t('audit_log', 'voice_disconnect_title')}",
            description=description,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )

    async def log_voice_state(self, log_channel: discord.TextChannel, member: discord.Member, changes: dict):
        t = _(guild_id=member.guild.id, bot=self.bot)
        STATE_LABELS = {
            'deaf': t('audit_log', 'voice_state_deaf'),
            'mute': t('audit_log', 'voice_state_mute'),
            'self_deaf': t('audit_log', 'voice_state_self_deaf'),
            'self_mute': t('audit_log', 'voice_state_self_mute'),
            'self_stream': t('audit_log', 'voice_state_stream'),
            'self_video': t('audit_log', 'voice_state_video'),
        }
        description = f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)"
        fields = []
        for change_type, (before, after) in changes.items():
            label = STATE_LABELS.get(change_type, change_type)
            fields.append({
                "name": f"> {t('audit_log', 'field_voice_changes')}:",
                "value": f"**{label}:** `{t('audit_log', 'on') if before else t('audit_log', 'off')}` ➜ `{t('audit_log', 'on') if after else t('audit_log', 'off')}`",
                "inline": False,
            })
        if not fields:
            return
        await self.webhooks.send_log(
            channel=log_channel,
            title=f"{Emojis.UNKNOWN} {t('audit_log', 'voice_state_title')}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=member.guild,
        )
