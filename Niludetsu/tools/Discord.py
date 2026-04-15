"""Общие Discord-утилиты."""

from __future__ import annotations

import asyncio
from typing import Optional, Union

import discord
from discord.ext import commands


async def resolve_member(
    bot: commands.Bot,
    user_id: Union[int, str],
    guild_id: Union[int, str],
) -> Union[discord.Member, discord.User]:
    """Получить участника сервера или, если не удалось, — пользователя Discord."""
    uid = int(user_id)
    gid = int(guild_id)
    guild = bot.get_guild(gid)
    if guild:
        member = guild.get_member(uid)
        if member:
            return member
    return await bot.fetch_user(uid)


async def safe_edit(message: discord.Message | None, **kwargs) -> bool:
    """Безопасно отредактировать сообщение. Возвращает ``True`` при успехе."""
    if not message:
        return False
    try:
        await message.edit(**kwargs)
        return True
    except discord.HTTPException:
        return False


async def safe_delete(message: discord.Message | None) -> bool:
    """Безопасно удалить сообщение. Возвращает ``True`` при успехе."""
    if not message:
        return False
    try:
        await message.delete()
        return True
    except discord.HTTPException:
        return False


def owner_check(owner_id: int, *, error_text: str = "Это не твоя панель"):
    """Декоратор-фабрика для ``interaction_check`` во View, ограничивающий доступ по user ID."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != owner_id:
            from Niludetsu.tools.Embed import Embed

            await interaction.response.send_message(
                embed=Embed.error(error_text), ephemeral=True,
            )
            return False
        return True

    return interaction_check


async def safe_fetch_user(
    bot: commands.Bot, user_id: Union[int, str],
) -> Optional[discord.User]:
    """``bot.get_user`` с fallback на ``bot.fetch_user``. Возвращает ``None`` при ошибке."""
    uid = int(user_id)
    user = bot.get_user(uid)
    if user:
        return user
    try:
        return await bot.fetch_user(uid)
    except discord.HTTPException:
        return None


async def safe_fetch_message(
    channel: discord.abc.Messageable, message_id: int,
) -> Optional[discord.Message]:
    """Безопасно получить сообщение по ID. Возвращает ``None`` при ошибке."""
    try:
        return await channel.fetch_message(message_id)
    except discord.HTTPException:
        return None


async def delete_after(message: discord.Message | None, delay: float = 5) -> None:
    """Подождать *delay* секунд и безопасно удалить сообщение."""
    if not message:
        return
    await asyncio.sleep(delay)
    await safe_delete(message)
