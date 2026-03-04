import random
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, send
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager

SLUT_SUCCESS_CHANCE = 0.65
SLUT_MIN_REWARD = 150
SLUT_MAX_REWARD = 400
SLUT_PENALTY_MIN = 100
SLUT_PENALTY_MAX = 300

SLUT_SUCCESS_MESSAGES = [
    "Ты провел ночь с богатым клиентом и получил щедрое вознаграждение.",
    "Твои танцы в клубе принесли хорошие чаевые от восторженных гостей.",
    "Соблазнительная фотосессия для журнала оказалась весьма прибыльной.",
    "Ты сопровождал влиятельную особу на вечеринку и получил солидную оплату.",
    "Приватный стриптиз для VIP-клиента принес щедрое вознаграждение.",
    "Ты поработал эскортом на закрытом мероприятии и заработал кучу денег.",
    "Соблазнительный массаж для богатого клиента принес отличные чаевые.",
    "Ты продал пару компрометирующих фото нужным людям за хорошие деньги.",
]

SLUT_FAIL_MESSAGES = [
    "Полиция нравов устроила рейд — тебя оштрафовали на месте.",
    "Клиент оказался мошенником и сбежал, не заплатив. Пришлось возместить убытки клубу.",
    "Тебя избили и ограбили в темном переулке после работы.",
    "Ты подхватил венерическое заболевание и потратил кучу денег на лечение.",
    "Твои фото попали не в те руки — пришлось платить за молчание.",
    "Клиент избил тебя и украл деньги. Медицинская помощь влетела в копеечку.",
]

class Slut(commands.Cog):
    """Команда для рискованного заработка с кулдауном."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="slut", description="💋 Рискованный способ заработка")
    @app_commands.describe()
    async def slut(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        can_use, error_msg = await self.economy.check_cooldown(user_id, guild_id, "slut")

        if not can_use:
            await send(ctx, embed=Embed.error(description=f"Ты недавно уже работал! {error_msg}"), ephemeral=True)
            return

        # Обновляем кулдаун
        await self.economy.update_cooldown(user_id, guild_id, "slut")

        # Случайный шанс успеха
        if random.random() <= SLUT_SUCCESS_CHANCE:
            # УСПЕХ
            reward = random.randint(SLUT_MIN_REWARD, SLUT_MAX_REWARD)
            success, message = await self.economy.add_money(
                user_id,
                guild_id,
                reward,
                share_spousal=True,
            )

            if not success:
                await send(ctx, embed=Embed.error(description=message), ephemeral=True)
                return

            wallet = await self.economy.get_wallet(user_id, guild_id)
            family = await self.economy.get_spousal_balance(user_id, guild_id)

            embed = Embed(
                title="💋 Работа удалась!",
                description=f"{random.choice(SLUT_SUCCESS_MESSAGES)}\n{message}",
                color=Colors.SUCCESS,
            )
            embed.add_field(name="Кошелёк", value=self.economy.format_money(wallet), inline=True)
            embed.add_field(name="Семейный счёт", value=self.economy.format_money(family), inline=True)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await send(ctx, embed=embed, ephemeral=False)

        else:
            # ПРОВАЛ
            penalty = random.randint(SLUT_PENALTY_MIN, SLUT_PENALTY_MAX)
            current_wallet = await self.economy.get_wallet(user_id, guild_id)

            # Вычитаем штраф (но не уходим в минус)
            actual_penalty = min(current_wallet, penalty)

            if actual_penalty > 0:
                await self.economy.remove_money(user_id, guild_id, actual_penalty)

            wallet = await self.economy.get_wallet(user_id, guild_id)

            embed = Embed(
                title="💔 Всё пошло не по плану!",
                description=(
                    f"{random.choice(SLUT_FAIL_MESSAGES)}\n"
                    f"Убытки: {self.economy.format_money(actual_penalty)}"
                ),
                color=Colors.ERROR,
            )
            embed.add_field(name="Осталось в кошельке", value=self.economy.format_money(wallet), inline=True)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await send(ctx, embed=embed, ephemeral=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slut(bot))

