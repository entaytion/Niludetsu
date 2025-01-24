import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import random

class RPSButton(discord.ui.Button):
    def __init__(self, emoji: str, choice: str):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji, label=choice)
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        view: RPSView = self.view
        
        # Проверяем, нажал ли кнопку игрок
        if interaction.user != view.player:
            await interaction.response.send_message(
                "Это не ваша игра!"
            )
            return

        # Выбор бота
        bot_choice = random.choice(["Камень", "Ножницы", "Бумага"])
        
        # Определяем победителя
        result = self.get_winner(self.choice, bot_choice)
        
        # Устанавливаем стили кнопок
        for button in view.children:
            button.disabled = True
            if button.choice == self.choice:
                button.style = discord.ButtonStyle.primary
            if button.choice == bot_choice:
                button.style = discord.ButtonStyle.danger

        # Формируем сообщение с результатом
        description = (
            f"**{interaction.user.mention} выбрал:** {self.choice}\n"
            f"**Бот выбрал:** {bot_choice}\n\n"
        )

        if result == "win":
            description += "🎉 **Вы победили!**"
        elif result == "lose":
            description += "❌ **Вы проиграли!**"
        else:
            description += "🤝 **Ничья!**"

        await interaction.response.edit_message(
            embed=create_embed(
                title="🎮 Камень, ножницы, бумага",
                description=description
            ),
            view=view
        )

    def get_winner(self, player_choice: str, bot_choice: str) -> str:
        """Определяет победителя игры"""
        if player_choice == bot_choice:
            return "draw"
            
        winning_combinations = {
            "Камень": "Ножницы",
            "Ножницы": "Бумага",
            "Бумага": "Камень"
        }
        
        if winning_combinations[player_choice] == bot_choice:
            return "win"
        return "lose"

class RPSView(discord.ui.View):
    def __init__(self, player: discord.Member):
        super().__init__(timeout=60)  # 1 минута на игру
        self.player = player
        
        # Добавляем кнопки
        self.add_item(RPSButton("🗿", "Камень"))
        self.add_item(RPSButton("✂️", "Ножницы"))
        self.add_item(RPSButton("📄", "Бумага"))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(
                embed=create_embed(
                    title="🎮 Камень, ножницы, бумага",
                    description="**Игра окончена из-за таймаута!** ⏰"
                ),
                view=self
            )
        except:
            pass

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="rps",
        description="Сыграть в камень, ножницы, бумага"
    )
    @app_commands.describe(opponent="Противник, с которым хотите сыграть")
    async def rps(self, interaction: discord.Interaction, opponent: discord.Member = None):
        # Если оппонент не указан, играем с ботом
        if opponent is None:
            opponent = self.bot.user

        # Проверка, не играет ли игрок сам с собой
        if opponent == interaction.user:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете играть сами с собой!"
                )
            )
            return

        # Проверка на бота
        if opponent.bot and opponent != self.bot.user:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы можете играть с ботом!"
                )
            )
            return

        # Создаем игру
        view = RPSView(interaction.user)
        
        # Отправляем сообщение с игрой
        await interaction.response.send_message(
            embed=create_embed(
                title="🎮 Камень, ножницы, бумага",
                description=(
                    f"**{interaction.user.mention} vs {opponent.mention}**\n\n"
                    "Выберите свой вариант:"
                )
            ),
            view=view
        )
        
        # Сохраняем сообщение для таймаута
        view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(RPS(bot)) 