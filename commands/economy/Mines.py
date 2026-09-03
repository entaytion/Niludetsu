import math
import random
import discord
from discord.ext import commands
from Niludetsu import EconomyManager, Embed, Emojis

class MinesView(discord.ui.View):
    def __init__(self, cog: "Mines", ctx: commands.Context, bet: int, bombs_count: int) -> None:
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.bet = bet
        self.bombs_count = bombs_count
        self.total_tiles = 16
        self.safe_count = self.total_tiles - bombs_count
        self.opened_count = 0
        self.finished = False

        self.bombs_positions = set(random.sample(range(self.total_tiles), bombs_count))
        self.tile_buttons: list[discord.ui.Button] = []

        for i in range(self.total_tiles):
            row = i // 4
            btn = discord.ui.Button(
                label="\u200b",
                emoji="⬛",
                style=discord.ButtonStyle.secondary,
                row=row,
                custom_id=f"tile_{i}",
            )
            btn.callback = self._create_tile_callback(i)
            self.tile_buttons.append(btn)
            self.add_item(btn)

        self.cashout_btn = discord.ui.Button(
            label="Забрать (0x)",
            emoji="💰",
            style=discord.ButtonStyle.success,
            row=4,
            disabled=True,
            custom_id="cashout_btn",
        )
        self.cashout_btn.callback = self._cashout_callback
        self.add_item(self.cashout_btn)

        self.status_btn = discord.ui.Button(
            label=f"💣 {self.bombs_count} | 💎 0/{self.safe_count}",
            style=discord.ButtonStyle.secondary,
            row=4,
            disabled=True,
            custom_id="status_btn",
        )
        self.add_item(self.status_btn)

    def _calculate_multiplier(self) -> float:
        if self.opened_count == 0:
            return 1.0
        n, m = self.total_tiles, self.bombs_count
        prob = 1.0
        for i in range(self.opened_count):
            prob *= (n - m - i) / (n - i)
        mult = 0.96 / prob
        return max(1.05, round(mult, 2))

    def _create_tile_callback(self, index: int):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("Это не ваша игра!", ephemeral=True)
                return
            if self.finished:
                await interaction.response.defer()
                return

            button = self.tile_buttons[index]
            if button.disabled:
                await interaction.response.defer()
                return

            if index in self.bombs_positions:
                self.finished = True
                button.emoji = "💥"
                button.style = discord.ButtonStyle.danger
                button.disabled = True

                for idx, btn in enumerate(self.tile_buttons):
                    btn.disabled = True
                    if idx in self.bombs_positions and idx != index:
                        btn.emoji = "💣"
                        btn.style = discord.ButtonStyle.danger
                    elif idx not in self.bombs_positions and btn.emoji == "⬛":
                        btn.emoji = "◽"

                self.cashout_btn.disabled = True
                self.status_btn.label = f"💣 Взрыв! Потеряно: {self.bet:,}"

                embed = Embed.error(
                    title="💥 Поражение в Сапёре!",
                    description=f"{self.ctx.author.mention}, вы наступили на мину и потеряли **{self.bet:,}** {Emojis.MONEY}!",
                )
                self.stop()
                await interaction.response.edit_message(embed=embed, view=self)
                return

            self.opened_count += 1
            button.emoji = "💎"
            button.style = discord.ButtonStyle.success
            button.disabled = True

            mult = self._calculate_multiplier()
            current_win = int(self.bet * mult)

            if self.opened_count == self.safe_count:
                self.finished = True
                for btn in self.tile_buttons:
                    btn.disabled = True
                self.cashout_btn.disabled = True
                self.status_btn.label = f"🏆 Все алмазы! {mult}x"

                uid, gid = str(self.ctx.author.id), str(self.ctx.guild.id)
                await self.cog.economy.add_money(uid, gid, current_win, event="mines_win")

                embed = Embed.success(
                    title="🏆 Невероятная победа!",
                    description=f"{self.ctx.author.mention}, вы открыли **ВСЕ алмазы**!\n"
                                f"Множитель: **{mult}x**\n"
                                f"Выигрыш: **+{current_win:,}** {Emojis.MONEY}!",
                )
                self.stop()
                await interaction.response.edit_message(embed=embed, view=self)
                return

            self.cashout_btn.disabled = False
            self.cashout_btn.label = f"Забрать {current_win:,} ({mult}x)"
            self.status_btn.label = f"💣 {self.bombs_count} | 💎 {self.opened_count}/{self.safe_count}"

            embed = Embed.default(
                title="💣 Сапёр (Mines)",
                description=f"Игрок: {self.ctx.author.mention}\n"
                            f"Ставка: **{self.bet:,}** {Emojis.MONEY}\n"
                            f"Мин на поле: **{self.bombs_count}**\n"
                            f"Открыто алмазов: **{self.opened_count}/{self.safe_count}**\n"
                            f"Текущий выигрыш: **{current_win:,}** {Emojis.MONEY} (**{mult}x**)\n\n"
                            f"Жмите следующую клетку или заберите выигрыш!",
            )
            await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def _cashout_callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Это не ваша игра!", ephemeral=True)
            return
        if self.finished or self.opened_count == 0:
            await interaction.response.defer()
            return

        self.finished = True
        mult = self._calculate_multiplier()
        win_amount = int(self.bet * mult)

        for idx, btn in enumerate(self.tile_buttons):
            btn.disabled = True
            if idx in self.bombs_positions:
                btn.emoji = "💣"
                btn.style = discord.ButtonStyle.secondary
            elif btn.emoji == "⬛":
                btn.emoji = "◽"

        self.cashout_btn.disabled = True
        self.status_btn.label = f"💰 Забрано: {win_amount:,} ({mult}x)"

        uid, gid = str(self.ctx.author.id), str(self.ctx.guild.id)
        await self.cog.economy.add_money(uid, gid, win_amount, event="mines_win")

        embed = Embed.success(
            title="💰 Выигрыш зафиксирован!",
            description=f"{self.ctx.author.mention} вовремя остановился и забрал **+{win_amount:,}** {Emojis.MONEY}!\n"
                        f"Множитель: **{mult}x** | Открыто алмазов: **{self.opened_count}/{self.safe_count}**",
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        if not self.finished:
            self.finished = True
            for btn in self.tile_buttons:
                btn.disabled = True
            self.cashout_btn.disabled = True
            self.status_btn.label = "Время вышло"

class Mines(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.economy = EconomyManager()

    @commands.hybrid_command(name="mines", aliases=["сапер", "мины"], description="Сыграть в сапёра на монеты")
    async def mines(self, ctx: commands.Context, bet: int, bombs: int = 3) -> None:
        if bet < 10:
            await ctx.reply(embed=Embed.error("Минимальная ставка — 10 монет!"), ephemeral=True)
            return

        if bombs < 1 or bombs > 14:
            await ctx.reply(embed=Embed.error("Количество мин должно быть от 1 до 14!"), ephemeral=True)
            return

        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        acc = await self.economy.get_account(uid, gid)
        if acc.get("balance", 0) < bet:
            await ctx.reply(embed=Embed.error("У вас недостаточно средств на балансе!"), ephemeral=True)
            return

        res = await self.economy.remove_money(uid, gid, bet, event="mines_bet")
        if not res.ok:
            await ctx.reply(embed=Embed.error(res.message or "Ошибка снятия средств!"), ephemeral=True)
            return

        view = MinesView(self, ctx, bet, bombs)
        embed = Embed.default(
            title="💣 Сапёр (Mines)",
            description=f"Игрок: {ctx.author.mention}\n"
                        f"Ставка: **{bet:,}** {Emojis.MONEY}\n"
                        f"Количество мин: **{bombs}** (из 16)\n\n"
                        f"Кликайте по серым клеткам, чтобы открывать алмазы 💎.\n"
                        f"Каждый алмаз увеличивает ваш выигрыш!\n"
                        f"Вы можете забрать монеты в любой момент кнопкой **Забрать**.",
        )
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Mines(bot))

