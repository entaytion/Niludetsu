import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.game.akinator import Akinator as AkinatorGame

class AkinatorView(discord.ui.View):
    def __init__(self, aki_instance):
        super().__init__(timeout=300)  # 5 минут таймаут
        self.aki = aki_instance

    @discord.ui.button(label="Да", style=discord.ButtonStyle.success, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 'y')

    @discord.ui.button(label="Нет", style=discord.ButtonStyle.danger, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 'n')

    @discord.ui.button(label="Не знаю", style=discord.ButtonStyle.gray, emoji="❓")
    async def idk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 'idk')

    @discord.ui.button(label="Вероятно да", style=discord.ButtonStyle.primary, emoji="👍")
    async def probably_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 'p')

    @discord.ui.button(label="Вероятно нет", style=discord.ButtonStyle.primary, emoji="👎")
    async def probably_not_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 'pn')

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.gray, emoji="↩️", row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            self.aki.go_back()
            embed = create_embed(
                title="🧞‍♂️ Акинатор",
                description=f"**Вопрос #{self.aki.step + 1}**\n{self.aki.question}",
                color="BLUE"
            )
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception as e:
            print(f"Error going back: {e}")

    @discord.ui.button(label="Закончить", style=discord.ButtonStyle.red, emoji="🏁", row=1)
    async def end_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.aki.progression >= 80:
            embed = create_embed(
                title="🧞‍♂️ Я думаю, это...",
                description=f"**{self.aki.name}**\n{self.aki.description}\n\n"
                          f"Я уверен на {round(self.aki.progression)}%",
                color="GREEN"
            )
            if self.aki.photo:
                embed.set_image(url=self.aki.photo)
        else:
            embed = create_embed(
                description="Игра завершена! Я не смог угадать 😢",
                color="RED"
            )
        await interaction.edit_original_response(embed=embed, view=None)

    async def process_answer(self, interaction: discord.Interaction, answer: str):
        await interaction.response.defer()
        try:
            self.aki.post_answer(answer)
            
            if self.aki.progression >= 80 and self.aki.step >= 10:
                embed = create_embed(
                    title="🧞‍♂️ Я думаю, это...",
                    description=f"**{self.aki.name}**\n{self.aki.description}\n\n"
                              f"Я уверен на {round(self.aki.progression)}%",
                    color="GREEN"
                )
                if self.aki.photo:
                    embed.set_image(url=self.aki.photo)
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                embed = create_embed(
                    title="🧞‍♂️ Акинатор",
                    description=f"**Вопрос #{self.aki.step + 1}**\n{self.aki.question}",
                    color="BLUE"
                )
                await interaction.edit_original_response(embed=embed, view=self)
                
        except Exception as e:
            embed = create_embed(
                description=f"❌ Произошла ошибка в игре: {str(e)}",
                color="RED"
            )
            await interaction.edit_original_response(embed=embed, view=None)

class Akinator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @discord.app_commands.command(name="akinator", description="Играть в Акинатора")
    async def akinator(self, interaction: discord.Interaction):
        if interaction.user.id in self.games:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы уже играете! Завершите текущую игру.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        try:
            aki = AkinatorGame()
            q = aki.start_game()

            embed = create_embed(
                title="🧞‍♂️ Акинатор",
                description=f"**Вопрос #{aki.step + 1}**\n{q}",
                color="BLUE"
            )

            self.games[interaction.user.id] = aki
            view = AkinatorView(aki)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ Произошла ошибка при запуске игры: {str(e)}",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Akinator(bot))