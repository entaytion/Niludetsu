import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
from Niludetsu.game.akinator import Akinator
import asyncio

class AkinatorButtons(discord.ui.View):
    def __init__(self, game_instance):
        super().__init__(timeout=180)
        self.game = game_instance

    @discord.ui.button(label="Да", style=discord.ButtonStyle.green, emoji="👍")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "y")

    @discord.ui.button(label="Нет", style=discord.ButtonStyle.red, emoji="👎")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "n")

    @discord.ui.button(label="Не знаю", style=discord.ButtonStyle.gray, emoji="❓")
    async def idk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "idk")

    @discord.ui.button(label="Возможно", style=discord.ButtonStyle.blurple, emoji="📝")
    async def probably_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "p")

    @discord.ui.button(label="Вероятно нет", style=discord.ButtonStyle.gray, emoji="❌")
    async def probably_not_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_answer(interaction, "pn")

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.gray, emoji="⬅️", row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.games:
            await interaction.response.send_message("У вас нет активной игры!", ephemeral=True)
            return

        try:
            aki = self.game.games[interaction.user.id]["aki"]
            await asyncio.get_event_loop().run_in_executor(None, aki.go_back)
            
            embed = create_embed(
                title="🧞‍♂️ Акинатор",
                description=f"**Вопрос #{aki.step}**\n{aki.question}"
            )
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            await interaction.response.send_message(f"Невозможно вернуться назад: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Закончить", style=discord.ButtonStyle.red, emoji="🏁", row=1)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_embed(
            title="🧞‍♂️ Акинатор",
            description="Игра завершена!"
        )
        await interaction.response.edit_message(embed=embed, view=None)
        if interaction.user.id in self.game.games:
            del self.game.games[interaction.user.id]

    async def handle_answer(self, interaction: discord.Interaction, answer: str):
        if interaction.user.id not in self.game.games:
            await interaction.response.send_message("У вас нет активной игры!", ephemeral=True)
            return

        try:
            aki = self.game.games[interaction.user.id]["aki"]
            
            # Отправляем ответ
            await asyncio.get_event_loop().run_in_executor(None, 
                lambda: aki.post_answer(answer))

            if aki.answer_id:
                embed = create_embed(
                    title="🧞‍♂️ Акинатор",
                    description=f"Я думаю, это **{aki.name}**!\n"
                               f"({aki.description})\n\n"
                               f"Я угадал?"
                )
                if aki.photo:
                    embed.set_thumbnail(url=aki.photo)

                # Создаем новые кнопки для финального ответа
                final_view = discord.ui.View(timeout=60)
                yes_button = discord.ui.Button(label="Да", style=discord.ButtonStyle.green, custom_id="yes")
                no_button = discord.ui.Button(label="Нет", style=discord.ButtonStyle.red, custom_id="no")
                
                async def yes_callback(inter: discord.Interaction):
                    await inter.response.edit_message(content="Я рад, что смог угадать! 🎉", embed=None, view=None)
                    if interaction.user.id in self.game.games:
                        del self.game.games[interaction.user.id]

                async def no_callback(inter: discord.Interaction):
                    await inter.response.edit_message(content="Жаль, что не угадал! Может, попробуем еще раз? 😊", embed=None, view=None)
                    if interaction.user.id in self.game.games:
                        del self.game.games[interaction.user.id]

                yes_button.callback = yes_callback
                no_button.callback = no_callback
                final_view.add_item(yes_button)
                final_view.add_item(no_button)
                
                await interaction.response.edit_message(embed=embed, view=final_view)
                return

            # Обновляем эмбед с новым вопросом
            embed = create_embed(
                title="🧞‍♂️ Акинатор",
                description=f"**Вопрос #{aki.step}**\n{aki.question}"
            )
            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            embed = create_embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка: {str(e)}"
            )
            await interaction.response.edit_message(embed=embed, view=None)
            if interaction.user.id in self.game.games:
                del self.game.games[interaction.user.id]

class AkinatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @app_commands.command(name="akinator", description="Играть в Акинатора")
    async def akinator_game(self, interaction: discord.Interaction):
        """Начать игру в Акинатора"""
        if interaction.user.id in self.games:
            await interaction.response.send_message("У вас уже есть активная игра!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Создаем экземпляр акинатора
            aki = Akinator()
            aki.language = "ru"
            
            # Начинаем игру
            await asyncio.get_event_loop().run_in_executor(None, aki.start_game)

            # Создаем эмбед с первым вопросом
            embed = create_embed(
                title="🧞‍♂️ Акинатор",
                description=f"**Вопрос #{aki.step}**\n{aki.question}"
            )

            # Создаем кнопки и отправляем сообщение
            view = AkinatorButtons(self)
            message = await interaction.followup.send(embed=embed, view=view)
            self.games[interaction.user.id] = {
                "aki": aki,
                "message_id": message.id
            }
                
        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка при запуске игры: {str(e)}", ephemeral=True)
            if interaction.user.id in self.games:
                del self.games[interaction.user.id]

async def setup(bot):
    await bot.add_cog(AkinatorCog(bot))