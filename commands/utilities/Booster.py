import discord
from discord.ext import commands
from typing import Optional, Dict, Any
from Niludetsu.config import SERVERS
from Niludetsu.database.supabase_database import database, SupabaseDatabase
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Emojis import Emojis

MAIN_SERVER_ID = SERVERS["MAIN_ID"]
NEWS_CHANNEL_ID = 1125546966076625038  # Канал новостей
BOOST_REWARD = 10000  # Награда за буст

async def get_booster_role_item(db: SupabaseDatabase, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
    """Получает запись о бустерской роли из инвентаря"""
    try:
        items = await db.fetch_inventory_items(user_id, guild_id)
        for item in items:
            if item.get("item_type") == "booster_role":
                return item
    except Exception as e:
        print(f"[Booster] Ошибка получения бустерской роли: {e}")
    return None

async def delete_booster_role(db: SupabaseDatabase, member: discord.Member, guild: discord.Guild, booster_item: Dict[str, Any]) -> bool:
    """Удаляет бустерскую роль"""
    try:
        role_id = int(booster_item.get("meta", {}).get("role_id"))
        role = guild.get_role(role_id)
        
        if role:
            await role.delete(reason=f"Удаление бустерской роли {member.name}")
        
        # Удаляем из инвентаря
        await db.delete_inventory_item(
            user_id=str(member.id),
            guild_id=str(guild.id),
            item_key=booster_item["item_key"]
        )
        
        return True
    except Exception as e:
        print(f"[Booster] Ошибка удаления бустерской роли: {e}")
        return False

class Booster(commands.Cog):
    """Обработка бустов сервера"""

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(database)

    async def _handle_boost_add(self, member: discord.Member):
        """Обрабатывает добавление буста"""
        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)

        success, message = await self.economy.add_money(
            user_id,
            guild_id,
            BOOST_REWARD,
            share_spousal=True
        )

        if not success:
            print(f"[Booster] Ошибка выдачи награды {member.name}: {message}")
            return

        news_channel = self.bot.get_channel(NEWS_CHANNEL_ID)
        if not news_channel:
            return

        embed = Embed(
            title="🚀 Новый буст на сервере!",
            description=(
                f"> {member.mention} бустанул сервер! Мы очень благодарны!\n"
                f"> За это награда в размере **{BOOST_REWARD:,} {Emojis.MONEY}**!"
            ),
            color=discord.Color.nitro_pink()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        try:
            await news_channel.send(embed=embed)
        except Exception as e:
            print(f"[Booster] Ошибка отправки в канал новостей: {e}")

    async def _handle_boost_remove(self, member: discord.Member):
        """Обрабатывает удаление буста"""
        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)

        # Получаем бустерскую роль из инвентаря
        booster_item = await get_booster_role_item(self.db, user_id, guild_id)
        
        if booster_item:
            await delete_booster_role(self.db, member, guild, booster_item)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Отслеживает изменения статуса буста"""
        # Работаем только с основным сервером
        if after.guild.id != MAIN_SERVER_ID:
            return

        if not before.premium_since and after.premium_since:
            await self._handle_boost_add(after)

        elif before.premium_since and not after.premium_since:
            await self._handle_boost_remove(after)

async def setup(bot):
    await bot.add_cog(Booster(bot))