import asyncio, discord
from discord.ext import commands
from Niludetsu.config import NOTIFICATION_CHANNEL_ID, OWNER_ID
from Niludetsu.development.Webhooks import Webhooks

class PrivateMessageCog(commands.Cog):
    """
    Ког для пересылки личных сообщений в баг-канал и ответа пользователям через !pm.
    """
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild and not message.author.bot:
            channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if not channel:
                return
            fields = [
                {"name": "ID пользователя", "value": str(message.author.id), "inline": True},
                {"name": "Профиль", "value": message.author.mention, "inline": True},
            ]
            image_url = message.attachments[0].url if message.attachments else None
            embed = discord.Embed(
                title="Новое личное сообщение",
                description=message.content or "[Без текста]",
                color=0x000001
            )
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )
            if image_url:
                embed.set_image(url=image_url)
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"Для ответа используйте !pm {message.author.id}")
            await channel.send(embed=embed)

    @commands.command(name="pm", ignore_extra=True)
    async def pm(self, ctx, user_id: str = None, *, text: str = None):
        """
        Отправить личное сообщение пользователю по ID.
        !pm <user_id> <текст>
        Только для OWNER_ID.
        """
        # Только OWNER_ID может использовать команду
        if ctx.author.id != OWNER_ID:
            await ctx.message.delete()
            return

        # Проверка на отсутствие аргументов (текст или вложения обязательны)
        if not user_id or (not text and not ctx.message.attachments):
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Использование: !pm <user_id> <текст или вложение>", delete_after=5)
            await asyncio.sleep(5)
            await ctx.message.delete()
            return

        # Преобразуем user_id в int, если возможно
        try:
            user_id_int = int(user_id.replace("<@", "").replace(">", "").replace("!", ""))
        except Exception:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Некорректный user_id.", delete_after=5)
            await asyncio.sleep(5)
            await ctx.message.delete()
            return

        user = self.bot.get_user(user_id_int)
        if not user:
            try:
                user = await self.bot.fetch_user(user_id_int)
            except Exception:
                user = None
        if not user:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Пользователь не найден.", delete_after=5)
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        try:
            files = [await a.to_file() for a in ctx.message.attachments]
            await user.send(text, files=files if files else None)
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.message.add_reaction("❌")
        await asyncio.sleep(5)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(PrivateMessageCog(bot)) 

