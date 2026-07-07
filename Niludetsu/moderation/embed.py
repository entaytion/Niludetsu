from typing import Optional
from ..tools.Embed import Colors, Embed
from ..locale import DEFAULT_LOCALE

import discord

SYSTEM_ICON = "https://cdn.discordapp.com/emojis/1355956973006225490.webp?size=160"

def _locale(key: str, **kwargs) -> str:
    text = DEFAULT_LOCALE.get("moderation", {}).get(key, key)
    if kwargs and text:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text

PUNISHMENT_NAMES = {
    "mute": _locale("punishment_mute"),
    "ban": _locale("punishment_ban"),
    "warn": _locale("punishment_warn"),
    "timeout": _locale("punishment_timeout"),
}

def format_duration(minutes: int) -> str:
    if minutes == 0:
        return _locale("duration_permanent")
    if minutes < 60:
        return _locale("duration_minutes", count=minutes)

    hours, remaining_minutes = divmod(minutes, 60)
    if hours < 24:
        if remaining_minutes == 0:
            return _locale("duration_hours", hours=hours)
        return _locale("duration_hours_minutes", hours=hours, minutes=remaining_minutes)

    days, remaining_hours = divmod(hours, 24)
    if days < 30:
        if remaining_hours == 0:
            return _locale("duration_days", days=days)
        return _locale("duration_days_hours", days=days, hours=remaining_hours)

    months, remaining_days = divmod(days, 30)
    if remaining_days == 0:
        return _locale("duration_months", months=months)
    return _locale("duration_months_days", months=months, days=remaining_days)

def _resolve_punishment_name(punishment_type: str) -> str:
    base_type = punishment_type[2:] if punishment_type.lower().startswith("un") else punishment_type
    return PUNISHMENT_NAMES.get(base_type.lower(), base_type.capitalize())

def _build_description(
    *,
    punishment_name: str,
    target_user: discord.Member | discord.User,
    mode: str,
    is_removal: bool,
) -> str:
    is_dm = mode == "dm"
    if is_removal:
        if is_dm:
            return _locale("dm_removal_desc", punishment=punishment_name)
        return _locale("channel_removal_desc", user_id=target_user.id, punishment=punishment_name)

    if is_dm:
        return _locale("dm_punishment_desc", punishment=punishment_name)
    return _locale("channel_punishment_desc", user_id=target_user.id, punishment=punishment_name)

def _moderator_name(moderator: discord.Member | discord.User) -> str:
    discriminator = getattr(moderator, "discriminator", "0")
    return f"{moderator.name}#{discriminator}" if discriminator != "0" else moderator.name

def moderationembed(
    punishment_type: str,
    target_user: discord.Member | discord.User,
    moderator: discord.Member | discord.User,
    punishment_id: int,
    reason: str,
    duration_minutes: Optional[int] = None,
    mode: str = "channel",
    is_removal: bool = False,
) -> discord.Embed:
    punishment_name = _resolve_punishment_name(punishment_type)
    embed = Embed(
        description=_build_description(
            punishment_name=punishment_name,
            target_user=target_user,
            mode=mode,
            is_removal=is_removal,
        ),
        color=Colors.PRIMARY,
        author={"name": _locale("system_name"), "icon_url": SYSTEM_ICON},
        footer={
            "text": _locale("moderator_footer", moderator=_moderator_name(moderator), mod_id=moderator.id),
            "icon_url": moderator.display_avatar.url,
        },
    )

    embed.add_field(
        name=_locale("field_action_id_removal") if is_removal else _locale("field_action_id"),
        value=f"```{punishment_id}```",
        inline=True,
    )
    embed.add_field(
        name=_locale("field_reason_removal") if is_removal else _locale("field_reason"),
        value=f"```{reason}```",
        inline=True,
    )

    if not is_removal and duration_minutes is not None:
        embed.add_field(
            name=_locale("field_duration"),
            value=f"```{format_duration(duration_minutes)}```",
            inline=True,
        )

    return embed

