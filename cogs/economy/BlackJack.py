import discord
from discord.ext import commands
import random
import asyncio
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS, get_user, save_user

class BlackJack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deck = []
        self.card_values = {
            'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
        }
        self.suits = ['♠', '♥', '♦', '♣']
        self.active_games = {}

    def create_deck(self):
        deck = []
        for suit in self.suits:
            for card in self.card_values.keys():
                deck.append(f"{card}{suit}")
        random.shuffle(deck)
        return deck

    def calculate_hand(self, hand):
        value = 0
        aces = 0
        
        for card in hand:
            card_value = card[:-1]
            if card_value == 'A':
                aces += 1
            else:
                value += self.card_values[card_value]
                
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
                
        return value

    @discord.app_commands.command(name="blackjack", description="Сыграть в блекджек")
    @discord.app_commands.describe(bet="Сумма ставки")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Ставка должна быть больше 0!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        user_data = get_user(self.bot, str(interaction.user.id))
        if not user_data or user_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description="У вас недостаточно средств для такой ставки! Снимите деньги с банка командой /withdraw",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        user_data['balance'] -= bet
        save_user(str(interaction.user.id), user_data)

        deck = self.create_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        self.active_games[interaction.user.id] = {
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'bet': bet
        }

        embed = create_embed(
            title="Блекджек",
            description=f"**Ваши карты:** {' '.join(player_hand)} (Сумма: {self.calculate_hand(player_hand)})\n"
                       f"**Карты дилера:** {dealer_hand[0]} ?\n\n"
                       "Выберите действие:",
            footer=FOOTER_SUCCESS
        )

        view = discord.ui.View()
        hit_button = discord.ui.Button(label="Взять карту", style=discord.ButtonStyle.green, custom_id="hit")
        stand_button = discord.ui.Button(label="Достаточно", style=discord.ButtonStyle.red, custom_id="stand")
        
        async def hit_callback(interaction: discord.Interaction):
            game = self.active_games.get(interaction.user.id)
            if not game:
                return
                
            game['player_hand'].append(game['deck'].pop())
            player_value = self.calculate_hand(game['player_hand'])
            
            if player_value > 21:
                await self.end_game(interaction, "bust")
            else:
                embed = create_embed(
                    title="Блекджек",
                    description=f"**Ваши карты:** {' '.join(game['player_hand'])} (Сумма: {player_value})\n"
                               f"**Карты дилера:** {game['dealer_hand'][0]} ?\n\n"
                               "Выберите действие:",
                    footer=FOOTER_SUCCESS
                )
                await interaction.response.edit_message(embed=embed, view=view)

        async def stand_callback(interaction: discord.Interaction):
            await self.end_game(interaction, "stand")

        hit_button.callback = hit_callback
        stand_button.callback = stand_callback
        
        view.add_item(hit_button)
        view.add_item(stand_button)
        
        await interaction.response.send_message(embed=embed, view=view)

    async def end_game(self, interaction: discord.Interaction, reason: str):
        game = self.active_games.get(interaction.user.id)
        if not game:
            return
            
        player_value = self.calculate_hand(game['player_hand'])
        dealer_value = self.calculate_hand(game['dealer_hand'])
        
        if reason == "stand":
            while dealer_value < 17:
                game['dealer_hand'].append(game['deck'].pop())
                dealer_value = self.calculate_hand(game['dealer_hand'])

        result = ""
        winnings = 0
        
        if reason == "bust":
            result = "**Вы проиграли! У вас перебор!**"
        elif dealer_value > 21:
            result = "**Вы выиграли! У дилера перебор!**"
            winnings = game['bet'] * 2
        elif player_value > dealer_value:
            result = "**Вы выиграли!**"
            winnings = game['bet'] * 2
        elif player_value < dealer_value:
            result = "**Вы проиграли!**"
        else:
            result = "**Ничья!**"
            winnings = game['bet']

        if winnings > 0:
            user_data = get_user(self.bot, str(interaction.user.id))
            user_data['balance'] += winnings
            save_user(str(interaction.user.id), user_data)

        embed = create_embed(
            title="Блекджек - Конец игры",
            description=f"**Ваши карты:** {' '.join(game['player_hand'])} (Сумма: {player_value})\n"
                       f"**Карты дилера:** {' '.join(game['dealer_hand'])} (Сумма: {dealer_value})\n\n"
                       f"{result}\n"
                       f"{'<:aeOutlineDot:1266066158029770833> **Выигрыш:** ' + str(winnings) + ' монет' if winnings > 0 else ''}",
            footer=FOOTER_SUCCESS
        )
        
        del self.active_games[interaction.user.id]
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(BlackJack(bot))
