import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
import random

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @app_commands.command(name="rps", description="Сыграть в Камень-Ножницы-Бумага с ботом или участником")
    @app_commands.describe(
        opponent="Участник, с которым хотите сыграть (оставьте пустым для игры с ботом)",
        choice="Ваш выбор: камень/ножницы/бумага"
    )
    async def rps(self, interaction: discord.Interaction, choice: str, opponent: discord.Member = None):
        choices = {
            "камень": "🗿",
            "ножницы": "✂️",
            "бумага": "📄"
        }
        
        choice = choice.lower()
        if choice not in choices:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Выберите: камень, ножницы или бумага!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if opponent is None:
            # Игра против бота
            bot_choice = random.choice(list(choices.keys()))
            
            # Определяем победителя
            if choice == bot_choice:
                result = "Ничья! 🤝"
                color = "BLUE"
            elif (
                (choice == "камень" and bot_choice == "ножницы") or
                (choice == "ножницы" and bot_choice == "бумага") or
                (choice == "бумага" and bot_choice == "камень")
            ):
                result = "Вы победили! 🎉"
                color = "GREEN"
            else:
                result = "Вы проиграли! 😢"
                color = "RED"
                
            await interaction.response.send_message(
                embed=create_embed(
                    title="🎮 Камень-Ножницы-Бумага",
                    description=f"**Ваш выбор:** {choices[choice]} {choice}\n"
                              f"**Выбор бота:** {choices[bot_choice]} {bot_choice}\n\n"
                              f"**{result}**",
                    color=color
                )
            )
        else:
            # Игра против участника
            if opponent.bot:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Вы не можете играть с ботами!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            if opponent.id == interaction.user.id:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Вы не можете играть сами с собой!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            game_id = f"{interaction.user.id}-{opponent.id}"
            if game_id in self.active_games:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="У вас уже есть активная игра с этим участником!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            self.active_games[game_id] = {
                "player1": {"id": interaction.user.id, "choice": choice},
                "player2": {"id": opponent.id, "choice": None}
            }

            # Создаем кнопки для второго игрока
            class RPSButtons(discord.ui.View):
                def __init__(self, cog, game_id):
                    super().__init__(timeout=30.0)
                    self.cog = cog
                    self.game_id = game_id

                @discord.ui.button(label="Камень", style=discord.ButtonStyle.gray)
                async def rock(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    await self.make_choice(button_interaction, "камень")

                @discord.ui.button(label="Ножницы", style=discord.ButtonStyle.gray)
                async def scissors(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    await self.make_choice(button_interaction, "ножницы")

                @discord.ui.button(label="Бумага", style=discord.ButtonStyle.gray)
                async def paper(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    await self.make_choice(button_interaction, "бумага")

                async def make_choice(self, button_interaction: discord.Interaction, choice):
                    if button_interaction.user.id != self.cog.active_games[self.game_id]["player2"]["id"]:
                        await button_interaction.response.send_message("Это не ваша игра!", ephemeral=True)
                        return

                    self.cog.active_games[self.game_id]["player2"]["choice"] = choice
                    game = self.cog.active_games[self.game_id]
                    
                    # Определяем победителя
                    choice1 = game["player1"]["choice"]
                    choice2 = choice
                    
                    if choice1 == choice2:
                        result = "Ничья! 🤝"
                        color = "BLUE"
                    elif (
                        (choice1 == "камень" and choice2 == "ножницы") or
                        (choice1 == "ножницы" and choice2 == "бумага") or
                        (choice1 == "бумага" and choice2 == "камень")
                    ):
                        result = f"Победитель: <@{game['player1']['id']}>! 🎉"
                        color = "GREEN"
                    else:
                        result = f"Победитель: <@{game['player2']['id']}>! 🎉"
                        color = "GREEN"

                    await button_interaction.message.edit(
                        embed=create_embed(
                            title="🎮 Камень-Ножницы-Бумага",
                            description=f"**Выбор <@{game['player1']['id']}>:** {choices[choice1]} {choice1}\n"
                                      f"**Выбор <@{game['player2']['id']}>:** {choices[choice2]} {choice2}\n\n"
                                      f"**{result}**",
                            color=color
                        ),
                        view=None
                    )
                    del self.cog.active_games[self.game_id]

                async def on_timeout(self):
                    if self.game_id in self.cog.active_games:
                        del self.cog.active_games[self.game_id]
                        await self.message.edit(
                            embed=create_embed(
                                description="Время на ответ истекло!",
                                color="RED"
                            ),
                            view=None
                        )

            view = RPSButtons(self, game_id)
            await interaction.response.send_message(
                content=f"{opponent.mention}, вас вызвали на игру в Камень-Ножницы-Бумага!",
                embed=create_embed(
                    title="🎮 Камень-Ножницы-Бумага",
                    description="Выберите свой ход:",
                    color="BLUE"
                ),
                view=view
            )
            view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(RPS(bot)) 