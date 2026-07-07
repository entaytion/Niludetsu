import discord
from discord.ext import commands
from Niludetsu import Embed, database
from Niludetsu.locale import _

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="inventory", description="Посмотреть свой инвентарь")
    async def inventory(self, ctx, user: discord.Member = None):
        t = _(ctx=ctx)
        target = user or ctx.author
        uid, gid = str(target.id), str(ctx.guild.id)

        items = await database.fetch_inventory_items(uid, gid)
        embed = Embed.default(title=t("inventory", "title", user_name=target.display_name))
        embed.set_thumbnail(url=target.display_avatar.url)
        
        if not items:
            embed.description = t("inventory", "empty")
        else:
            roles = [i for i in items if i["item_type"] == "role"]
            others = [i for i in items if i["item_type"] != "role"]
            
            if roles:
                embed.add_field(name=t("inventory", "roles"), value="\n".join([f"<@&{i['item_key']}>" for i in roles[:10]]), inline=False)
            if others:
                embed.add_field(name=t("inventory", "items"), value="\n".join([f"**{i['item_key']}** ({i['item_type']})" for i in others[:10]]), inline=False)
                
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot): await bot.add_cog(Inventory(bot))
