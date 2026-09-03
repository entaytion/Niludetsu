import discord
from ..tools.Emojis import Emojis
from Niludetsu.locale import _

from Niludetsu.webhooks.base import BaseLogger

class StageLogger(BaseLogger):

    async def log_stage_create(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        t = _(guild_id=stage_instance.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_id')}:** `{stage_instance.id}`\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
            f"**{t('audit_log', 'field_stage_topic')}:** `{stage_instance.topic}`\n"
            f"**{t('audit_log', 'field_stage_privacy')}:** `{stage_instance.privacy_level.name}`\n"
            f"**{t('audit_log', 'field_stage_discoverable')}:** `{t('audit_log', 'yes') if stage_instance.discoverable_disabled else t('audit_log', 'no')}`"
        )
        fields = []
        if stage_instance.scheduled_event:
            fields.append({"name": t('audit_log', 'field_stage_scheduled_event'), "value": f"`{stage_instance.scheduled_event.name}`", "inline": False})
        if hasattr(stage_instance.channel, 'members'):
            fields.append({"name": t('audit_log', 'field_stage_members'), "value": f"`{len(stage_instance.channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'stage_create_title')}",
            description=description, fields=fields, guild=stage_instance.guild,
        )

    async def log_stage_delete(self, channel: discord.TextChannel, stage_instance: discord.StageInstance):
        t = _(guild_id=stage_instance.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_id')}:** `{stage_instance.id}`\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)\n"
            f"**{t('audit_log', 'field_stage_topic')}:** `{stage_instance.topic}`"
        )
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'stage_delete_title')}",
            description=description, guild=stage_instance.guild,
        )

    async def log_stage_update(self, channel: discord.TextChannel, before: discord.StageInstance, after: discord.StageInstance):
        t = _(guild_id=after.guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_id')}:** `{after.id}`\n**{t('audit_log', 'field_channel')}:** {after.channel.mention} (`{after.channel.id}`)"
        fields = []
        if before.topic != after.topic:
            fields.append({"name": t('audit_log', 'field_stage_topic'), "value": f"`{before.topic}` ➜ `{after.topic}`", "inline": False})
        if before.privacy_level != after.privacy_level:
            fields.append({"name": t('audit_log', 'field_stage_privacy'), "value": f"`{before.privacy_level.name}` ➜ `{after.privacy_level.name}`", "inline": False})
        if before.discoverable_disabled != after.discoverable_disabled:
            fields.append({"name": t('audit_log', 'field_stage_discoverable'), "value": f"`{t('audit_log', 'off') if before.discoverable_disabled else t('audit_log', 'on')}` ➜ `{t('audit_log', 'off') if after.discoverable_disabled else t('audit_log', 'on')}`", "inline": False})
        if getattr(before, 'scheduled_event', None) != getattr(after, 'scheduled_event', None):
            fields.append({"name": t('audit_log', 'field_stage_scheduled_event'), "value": f"`{getattr(before, 'scheduled_event', None)}` ➜ `{getattr(after, 'scheduled_event', None)}`", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'stage_update_title')}",
            description=description, fields=fields, guild=after.guild,
        )

    async def log_stage_speaker_join(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**{t('audit_log', 'field_stage_topic')}:** `{stage_channel.instance.topic}`"
        fields = []
        if hasattr(stage_channel, 'members'):
            fields.append({"name": t('audit_log', 'field_stage_members'), "value": f"`{len(stage_channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'stage_speaker_join')}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_speaker_leave(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**{t('audit_log', 'field_stage_topic')}:** `{stage_channel.instance.topic}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'stage_speaker_leave')}",
            description=description,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_request_to_speak(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**{t('audit_log', 'field_stage_topic')}:** `{stage_channel.instance.topic}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'stage_request_speak')}",
            description=description,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )

    async def log_stage_audience_join(self, channel: discord.TextChannel, member: discord.Member, stage_channel: discord.StageChannel):
        t = _(guild_id=member.guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_user')}:** {member.mention} (`{member.id}`)\n"
            f"**{t('audit_log', 'field_channel')}:** {stage_channel.mention} (`{stage_channel.id}`)"
        )
        if hasattr(stage_channel, 'instance') and stage_channel.instance:
            description += f"\n**{t('audit_log', 'field_stage_topic')}:** `{stage_channel.instance.topic}`"
        fields = []
        if hasattr(stage_channel, 'members'):
            fields.append({"name": t('audit_log', 'field_stage_members'), "value": f"`{len(stage_channel.members)}`", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'stage_audience_join')}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=member.guild,
        )
