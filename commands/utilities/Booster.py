import discord
from Niludetsu import EconomyManager, Embed, Emojis, config
from Niludetsu.locale import _
from discord.ext import commands
from typing import Optional, Dict, Any
from Niludetsu.database import Database, database

MAIN_SERVER_ID = config.SERVERS["MAIN_ID"]
NEWS_CHANNEL_ID = 1125546966076625038
BOOST_REWARD = 10000

async def get_booster_role_item(db: Database, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
    try:
        items = await db.fetch_inventory_items(user_id, guild_id)
        for item in items:
            if item.get("item_type") == "booster_role":
                return item
    except Exception as e:
        print(f"[Booster] Ошибка получения бустерской роли: {e}")
    return None

async def delete_booster_role(db: Database, member: discord.Member, guild: discord.Guild, booster_item: Dict[str, Any]) -> bool:
    try:
        role_id = int(booster_item.get("meta", {}).get("role_id"))
        role = guild.get_role(role_id)
        
        if role:
            await role.delete(reason=f"Удаление бустерской роли {member.name}")
        
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

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(database)

    async def _handle_boost_add(self, member: discord.Member):
        guild = member.guild
        guild_id = guild.id
        user_id = str(member.id)
        t = _(guild_id=guild_id, bot=self.bot)

        if guild.id == MAIN_SERVER_ID:
            success, message = await self.economy.add_money(
                user_id,
                str(guild_id),
                BOOST_REWARD,
                share_spousal=True
            )
            if not success:
                print(f"[Booster] Ошибка выдачи награды {member.name}: {message}")

            news_channel = self.bot.get_channel(NEWS_CHANNEL_ID)
            if news_channel:
                embed = Embed(
                    title=t("utilities", "booster_new_title"),
                    description=t("utilities", "booster_new_desc", member_mention=member.mention, reward=f"{BOOST_REWARD:,}", currency=Emojis.MONEY),
                    color=discord.Color.nitro_pink()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await news_channel.send(embed=embed)
                except Exception as e:
                    print(f"[Booster] Ошибка отправки в канал новостей: {e}")
            return

        cm = getattr(self.bot, "config_manager", None)
        if cm and cm.is_premium(guild_id):
            boost_channel_id = cm.get_custom_text(guild_id, "boost", "channel_id", None)
            if boost_channel_id:
                channel = guild.get_channel(int(boost_channel_id))
                if channel:
                    custom = cm.get_custom_embed(
                        guild_id, "boost", "boost_embed",
                        default_embed_data=None,
                        user_mention=member.mention,
                        user_name=member.display_name,
                        server_name=guild.name,
                    )
                    if custom:
                        await channel.send(embed=Embed(**custom))

    async def _handle_boost_remove(self, member: discord.Member):
        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)

        booster_item = await get_booster_role_item(self.db, user_id, guild_id)
        
        if booster_item:
            await delete_booster_role(self.db, member, guild, booster_item)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        cm = getattr(self.bot, "config_manager", None)

        is_main = (guild.id == MAIN_SERVER_ID)
        is_prem = (cm and cm.is_premium(guild.id))

        if not is_main and not is_prem:
            return

        if not before.premium_since and after.premium_since:
            await self._handle_boost_add(after)

        elif before.premium_since and not after.premium_since:
            await self._handle_boost_remove(after)

async def setup(bot):
    await bot.add_cog(Booster(bot))
