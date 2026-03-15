import discord
from Niludetsu import Emojis
from Niludetsu.webhooks.base import BaseLogger


class MemberLogger(BaseLogger):
    """Логгер для событий участников (join/leave/update/ban/timeout)."""

    async def log_member_join(self, channel: discord.TextChannel, member: discord.Member, inviter: discord.Member = None):
        description = f"**Пользователь:** {member.mention} ({member.id})\n**Аккаунт создан:** <t:{int(member.created_at.timestamp())}:R>"
        if inviter:
            description += f"\n**Пригласил:** {inviter.mention} ({inviter.id})"
        fields = []
        fields.append({"name": "Роли", "value": ", ".join([r.mention for r in member.roles if r.name != '@everyone']) or 'Нет', "inline": False})
        if member.premium_since:
            fields.append({"name": "Бустер", "value": f"С {member.premium_since.strftime('%d.%m.%Y %H:%M')}", "inline": True})
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Участник: вошёл на сервер",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=channel.guild,
        )

    async def log_member_remove(self, channel: discord.TextChannel, member: discord.Member):
        """Логирует выход, кик или прюн участника (определяет через audit log)."""
        description = f"**Пользователь:** {member.mention} ({member.id})"
        if member.joined_at:
            description += f"\n**Дата входа:** <t:{int(member.joined_at.timestamp())}:R>"

        # Sapphire: определяем кик через audit log
        action_type = "покинул сервер"
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
                if entry.target and entry.target.id == member.id:
                    action_type = "кикнут"
                    description += f"\n**Модератор:** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**Причина:** {entry.reason}"
                    break
        except Exception:
            pass

        fields = []
        roles = [r.mention for r in member.roles if r.name != '@everyone']
        if roles:
            fields.append({"name": "Роли", "value": ", ".join(roles), "inline": False})

        emoji = Emojis.ERROR if action_type == "кикнут" else Emojis.ERROR
        await self.webhooks.send_log(
            channel=channel, title=f"{emoji} Участник: {action_type}",
            description=description, fields=fields,
            thumbnail_url=member.display_avatar.url, guild=channel.guild,
        )

    async def log_member_update(self, channel: discord.TextChannel, before: discord.Member, after: discord.Member):
        description = f"**Пользователь:** {after.mention} ({after.id})"
        fields = []
        if before.display_name != after.display_name:
            fields.append({"name": "Никнейм", "value": f"`{before.display_name}` ➜ `{after.display_name}`", "inline": False})
        if before.display_avatar != after.display_avatar:
            fields.append({"name": "Аватар", "value": "Изменён", "inline": False})
        # Роли
        if set(before.roles) != set(after.roles):
            added = set(after.roles) - set(before.roles)
            removed = set(before.roles) - set(after.roles)
            if added:
                fields.append({"name": "Добавлены роли", "value": ", ".join([r.mention for r in added]), "inline": False})
            if removed:
                fields.append({"name": "Удалены роли", "value": ", ".join([r.mention for r in removed]), "inline": False})
        # Бустер
        if before.premium_since != after.premium_since:
            fields.append({"name": "Бустер", "value": f"`{before.premium_since}` ➜ `{after.premium_since}`", "inline": False})
        # Sapphire: Timeout
        before_timeout = getattr(before, 'timed_out_until', None)
        after_timeout = getattr(after, 'timed_out_until', None)
        if before_timeout != after_timeout:
            if after_timeout and (not before_timeout or after_timeout > before_timeout):
                fields.append({"name": "Тайм-аут", "value": f"Выдан до <t:{int(after_timeout.timestamp())}:F>", "inline": False})
            elif before_timeout and not after_timeout:
                fields.append({"name": "Тайм-аут", "value": "Снят", "inline": False})
        if not fields:
            return
        await self.webhooks.send_log(
            channel=after.guild.get_channel(channel.id),
            title=f"{Emojis.UNKNOWN} Участник: изменён",
            description=description, fields=fields,
            thumbnail_url=after.display_avatar.url, guild=after.guild,
        )

    async def log_member_ban(self, channel: discord.TextChannel, user: discord.User):
        description = f"**Пользователь:** {user.mention} ({user.id})"
        # Получаем модератора и причину через audit log
        try:
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == user.id:
                    description += f"\n**Модератор:** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**Причина:** {entry.reason}"
                    break
        except Exception:
            pass
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.ERROR} Бан: участник забанен",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild,
        )

    async def log_member_unban(self, channel: discord.TextChannel, user: discord.User):
        description = f"**Пользователь:** {user.mention} ({user.id})"
        try:
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.unban):
                if entry.target and entry.target.id == user.id:
                    description += f"\n**Модератор:** {entry.user.mention} ({entry.user.id})"
                    if entry.reason:
                        description += f"\n**Причина:** {entry.reason}"
                    break
        except Exception:
            pass
        await self.webhooks.send_log(
            channel=channel, title=f"{Emojis.SUCCESS} Бан: участник разбанен",
            description=description, fields=[],
            thumbnail_url=getattr(user, 'display_avatar', None) and user.display_avatar.url,
            guild=channel.guild,
        )
