import discord
from ..tools.Emojis import Emojis

from Niludetsu.locale import _
from Niludetsu.webhooks.base import BaseLogger

class ServerLogger(BaseLogger):

    async def log_guild_join(self, channel: discord.TextChannel, guild: discord.Guild):
        t = _(guild_id=guild.id, bot=self.bot)
        description = (
            f"**{t('audit_log', 'field_server')}:** `{guild.name}` (`{guild.id}`)\n"
            f"**{t('audit_log', 'field_owner')}:** {guild.owner.mention if guild.owner else t('audit_log', 'unknown')}\n"
            f"**{t('audit_log', 'field_member_count')}:** `{guild.member_count}`"
        )
        fields = []
        if guild.description:
            fields.append({"name": t('audit_log', 'field_description'), "value": guild.description, "inline": False})
        fields.append({"name": t('audit_log', 'field_verification_level'), "value": f"`{guild.verification_level}`", "inline": True})
        fields.append({"name": t('audit_log', 'field_premium_tier'), "value": f"`{guild.premium_tier}` ({t('audit_log', 'field_boosts_count', count=guild.premium_subscription_count)})", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} {t('audit_log', 'server_join_title')}",
            description=description, fields=fields, guild=guild,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

    async def log_guild_remove(self, channel: discord.TextChannel, guild: discord.Guild):
        t = _(guild_id=guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_server')}:** `{guild.name}` (`{guild.id}`)\n**{t('audit_log', 'field_member_count')}:** `{guild.member_count}`"
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} {t('audit_log', 'server_remove_title')}",
            description=description, guild=guild,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

    async def log_guild_update(self, channel: discord.TextChannel, before: discord.Guild, after: discord.Guild):
        t = _(guild_id=after.id, bot=self.bot)
        none_label = t('audit_log', 'none')
        on_label = t('audit_log', 'on')
        off_label = t('audit_log', 'off')
        was_label = t('audit_log', 'was')
        became_label = t('audit_log', 'became')
        open_label = t('audit_log', 'open_link')

        changes = []

        if before.name != after.name:
            changes.append(f"**{t('audit_log', 'field_name')}:** `{before.name}` → `{after.name}`")
        if before.description != after.description:
            changes.append(f"**{t('audit_log', 'field_description')}:**\n{was_label}: `{before.description or '—'}`\n{became_label}: `{after.description or '—'}`")
        if before.owner_id != after.owner_id:
            changes.append(f"**{t('audit_log', 'field_owner')}:** <@{before.owner_id}> → <@{after.owner_id}>")
        if before.preferred_locale != after.preferred_locale:
            changes.append(f"**Язык:** `{before.preferred_locale}` → `{after.preferred_locale}`")

        if before.icon != after.icon:
            before_url = before.icon.url if before.icon else None
            after_url = after.icon.url if after.icon else None
            changes.append(
                f"**{t('audit_log', 'field_icon')}:**\n"
                f"{was_label}: {('[' + open_label + '](' + before_url + ')') if before_url else '—'}\n"
                f"{became_label}: {('[' + open_label + '](' + after_url + ')') if after_url else '—'}"
            )
        if before.banner != after.banner:
            before_url = before.banner.url if before.banner else None
            after_url = after.banner.url if after.banner else None
            changes.append(
                f"**Баннер:**\n"
                f"{was_label}: {('[' + open_label + '](' + before_url + ')') if before_url else '—'}\n"
                f"{became_label}: {('[' + open_label + '](' + after_url + ')') if after_url else '—'}"
            )
        if before.splash != after.splash:
            before_url = before.splash.url if before.splash else None
            after_url = after.splash.url if after.splash else None
            changes.append(
                f"**Сплэш приглашения:**\n"
                f"{was_label}: {('[' + open_label + '](' + before_url + ')') if before_url else '—'}\n"
                f"{became_label}: {('[' + open_label + '](' + after_url + ')') if after_url else '—'}"
            )
        if before.discovery_splash != after.discovery_splash:
            before_ds = before.discovery_splash.url if before.discovery_splash else None
            after_ds = after.discovery_splash.url if after.discovery_splash else None
            changes.append(
                f"**Сплэш обнаружения:**\n"
                f"{was_label}: {('[' + open_label + '](' + before_ds + ')') if before_ds else '—'}\n"
                f"{became_label}: {('[' + open_label + '](' + after_ds + ')') if after_ds else '—'}"
            )

        if before.afk_channel != after.afk_channel:
            bc = before.afk_channel.mention if before.afk_channel else f'`{none_label}`'
            ac = after.afk_channel.mention if after.afk_channel else f'`{none_label}`'
            changes.append(f"**AFK канал:** {bc} → {ac}")
        if before.afk_timeout != after.afk_timeout:
            changes.append(f"**AFK таймаут:** `{before.afk_timeout // 60}мин` → `{after.afk_timeout // 60}мин`")
        if before.system_channel != after.system_channel:
            bc = before.system_channel.mention if before.system_channel else f'`{none_label}`'
            ac = after.system_channel.mention if after.system_channel else f'`{none_label}`'
            changes.append(f"**Системный канал:** {bc} → {ac}")
        if before.system_channel_flags != after.system_channel_flags:
            bf = before.system_channel_flags.value
            af = after.system_channel_flags.value
            changes.append(f"**Флаги системного канала:** `{bf}` → `{af}`")
        if before.rules_channel != after.rules_channel:
            bc = before.rules_channel.mention if before.rules_channel else f'`{none_label}`'
            ac = after.rules_channel.mention if after.rules_channel else f'`{none_label}`'
            changes.append(f"**Канал правил:** {bc} → {ac}")
        if before.public_updates_channel != after.public_updates_channel:
            bc = before.public_updates_channel.mention if before.public_updates_channel else f'`{none_label}`'
            ac = after.public_updates_channel.mention if after.public_updates_channel else f'`{none_label}`'
            changes.append(f"**Канал обновлений:** {bc} → {ac}")
        if getattr(before, 'safety_alerts_channel', None) != getattr(after, 'safety_alerts_channel', None):
            bc = before.safety_alerts_channel.mention if getattr(before, 'safety_alerts_channel', None) else f'`{none_label}`'
            ac = after.safety_alerts_channel.mention if getattr(after, 'safety_alerts_channel', None) else f'`{none_label}`'
            changes.append(f"**Канал безопасности:** {bc} → {ac}")

        if before.verification_level != after.verification_level:
            changes.append(f"**{t('audit_log', 'field_verification_level')}:** `{before.verification_level}` → `{after.verification_level}`")
        if before.default_notifications != after.default_notifications:
            changes.append(f"**Уведомления по умолчанию:** `{before.default_notifications}` → `{after.default_notifications}`")
        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(f"**Контент-фильтр:** `{before.explicit_content_filter}` → `{after.explicit_content_filter}`")
        if before.mfa_level != after.mfa_level:
            changes.append(f"**Требование 2FA:** `{before.mfa_level}` → `{after.mfa_level}`")
        if getattr(before, 'nsfw_level', None) != getattr(after, 'nsfw_level', None):
            changes.append(f"**NSFW уровень:** `{getattr(before, 'nsfw_level', '—')}` → `{getattr(after, 'nsfw_level', '—')}`")

        if before.premium_tier != after.premium_tier:
            changes.append(f"**{t('audit_log', 'field_premium_tier')}:** `{before.premium_tier}` → `{after.premium_tier}`")
        if before.premium_subscription_count != after.premium_subscription_count:
            changes.append(f"**{t('audit_log', 'field_boost_count')}:** `{before.premium_subscription_count}` → `{after.premium_subscription_count}`")
        if getattr(before, 'premium_progress_bar_enabled', None) != getattr(after, 'premium_progress_bar_enabled', None):
            changes.append(f"**Прогресс-бар буста:** `{on_label if after.premium_progress_bar_enabled else off_label}`")

        if getattr(before, 'vanity_url_code', None) != getattr(after, 'vanity_url_code', None):
            changes.append(f"**Vanity URL:** `{getattr(before, 'vanity_url_code', '—')}` → `{getattr(after, 'vanity_url_code', '—')}`")
        if getattr(before, 'widget_enabled', None) != getattr(after, 'widget_enabled', None):
            changes.append(f"**Виджет:** `{on_label if getattr(after, 'widget_enabled', False) else off_label}`")
        if getattr(before, 'widget_channel', None) != getattr(after, 'widget_channel', None):
            bc = before.widget_channel.mention if getattr(before, 'widget_channel', None) else f'`{none_label}`'
            ac = after.widget_channel.mention if getattr(after, 'widget_channel', None) else f'`{none_label}`'
            changes.append(f"**Канал виджета:** {bc} → {ac}")

        if set(before.features) != set(after.features):
            added = set(after.features) - set(before.features)
            removed = set(before.features) - set(after.features)
            if added:
                changes.append(f"**Фичи (добавлены):** {', '.join(f'`{f}`' for f in added)}")
            if removed:
                changes.append(f"**Фичи (убраны):** {', '.join(f'`{f}`' for f in removed)}")

        if getattr(before, 'max_presences', None) != getattr(after, 'max_presences', None):
            changes.append(f"**Макс. присутствий:** `{getattr(before, 'max_presences', '—')}` → `{getattr(after, 'max_presences', '—')}`")
        if getattr(before, 'max_members', None) != getattr(after, 'max_members', None):
            changes.append(f"**Макс. участников:** `{getattr(before, 'max_members', '—')}` → `{getattr(after, 'max_members', '—')}`")
        if getattr(before, 'max_video_channel_users', None) != getattr(after, 'max_video_channel_users', None):
            changes.append(f"**Макс. видео-пользователей:** `{getattr(before, 'max_video_channel_users', '—')}` → `{getattr(after, 'max_video_channel_users', '—')}`")

        if not changes:
            return

        description = f"**{t('audit_log', 'field_server')}:** `{after.name}`\n**{t('audit_log', 'field_id')}:** `{after.id}`"

        updater = None
        try:
            async for entry in after.audit_logs(limit=3, action=discord.AuditLogAction.guild_update):
                updater = entry.user
                break
        except Exception:
            pass
        if updater:
            description += f"\n**{t('audit_log', 'updated_by')}** {updater.mention} (`{updater.id}`)"

        fields = [{"name": t('audit_log', 'field_change_field'), "value": c, "inline": False} for c in changes]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'server_update_title')}",
            description=description, fields=fields, guild=after,
            thumbnail_url=after.icon.url if after.icon else None,
        )

    async def log_guild_integrations_update(self, channel: discord.TextChannel, guild: discord.Guild):
        t = _(guild_id=guild.id, bot=self.bot)
        description = f"**{t('audit_log', 'field_server')}:** `{guild.name}` (`{guild.id}`)\n{t('audit_log', 'field_integrations_updated')}"
        fields = []
        try:
            integrations = await guild.integrations()
            for integ in integrations[:10]:
                status = f"{t('audit_log', 'field_type')}: `{integ.type}`"
                if hasattr(integ, 'enabled'):
                    status += f"\n{t('audit_log', 'automod_enabled')}: `{t('audit_log', 'yes') if integ.enabled else t('audit_log', 'no')}`"
                if hasattr(integ, 'syncing'):
                    status += f"\n{t('audit_log', 'field_app_syncing')}: `{t('audit_log', 'yes') if integ.syncing else t('audit_log', 'no')}`"
                if hasattr(integ, 'role') and integ.role:
                    status += f"\n{t('audit_log', 'field_role')}: {integ.role.mention}"
                if hasattr(integ, 'account') and integ.account:
                    status += f"\nАккаунт: `{integ.account.name}`"
                fields.append({
                    "name": f"{integ.name}",
                    "value": status,
                    "inline": True,
                })
        except Exception:
            pass
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} {t('audit_log', 'server_integrations_title')}",
            description=description, fields=fields, guild=guild,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )
