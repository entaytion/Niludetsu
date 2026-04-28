import discord, time
from discord.ext import commands
from Niludetsu import EconomyManager, EconomyEmbed, Emojis, Time

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
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        
        # Получаем все роли, которыми владеет юзер
        all_roles = await self.economy.db.get_rows("roles", guild_id=gid, owner_id=uid)
        if not all_roles: return await ctx.reply("У вас нет ролей в магазине!", ephemeral=True)

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
                # Считаем владельцев
                holders = await self.economy.db.get_role_holders(gid, rid)
                # Только те, кто купил, а не владелец
                real_holders = sum(1 for h in holders if h["user_id"] != uid)
                
                income = real_holders * ROLE_INCOME_AMOUNT
                if income > 0:
                    claimed_total += income
                    updates[f"{CD_PREFIX}{rid}"] = now
                    status_lines.append(f"<@&{rid}> — **+{income:,}** {Emojis.MONEY} ({real_holders} чел.)")
                else:
                    status_lines.append(f"<@&{rid}> — нет покупателей.")
            else:
                wait = self.time.format_duration(ROLE_INCOME_INTERVAL - (now - last_claim))
                status_lines.append(f"<@&{rid}> — ждать {wait}")

        if claimed_total > 0:
            await self.economy.add_money(uid, gid, claimed_total, share_spousal=False, event="role_income")
            # Обновляем кулдауны точечно
            new_cds = {**cooldowns, **updates}
            await self.economy.db.update_record("user_economy", {"user_id": uid, "guild_id": gid}, {"cooldowns": new_cds})
            await self.economy.db.update_user_cache(uid, gid, "economy", {"cooldowns": new_cds})
            text = f"вы получили **{claimed_total:,}** {Emojis.MONEY} дохода!\n" + "\n".join(status_lines)
        else:
            text = "сейчас доход недоступен.\n" + "\n".join(status_lines)

        await ctx.reply(embed=EconomyEmbed.result(action="Доход с ролей", user=ctx.author, text=text))

async def setup(bot): await bot.add_cog(IncomeRoles(bot))
