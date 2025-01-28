import discord
from discord import Interaction, ButtonStyle
from discord.ext import commands
import random
import asyncio
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class SpinAgainButton(discord.ui.Button):
    def __init__(self, slots_instance, bet):
        super().__init__(style=ButtonStyle.primary, label="Крутить еще раз", custom_id="spin_again")
        self.slots = slots_instance
        self.bet = bet
        
    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        await self.slots.play_slots(interaction, self.bet, interaction.message)

class SpinAgainNewBetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.secondary, label="Изменить ставку", custom_id="new_bet")
        
    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(
            embed=create_embed(
                description="Используйте команду `/slots` чтобы сделать новую ставку"
            )
        )

class SlotsView(discord.ui.View):
    def __init__(self, slots_instance, bet):
        super().__init__(timeout=180)
        self.add_item(SpinAgainButton(slots_instance, bet))
        self.add_item(SpinAgainNewBetButton())

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.slots_emojis = ['🍎', '🍊', '🍋', '🍒', '🍇', '🍓', '💎']
        self.multipliers = {
            3: {'💎': 10, '🍓': 7, '🍇': 6, '🍒': 5, '🍋': 4, '🍊': 3, '🍎': 2},
            2: {'💎': 3, '🍓': 2, '🍇': 2, '🍒': 2, '🍋': 1.5, '🍊': 1.5, '🍎': 1.5}
        }

    async def spin_animation(self, message, bet):
        for _ in range(3):
            slots = [random.choice(self.slots_emojis) for _ in range(3)]
            slots_display = " | ".join(slots)
            description = f"**{EMOJIS['DOT']} Слоты крутятся...** \n[ {slots_display} ]\n\n"
            description += f"**{EMOJIS['DOT']} Ставка:** {bet} {EMOJIS['MONEY']}"
            
            embed = create_embed(
                title="🎰 Слот-машина",
                description=description
            )
            
            await message.edit(embed=embed)
            await asyncio.sleep(0.7)

    async def play_slots(self, interaction: Interaction, bet: int, message=None):
        try:
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
                if message:
                    await message.edit(
                        embed=create_embed(
                            description=f"У вас недостаточно средств для такой ставки!\n"
                                      f"Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        embed=create_embed(
                            description=f"У вас недостаточно средств для такой ставки!\n"
                                      f"Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                            color="RED"
                        ),
                        ephemeral=True
                    )
                return

            user_data['balance'] -= bet
            save_user(user_id, user_data)

            initial_embed = create_embed(
                title="🎰 Слот-машина",
                description="**Крутим барабаны...**"
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
            description = f"**{EMOJIS['DOT']} Слоты:** [ {slots_display} ]\n\n"

            if winnings > 0:
                user_data = get_user(user_id)
                user_data['balance'] += winnings
                save_user(user_id, user_data)
                
                description += f"**{EMOJIS['DOT']} Поздравляем! Вы выиграли!**\n"
                description += f"**{EMOJIS['DOT']} Множитель:** x{self.multipliers[max_count][winning_symbol]}\n"
                description += f"**{EMOJIS['DOT']} Выигрыш:** {winnings:,} {EMOJIS['MONEY']}\n"
                description += f"**{EMOJIS['DOT']} Баланс:** {user_data['balance']:,} {EMOJIS['MONEY']}"
                color = "GREEN"
            else:
                description += f"**{EMOJIS['DOT']} К сожалению, вы проиграли!**\n"
                description += f"**{EMOJIS['DOT']} Ставка:** {bet:,} {EMOJIS['MONEY']}\n"
                description += f"**{EMOJIS['DOT']} Баланс:** {user_data['balance']:,} {EMOJIS['MONEY']}"
                color = "RED"

            embed = create_embed(
                title="🎰 Слот-машина",
                description=description,
                color=color
            )

            view = SlotsView(self, bet)
            await message.edit(embed=embed, view=view)

        except Exception as e:
            print(f"Error in slots command: {e}")
            error_embed = create_embed(
                description="Произошла ошибка при выполнении команды."
            )
            if message:
                await message.edit(embed=error_embed)
            else:
                await interaction.followup.send(embed=error_embed)

    @discord.app_commands.command(name="slots", description="Сыграть в слоты")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await self.play_slots(interaction, bet)

    @slots.error
    async def slots_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пожалуйста, укажите сумму ставки: `/slots bet:сумма`"
                )
            )

async def setup(bot):
    await bot.add_cog(Slots(bot))