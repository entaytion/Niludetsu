import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class InviteLogger(BaseLogger):
    """Логгер для событий инвайтов."""

    async def log_invite_create(self, channel: discord.TextChannel, invite: discord.Invite):
        description = (
            f"**Код:** `{invite.code}`\n"
            f"**Канал:** {invite.channel.mention if invite.channel else 'Неизвестно'}\n"
            f"**Создатель:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        )
        fields = [
            {"name": "Макс. использований", "value": f"{invite.max_uses if invite.max_uses else '∞'}", "inline": True},
            {"name": "Временное", "value": f"{'Да' if invite.temporary else 'Нет'}", "inline": True},
            {"name": "Срок действия", "value": f"<t:{int(invite.expires_at.timestamp())}:F>" if invite.expires_at else '∞', "inline": True},
            {"name": "Ссылка", "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False},
        ]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Приглашение: создано",
            description=description, fields=fields,
            thumbnail_url=invite.inviter.display_avatar.url if invite.inviter else None,
            guild=channel.guild,
        )

    async def log_invite_delete(self, channel: discord.TextChannel, invite: discord.Invite):
        description = (
            f"**Код:** `{invite.code}`\n"
            f"**Канал:** {invite.channel.mention if invite.channel else 'Неизвестно'}\n"
            f"**Создатель:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        )
        fields = [
            {"name": "Использований", "value": f"{invite.uses if invite.uses else '0'}", "inline": True},
            {"name": "Ссылка", "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False},
        ]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Приглашение: удалено",
            description=description, fields=fields,
            thumbnail_url=invite.inviter.display_avatar.url if invite.inviter else None,
            guild=channel.guild,
        )

    async def log_invite_post(self, channel: discord.TextChannel, invite: discord.Invite, message: discord.Message):
        description = (
            f"**Автор:** {message.author.mention} ({message.author.id})\n"
            f"**Канал:** {message.channel.mention}\n"
        )
        if invite.guild:
            description += f"**Целевой сервер:** `{invite.guild.name}`\n"
        description += f"**Создатель приглашения:** {invite.inviter.mention if invite.inviter else 'Система'} ({invite.inviter.id if invite.inviter else 'N/A'})"
        fields = [{"name": "Ссылка", "value": f"[discord.gg/{invite.code}](https://discord.gg/{invite.code})", "inline": False}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Приглашение: опубликовано",
            description=description, fields=fields,
            thumbnail_url=message.author.display_avatar.url, guild=channel.guild,
        )

    async def log_invite_use(self, channel: discord.TextChannel, invite: discord.Invite, user: discord.Member):
        description = (
            f"**Пользователь:** {user.mention} ({user.id})\n"
            f"**Код приглашения:** `{invite.code}`\n"
        )
        if invite.inviter:
            description += f"**Создатель приглашения:** {invite.inviter.mention} ({invite.inviter.id})\n"
        if invite.channel:
            description += f"**Канал приглашения:** {invite.channel.mention}\n"
        fields = [{"name": "Использований", "value": f"{invite.uses}/{invite.max_uses if invite.max_uses else '∞'}", "inline": True}]
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.UNKNOWN} Приглашение: использовано",
            description=description, fields=fields,
            thumbnail_url=user.display_avatar.url, guild=channel.guild,
        )
