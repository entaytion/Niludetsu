import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import random
import json
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class Game2048:
    def __init__(self):
        self.board = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
    
    def add_new_tile(self):
        empty = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty:
            i, j = random.choice(empty)
            self.board[i][j] = 2 if random.random() < 0.9 else 4
    
    def move(self, direction):
        # Сохраняем предыдущее состояние для проверки изменений
        old_board = [row[:] for row in self.board]
        old_score = self.score
        
        # Поворачиваем доску для унификации движений
        if direction == "up":
            self.rotate_ccw()
        elif direction == "right":
            self.rotate_ccw()
            self.rotate_ccw()
        elif direction == "down":
            self.rotate_cw()
            
        # Двигаем влево (базовое движение)
        for i in range(4):
            # Убираем нули
            row = [x for x in self.board[i] if x != 0]
            # Объединяем одинаковые числа
            for j in range(len(row)-1):
                if row[j] == row[j+1]:
                    row[j] *= 2
                    self.score += row[j]
                    row[j+1] = 0
            # Снова убираем нули после объединения
            row = [x for x in row if x != 0]
            # Дополняем нулями справа
            row.extend([0] * (4 - len(row)))
            self.board[i] = row
            
        # Возвращаем доску в исходное положение
        if direction == "up":
            self.rotate_cw()
        elif direction == "right":
            self.rotate_cw()
            self.rotate_cw()
        elif direction == "down":
            self.rotate_ccw()
            
        # Проверяем, изменилась ли доска
        if old_board != self.board:
            self.add_new_tile()
            return True
        return False
    
    def rotate_cw(self):
        self.board = [list(row) for row in zip(*self.board[::-1])]
        
    def rotate_ccw(self):
        self.board = [list(row) for row in zip(*self.board)][::-1]
    
    def is_game_over(self):
        # Проверяем наличие пустых клеток
        if any(0 in row for row in self.board):
            return False
            
        # Проверяем возможность объединения по горизонтали
        for i in range(4):
            for j in range(3):
                if self.board[i][j] == self.board[i][j+1]:
                    return False
                    
        # Проверяем возможность объединения по вертикали
        for i in range(3):
            for j in range(4):
                if self.board[i][j] == self.board[i+1][j]:
                    return False
                    
        return True
    
    def get_board_str(self):
        # Создаем строковое представление доски с эмодзи
        number_emojis = {
            0: Emojis.TILE_0,
            2: Emojis.TILE_2,
            4: Emojis.TILE_4,
            8: Emojis.TILE_8,
            16: Emojis.TILE_16,
            32: Emojis.TILE_32,
            64: Emojis.TILE_64,
            128: Emojis.TILE_128,
            256: Emojis.TILE_256,
            512: Emojis.TILE_512,
            1024: Emojis.TILE_1024,
            2048: Emojis.TILE_2048
        }
        
        return "\n".join(
            " ".join(number_emojis.get(num, str(num)) for num in row)
            for row in self.board
        )

class GameView(View):
    def __init__(self, game, user_id):
        super().__init__(timeout=300)  # 5 минут таймаут
        self.game = game
        self.user_id = user_id
        
    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.primary, custom_id="up")
    async def up(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваша игра!")
            return
            
        if self.game.move("up"):
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("Недопустимый ход!")
    
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="left")
    async def left(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваша игра!")
            return
            
        if self.game.move("left"):
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("Недопустимый ход!")
    
    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.primary, custom_id="down")
    async def down(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваша игра!")
            return
            
        if self.game.move("down"):
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("Недопустимый ход!")
    
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="right")
    async def right(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваша игра!")
            return
            
        if self.game.move("right"):
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("Недопустимый ход!", ephemeral=True)
            
    @discord.ui.button(label="🔄", style=discord.ButtonStyle.danger, custom_id="restart")
    async def restart(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Это не ваша игра!")
            return
            
        self.game = Game2048()
        await self.update_game(interaction)
    
    async def update_game(self, interaction: discord.Interaction):
        embed=Embed(
            title="🎮 2048",
            description=f"**Счёт:** {self.game.score}\n\n{self.game.get_board_str()}",
            color="BLUE"
        )
        
        if self.game.is_game_over():
            embed.add_field(name="Игра окончена!", value="Нажмите 🔄 для новой игры", inline=False)
            for child in self.children[:-1]:  # Кроме кнопки рестарта
                child.disabled = True
                
        await interaction.response.edit_message(embed=embed, view=self)

class Game2048Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="2048", description="Начать игру в 2048")
    async def start_game(self, interaction: discord.Interaction):
        game = Game2048()
        view = GameView(game, interaction.user.id)
        
        embed=Embed(
            title="🎮 2048",
            description=f"**Счёт:** {game.score}\n\n{game.get_board_str()}",
            color="BLUE"
        )
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Game2048Cog(bot)) 