import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class MemberLogger(BaseLogger):

    async def log_member_join(self, channel: discord.TextChannel, member: discord.Member, inviter: discord.Member = None):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_user')}:** {member.mention} ({member.id})\n**{t('audit_log', 'field_account_created')}:** <t:{int(member.created_at.timestamp())}:R>"
        if inviter:
            description += f"\n**Пригласил:** {inviter.mention} ({inviter.id})"
        fields = []
        fields.append({"name": t('audit_log', 'field_roles'), "value": ", ".join([r.mention for r in member.roles if r.name != '@everyone']) or t('audit_log', 'none'), "inline": False})
        if member.premium_since:
            fields.append({"name": t('audit_log', 'field_booster'), "value": f"{t('audit_log', 'boost_from')} {member.premium_since.strftime('%d.%m.%Y %H:%M')}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'member_join_title')}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=channel.guild,
        )

    async def log_member_remove(self, channel: discord.TextChannel, member: discord.Member):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_user')}:** {member.mention} ({member.id})"
        if member.joined_at:
            description += f"\n**{t('audit_log', 'field_joined_at')}:** <t:{int(member.joined_at.timestamp())}:R>"

        action_type = t('audit_log', 'member_left')
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
                if entry.target and entry.target.id == member.id:
                    action_type = t('audit_log', 'member_kicked')
                    description += f"\n**{t('audit_log', 'moderator')}** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**{t('audit_log', 'reason')}** {entry.reason}"
                    break
        except Exception:
            pass

        fields = []
        roles = [r.mention for r in member.roles if r.name != '@everyone']
        if roles:
            fields.append({"name": t('audit_log', 'field_roles'), "value": ", ".join(roles), "inline": False})

        emoji = Emojis.ERROR if action_type == t('audit_log', 'member_kicked') else Emojis.ERROR
        await self.webhooks.send_log(
            channel=channel, title=f"{emoji} {t('audit_log', 'member_leave_title')} — {action_type}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=channel.guild,
        )

    async def log_member_update(self, channel: discord.TextChannel, before: discord.Member, after: discord.Member):
        t = _(guild_id=after.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_user')}:** {after.mention} ({after.id})"
        fields = []
        if before.display_name != after.display_name:
            fields.append({"name": t('audit_log', 'field_nickname'), "value": f"`{before.display_name}` ➜ `{after.display_name}`", "inline": False})
        if before.display_avatar != after.display_avatar:
            fields.append({"name": t('audit_log', 'field_avatar'), "value": t('audit_log', 'field_avatar_changed'), "inline": False})
        if set(before.roles) != set(after.roles):
            added = set(after.roles) - set(before.roles)
            removed = set(before.roles) - set(after.roles)
            if added:
                fields.append({"name": t('audit_log', 'added_roles'), "value": ", ".join([r.mention for r in added]), "inline": False})
            if removed:
                fields.append({"name": t('audit_log', 'removed_roles'), "value": ", ".join([r.mention for r in removed]), "inline": False})
        if before.premium_since != after.premium_since:
            fields.append({"name": t('audit_log', 'field_booster'), "value": f"`{before.premium_since}` ➜ `{after.premium_since}`", "inline": False})
        before_timeout = getattr(before, 'timed_out_until', None)
        after_timeout = getattr(after, 'timed_out_until', None)
        if before_timeout != after_timeout:
            if after_timeout and (not before_timeout or after_timeout > before_timeout):
                fields.append({"name": t('audit_log', 'field_timeout'), "value": t('audit_log', 'field_timeout_issued', ts=int(after_timeout.timestamp())), "inline": False})
            elif before_timeout and not after_timeout:
                fields.append({"name": t('audit_log', 'field_timeout'), "value": t('audit_log', 'field_timeout_removed'), "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=after.guild.get_channel(channel.id),
            title=f"{Emojis.UNKNOWN} {t('audit_log', 'member_update_title')}",
            description=description, fields=fields,
            thumbnail_url=after.display_avatar.url, guild=after.guild,
        )

    async def log_member_ban(self, channel: discord.TextChannel, user: discord.User):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_user')}:** {user.mention} ({user.id})"
        try:
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == user.id:
                    description += f"\n**{t('audit_log', 'moderator')}** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**{t('audit_log', 'reason')}** {entry.reason}"
                    break
        except Exception:
            pass
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'member_ban_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild,
        )

    async def log_member_unban(self, channel: discord.TextChannel, user: discord.User):
        t = _(guild_id=channel.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_user')}:** {user.mention} ({user.id})"
        try:
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.unban):
                if entry.target and entry.target.id == user.id:
                    description += f"\n**{t('audit_log', 'moderator')}** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**{t('audit_log', 'reason')}** {entry.reason}"
                    break
        except Exception:
            pass
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'member_unban_title')}",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild,
        )
