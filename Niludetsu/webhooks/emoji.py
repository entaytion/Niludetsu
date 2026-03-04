import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class EmojiLogger:
    """
    Логгер для действий с эмодзи через вебхук (максимум информации).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_emoji_create(self, channel: discord.TextChannel, emoji: discord.Emoji):
        title = f"{Emojis.SUCCESS} Эмодзи: добавлено"
        description = f"**ID:** `{emoji.id}`\n**Название:** `:{emoji.name}:`"
        author = None
        async for entry in emoji.guild.audit_logs(limit=3, action=discord.AuditLogAction.emoji_create):
            if entry.target.id == emoji.id:
                description += f"\n**Создал:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            thumbnail_url=emoji.url,
            guild=emoji.guild
        )

    async def log_emoji_delete(self, channel: discord.TextChannel, emoji: discord.Emoji):
        title = f"{Emojis.ERROR} Эмодзи: удалено"
        description = f"**ID:** `{emoji.id}`\n**Название:** `:{emoji.name}:`"
        author = None
        async for entry in emoji.guild.audit_logs(limit=3, action=discord.AuditLogAction.emoji_delete):
            if entry.target.id == emoji.id:
                description += f"\n**Удалил:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            thumbnail_url=emoji.url,
            guild=emoji.guild
        )

    async def log_emoji_update(self, channel: discord.TextChannel, before: discord.Emoji, after: discord.Emoji):
        title = f"{Emojis.UNKNOWN} Эмодзи: обновлено"
        fields = []
        if before.name != after.name:
            fields.append({
                "name": "> Изменения:",
                "value": f"- Название: `:{before.name}:` ➜ `:{after.name}:`",
                "inline": False
            })
        if not fields:
            return
        description = f"**ID:** `{after.id}`\n**Название:** `:{after.name}:`"
        author = None
        async for entry in after.guild.audit_logs(limit=3, action=discord.AuditLogAction.emoji_update):
            if entry.target.id == after.id:
                description += f"\n**Изменил:** {entry.user.mention} (`{entry.user.id}`)"
                author = entry.user
                break
        await self.webhooks.send_log(
            channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.url,
            guild=after.guild
        )

