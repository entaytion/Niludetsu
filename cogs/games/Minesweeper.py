import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import random

class Minesweeper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Эмодзи для цифр и мин
        self.numbers = {
            0: "||:zero:||",
            1: "||:one:||",
            2: "||:two:||",
            3: "||:three:||",
            4: "||:four:||",
            5: "||:five:||",
            6: "||:six:||",
            7: "||:seven:||",
            8: "||:eight:||",
            "mine": "||:bomb:||"
        }
        # Стандартные настройки
        self.default_settings = {
            "rows": 8,
            "cols": 8,
            "mines": 10
        }
        # Ограничения
        self.limits = {
            "min_size": 4,
            "max_size": 12,
            "max_mines": 50
        }

    def create_board(self, rows, cols, mines):
        # Создаем пустое поле
        board = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # Размещаем мины
        mines_placed = 0
        while mines_placed < mines:
            x = random.randint(0, rows - 1)
            y = random.randint(0, cols - 1)
            if board[x][y] != "mine":
                board[x][y] = "mine"
                mines_placed += 1
                
                # Увеличиваем счетчики вокруг мины
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        new_x, new_y = x + dx, y + dy
                        if (0 <= new_x < rows and 
                            0 <= new_y < cols and 
                            board[new_x][new_y] != "mine"):
                            board[new_x][new_y] += 1
        
        return board

    def board_to_string(self, board):
        return "\n".join(
            "".join(self.numbers[cell] for cell in row)
            for row in board
        )

    minesweeper_group = app_commands.Group(name="minesweeper", description="Команды игры Сапёр")

    @minesweeper_group.command(name="play", description="Сыграть в сапёра")
    @app_commands.describe(
        rows="Количество строк (4-12, по умолчанию 8)",
        cols="Количество столбцов (4-12, по умолчанию 8)",
        mines="Количество мин (максимум 50, по умолчанию 10)"
    )
    async def minesweeper(
        self, 
        interaction: discord.Interaction, 
        rows: int = None,
        cols: int = None,
        mines: int = None
    ):
        # Если параметры не указаны, используем стандартные
        if rows is None:
            rows = self.default_settings["rows"]
        if cols is None:
            cols = self.default_settings["cols"]
        if mines is None:
            mines = self.default_settings["mines"]

        # Проверяем ограничения
        if rows < self.limits["min_size"] or rows > self.limits["max_size"]:
            return await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ Количество строк должно быть от {self.limits['min_size']} до {self.limits['max_size']}!"
                ),
                ephemeral=True
            )

        if cols < self.limits["min_size"] or cols > self.limits["max_size"]:
            return await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ Количество столбцов должно быть от {self.limits['min_size']} до {self.limits['max_size']}!"
                ),
                ephemeral=True
            )

        max_possible_mines = (rows * cols) - 1
        if mines < 1 or mines > min(max_possible_mines, self.limits["max_mines"]):
            return await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ Количество мин должно быть от 1 до {min(max_possible_mines, self.limits['max_mines'])}!"
                ),
                ephemeral=True
            )

        # Создаем игровое поле
        board = self.create_board(rows, cols, mines)
        board_str = self.board_to_string(board)

        # Создаем эмбед с игрой
        embed = create_embed(
            title="💣 Сапёр",
            description=(
                f"**Размер поля:** {rows}x{cols}\n"
                f"**Количество мин:** {mines}\n\n"
                f"{board_str}"
            )
        )

        await interaction.response.send_message(embed=embed)

    @minesweeper_group.command(name="help", description="Показать помощь по игре Сапёр")
    async def minesweeper_help(self, interaction: discord.Interaction):
        embed = create_embed(
            title="💣 Помощь по игре Сапёр",
            description=(
                "**Как играть:**\n"
                "1. Нажимайте на спойлеры, чтобы открыть клетки\n"
                "2. Цифры показывают количество мин вокруг клетки\n"
                "3. Избегайте мин 💣\n\n"
                "**Стандартные настройки:**\n"
                f"• Размер поля: {self.default_settings['rows']}x{self.default_settings['cols']}\n"
                f"• Количество мин: {self.default_settings['mines']}\n\n"
                "**Ограничения:**\n"
                f"• Размер поля: от {self.limits['min_size']}x{self.limits['min_size']} до {self.limits['max_size']}x{self.limits['max_size']}\n"
                f"• Максимум мин: {self.limits['max_mines']}\n\n"
                "**Примеры использования:**\n"
                "• `/minesweeper play` - стандартная игра\n"
                "• `/minesweeper play rows:10 cols:5 mines:10` - настроенная игра"
            )
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Minesweeper(bot)) 