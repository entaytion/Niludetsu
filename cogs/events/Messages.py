import discord
from discord.ext import commands
from Niludetsu.logging.messages import MessageLogger

class MessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = MessageLogger(bot)
        
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Вызывается при удалении сообщения"""
        if message.author.bot:
            return
            
        await self.logger.log_message_delete(message)
        
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        """Вызывается при массовом удалении сообщений"""
        # Фильтруем сообщения ботов
        messages = [m for m in messages if not m.author.bot]
        if not messages:
            return
            
        await self.logger.log_bulk_message_delete(messages)
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Вызывается при редактировании сообщения"""
        if before.author.bot:
            return
            
        await self.logger.log_message_edit(before, after)
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Вызывается при отправке сообщения"""
        if message.author.bot:
            return
            
        # Здесь можно добавить дополнительную логику обработки сообщений
        
async def setup(bot):
    await bot.add_cog(MessageEvents(bot)) 