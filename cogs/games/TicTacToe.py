import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import random

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        
        # Проверяем, ход ли игрока
        if interaction.user != view.current_player:
            await interaction.response.send_message("Сейчас не ваш ход!")
            return

        # Ставим символ
        self.label = "X" if view.current_player == view.player1 else "O"
        self.disabled = True
        
        if view.current_player == view.player1:
            self.style = discord.ButtonStyle.danger
        else:
            self.style = discord.ButtonStyle.success

        # Обновляем состояние игры
        view.board[self.y][self.x] = self.label

        # Проверяем победу
        if view.check_win():
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(
                embed=create_embed(
                    title="🎮 Крестики-нолики",
                    description=f"**Победитель: {view.current_player.mention}!** 🎉"
                ),
                view=view
            )
            return

        # Проверяем ничью
        if view.is_board_full():
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(
                embed=create_embed(
                    title="🎮 Крестики-нолики", 
                    description="**Ничья!** 🤝"
                ),
                view=view
            )
            return

        # Меняем игрока
        view.current_player = view.player2 if view.current_player == view.player1 else view.player1
        
        await interaction.response.edit_message(
            embed=create_embed(
                title="🎮 Крестики-нолики",
                description=f"Ход игрока: {view.current_player.mention}"
            ),
            view=view
        )

        # Если следующий ход бота и игра не закончена
        if view.current_player.bot and not view.check_win() and not view.is_board_full():
            await view.bot_move()

class TicTacToeView(discord.ui.View):
    def __init__(self, player1: discord.Member, player2: discord.Member, first_move: discord.Member):
        super().__init__(timeout=300)  # 5 минут на игру
        self.player1 = player1
        self.player2 = player2
        self.current_player = first_move
        self.board = [["\u200b" for _ in range(3)] for _ in range(3)]

        # Создаем кнопки
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    async def bot_move(self):
        """Логика хода бота"""
        # Проверяем возможность победы
        for button in self.children:
            if button.label == "\u200b":
                # Пробуем сделать ход
                button.label = "O"
                self.board[button.y][button.x] = "O"
                
                # Если этот ход ведет к победе, оставляем его
                if self.check_win():
                    button.style = discord.ButtonStyle.success
                    button.disabled = True
                    
                    # Отключаем все кнопки
                    for child in self.children:
                        child.disabled = True
                    
                    await self.message.edit(
                        embed=create_embed(
                            title="🎮 Крестики-нолики",
                            description=f"**Победитель: {self.current_player.mention}!** 🎉"
                        ),
                        view=self
                    )
                    return
                
                # Если нет, отменяем ход
                button.label = "\u200b"
                self.board[button.y][button.x] = "\u200b"

        # Проверяем необходимость блокировки победы противника
        for button in self.children:
            if button.label == "\u200b":
                # Пробуем сделать ход за противника
                button.label = "X"
                self.board[button.y][button.x] = "X"
                
                # Если этот ход ведет к победе противника, блокируем его
                if self.check_win():
                    button.label = "O"
                    self.board[button.y][button.x] = "O"
                    button.style = discord.ButtonStyle.success
                    button.disabled = True
                    
                    # Меняем игрока
                    self.current_player = self.player1
                    
                    await self.message.edit(
                        embed=create_embed(
                            title="🎮 Крестики-нолики",
                            description=f"Ход игрока: {self.current_player.mention}"
                        ),
                        view=self
                    )
                    return
                
                # Отменяем пробный ход
                button.label = "\u200b"
                self.board[button.y][button.x] = "\u200b"

        # Если нет выигрышных ходов, делаем случайный ход
        available_moves = [button for button in self.children if button.label == "\u200b"]
        if available_moves:
            button = random.choice(available_moves)
            button.label = "O"
            button.style = discord.ButtonStyle.success
            button.disabled = True
            self.board[button.y][button.x] = "O"

            # Проверяем ничью
            if self.is_board_full():
                for child in self.children:
                    child.disabled = True
                await self.message.edit(
                    embed=create_embed(
                        title="🎮 Крестики-нолики", 
                        description="**Ничья!** 🤝"
                    ),
                    view=self
                )
                return

            # Меняем игрока
            self.current_player = self.player1
            
            await self.message.edit(
                embed=create_embed(
                    title="🎮 Крестики-нолики",
                    description=f"Ход игрока: {self.current_player.mention}"
                ),
                view=self
            )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(
                embed=create_embed(
                    title="🎮 Крестики-нолики",
                    description="**Игра окончена из-за таймаута!** ⏰"
                ),
                view=self
            )
        except:
            pass

    def check_win(self):
        # Проверка строк
        for row in self.board:
            if row.count(row[0]) == 3 and row[0] != "\u200b":
                return True

        # Проверка столбцов
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != "\u200b":
                return True

        # Проверка диагоналей
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "\u200b":
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "\u200b":
            return True

        return False

    def is_board_full(self):
        return all(cell != "\u200b" for row in self.board for cell in row)

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tictactoe", description="Сыграть в крестики-нолики")
    @app_commands.describe(opponent="Противник, с которым хотите сыграть")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member = None):
        # Если противник не указан, играем с ботом
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
                    description="Вы можете играть только с этим ботом!"
                )
            )
            return

        # Случайно выбираем, кто ходит первым
        first_move = random.choice([interaction.user, opponent])
        
        # Создаем игру
        view = TicTacToeView(interaction.user, opponent, first_move)
        
        # Отправляем сообщение с игрой
        await interaction.response.send_message(
            embed=create_embed(
                title="🎮 Крестики-нолики",
                description=f"Ход игрока: {first_move.mention}\nПротивник: {opponent.mention if first_move == interaction.user else interaction.user.mention}"
            ),
            view=view
        )
        
        # Сохраняем сообщение для таймаута
        view.message = await interaction.original_response()
        
        # Если первый ход за ботом, делаем его
        if first_move.bot:
            await view.bot_move()

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))