import discord
from discord import Interaction, ButtonStyle
from discord.ext import commands
import random
import asyncio
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS, get_user, save_user, EMOJIS

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
                description="Используйте команду `/slots` чтобы сделать новую ставку",
                footer=FOOTER_SUCCESS
            ),
            ephemeral=True
        )

class SlotsView(discord.ui.View):
    def __init__(self, slots_instance, bet):
        super().__init__(timeout=180)
        self.add_item(SpinAgainButton(slots_instance, bet))
        self.add_item(SpinAgainNewBetButton())

class Slots(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.symbols = ['🍒', '🍊', '🍋', '🍇', '💎', '7️⃣']
        self.payouts = {
            '🍒': 2,  # x2 за три вишни
            '🍊': 3,  # x3 за три апельсина
            '🍋': 4,  # x4 за три лимона
            '🍇': 5,  # x5 за три винограда
            '💎': 10, # x10 за три алмаза
            '7️⃣': 15  # x15 за три семерки
        }

    async def spin_animation(self, message, bet):
        for _ in range(3):
            slots = [random.choice(self.symbols) for _ in range(3)]
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
            user_data = get_user(self.client, user_id)

            if user_data['balance'] < bet:
                if message:
                    await message.edit(
                        embed=create_embed(
                            description=f"Недостаточно средств! У вас есть: {user_data['balance']} {EMOJIS['MONEY']}",
                            footer=FOOTER_ERROR
                        )
                    )
                else:
                    await interaction.followup.send(
                        embed=create_embed(
                            description=f"Недостаточно средств! У вас есть: {user_data['balance']} {EMOJIS['MONEY']}",
                            footer=FOOTER_ERROR
                        )
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

            slots = [random.choice(self.symbols) for _ in range(3)]
            won = False
            multiplier = 0
            
            if slots[0] == slots[1] == slots[2]:
                won = True
                multiplier = self.payouts[slots[0]]

            slots_display = " | ".join(slots)
            description = f"**{EMOJIS['DOT']} Слоты:** [ {slots_display} ]\n\n"

            if won:
                winnings = bet * multiplier
                user_data['balance'] += winnings
                save_user(user_id, user_data)
                
                description += f"**{EMOJIS['DOT']} Поздравляем! Вы выиграли!**\n"
                description += f"**{EMOJIS['DOT']} Множитель:** x{multiplier}\n"
                description += f"**{EMOJIS['DOT']} Выигрыш:** {winnings} {EMOJIS['MONEY']}\n"
                description += f"**{EMOJIS['DOT']} Баланс:** {user_data['balance']} {EMOJIS['MONEY']}"
                
                footer = FOOTER_SUCCESS
            else:
                description += f"**{EMOJIS['DOT']} К сожалению, вы проиграли!**\n"
                description += f"**{EMOJIS['DOT']} Ставка:** {bet} {EMOJIS['MONEY']}\n"
                description += f"**{EMOJIS['DOT']} Баланс:** {user_data['balance']} {EMOJIS['MONEY']}"
                
                footer = FOOTER_ERROR

            embed = create_embed(
                title="🎰 Слот-машина",
                description=description,
                footer=footer
            )

            view = SlotsView(self, bet)
            await message.edit(embed=embed, view=view)

        except Exception as e:
            print(f"Error in slots command: {e}")
            error_embed = create_embed(
                description="Произошла ошибка при выполнении команды.",
                footer=FOOTER_ERROR
            )
            if message:
                await message.edit(embed=error_embed)
            else:
                await interaction.followup.send(embed=error_embed)

    @discord.app_commands.command(name="slots", description="Испытайте удачу в слот-машине")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def slots(self, interaction: Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Ставка должна быть больше 0!",
                    footer=FOOTER_ERROR
                )
            )
            return
            
        await interaction.response.defer()
        await self.play_slots(interaction, bet)

    @slots.error
    async def slots_error(self, interaction: Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пожалуйста, укажите сумму ставки: `/slots bet:сумма`",
                    footer=FOOTER_ERROR
                )
            )

async def setup(client):
    await client.add_cog(Slots(client))