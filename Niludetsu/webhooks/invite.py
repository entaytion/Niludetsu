import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class InviteLogger(BaseLogger):

    async def log_invite_create(self, channel: discord.TextChannel, invite: discord.Invite):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_invite_code')}:** `{invite.code}`\n"
            f"**{t('audit_log', 'field_channel')}:** {invite.channel.mention if invite.channel else t('audit_log', 'unknown')}\n"
            f"**{t('audit_log', 'field_invite_inviter')}:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        )
        fields = [
            {"name": t('audit_log', 'field_invite_max_uses'), "value": f"{invite.max_uses if invite.max_uses else '∞'}", "inline": True},
            {"name": t('audit_log', 'field_invite_temporary'), "value": f"{t('audit_log', 'yes') if invite.temporary else t('audit_log', 'no')}", "inline": True},
            {"name": t('audit_log', 'field_invite_expires'), "value": f"<t:{int(invite.expires_at.timestamp())}:F>" if invite.expires_at else '∞', "inline": True},
            {"name": t('audit_log', 'field_invite_link'), "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False},
        ]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'invite_create_title')}",
            description=description, fields=fields,
            thumbnail_url=invite.inviter.display_avatar.url if invite.inviter else None,
            guild=channel.guild,
        )

    async def log_invite_delete(self, channel: discord.TextChannel, invite: discord.Invite):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_invite_code')}:** `{invite.code}`\n"
            f"**{t('audit_log', 'field_channel')}:** {invite.channel.mention if invite.channel else t('audit_log', 'unknown')}\n"
            f"**{t('audit_log', 'field_invite_inviter')}:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        )
        fields = [
            {"name": t('audit_log', 'field_invite_uses'), "value": f"{invite.uses if invite.uses else '0'}", "inline": True},
            {"name": t('audit_log', 'field_invite_link'), "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False},
        ]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'invite_delete_title')}",
            description=description, fields=fields,
            thumbnail_url=invite.inviter.display_avatar.url if invite.inviter else None,
            guild=channel.guild,
        )

    async def log_invite_post(self, channel: discord.TextChannel, invite: discord.Invite, message: discord.Message):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_author')}:** {message.author.mention} ({message.author.id})\n"
            f"**{t('audit_log', 'field_channel')}:** {message.channel.mention}\n"
        )
        if invite.guild:
            description += f"**{t('audit_log', 'field_invite_target')}:** `{invite.guild.name}`\n"
        description += f"**{t('audit_log', 'field_invite_creator')}:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        fields = [{"name": t('audit_log', 'field_invite_link'), "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'invite_post_title')}",
            description=description, fields=fields,
            thumbnail_url=message.author.display_avatar.url, guild=channel.guild,
        )

    async def log_invite_use(self, channel: discord.TextChannel, invite: discord.Invite, user: discord.Member):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {user.mention} ({user.id})\n"
            f"**{t('audit_log', 'field_invite_code')}:** `{invite.code}`\n"
        )
        if invite.inviter:
            description += f"**{t('audit_log', 'field_invite_creator')}:** {invite.inviter.mention} ({invite.inviter.id})\n"
        if invite.channel:
            description += f"**{t('audit_log', 'field_invite_channel')}:** {invite.channel.mention}\n"
        fields = [{"name": t('audit_log', 'field_invite_uses'), "value": f"{invite.uses}/{invite.max_uses if invite.max_uses else '∞'}", "inline": True}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'invite_use_title')}",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )
