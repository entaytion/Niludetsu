import discord
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.settings import settings
from Niludetsu.database import database
from typing import List

MAIN_SERVER_ID = settings.SERVERS["MAIN_ID"]

# Роли для выдачи
ROLE_BASE = 1126146184482930740       # Базовая роль участника
ROLE_BOT = 1125344221960871999        # Бот
ROLE_GIVEAWAYS = 1364498617758388245  # Розыгрыши
ROLE_NEWS = 1364498609340416040       # Новости
ROLE_BAN = 1125344224108470373        # Роль бана
ROLE_UNVERIFIED = 1452231718944903249 # Роль неверифицированного

VERIFICATION_CHANNEL_ID = 1414934353087303720

# Роли для ботов
BOT_ROLES = [ROLE_BASE, ROLE_BOT]

# Роли для пользователей

USER_ROLES = [] # Роли выдаются только после верификации

class AutoRole(commands.Cog):
    """Автоматическая выдача ролей при входе"""

    def __init__(self, bot):
        self.bot = bot
        self.db = database

    async def _has_active_ban(self, guild_id: int, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя активный бан

        Args:
            guild_id: ID сервера
            user_id: ID пользователя

        Returns:
            True если есть активный бан
        """
        try:
            # Получаем все активные наказания пользователя
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
            print(f"[AutoRole] Ошибка проверки бана: {e}")
            return False

    async def _get_roles_to_assign(
        self,
        member: discord.Member,
        has_ban: bool
    ) -> List[discord.Role]:
        """
        Определяет список ролей для выдачи

        Args:
            member: Участник сервера
            has_ban: Есть ли у участника активный бан

        Returns:
            Список ролей для выдачи
        """
        guild = member.guild
        roles_to_add = []

        # Если есть бан — выдаём только роль бана
        if has_ban:
            ban_role = guild.get_role(ROLE_BAN)
            if ban_role and ban_role not in member.roles:
                roles_to_add.append(ban_role)
            return roles_to_add

        # Определяем роли в зависимости от типа пользователя
        role_ids = BOT_ROLES if member.bot else USER_ROLES

        # Получаем объекты ролей
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role and role not in member.roles:
                roles_to_add.append(role)

        return roles_to_add

    async def _assign_roles(self, member: discord.Member) -> None:
        """
        Выдаёт роли пользователю при входе на сервер

        Логика:
        - Если есть активный бан → только роль бана
        - Если бот → базовая роль
        - Если пользователь → базовая + уведомления

        Args:
            member: Участник сервера
        """
        guild = member.guild

        has_ban = await self._has_active_ban(guild.id, member.id)

        roles_to_add = await self._get_roles_to_assign(member, has_ban)

        # Проверка на whitelist (join_count > 1) через таблицу invites
        # Если пользователь уже был на сервере (join_count > 1), мы ему доверяем
        if not member.bot and not has_ban:
            # Якщо верифікація відключена в settings — видаємо всі ролі одразу
            if not getattr(settings, "VERIFICATION_ENABLED", True):
                base_role = guild.get_role(ROLE_BASE)
                news_role = guild.get_role(ROLE_NEWS)
                giveaways_role = guild.get_role(ROLE_GIVEAWAYS)

                if base_role: roles_to_add.append(base_role)
                if news_role: roles_to_add.append(news_role)
                if giveaways_role: roles_to_add.append(giveaways_role)
            else:
                try:
                    invite_record = await self.db.get_row("invites", guild_id=str(guild.id), user_id=str(member.id))
                    join_count = invite_record.get("join_count", 0) if invite_record else 0

                    if join_count > 1:
                       # Whitelist: даем роль Verified (BASE) + News + Giveaways
                       base_role = guild.get_role(ROLE_BASE)
                       news_role = guild.get_role(ROLE_NEWS)
                       giveaways_role = guild.get_role(ROLE_GIVEAWAYS)

                       if base_role: roles_to_add.append(base_role)
                       if news_role: roles_to_add.append(news_role)
                       if giveaways_role: roles_to_add.append(giveaways_role)

                       # Notification
                       try:
                           channel = guild.get_channel(VERIFICATION_CHANNEL_ID)
                           if channel:
                               embed = Embed(
                                   title="Автоматическая верификация",
                                   description=f"Пользователь {member.mention} автоматический верифицирован (WhiteList).",
                                   color=Colors.SUCCESS
                               )
                               embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
                               embed.add_field(name="🔢 Входов", value=f"`{join_count}`", inline=True)
                               embed.set_thumbnail(url=member.display_avatar.url)
                               embed.set_footer(text="Система доверия (WhiteList)")
                               await channel.send(embed=embed)
                       except Exception as ex:
                           print(f"[AutoRole] Failed to send whitelist log: {ex}")
                    else:
                       # Not Whitelisted: даем роль Unverified
                       unverified_role = guild.get_role(ROLE_UNVERIFIED)
                       if unverified_role:
                           roles_to_add.append(unverified_role)

                except Exception as e:
                    print(f"[AutoRole] Ошибка проверки whitelist: {e}")
                    # Fallback: даем Unverified на всякий случай
                    unverified_role = guild.get_role(ROLE_UNVERIFIED)
                    if unverified_role:
                        roles_to_add.append(unverified_role)



        if roles_to_add:
            try:
                reason = "Роль бана" if has_ban else "Автоматическая выдача ролей"
                await member.add_roles(*roles_to_add, reason=reason)

                # Логируем
                role_names = ", ".join(r.name for r in roles_to_add)
                print(f"[AutoRole] Выданы роли {member.name}: {role_names}")

            except discord.Forbidden:
                print(f"[AutoRole] Нет прав для выдачи ролей {member.name}")
            except Exception as e:
                print(f"[AutoRole] Ошибка выдачи ролей {member.name}: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Обработчик события входа участника на сервер"""
        # Работаем только с основным сервером
        if member.guild.id != MAIN_SERVER_ID:
            return

        await self._assign_roles(member)

    @commands.command(name="enableverify")
    @commands.has_permissions(administrator=True)
    async def enable_verify(self, ctx):
        """Включити систему верифікації."""
        await settings.set("VERIFICATION_ENABLED", True)
        unverified_role = ctx.guild.get_role(ROLE_UNVERIFIED)
        role_name = unverified_role.name if unverified_role else "Unknown"
        await ctx.send(f"{Emojis.SUCCESS} Верификация **включена**. Теперь новые пользователи будут получать роль `{role_name}`.")

    @commands.command(name="disableverify")
    @commands.has_permissions(administrator=True)
    async def disable_verify(self, ctx):
        """Відключити систему верифікації."""
        await settings.set("VERIFICATION_ENABLED", False)
        await ctx.send(f"{Emojis.SUCCESS} Верификация **отключена**. Теперь новые пользователи будут получать все роли сразу.")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))

