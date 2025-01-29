import discord
from discord.ext import commands
import random
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

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
                    description=f"У вас недостаточно средств для такой ставки!\n"
                              f"Ваш баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        user_data['balance'] -= bet
        save_user(user_id, user_data)

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
            title=f"🎰 Блекджек | Ставка: {bet:,} {EMOJIS['MONEY']}",
            description=(
                f"{EMOJIS['DOT']} **Ваши карты:** {' '.join(player_hand)} `{self.calculate_hand(player_hand)}`\n"
                f"{EMOJIS['DOT']} **Карты дилера:** {dealer_hand[0]} ? `?`\n\n"
                f"**Выберите действие:**\n"
                f"🎯 `Взять карту` - получить еще одну карту\n"
                f"⏹️ `Достаточно` - закончить набор карт"
            ),
            color="BLUE",
            footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
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
                    title=f"🎰 Блекджек | Ставка: {game['bet']:,} {EMOJIS['MONEY']}",
                    description=(
                        f"{EMOJIS['DOT']} **Ваши карты:** {' '.join(game['player_hand'])} `{player_value}`\n"
                        f"{EMOJIS['DOT']} **Карты дилера:** {game['dealer_hand'][0]} ? `?`\n\n"
                        f"**Выберите действие:**\n"
                        f"🎯 `Взять карту` - получить еще одну карту\n"
                        f"⏹️ `Достаточно` - закончить набор карт"
                    ),
                    color="BLUE",
                    footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
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
            result = "❌ **Перебор!** Вы проиграли..."
            color = "RED"
        elif dealer_value > 21:
            result = "🎉 **Поздравляем!** У дилера перебор - вы выиграли!"
            color = "GREEN"
        elif player_value > dealer_value:
            result = "🎉 **Поздравляем!** Ваша комбинация оказалась сильнее!"
            color = "GREEN"
        elif player_value < dealer_value:
            result = "❌ **Вы проиграли!** Комбинация дилера оказалась сильнее."
            color = "RED"
        else:
            result = "🤝 **Ничья!** Ваши комбинации равны."
            color = "YELLOW"

        description = (
            f"{EMOJIS['DOT']} **Ваши карты:** {' '.join(game['player_hand'])} `{player_value}`\n"
            f"{EMOJIS['DOT']} **Карты дилера:** {' '.join(game['dealer_hand'])} `{dealer_value}`\n\n"
        )

        description += result + "\n"

        if player_value > 21:
            winnings = 0
        elif dealer_value > 21:
            winnings = game['bet'] * 2
        elif player_value > dealer_value:
            winnings = game['bet'] * 2
        else:
            winnings = game['bet']

        if winnings > 0:
            user_id = str(interaction.user.id)
            user_data = get_user(user_id)
            user_data['balance'] += winnings
            save_user(user_id, user_data)

        if winnings > 0:
            description += f"\n💰 **Выигрыш:** {winnings:,} {EMOJIS['MONEY']}"

        embed = create_embed(
            title="🎰 Результаты игры в Блекджек",
            description=description,
            color=color,
            footer={"text": f"Игрок: {interaction.user.name}", "icon_url": interaction.user.display_avatar.url}
        )
        
        del self.active_games[interaction.user.id]
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(BlackJack(bot))
