import discord
from .RewardSystem import RewardSystem, AdRedeemView
from discord.ext import commands
from Niludetsu import Embed, Colors
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
        if not await self.ensure_manager():
            await ctx.reply("Система партнёрств временно недоступна.")
            return

        # Получаем топ ПМов
        top_managers = await self.partnership_manager.get_leaderboard(limit=10)

        if not top_managers:
            await ctx.reply(
                embed=Embed.info(
                    title="Топ партнер-менеджеров",
                    description="Пока нет партнер-менеджеров с баллами."
                ),
                mention_author=False
            )
            return

        description = ""

        for i, manager in enumerate(top_managers, 1):
            user = self.bot.get_user(int(manager['user_id']))
            username = user.mention if user else f"<@{manager['user_id']}>"

            # Форматируем баллы
            points_word = "балл" if manager['points'] == 1 else "балла" if 2 <= manager['points'] <= 4 else "баллов"

            description += (
                f"**{i}.** {username} — **{manager['points']}** {points_word}\n"
                f"- 🆕 {manager['new_partnerships']} новых партнёрств, 🔄 {manager['renewed_partnerships']} обновлений\n\n"
            )

        embed = Embed.default(
            title="Топ партнер-менеджеров по баллам",
            description=description.strip()
        )
        embed.set_footer(text="2 балла за новое партнерство, 1 балл за обновление после 12 часов")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="pminfo")
    async def pminfo(self, ctx, user: Optional[discord.Member] = None):
        """Показывает профиль партнер-менеджера"""
        if not await self.ensure_manager():
            await ctx.reply("Система партнёрств временно недоступна.")
            return

        # Если пользователь не указан, показываем профиль автора команды
        if not user:
            user = ctx.author

        # Проверяем, является ли пользователь партнер-менеджером
        partnership_cog = self.bot.get_cog("Partnership")
        if not partnership_cog:
            await ctx.reply("Система партнёрств временно недоступна.")
            return

        pm_role_id = partnership_cog.partner_manager_role_id
        is_pm = any(r.id == pm_role_id for r in user.roles) or user.guild_permissions.administrator

        if not is_pm:
            await ctx.reply(
                embed=Embed.error(description="У пользователя нет прав партнер-менеджера."),
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
        new_word = "новое" if user_stats['new_partnerships'] == 1 else "новых"
        renew_word = "обновление" if user_stats['renewed_partnerships'] == 1 else "обновлений"
        points_word = "балл" if user_stats['points'] == 1 else "балла" if 2 <= user_stats['points'] <= 4 else "баллов"

        stats_text = (
            f"📊 **Статистика партнёрств:**\n"
            f"• **{user_stats['new_partnerships']}** {new_word} партнёрств\n"
            f"• **{user_stats['renewed_partnerships']}** {renew_word}\n"
            f"💎 **Баллы:** {user_stats['points']} {points_word}"
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
                    name="> 🏆 Позиция в рейтинге",
                    value=f"{medal} место",
                    inline=False
                )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="pmrewards")
    async def pmrewards(self, ctx: commands.Context):
        """Показывает доступную награду и позволяет её обменять"""
        if not await self.ensure_manager():
            await ctx.reply(
                embed=Embed.error(description="Система партнёрств временно недоступна."),
                mention_author=False
            )
            return

        user_id = str(ctx.author.id)
        user_points = await self.partnership_manager.get_user_points(user_id)

        reward = self.reward_system.REWARDS["ad_500"]
        status = "✅ Доступно" if user_points >= reward["cost"] else f"❌ Не хватает {reward['cost'] - user_points} баллов"

        embed = Embed.default(
            title="Награда за баллы партнёрств",
            description=f"У вас **{user_points}** баллов",
        )

        embed.add_field(
            name=reward["name"],
            value=f"{reward['description']}\nСтоимость: **{reward['cost']}** баллов\nСтатус: {status}",
            inline=False
        )

        view = AdRedeemView(self.reward_system, user_id)
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    """Настройка расширения"""
    await bot.add_cog(PMCommands(bot))

