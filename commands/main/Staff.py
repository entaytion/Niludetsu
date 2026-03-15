from discord.ext import commands
from Niludetsu.config import PARTNER_MANAGER_ID, EVENT_MANAGER_ID, JUNIOR_MODERATOR_ID, MODERATOR_ID, SENIOR_MODERATOR_ID, ADMIN_MODERATOR_ID, ADMINISTRATOR_ID, SERVER_TEAM_ID
from Niludetsu import Embed

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="staff")
    async def staff(self, ctx):
        """Отобразить информацию о составе команды"""
        guild = ctx.guild
        if not guild:
            await ctx.send("Команда работает только на сервере.")
            return

        # Получаем роли
        pm_role = guild.get_role(PARTNER_MANAGER_ID)
        event_mgr_role = guild.get_role(EVENT_MANAGER_ID)
        jr_mod_role = guild.get_role(JUNIOR_MODERATOR_ID)
        mod_role = guild.get_role(MODERATOR_ID)
        sr_mod_role = guild.get_role(SENIOR_MODERATOR_ID)
        admin_mod_role = guild.get_role(ADMIN_MODERATOR_ID)
        admin_role = guild.get_role(ADMINISTRATOR_ID)
        server_team_role = guild.get_role(SERVER_TEAM_ID)

        # Функция для получения членов роли
        def get_role_members(role):
            if not role:
                return []
            return [m.mention for m in role.members if not m.bot]

        # Получаем членов команды
        pm_members = get_role_members(pm_role)
        event_mgr_members = get_role_members(event_mgr_role)
        jr_mod_members = get_role_members(jr_mod_role)
        mod_members = get_role_members(mod_role)
        sr_mod_members = get_role_members(sr_mod_role)
        admin_mod_members = get_role_members(admin_mod_role)
        admin_members = get_role_members(admin_role)

        # Создаём embed
        embed = Embed.default(
            title="👥 Состав команды Æther!",
            description="Информация о членах команды сервера",
        )

        # Администрация
        embed.add_field(
            name="👑 Администраторы",
            value=", ".join(admin_members) if admin_members else "Нет",
            inline=True
        )

        # Админ-модераторы
        embed.add_field(
            name="🛡️ Админ-модераторы",
            value=", ".join(admin_mod_members) if admin_mod_members else "Нет",
            inline=True
        )

        # Старшие модераторы
        embed.add_field(
            name="⭐ Старшие модераторы",
            value=", ".join(sr_mod_members) if sr_mod_members else "Нет",
            inline=True
        )

        # Модераторы
        embed.add_field(
            name="🔨 Модераторы",
            value=", ".join(mod_members) if mod_members else "Нет",
            inline=True
        )

        # Младшие модераторы
        embed.add_field(
            name="📋 Младшие модераторы",
            value=", ".join(jr_mod_members) if jr_mod_members else "Нет",
            inline=True
        )

        # Менеджер событий
        embed.add_field(
            name="🎉 Менеджер событий",
            value=", ".join(event_mgr_members) if event_mgr_members else "Нет",
            inline=False
        )

        # Менеджер партнёрств
        embed.add_field(
            name="🤝 Менеджер партнёрств",
            value=", ".join(pm_members) if pm_members else "Нет",
            inline=False
        )

        # Команды
        embed.add_field(name="━━━━━━━━━━━━━━━━━━", value="", inline=False)

        server_team_members = get_role_members(server_team_role)
        embed.add_field(
            name="🏢 Команда сервера",
            value=", ".join(server_team_members) if server_team_members else "Нет",
            inline=False
        )
        embed.set_footer(text=f"Всего участников: {len(set([m for members in [admin_members, admin_mod_members, sr_mod_members, mod_members, jr_mod_members, event_mgr_members, pm_members, server_team_members] for m in members]))} человек")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Staff(bot))
