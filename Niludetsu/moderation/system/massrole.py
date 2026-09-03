from ...tools.Embed import Embed

"""
Система массовой выдачи/снятия ролей с расширенными проверками безопасности.
"""
import asyncio, discord
import Niludetsu.config as config
from Niludetsu.moderation.exceptions import ModerationError

from typing import Optional, List, Tuple

class MassRoleSystem:

    def __init__(self, bot):
        self.bot = bot

        self.dangerous_perms = [
            "administrator", "manage_guild", "manage_roles", "manage_channels",
            "ban_members", "kick_members", "manage_webhooks", "mention_everyone",
            "view_audit_log", "manage_messages", "moderate_members",
            "manage_emojis_and_stickers", "manage_threads", "manage_nicknames",
            "move_members", "mute_members", "deafen_members"
        ]

        self.perm_translations = {
            "administrator": "Администратор",
            "manage_guild": "Управление сервером",
            "manage_roles": "Управление ролями",
            "manage_channels": "Управление каналами",
            "ban_members": "Банить участников",
            "kick_members": "Кикать участников",
            "manage_webhooks": "Управление вебхуками",
            "mention_everyone": "Упоминать всех (@everyone/@here)",
            "view_audit_log": "Просмотр журнала аудита",
            "manage_messages": "Управление сообщениями",
            "moderate_members": "Модерировать участников (таймаут)",
            "manage_emojis_and_stickers": "Управление эмодзи и стикерами",
            "manage_threads": "Управление ветками",
            "manage_nicknames": "Управление никнеймами",
            "move_members": "Перемещать участников",
            "mute_members": "Заглушать участников в голосовых",
            "deafen_members": "Оглушать участников в голосовых"
        }

    def has_dangerous_permissions(self, role: discord.Role) -> Tuple[bool, List[str]]:
        role_perms = role.permissions
        found_dangerous = []

        for perm_name in self.dangerous_perms:
            if hasattr(role_perms, perm_name) and getattr(role_perms, perm_name):
                translated = self.perm_translations.get(perm_name, perm_name)
                found_dangerous.append(f"• {translated}")

        return len(found_dangerous) > 0, found_dangerous

    def validate_role_hierarchy(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        role: discord.Role
    ) -> Tuple[bool, Optional[str]]:
        if moderator.top_role <= role and moderator != guild.owner:
            return False, "Эта роль выше или равна вашей роли!"

        if guild.me.top_role <= role:
            return False, "Эта роль выше или равна моей роли! Переместите мою роль выше в настройках сервера."

        return True, None

    def validate_role(
        self,
        guild: discord.Guild,
        role: discord.Role
    ) -> Tuple[bool, Optional[str]]:
        if role == guild.default_role:
            return False, "Нельзя массово назначать роль @everyone!"

        if role.managed:
            return False, "Эта роль управляется интеграцией (бот/буст) и не может быть назначена вручную!"

        if role.is_premium_subscriber():
            return False, "Нельзя массово назначать роль бустера сервера!"

        return True, None

    async def process_mass_role(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        role: discord.Role,
        action: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[int, int, List[str]]:
        members = [m for m in guild.members if not m.bot]

        if not members:
            raise ModerationError("На сервере нет участников для обработки!")

        success_count = 0
        error_count = 0
        processed_members = []

        batch_size = 10
        total_batches = (len(members) + batch_size - 1) // batch_size

        for batch_index, i in enumerate(range(0, len(members), batch_size), 1):
            batch = members[i:i + batch_size]

            for member in batch:
                try:
                    if action == "add":
                        if role not in member.roles:
                            await member.add_roles(
                                role,
                                reason=f"Массовая выдача ролей от {moderator} ({moderator.id})"
                            )
                            success_count += 1
                            processed_members.append(f"✅ {member.mention}")
                        else:
                            processed_members.append(f"⏭️ {member.mention} (уже есть)")

                    elif action == "remove":
                        if role in member.roles:
                            await member.remove_roles(
                                role,
                                reason=f"Массовое снятие ролей от {moderator} ({moderator.id})"
                            )
                            success_count += 1
                            processed_members.append(f"❌ {member.mention}")
                        else:
                            processed_members.append(f"⏭️ {member.mention} (нет роли)")

                except discord.Forbidden:
                    error_count += 1
                    processed_members.append(f"⚠️ {member.mention} (нет прав)")
                except discord.HTTPException:
                    error_count += 1
                    processed_members.append(f"⚠️ {member.mention} (ошибка API)")
                except Exception as e:
                    error_count += 1
                    processed_members.append(f"⚠️ {member.mention} (ошибка: {str(e)[:50]})")

            if progress_callback:
                await progress_callback(min(i + batch_size, len(members)), len(members))

            if batch_index < total_batches:
                await asyncio.sleep(1.0)

        return success_count, error_count, processed_members

    async def log_mass_role_action(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        role: discord.Role,
        action: str,
        success_count: int,
        error_count: int
    ) -> None:
        action_text = "🎭 Массовая выдача ролей" if action == "add" else "🎭 Массовое снятие ролей"
        action_verb = "выдана" if action == "add" else "снята"

        embed = Embed(
            title=action_text,
            description=(
                f"**Роль:** {role.mention}\n"
                f"**Модератор:** {moderator.mention} ({moderator.id})\n"
                f"**Успешно:** {success_count}\n"
                f"**Ошибок:** {error_count}\n"
                f"**Итого:** Роль {action_verb} {success_count} участникам"
            ),
            color=0x77dd77 if error_count == 0 else 0xffa500
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        log_channel = None

        if config.NOTIFICATION_CHANNEL_ID:
            log_channel = guild.get_channel(int(config.NOTIFICATION_CHANNEL_ID))

        if not log_channel:
            log_channel = discord.utils.get(
                guild.text_channels,
                name__in=["mod-logs", "модерация", "logs"]
            )

        if log_channel:
            try:
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

