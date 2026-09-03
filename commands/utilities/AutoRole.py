import discord
from discord.ext import commands
from Niludetsu import logger
from Niludetsu.settings import settings
from Niludetsu.database import database
from typing import List

MAIN_SERVER_ID = settings.SERVERS["MAIN_ID"]

ROLE_BASE = 1126146184482930740
ROLE_BOT = 1125344221960871999
ROLE_GIVEAWAYS = 1364498617758388245
ROLE_NEWS = 1364498609340416040
ROLE_BAN = 1125344224108470373

BOT_ROLES = [ROLE_BASE, ROLE_BOT]
USER_ROLES = [ROLE_BASE, ROLE_NEWS, ROLE_GIVEAWAYS]

class AutoRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database

    async def _has_active_ban(self, guild_id: int, user_id: int) -> bool:
        try:
            punishments = await self.db.where(
                "user_rudiments",
                filters=[
                    {"column": "guild_id", "value": str(guild_id)},
                    {"column": "user_id", "value": str(user_id)},
                    {"column": "active", "value": True},
                    {"column": "type", "value": "ban"},
                ]
            )
            return len(punishments) > 0
        except Exception as e:
            logger.error(f"[AutoRole] Ошибка проверки бана: {e}")
            return False

    async def _get_roles_to_assign(
        self,
        member: discord.Member,
        has_ban: bool
    ) -> List[discord.Role]:
        guild = member.guild
        roles_to_add = []

        if has_ban:
            ban_role = guild.get_role(ROLE_BAN)
            if ban_role and ban_role not in member.roles:
                roles_to_add.append(ban_role)
            return roles_to_add

        role_ids = BOT_ROLES if member.bot else USER_ROLES
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role and role not in member.roles:
                roles_to_add.append(role)

        return roles_to_add

    async def _assign_roles(self, member: discord.Member) -> None:
        guild = member.guild
        has_ban = await self._has_active_ban(guild.id, member.id)
        roles_to_add = await self._get_roles_to_assign(member, has_ban)

        if roles_to_add:
            try:
                reason = "Роль бана" if has_ban else "Автоматическая выдача ролей"
                await member.add_roles(*roles_to_add, reason=reason)
                role_names = ", ".join(r.name for r in roles_to_add)
                logger.info(f"[AutoRole] Выданы роли {member.name}: {role_names}")
            except discord.Forbidden:
                logger.warning(f"[AutoRole] Нет прав для выдачи ролей {member.name}")
            except Exception as e:
                logger.error(f"[AutoRole] Ошибка выдачи ролей {member.name}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != MAIN_SERVER_ID:
            return
        await self._assign_roles(member)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
