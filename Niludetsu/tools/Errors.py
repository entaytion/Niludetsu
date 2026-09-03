import discord
import aiohttp
import traceback
from discord.ext import commands
from Niludetsu.tools.Embed import Embed
from Niludetsu.locale import _

class PastebinClient:
    API_URL = "https://dpaste.com/api/"

    async def create_paste(self, title: str, content: str) -> str:
        payload = {"content": content, "title": title, "expiry_days": 1}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, data=payload) as resp:
                if not resp.ok: return "Paste service error"
                return (await resp.text()).strip()

class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot
        self.pastebin = PastebinClient()

    async def handle_error(self, ctx, error):
        t = _(ctx=ctx)
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.reply(embed=Embed.error(t("errors", "cooldown", time=f"{error.retry_after:.2f}с")), ephemeral=True)
        
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        paste_url = await self.pastebin.create_paste(f"Error: {ctx.command}", tb)
        
        embed = Embed.error(title=t("errors", "error_title"), description=t("errors", "error_desc", error_text=str(error), paste_url=paste_url))
        await ctx.reply(embed=embed, ephemeral=True)
