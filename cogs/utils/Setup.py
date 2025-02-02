import discord
from discord.ext import commands
from Niludetsu.utils.setup_manager import SetupManager, SetupView
from Niludetsu.utils.embed import Embed
import asyncio

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_manager = SetupManager(bot)
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Вызывается когда бот полностью готов"""
        await asyncio.sleep(5)  # Ждем 5 секунд
        await self.setup_manager.initialize()

async def setup(bot):
    await bot.add_cog(Setup(bot)) 