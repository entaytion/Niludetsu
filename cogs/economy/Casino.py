import discord
from discord.ext import commands
import random
import asyncio
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class BetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None

    @discord.ui.button(label="Красное", style=discord.ButtonStyle.red, emoji="🟥")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "красное"
        self.stop()
        
    @discord.ui.button(label="Черное", style=discord.ButtonStyle.gray, emoji="⬛")
    async def black(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "черное"
        self.stop()

    @discord.ui.button(label="Зеленое", style=discord.ButtonStyle.green, emoji="🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "зеленое"
        self.stop()

    @discord.ui.button(label="Четное", style=discord.ButtonStyle.blurple, emoji="2️⃣")
    async def even(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "четное"
        self.stop()

    @discord.ui.button(label="Нечетное", style=discord.ButtonStyle.blurple, emoji="1️⃣")
    async def odd(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "нечетное"
        self.stop()

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roulette_numbers = {
            0: {"color": "🟢", "type": "zero"},
            **{i: {"color": "⬛" if i % 2 == 0 else "🟥", "type": "even" if i % 2 == 0 else "odd"}
               for i in range(1, 37)}
        }

    @discord.app_commands.command(name="casino", description="Сыграть в казино")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def casino(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        user_id = str(interaction.user.id)
        user_data = get_user(user_id)
        
        if not user_data:
            user_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }
            save_user(user_id, user_data)

        if user_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ У вас недостаточно средств для такой ставки!\n"
                              f"Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Выбор типа ставки через кнопки
        view = BetView()
        embed = create_embed(
            title="🎰 Рулетка | Выбор ставки",
            description=(
                f"**Ваша ставка:** {bet:,} {EMOJIS['MONEY']}\n\n"
                "**Выберите тип ставки:**\n"
                "🟥 `Красное` - x2\n"
                "⬛ `Черное` - x2\n"
                "🟢 `Зеленое` - x35\n"
                "2️⃣ `Четное` - x2\n"
                "1️⃣ `Нечетное` - x2"
            ),
            color="BLUE",
            footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
        )
        await interaction.response.send_message(embed=embed, view=view)
        
        # Ожидание выбора ставки
        await view.wait()
        if view.value is None:
            await interaction.edit_original_response(
                embed=create_embed(
                    description="❌ Время выбора ставки истекло!",
                    color="RED"
                ),
                view=None
            )
            return

        bet_type = view.value
        user_data['balance'] -= bet
        save_user(user_id, user_data)

        # Начальное сообщение
        embed = create_embed(
            title="🎰 Рулетка | Запуск",
            description="🎲 Рулетка запущена...\n\n" +
                       f"**Ставка:** {bet:,} {EMOJIS['MONEY']}\n" +
                       f"**Тип ставки:** {bet_type}",
            color="BLUE",
            footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
        )
        await interaction.edit_original_response(embed=embed, view=None)

        # Анимация
        arrows = ["⬇️", "↙️", "⬅️", "↖️", "⬆️", "↗️", "➡️", "↘️"]
        arrow_pos = 0
        for i in range(3):
            numbers = [random.randint(0, 36) for _ in range(5)]
            animation = " ".join([self.roulette_numbers[n]["color"] for n in numbers])
            arrow_pos = (arrow_pos + 1) % len(arrows)
            embed.description = (
                f"🎲 Рулетка крутится...\n"
                f"{' ' * 10}{arrows[arrow_pos]}\n"
                f"{animation}\n\n"
                f"**Ставка:** {bet:,} {EMOJIS['MONEY']}\n"
                f"**Тип ставки:** {bet_type}"
            )
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(0.7)

        # Финальный результат с падающей стрелкой
        number = random.randint(0, 36)
        result = self.roulette_numbers[number]
        
        # Анимация падения стрелки
        arrow_frames = ["⬆️", "↗️", "➡️", "↘️", "⬇️"]
        for frame in arrow_frames:
            animation = [self.roulette_numbers[number]["color"]] * 5
            embed.description = (
                f"🎲 Рулетка останавливается...\n"
                f"{' ' * 10}{frame}\n"
                f"{' '.join(animation)}\n\n"
                f"**Ставка:** {bet:,} {EMOJIS['MONEY']}\n"
                f"**Тип ставки:** {bet_type}"
            )
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(0.3)

        winnings = 0
        
        # Определение выигрыша
        if bet_type == "зеленое" and number == 0:
            winnings = bet * 35
        elif bet_type == "черное" and result["color"] == "⬛":
            winnings = bet * 2
        elif bet_type == "красное" and result["color"] == "🟥":
            winnings = bet * 2
        elif bet_type == "четное" and number != 0 and number % 2 == 0:
            winnings = bet * 2
        elif bet_type == "нечетное" and number != 0 and number % 2 != 0:
            winnings = bet * 2

        if winnings > 0:
            user_data = get_user(user_id)
            user_data['balance'] += winnings
            save_user(user_id, user_data)
            result_text = f"🎉 **Поздравляем! Вы выиграли!**"
            color = "GREEN"
        else:
            result_text = "❌ **Вы проиграли!**"
            color = "RED"

        final_embed = create_embed(
            title="🎰 Результаты игры в рулетку",
            description=(
                f"**Выпало число:** {number} {result['color']}\n"
                f"{' ' * 11}⬇️\n"
                f"{result['color'] * 5}\n\n"
                f"**Ваша ставка:** {bet:,} {EMOJIS['MONEY']}\n"
                f"**Тип ставки:** {bet_type}\n\n"
                f"{result_text}\n" +
                (f"💰 **Выигрыш:** {winnings:,} {EMOJIS['MONEY']}" if winnings > 0 else "")
            ),
            color=color,
            footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
        )
        await interaction.edit_original_response(embed=final_embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))
