from typing import Optional
from ..tools.Embed import Colors, Embed

import discord

SYSTEM_NAME = "Æther! System"
SYSTEM_ICON = "https://cdn.discordapp.com/emojis/1355956973006225490.webp?size=160"
PUNISHMENT_NAMES = {
    "mute": "Мут",
    "ban": "Бан",
    "warn": "Предупреждение",
    "timeout": "Тайм-аут",
}

def format_duration(minutes: int) -> str:
    """Конвертирует минуты в читаемый формат времени."""
    if minutes == 0:
        return "Навсегда"
    if minutes < 60:
        return f"{minutes} мин."

    hours, remaining_minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} ч." if remaining_minutes == 0 else f"{hours} ч. {remaining_minutes} мин."

    days, remaining_hours = divmod(hours, 24)
    if days < 30:
        return f"{days} д." if remaining_hours == 0 else f"{days} д. {remaining_hours} ч."

    months, remaining_days = divmod(days, 30)
    return f"{months} мес." if remaining_days == 0 else f"{months} мес. {remaining_days} д."

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
            return (
                f"С вас было **снято** наказание: **``{punishment_name}``**.\n"
                "-# - Наказание больше не действует."
            )
        return f"С <@{target_user.id}> было **снято** наказание **``{punishment_name}``**."

    if is_dm:
        return (
            f"Вы получили за нарушение правил сервера: **``{punishment_name}``**.\n"
            "-# - Если вы не согласны с наказанием, обжалуйте его, прикрепивши его айди."
        )
    return f"<@{target_user.id}> получает за нарушение правил сервера: **``{punishment_name}``**."

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
    """Создаёт embed модерационного действия для канала или DM."""
    punishment_name = _resolve_punishment_name(punishment_type)
    embed = Embed(
        description=_build_description(
            punishment_name=punishment_name,
            target_user=target_user,
            mode=mode,
            is_removal=is_removal,
        ),
        color=Colors.PRIMARY,
        author={"name": SYSTEM_NAME, "icon_url": SYSTEM_ICON},
        footer={
            "text": f"Модератор: {_moderator_name(moderator)} | {moderator.id}",
            "icon_url": moderator.display_avatar.url,
        },
    )

    embed.add_field(
        name="> ID снятого наказания:" if is_removal else "> ID наказания:",
        value=f"```{punishment_id}```",
        inline=True,
    )
    embed.add_field(
        name="> Причина снятия:" if is_removal else "> Причина:",
        value=f"```{reason}```",
        inline=True,
    )

    if not is_removal and duration_minutes is not None:
        embed.add_field(
            name="> Длительность:",
            value=f"```{format_duration(duration_minutes)}```",
            inline=True,
        )

    return embed

