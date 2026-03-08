import discord, time
from discord.ext import commands
from Niludetsu import Emojis, Time
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.embeds.Economy import EconomyEmbed
from typing import Any, Dict, List, Optional

_time = Time()
ROLE_INCOME_AMOUNT = 100
ROLE_INCOME_INTERVAL_SECONDS = 6 * 60 * 60
COOLDOWN_PREFIX = "income:role_shop"


def _extract_data(response: Optional[Any]) -> Optional[Any]:
    return getattr(response, "data", None) if response is not None else None


class IncomeRolesSystem:
    def __init__(self, db, economy: EconomyManager):
        self.db = db
        self.economy = economy

    async def fetch_owned_roles(self, guild_id: str, owner_id: str) -> List[Dict[str, Any]]:
        response = (
            self.db.client.table("roles")
            .select("id, role_id, name, color, price")
            .eq("guild_id", guild_id)
            .eq("owner_id", owner_id)
            .execute()
        )
        return _extract_data(response) or []

    async def count_role_holders(self, guild_id: str, role_id: str) -> int:
        response = (
            self.db.client.table("user_inventory")
            .select("user_id,meta")
            .eq("guild_id", guild_id)
            .eq("item_type", "role")
            .eq("item_key", role_id)
            .execute()
        )
        rows = _extract_data(response) or []
        return sum(1 for r in rows if (r.get("meta") or {}).get("source") != "personal_role")

    async def get_cooldown_timestamp(self, user_id: str, guild_id: str, role_id: str) -> int:
        record = await self.db.get_row("user_economy", user_id=str(user_id), guild_id=str(guild_id))
        if not record:
            return 0
        cooldowns = record.get("cooldowns") or {}
        key = f"{COOLDOWN_PREFIX}:{role_id}"
        return int(cooldowns.get(key, 0))

    async def set_cooldown_timestamp(self, user_id: str, guild_id: str, role_id: str, value: int) -> None:
        key = f"{COOLDOWN_PREFIX}:{role_id}"
        await self.db.update_economy(
            user_id=str(user_id),
            guild_id=str(guild_id),
            values={"cooldowns": {key: value}},
        )

    async def get_income_status(self, *, user_id: str, guild: discord.Guild) -> List[Dict[str, Any]]:
        guild_id = str(guild.id)
        roles = await self.fetch_owned_roles(guild_id, user_id)
        status: List[Dict[str, Any]] = []
        now = int(time.time())

        for role in roles:
            role_id = role["role_id"]
            holders = await self.count_role_holders(guild_id, role_id)
            last_claim = await self.get_cooldown_timestamp(user_id, guild_id, role_id)
            elapsed = now - last_claim
            can_claim = elapsed >= ROLE_INCOME_INTERVAL_SECONDS
            time_left = max(0, ROLE_INCOME_INTERVAL_SECONDS - elapsed)

            status.append({
                "role_id": role_id,
                "discord_role": guild.get_role(int(role_id)),
                "holders": holders,
                "income": ROLE_INCOME_AMOUNT,
                "can_claim": can_claim,
                "time_left": time_left,
            })
        return status

    async def claim_income(self, *, user_id: str, guild: discord.Guild) -> Dict[str, Any]:
        status = await self.get_income_status(user_id=user_id, guild=guild)
        total_income = 0
        now = int(time.time())
        claimed: List[Dict[str, Any]] = []

        for item in status:
            if item["can_claim"]:
                total_income += item["income"]
                await self.set_cooldown_timestamp(user_id, str(guild.id), item["role_id"], now)
                claimed.append(item)

        if total_income:
            await self.economy.add_money(user_id, str(guild.id), total_income, share_spousal=False)

        return {"total": total_income, "claimed": claimed, "status": status}


class IncomeRoles(commands.Cog):
    """Пассивный доход владельцам ролей магазина."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)
        self.system = IncomeRolesSystem(self.db, self.economy)

    @commands.hybrid_command(name="income", aliases=["ic"], description="💱 Получить пассивный доход с ролей магазина")
    async def income(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.reply(embed=EconomyEmbed.error("Команда работает только на сервере."), ephemeral=True)
            return

        user_id = str(ctx.author.id)
        result = await self.system.claim_income(user_id=user_id, guild=ctx.guild)

        total = result["total"]
        status = result["status"]

        if total > 0:
            role_lines = []
            for item in result["claimed"]:
                role = item["discord_role"]
                mention = role.mention if role else f"<@&{item['role_id']}>"
                role_lines.append(f"{mention} — **+{item['income']}** {Emojis.MONEY}")
            roles_text = "\n".join(role_lines)
            text = (
                f"вы получили **+{total}** {Emojis.MONEY} дохода с ролей!\n"
                f"{roles_text}\n\n"
                f"Следующая выдача будет доступна через 6 часов."
            )
        else:
            role_lines = []
            for item in status:
                role = item["discord_role"]
                mention = role.mention if role else f"<@&{item['role_id']}>"
                pretty_wait = _time.format_duration(item["time_left"])
                role_lines.append(f"{mention} — ждать {pretty_wait}")
            roles_text = "\n".join(role_lines) if role_lines else "Нет ролей для дохода."
            text = f"сейчас доход недоступен.\n{roles_text}"

        embed = EconomyEmbed.result(
            action="Пассивный доход",
            user=ctx.author,
            text=text,
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(IncomeRoles(bot))
