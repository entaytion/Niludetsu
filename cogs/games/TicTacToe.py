import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
import random

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        state = view.board[self.y][self.x]

        if state in (view.X, view.O):
            return

        if interaction.user != view.current_player:
            await interaction.response.send_message(
                embed=Embed(
                    description="Сейчас не ваш ход!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if view.current_player == view.playerX:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            view.board[self.y][self.x] = view.X
            view.current_player = view.playerO
            content = f"Ход игрока {view.playerO.mention}"
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            view.board[self.y][self.x] = view.O
            view.current_player = view.playerX
            content = f"Ход игрока {view.playerX.mention}"

        self.disabled = True
        winner = view.check_board_winner()

        if winner is not None:
            if winner == view.X:
                content = f"{view.playerX.mention} победил!"
                color = "GREEN"
            elif winner == view.O:
                content = f"{view.playerO.mention} победил!"
                color = "GREEN"
            else:
                content = "Ничья!"
                color = "BLUE"

            for child in view.children:
                child.disabled = True
        else:
            color = "BLUE"

        await interaction.response.edit_message(
            embed=Embed(
                title="🎮 Крестики-нолики",
                description=content,
                color=color
            ),
            view=view
        )

class TicTacToeView(discord.ui.View):
    X = -1
    O = 1
    Tie = 2

    def __init__(self, playerX: discord.Member, playerO: discord.Member):
        super().__init__()
        self.current_player = playerX
        self.board = [[0, 0, 0] for _ in range(3)]
        self.playerX = playerX
        self.playerO = playerO

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        # Проверка по горизонтали
        for row in self.board:
            value = sum(row)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Проверка по вертикали
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Проверка по диагонали
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # Проверка на ничью
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tictactoe", description="Сыграть в крестики-нолики")
    @app_commands.describe(opponent="Противник для игры")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете играть с ботом!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        if opponent == interaction.user:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете играть сами с собой!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        view = TicTacToeView(interaction.user, opponent)
        await interaction.response.send_message(
            embed=Embed(
                title="🎮 Крестики-нолики",
                description=f"Ход игрока {interaction.user.mention}",
                color="BLUE"
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))