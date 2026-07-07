import discord
from discord.ext import commands
from Niludetsu.tools.Embed import Embed
from Niludetsu import send
from typing import Optional
from Niludetsu.analytics.repository import AnalyticsRepository
from Niludetsu import Time
import pendulum


# Роли-"пропуск" — якщо є хоча б одна, користувача не кікають
SAFE_ROLE_IDS = {
    1125344222027980863,
    1133089102883987547,
    1125344222027980866,
    1125344222027980865,
}

TARGET_ROLE_ID = 1126146184482930740
INACTIVE_ROLE_ID = 1452231718944903249


class PurgeCog(commands.Cog):
    """Команди масового кіку: по ролях і по активності в чаті."""

    def __init__(self, bot):
        self.bot = bot
        self.repo = AnalyticsRepository()
        self.time = Time()

    # ─── Допоміжні ───

    def _is_protected(self, member: discord.Member, invoker_id: int) -> bool:
        """Чи захищений мембер від кіку."""
        if member.bot:
            return True
        if member.id == member.guild.owner_id:
            return True
        if member.id == invoker_id:
            return True
        member_role_ids = {role.id for role in member.roles}
        if member_role_ids & SAFE_ROLE_IDS:
            return True
        return False

    async def _confirm(self, ctx: commands.Context, text: str) -> bool:
        """Запитує підтвердження. Повертає True якщо підтверджено."""
        warn_embed = Embed.warning(
            title="⚠️ Підтвердження",
            description=f"{text}\nНапиши `ПІДТВЕРДЖУЮ` протягом 30 секунд."
        )
        await ctx.send(embed=warn_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == "ПІДТВЕРДЖУЮ"

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
            return True
        except Exception:
            cancel_embed = Embed.error(description="Час вийшов. Операцію скасовано.")
            await send(ctx, embed=cancel_embed)
            return False

    async def _kick_list(self, ctx: commands.Context, members: list, reason: str):
        """Кікає список мемберів з прогресом."""
        progress_embed = Embed.warning(
            title="🧹 Чистка запущена",
            description=f"Кікаю **{len(members)}** учасників, зачекай..."
        )
        msg = await ctx.send(embed=progress_embed)

        kicked = 0
        failed = 0

        for member in members:
            try:
                await member.kick(reason=f"{reason} | {ctx.author}")
                kicked += 1
            except Exception:
                failed += 1

        description = f"Кікнуто: **{kicked}** учасників."
        if failed:
            description += f"\nНе вдалось кікнути: **{failed}**."

        result_embed = Embed.success(
            title="🧹 Чистка завершена",
            description=description
        )
        await msg.edit(embed=result_embed)

    # ─── !purge_members ───

    @commands.command(name="purge_members")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(kick_members=True)
    async def purge_members(self, ctx: commands.Context):
        """
        🧹 Кікнути всіх учасників без жодної з захищених ролей.

        Примеры:
        • !purge_members
        """
        confirmed = await self._confirm(ctx, "Ця команда **кікне** всіх учасників без жодної з захищених ролей.")
        if not confirmed:
            return

        to_kick = [m for m in ctx.guild.members if not self._is_protected(m, ctx.author.id)]

        if not to_kick:
            return await send(ctx, embed=Embed.success(description="Нікого кікати — у всіх є потрібні ролі."))

        await self._kick_list(ctx, to_kick, "Purge: немає захищених ролей")

    # ─── !purge_lurkers ───

    @commands.command(name="purge_lurkers")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(kick_members=True)
    async def purge_lurkers(self, ctx: commands.Context, depth: Optional[int] = 5000):
        """
        👻 Кікнути всіх, хто ніколи не писав у жодному каналі.
        Сканує останні N повідомлень в кожному текстовому каналі.

        Параметри:
        • depth — кількість повідомлень на канал (за замовчуванням 5000)

        Примеры:
        • !purge_lurkers
        • !purge_lurkers 10000
        """
        guild = ctx.guild
        depth = max(100, min(depth, 50000))  # клемп 100–50000

        # ── Фаза 1: сканування каналів ──
        scan_embed = Embed.warning(
            title="🔍 Сканування чатів",
            description=f"Перевіряю історію повідомлень (до **{depth}** на канал)...\nЦе може зайняти кілька хвилин."
        )
        msg = await ctx.send(embed=scan_embed)

        active_user_ids: set[int] = set()
        text_channels = [
            ch for ch in guild.channels
            if isinstance(ch, discord.TextChannel) and ch.permissions_for(guild.me).read_message_history
        ]

        scanned = 0
        total_channels = len(text_channels)

        for channel in text_channels:
            try:
                async for message in channel.history(limit=depth):
                    active_user_ids.add(message.author.id)
            except (discord.Forbidden, discord.HTTPException):
                pass

            scanned += 1
            # Оновлюємо прогрес кожні 5 каналів
            if scanned % 5 == 0 or scanned == total_channels:
                try:
                    progress_embed = Embed.warning(
                        title="🔍 Сканування чатів",
                        description=(
                            f"Просканувано **{scanned}/{total_channels}** каналів\n"
                            f"Знайдено **{len(active_user_ids)}** активних користувачів"
                        )
                    )
                    await msg.edit(embed=progress_embed)
                except Exception:
                    pass

        # ── Фаза 2: збираємо лурксрів ──
        lurkers = []
        for member in guild.members:
            if self._is_protected(member, ctx.author.id):
                continue
            if member.id in active_user_ids:
                continue  # писав хоча б раз — живи
            lurkers.append(member)

        if not lurkers:
            done_embed = Embed.success(
                title="👻 Лурксрів не знайдено",
                description=(
                    f"Просканувано **{total_channels}** каналів, "
                    f"**{len(active_user_ids)}** активних юзерів.\n"
                    "Усі учасники хоча б раз писали в чат або мають захищену роль."
                )
            )
            return await msg.edit(embed=done_embed)

        # Показуємо результат сканування і просимо підтвердження
        scan_done_embed = Embed.warning(
            title="👻 Сканування завершено",
            description=(
                f"Просканувано **{total_channels}** каналів\n"
                f"Активних юзерів: **{len(active_user_ids)}**\n"
                f"Лурксрів для кіку: **{len(lurkers)}**\n\n"
                "Напиши `ПІДТВЕРДЖУЮ` протягом 30 сек щоб кікнути їх."
            )
        )
        await msg.edit(embed=scan_done_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == "ПІДТВЕРДЖУЮ"

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
        except Exception:
            cancel_embed = Embed.error(description="Час вийшов. Операцію скасовано.")
            return await send(ctx, embed=cancel_embed)

        # ── Фаза 3: кікаємо ──
        await self._kick_list(ctx, lurkers, "Purge lurkers: ніколи не писав в чат")

    # ─── !purge_inactive ───

    @commands.command(name="purge_inactive")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def purge_inactive(self, ctx: commands.Context):
        """
        📉 Знайти всіх з роллю 1126146184482930740, хто не писав більше місяця.
        Забирає всі ролі та видає 1452231718944903249.
        """
        guild = ctx.guild
        target_role = guild.get_role(TARGET_ROLE_ID)
        inactive_role = guild.get_role(INACTIVE_ROLE_ID)

        if not target_role or not inactive_role:
            return await send(ctx, embed=Embed.error(description="Не знайдено цільову роль або роль неактивності в константах."))

        # Отримуємо аналітику для всього сервера
        rows = await self.repo.db.where("user_analytics", filters=[{"column": "guild_id", "value": str(guild.id)}])
        analytics = {row["user_id"]: row for row in rows}

        threshold = self.time.now().subtract(months=1)
        to_process = []

        for member in target_role.members:
            if self._is_protected(member, ctx.author.id):
                continue
            
            user_data = analytics.get(str(member.id))
            is_inactive = False

            # Якщо юзер зайшов на сервер менше місяця тому — він не може бути "неактивним більше місяця"
            if member.joined_at and member.joined_at > threshold:
                continue

            if not user_data:
                # Мембера немає в базі — значить він нічого не писав з моменту запуску трекера
                # Тут можна додати логіку перевірки member.joined_at, якщо трекер новий
                is_inactive = True
            else:
                last_active = self.time.parse(user_data.get("last_updated"))
                if not last_active or last_active < threshold:
                    is_inactive = True

            if is_inactive:
                to_process.append(member)

        if not to_process:
            return await send(ctx, embed=Embed.success(description="Не знайдено неактивних користувачів з цією роллю."))

        confirm_text = f"Ця команда змінить ролі для **{len(to_process)}** учасників (забере всі і дасть роль неактивності)."
        if not await self._confirm(ctx, confirm_text):
            return

        progress_embed = Embed.warning(
            title="⏳ Обробка неактивних",
            description=f"Оновлюю ролі для **{len(to_process)}** учасників..."
        )
        msg = await ctx.send(embed=progress_embed)

        success = 0
        failed = 0

        for member in to_process:
            try:
                # Видаємо нову роль і видаляємо всі старі (крім @everyone)
                await member.edit(roles=[inactive_role], reason="Purge: неактивність понад місяць")
                success += 1
            except Exception:
                failed += 1

        result_embed = Embed.success(
            title="✅ Обробка завершена",
            description=f"Оновлено: **{success}**\nПомилок: **{failed}**"
        )
        await msg.edit(embed=result_embed)


async def setup(bot):
    await bot.add_cog(PurgeCog(bot))
