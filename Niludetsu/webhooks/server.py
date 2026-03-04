import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class ServerLogger:
    """
    Логгер для событий сервера через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_guild_join(self, channel: discord.TextChannel, guild: discord.Guild):
        title = f"{Emojis.SUCCESS} Сервер: бот добавлен"
        description = f"**ID:** `{guild.id}`\n"
        description += f"**Название:** `{guild.name}`\n"
        description += f"**Владелец:** {guild.owner.mention if guild.owner else 'N/A'} (`{guild.owner_id}`)\n"
        description += f"**Участников:** `{guild.member_count}`\n"
        description += f"**Уровень проверки:** `{guild.verification_level.name}`\n"
        description += f"**Создан:** <t:{int(guild.created_at.timestamp())}:R>"
        if guild.description:
            description += f"\n**Описание:** `{guild.description}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=guild.icon.url if guild.icon else None,
            guild=guild
        )

    async def log_guild_remove(self, channel: discord.TextChannel, guild: discord.Guild):
        title = f"{Emojis.ERROR} Сервер: бот удалён"
        description = f"**ID:** `{guild.id}`\n"
        description += f"**Название:** `{guild.name}`\n"
        description += f"**Владелец:** {guild.owner.mention if guild.owner else 'N/A'} (`{guild.owner_id}`)\n"
        description += f"**Участников:** `{guild.member_count}`"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            thumbnail_url=guild.icon.url if guild.icon else None,
            guild=guild
        )

    async def log_guild_update(self, channel: discord.TextChannel, before: discord.Guild, after: discord.Guild):
        title = f"{Emojis.UNKNOWN} Сервер: обновлены настройки"
        description = f"**ID:** `{after.id}`\n**Название:** `{after.name}`"
        fields = []
        def add_field(name, value):
            fields.append({"name": "> Изменения:", "value": value, "inline": False})
        if before.name != after.name:
            add_field("name", f"- Название: `{before.name}` ➜ `{after.name}`")
        if before.description != after.description:
            add_field("description", f"- Описание: `{before.description or 'Нет'}` ➜ `{after.description or 'Нет'}`")
        if before.icon != after.icon:
            before_icon = before.icon.url if before.icon else None
            after_icon = after.icon.url if after.icon else None
            add_field(
                "icon",
                f"- Иконка:\nБыло: {('[Открыть](' + before_icon + ')') if before_icon else '—'}\nСтало: {('[Открыть](' + after_icon + ')') if after_icon else '—'}"
            )
        if before.banner != after.banner:
            before_banner = before.banner.url if before.banner else None
            after_banner = after.banner.url if after.banner else None
            add_field(
                "banner",
                f"- Баннер:\nБыло: {('[Открыть](' + before_banner + ')') if before_banner else '—'}\nСтало: {('[Открыть](' + after_banner + ')') if after_banner else '—'}"
            )
        if before.splash != after.splash:
            before_splash = before.splash.url if before.splash else None
            after_splash = after.splash.url if after.splash else None
            add_field(
                "splash",
                f"- Сплэш:\nБыло: {('[Открыть](' + before_splash + ')') if before_splash else '—'}\nСтало: {('[Открыть](' + after_splash + ')') if after_splash else '—'}"
            )
        if before.discovery_splash != after.discovery_splash:
            before_ds = before.discovery_splash.url if before.discovery_splash else None
            after_ds = after.discovery_splash.url if after.discovery_splash else None
            add_field(
                "discovery_splash",
                f"- Сплэш обнаружения:\nБыло: {('[Открыть](' + before_ds + ')') if before_ds else '—'}\nСтало: {('[Открыть](' + after_ds + ')') if after_ds else '—'}"
            )
        if before.owner_id != after.owner_id:
            add_field("owner", f"- Владелец: {before.owner.mention if before.owner else 'N/A'} (`{before.owner_id}`) ➜ {after.owner.mention if after.owner else 'N/A'} (`{after.owner_id}`)")
        if before.afk_channel != after.afk_channel:
            add_field("afk_channel", f"- AFK канал: {before.afk_channel.mention if before.afk_channel else 'Нет'} ➜ {after.afk_channel.mention if after.afk_channel else 'Нет'}")
        if before.afk_timeout != after.afk_timeout:
            add_field("afk_timeout", f"- AFK таймаут: `{before.afk_timeout} сек.` ➜ `{after.afk_timeout} сек.`")
        if before.verification_level != after.verification_level:
            add_field("verification_level", f"- Уровень проверки: `{before.verification_level.name}` ➜ `{after.verification_level.name}`")
        if before.default_notifications != after.default_notifications:
            add_field("default_notifications", f"- Уведомления по умолчанию: `{before.default_notifications.name}` ➜ `{after.default_notifications.name}`")
        if before.explicit_content_filter != after.explicit_content_filter:
            add_field("explicit_content_filter", f"- Фильтр контента: `{before.explicit_content_filter.name}` ➜ `{after.explicit_content_filter.name}`")
        if before.system_channel != after.system_channel:
            add_field("system_channel", f"- Системный канал: {before.system_channel.mention if before.system_channel else 'Нет'} ➜ {after.system_channel.mention if after.system_channel else 'Нет'}")
        if before.rules_channel != after.rules_channel:
            add_field("rules_channel", f"- Канал правил: {before.rules_channel.mention if before.rules_channel else 'Нет'} ➜ {after.rules_channel.mention if after.rules_channel else 'Нет'}")
        if before.public_updates_channel != after.public_updates_channel:
            add_field("public_updates_channel", f"- Канал обновлений: {before.public_updates_channel.mention if before.public_updates_channel else 'Нет'} ➜ {after.public_updates_channel.mention if after.public_updates_channel else 'Нет'}")
        if before.premium_tier != after.premium_tier:
            add_field("premium_tier", f"- Уровень буста: `{before.premium_tier}` ➜ `{after.premium_tier}`")
        if before.premium_subscription_count != after.premium_subscription_count:
            add_field("premium_subscription_count", f"- Количество бустов: `{before.premium_subscription_count}` ➜ `{after.premium_subscription_count}`")
        if before.preferred_locale != after.preferred_locale:
            add_field("preferred_locale", f"- Основной язык: `{before.preferred_locale}` ➜ `{after.preferred_locale}`")
        if before.mfa_level != after.mfa_level:
            add_field("mfa_level", f"- Уровень 2FA: `{before.mfa_level.name}` ➜ `{after.mfa_level.name}`")
        if before.nsfw_level != after.nsfw_level:
            add_field("nsfw_level", f"- Уровень NSFW: `{before.nsfw_level.name}` ➜ `{after.nsfw_level.name}`")
        if not fields:
            return
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.icon.url if after.icon else None,
            guild=after
        )

    async def log_guild_integrations_update(self, channel: discord.TextChannel, guild: discord.Guild):
        title = f"{Emojis.UNKNOWN} Сервер: обновлены интеграции"
        description = f"**ID:** `{guild.id}`\n**Название:** `{guild.name}`"
        fields = []
        # Пытаемся получить список интеграций (нужны права manage_guild)
        integrations = None
        webhooks = None
        try:
            integrations = await guild.integrations()
        except discord.Forbidden:
            fields.append({
                "name": "> Интеграции",
                "value": "Недостаточно прав для просмотра интеграций (нужны Manage Guild).",
                "inline": False
            })
        except discord.HTTPException:
            fields.append({
                "name": "> Интеграции",
                "value": "Не удалось получить список интеграций (HTTP ошибка).",
                "inline": False
            })

        # Вебхуки — могут помочь понять изменения
        try:
            webhooks = await guild.webhooks()
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        if integrations is not None:
            total = len(integrations)
            fields.append({"name": "Всего интеграций", "value": f"`{total}`", "inline": True})
            # Краткое содержание по первым N интеграциям
            parts = []
            for integ in integrations[:10]:
                # Integration fields are not always present, guard with getattr
                name = getattr(integ, 'name', 'Без имени')
                itype = getattr(integ, 'type', 'unknown')
                enabled = getattr(integ, 'enabled', None)
                syncing = getattr(integ, 'syncing', None)
                account = getattr(integ, 'account', None)
                account_name = getattr(account, 'name', None) if account else None
                role = getattr(integ, 'role', None)
                expire_behavior = getattr(integ, 'expire_behavior', None)
                expire_grace = getattr(integ, 'expire_grace_period', None)
                flags = []
                if enabled is not None:
                    flags.append(f"Статус: {'Включено' if enabled else 'Выключено'}")
                if syncing is not None:
                    flags.append(f"Синхронизация: {'Включено' if syncing else 'Выключено'}")
                if account_name:
                    flags.append(f"Аккаунт: {account_name}")
                if role:
                    flags.append(f"Роль: {role.mention}")
                if expire_behavior is not None:
                    flags.append(f"Поведение при истечении: {expire_behavior}")
                if expire_grace is not None:
                    flags.append(f"Период отсрочки: {expire_grace}м")
                flag_str = ", ".join(flags) if flags else ""
                parts.append(f"• {name} (`{itype}`){' — ' + flag_str if flag_str else ''}")
            if parts:
                fields.append({
                    "name": "Интеграции (топ 10)",
                    "value": "\n".join(parts),
                    "inline": False
                })

        if webhooks is not None:
            fields.append({"name": "Вебхуков", "value": f"`{len(webhooks)}`", "inline": True})

        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields if fields else None,
            thumbnail_url=guild.icon.url if guild.icon else None,
            guild=guild
        )

