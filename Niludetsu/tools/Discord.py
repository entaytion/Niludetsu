import asyncio
import discord
from discord.ext import commands
from typing import Optional, Union

async def resolve_member(bot: commands.Bot, user_id: Union[int, str], guild_id: Union[int, str]) -> Union[discord.Member, discord.User]:
    uid, gid = int(user_id), int(guild_id)
    guild = bot.get_guild(gid)
    if guild:
        member = guild.get_member(uid)
        if member: return member
    try: return await bot.fetch_user(uid)
    except: return None

async def safe_edit(message: Optional[discord.Message], **kwargs) -> bool:
    if not message: return False
    try:
        await message.edit(**kwargs)
        return True
    except: return False

async def safe_delete(message: Optional[discord.Message]) -> bool:
    if not message: return False
    try:
        await message.delete()
        return True
    except: return False

async def safe_fetch_user(bot: commands.Bot, user_id: Union[int, str]) -> Optional[discord.User]:
    uid = int(user_id)
    user = bot.get_user(uid)
    if user: return user
    try: return await bot.fetch_user(uid)
    except: return None

async def safe_fetch_message(channel: discord.abc.Messageable, message_id: int) -> Optional[discord.Message]:
    try: return await channel.fetch_message(message_id)
    except: return None

def owner_check(owner_id: int):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != owner_id:
            from .Embed import Embed
            await interaction.response.send_message(embed=Embed.error("Это не твоя панель!"), ephemeral=True)
            return False
        return True
    return interaction_check

async def delete_after(message: Optional[discord.Message], delay: float = 5) -> None:
    if not message: return
    await asyncio.sleep(delay)
    await safe_delete(message)
