import discord
from discord import Interaction, ButtonStyle
from discord.ext import commands
import random
import asyncio
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class SpinAgainButton(discord.ui.Button):
    def __init__(self, slots_instance, bet):
        super().__init__(style=ButtonStyle.primary, label="Крутить еще раз", emoji="🎰")
        self.slots = slots_instance
        self.bet = bet
        
    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.slots.last_player:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Это не ваша игра!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
        await interaction.response.defer()
        await self.slots.play_slots(interaction, self.bet, interaction.message)

class SpinAgainNewBetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.secondary, label="Изменить ставку", emoji="💰")
        
    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            embed=Embed(
                description="Используйте команду `/slots` чтобы сделать новую ставку",
                color="BLUE"
            ),
            ephemeral=True
        )

class SlotsView(discord.ui.View):
    def __init__(self, slots_instance, bet):
        super().__init__(timeout=180)
        self.add_item(SpinAgainButton(slots_instance, bet))
        self.add_item(SpinAgainNewBetButton())

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.slots_emojis = ['🍎', '🍊', '🍋', '🍒', '🍇', '🍓', '💎']
        self.multipliers = {
            3: {'💎': 10, '🍓': 7, '🍇': 6, '🍒': 5, '🍋': 4, '🍊': 3, '🍎': 2},
            2: {'💎': 3, '🍓': 2, '🍇': 2, '🍒': 2, '🍋': 1.5, '🍊': 1.5, '🍎': 1.5}
        }
        self.last_player = None

    async def spin_animation(self, message, bet):
        for _ in range(3):
            slots = [random.choice(self.slots_emojis) for _ in range(3)]
            slots_display = " | ".join(slots)
            description = (
                f"🎲 **Слоты крутятся...**\n"
                f"[ {slots_display} ]\n\n"
                f"💰 **Ставка:** {bet:,} {EMOJIS['MONEY']}"
            )
            
            embed=Embed(
                title="🎰 Слот-машина",
                description=description,
                color="BLUE"
            )
            
            await message.edit(embed=embed)
            await asyncio.sleep(0.7)

    async def play_slots(self, interaction: Interaction, bet: int, message=None):
        user_id = str(interaction.user.id)
        self.last_player = interaction.user.id
        user_data = await self.db.ensure_user(user_id)

        if user_data['balance'] < bet:
            embed=Embed(
                description=f"❌ У вас недостаточно средств!\n"
                          f"💰 Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                color="RED"
            )
            if message:
                await message.edit(embed=embed, view=None)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Снимаем ставку
        await self.db.update(
            "users",
            where={"user_id": user_id},
            values={"balance": user_data['balance'] - bet}
        )

        initial_embed=Embed(
            title="🎰 Слот-машина",
            description="🎲 **Крутим барабаны...**",
            color="BLUE"
        )
        
        if message:
            await message.edit(embed=initial_embed)
        else:
            await interaction.followup.send(embed=initial_embed)
            message = await interaction.original_response()
        
        await self.spin_animation(message, bet)

        slots = [random.choice(self.slots_emojis) for _ in range(3)]
        symbol_counts = {}
        for symbol in slots:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        winnings = 0
        max_count = max(symbol_counts.values())
        if max_count >= 2:
            winning_symbol = max(symbol_counts.items(), key=lambda x: (x[1], self.multipliers[x[1]][x[0]]))[0]
            winnings = int(bet * self.multipliers[max_count][winning_symbol])

        slots_display = " | ".join(slots)
        description = [f"🎲 **Результат:** [ {slots_display} ]\n"]

        if winnings > 0:
            user_data = await self.db.get_row("users", user_id=user_id)
            new_balance = user_data['balance'] + winnings
            await self.db.update(
                "users",
                where={"user_id": user_id},
                values={"balance": new_balance}
            )
            
            description.extend([
                f"🎉 **Поздравляем! Вы выиграли!**",
                f"✨ **Множитель:** x{self.multipliers[max_count][winning_symbol]}",
                f"💰 **Выигрыш:** {winnings:,} {EMOJIS['MONEY']}",
                f"💳 **Баланс:** {new_balance:,} {EMOJIS['MONEY']}"
            ])
            color = "GREEN"
        else:
            description.extend([
                f"❌ **Вы проиграли!**",
                f"💰 **Ставка:** {bet:,} {EMOJIS['MONEY']}",
                f"💳 **Баланс:** {user_data['balance'] - bet:,} {EMOJIS['MONEY']}"
            ])
            color = "RED"

        embed=Embed(
            title="🎰 Слот-машина",
            description="\n".join(description),
            color=color
        )

        view = SlotsView(self, bet)
        await message.edit(embed=embed, view=view)

    @discord.app_commands.command(name="slots", description="Сыграть в слоты")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await self.play_slots(interaction, bet)

    @slots.error
    async def slots_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(
            embed=Embed(
                description="❌ Пожалуйста, укажите сумму ставки: `/slots bet:сумма`",
                color="RED"
            ),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Slots(bot))