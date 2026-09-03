import discord, time
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Time
from Niludetsu.locale import _

ROLE_INCOME_AMOUNT = 100
ROLE_INCOME_INTERVAL = 6 * 3600
CD_PREFIX = "ic:"

class IncomeRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = EconomyManager()
        self.time = Time()

    @commands.hybrid_command(name="income", aliases=["ic"], description="Получить доход с ролей магазина")
    async def income(self, ctx):
        t = _(ctx=ctx)
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        
        all_roles = await self.economy.db.get_rows("roles", guild_id=gid, owner_id=uid)
        if not all_roles: return await ctx.reply(t("income", "no_roles"), ephemeral=True)

        acc = await self.economy.get_account(uid, gid)
        cooldowns = acc.get("cooldowns") or {}
        now = int(time.time())
        
        claimed_total = 0
        status_lines = []
        updates = {}

        for r in all_roles:
            rid = r["role_id"]
            last_claim = int(cooldowns.get(f"{CD_PREFIX}{rid}", 0))
            
            if now - last_claim >= ROLE_INCOME_INTERVAL:
                holders = await self.economy.db.get_role_holders(gid, rid)
                real_holders = sum(1 for h in holders if h["user_id"] != uid)
                
                income = real_holders * ROLE_INCOME_AMOUNT
                if income > 0:
                    claimed_total += income
                    updates[f"{CD_PREFIX}{rid}"] = now
                    status_lines.append(t("income", "status_income", rid=rid, income=income, emoji=Emojis.MONEY, count=real_holders))
                else:
                    status_lines.append(t("income", "status_no_buyers", rid=rid))
            else:
                wait = self.time.format_duration(ROLE_INCOME_INTERVAL - (now - last_claim))
                status_lines.append(t("income", "status_wait", rid=rid, time=wait))

        if claimed_total > 0:
            await self.economy.add_money(uid, gid, claimed_total, share_spousal=False, event="role_income")
            new_cds = {**cooldowns, **updates}
            await self.economy.db.update_record("user_economy", {"user_id": uid, "guild_id": gid}, {"cooldowns": new_cds})
            await self.economy.db.update_user_cache(uid, gid, "economy", {"cooldowns": new_cds})
            text = t("income", "claimed", total=claimed_total, emoji=Emojis.MONEY, status="\n".join(status_lines))
        else:
            text = t("income", "unavailable", status="\n".join(status_lines))

        await ctx.reply(embed=EconomyEmbed.result(action=t("income", "action"), user=ctx.author, text=text))

async def setup(bot): await bot.add_cog(IncomeRoles(bot))
