import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
import random

class Minesweeper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.numbers = {
            0: "0️⃣",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣"
        }
        self.bomb = "💣"
        self.cover = "||"
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

    def create_board(self, size: int, bombs: int) -> list:
        # Создаем пустое поле
        board = [[0 for _ in range(size)] for _ in range(size)]
        
        # Расставляем бомбы
        bombs_placed = 0
        while bombs_placed < bombs:
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            if board[y][x] != self.bomb:
                board[y][x] = self.bomb
                bombs_placed += 1
                
                # Увеличиваем счетчики вокруг бомбы
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if 0 <= y + dy < size and 0 <= x + dx < size:
                            if board[y + dy][x + dx] != self.bomb:
                                board[y + dy][x + dx] += 1
                                
        return board

    def format_board(self, board: list) -> str:
        size = len(board)
        result = []
        
        for y in range(size):
            row = []
            for x in range(size):
                cell = board[y][x]
                if cell == self.bomb:
                    row.append(f"{self.cover}{self.bomb}{self.cover}")
                else:
                    row.append(f"{self.cover}{self.numbers[cell]}{self.cover}")
            result.append("".join(row))
            
        return "\n".join(result)

    minesweeper_group = app_commands.Group(name="minesweeper", description="Команды игры Сапёр")

    @minesweeper_group.command(name="play", description="Сыграть в сапёра")
    @app_commands.describe(
        size="Размер поля (от 5 до 10)",
        bombs="Количество бомб (от 3 до размер²/3)"
    )
    async def minesweeper(
        self,
        interaction: discord.Interaction,
        size: int = 5,
        bombs: int = 5
    ):
        # Проверяем размер поля
        if not 5 <= size <= 10:
            await interaction.response.send_message(
                embed=Embed(
                    description="Размер поля должен быть от 5 до 10!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        # Проверяем количество бомб
        max_bombs = (size * size) // 3
        if not 3 <= bombs <= max_bombs:
            await interaction.response.send_message(
                embed=Embed(
                    description=f"Количество бомб должно быть от 3 до {max_bombs}!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        # Создаем и форматируем поле
        board = self.create_board(size, bombs)
        formatted_board = self.format_board(board)
        
        await interaction.response.send_message(
            embed=Embed(
                title="💣 Сапер",
                description=f"**Размер поля:** {size}x{size}\n"
                          f"**Количество бомб:** {bombs}\n\n"
                          f"{formatted_board}",
                color="BLUE"
            )
        )

    @minesweeper_group.command(name="help", description="Показать помощь по игре Сапёр")
    async def minesweeper_help(self, interaction: discord.Interaction):
        embed=Embed(
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
                "• `/minesweeper play size:10 bombs:5` - настроенная игра"
            )
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Minesweeper(bot)) 