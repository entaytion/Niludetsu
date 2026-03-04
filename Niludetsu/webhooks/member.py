import discord
from Niludetsu import Emojis
from Niludetsu.development.Webhooks import Webhooks

class MemberLogger:
    """
    Логгер для событий участников (join/leave/update) через вебхук.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    async def log_member_join(self, channel: discord.TextChannel, member: discord.Member, inviter: discord.Member = None):
        title = f"{Emojis.SUCCESS} Участник: вошёл на сервер"
        description = f"**Пользователь:** {member.mention} ({member.id})\n**Аккаунт создан:** <t:{int(member.created_at.timestamp())}:R>"
        if inviter:
            description += f"\n**Пригласил:** {inviter.mention} ({inviter.id})"
        fields = []
        fields.append({"name": "Роли", "value": ", ".join([r.mention for r in member.roles if r.name != '@everyone']) or 'Нет', "inline": False})
        if member.premium_since:
            fields.append({"name": "Бустер", "value": f"С {member.premium_since.strftime('%d.%m.%Y %H:%M')}", "inline": True})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=channel.guild
        )

    async def log_member_remove(self, channel: discord.TextChannel, member: discord.Member, reason: str = None):
        title = f"{Emojis.ERROR} Участник: покинул сервер"
        description = f"**Пользователь:** {member.mention} ({member.id})\n**Дата входа:** <t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else f"**Пользователь:** {member.mention} ({member.id})"
        if reason:
            description += f"\n**Причина:** {reason}"
        fields = []
        fields.append({"name": "Роли", "value": ", ".join([r.mention for r in member.roles if r.name != '@everyone']) or 'Нет', "inline": False})
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=member.display_avatar.url,
            guild=channel.guild
        )

    async def log_member_update(self, channel: discord.TextChannel, before: discord.Member, after: discord.Member):
        title = f"{Emojis.UNKNOWN} Участник: изменён"
        description = f"**Пользователь:** {after.mention} ({after.id})"
        fields = []
        if before.display_name != after.display_name:
            fields.append({"name": "Никнейм", "value": f"`{before.display_name}` ➜ `{after.display_name}`", "inline": False})
        if before.display_avatar != after.display_avatar:
            fields.append({"name": "Аватар", "value": "Изменён", "inline": False})
        if set(before.roles) != set(after.roles):
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                fields.append({"name": "Добавлены роли", "value": ", ".join([r.mention for r in added]), "inline": False})
            if removed:
                fields.append({"name": "Удалены роли", "value": ", ".join([r.mention for r in removed]), "inline": False})
        if before.premium_since != after.premium_since:
            fields.append({"name": "Бустер", "value": f"`{before.premium_since}` ➜ `{after.premium_since}`", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=after.guild.get_channel(channel.id),
            title=title,
            description=description,
            fields=fields,
            thumbnail_url=after.display_avatar.url,
            guild=after.guild
        )

    async def log_member_ban(self, channel: discord.TextChannel, user: discord.User, reason: str = None, moderator: discord.Member = None):
        title = f"{Emojis.ERROR} Бан: участник забанен"
        description = f"**Пользователь:** {user.mention} ({user.id})"
        if moderator:
            description += f"\n**Модератор:** {moderator.mention} ({moderator.id})"
        if reason:
            description += f"\n**Причина:** {reason}"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild
        )

    async def log_member_unban(self, channel: discord.TextChannel, user: discord.User, moderator: discord.Member = None):
        title = f"{Emojis.SUCCESS} Бан: участник разбанен"
        description = f"**Пользователь:** {user.mention} ({user.id})"
        if moderator:
            description += f"\n**Модератор:** {moderator.mention} ({moderator.id})"
        await self.webhooks.send_log(
            channel=channel,
            title=title,
            description=description,
            fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild
        ) 

