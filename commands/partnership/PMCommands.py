import discord
from .RewardSystem import RewardSystem, AdRedeemView
from discord.ext import commands
from Niludetsu import Embed, Colors
from Niludetsu.locale import _
from Niludetsu.database import database
from typing import Optional

class PMCommands(commands.Cog):
    """Команды для партнер-менеджеров (лидерборд и награды)"""

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.partnership_manager = None  # Будет инициализировано после загрузки Partnership
        self.reward_system = None

    async def ensure_manager(self):
        """Убеждается, что partnership_manager инициализирован"""
        if not self.partnership_manager:
            partnership_cog = self.bot.get_cog("Partnership")
            if partnership_cog:
                self.partnership_manager = partnership_cog.partnership_manager
                self.reward_system = RewardSystem(self.bot, self.partnership_manager)
        return self.partnership_manager is not None

    @commands.command(name="pmleaderboard")
    async def pmleaderboard(self, ctx):
        """Показывает топ партнер-менеджеров по баллам"""
        t = _(ctx=ctx)

        if not await self.ensure_manager():
            await ctx.reply(t("partnership", "pm_system_unavailable"))
            return

        # Получаем топ ПМов
        top_managers = await self.partnership_manager.get_leaderboard(limit=10)

        if not top_managers:
            await ctx.reply(
                embed=Embed.info(
                    title=t("partnership", "pm_leaderboard_title"),
                    description=t("partnership", "pm_leaderboard_empty")
                ),
                mention_author=False
            )
            return

        description = ""

        for i, manager in enumerate(top_managers, 1):
            user = self.bot.get_user(int(manager['user_id']))
            username = user.mention if user else f"<@{manager['user_id']}>"

            # Форматируем баллы
            points = manager['points']
            if points == 1:
                points_word = t("partnership", "partner_points_word_1")
            elif 2 <= points <= 4:
                points_word = t("partnership", "partner_points_word_2")
            else:
                points_word = t("partnership", "partner_points_word_5")

            description += (
                f"**{i}.** {username} — **{points}** {points_word}\n"
                f"- 🆕 {manager['new_partnerships']} {t('partnership', 'pm_leaderboard_new')}, "
                f"🔄 {manager['renewed_partnerships']} {t('partnership', 'pm_leaderboard_renewed')}\n\n"
            )

        embed = Embed.default(
            title=t("partnership", "pm_leaderboard_full_title"),
            description=description.strip()
        )
        embed.set_footer(text=t("partnership", "pm_leaderboard_footer"))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="pminfo")
    async def pminfo(self, ctx, user: Optional[discord.Member] = None):
        """Показывает профиль партнер-менеджера"""
        t = _(ctx=ctx)

        if not await self.ensure_manager():
            await ctx.reply(t("partnership", "pm_system_unavailable"))
            return

        # Если пользователь не указан, показываем профиль автора команды
        if not user:
            user = ctx.author

        # Проверяем, является ли пользователь партнер-менеджером
        partnership_cog = self.bot.get_cog("Partnership")
        if not partnership_cog:
            await ctx.reply(t("partnership", "pm_system_unavailable"))
            return

        pm_role_id = partnership_cog.partner_manager_role_id
        is_pm = any(r.id == pm_role_id for r in user.roles) or user.guild_permissions.administrator

        if not is_pm:
            await ctx.reply(
                embed=Embed.error(description=t("partnership", "pm_no_pm_rights")),
                mention_author=False
            )
            return

        # Получаем статистику менеджера
        user_stats = await self.partnership_manager.get_manager_stats(str(user.id))

        # Создаем эмбед с профилем
        embed = Embed.default(
            title=f"<:aePartnership:1394707131386564700> {user.display_name}",
            color=Colors.INFO
        )

        # Форматируем статистику
        new_word = t("partnership", "pm_stats_new_single") if user_stats['new_partnerships'] == 1 else t("partnership", "pm_stats_new_multi")
        renew_word = t("partnership", "pm_stats_renew_single") if user_stats['renewed_partnerships'] == 1 else t("partnership", "pm_stats_renew_multi")

        points = user_stats['points']
        if points == 1:
            points_word = t("partnership", "partner_points_word_1")
        elif 2 <= points <= 4:
            points_word = t("partnership", "partner_points_word_2")
        else:
            points_word = t("partnership", "partner_points_word_5")

        stats_text = (
            f"{t('partnership', 'pm_stats_header')}\n"
            f"• **{user_stats['new_partnerships']}** {new_word} партнёрств\n"
            f"• **{user_stats['renewed_partnerships']}** {renew_word}\n"
            f"{t('partnership', 'pm_stats_points', points=points, points_word=points_word)}"
        )

        embed.description = stats_text
        embed.set_thumbnail(url=user.display_avatar.url)

        # Добавляем позицию в лидерборде, если есть баллы
        if user_stats['points'] > 0:
            leaderboard = await self.partnership_manager.get_leaderboard(limit=50)
            position = next((i for i, m in enumerate(leaderboard, 1) if m['user_id'] == str(user.id)), None)
            if position:
                medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else f"#{position}"
                embed.add_field(
                    name=t("partnership", "pm_position_title"),
                    value=t("partnership", "pm_position_value", medal=medal),
                    inline=False
                )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="pmrewards")
    async def pmrewards(self, ctx: commands.Context):
        """Показывает доступную награду и позволяет её обменять"""
        t = _(ctx=ctx)

        if not await self.ensure_manager():
            await ctx.reply(
                embed=Embed.error(description=t("partnership", "pm_system_unavailable")),
                mention_author=False
            )
            return

        user_id = str(ctx.author.id)
        user_points = await self.partnership_manager.get_user_points(user_id)

        reward = self.reward_system.REWARDS["ad_500"]
        if user_points >= reward["cost"]:
            status = t("partnership", "pm_rewards_available")
        else:
            status = t("partnership", "pm_rewards_not_enough", count=reward['cost'] - user_points)

        embed = Embed.default(
            title=t("partnership", "pm_rewards_title"),
            description=t("partnership", "pm_rewards_balance", points=user_points),
        )

        embed.add_field(
            name=reward["name"],
            value=f"{reward['description']}\n{t('partnership', 'pm_rewards_cost')} **{reward['cost']}** баллов\n{t('partnership', 'pm_rewards_status')} {status}",
            inline=False
        )

        view = AdRedeemView(self.reward_system, user_id)
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    """Настройка расширения"""
    await bot.add_cog(PMCommands(bot))
