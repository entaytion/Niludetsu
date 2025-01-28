import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.game.akinator import Akinator as AkinatorGame

class Akinator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @discord.app_commands.command(name="akinator", description="Играть в Акинатора")
    async def akinator(self, interaction: discord.Interaction):
        if interaction.user.id in self.games:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы уже играете! Завершите текущую игру.",
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
                description=f"**Вопрос #{aki.step + 1}**\n{q}\n\n"
                          "Варианты ответов:\n"
                          "✅ - Да\n"
                          "❌ - Нет\n"
                          "❓ - Не знаю\n"
                          "👍 - Вероятно да\n"
                          "👎 - Вероятно нет\n"
                          "↩️ - Назад\n"
                          "🏁 - Закончить игру",
                color="BLUE"
            )

            self.games[interaction.user.id] = {
                'aki': aki,
                'question': q,
                'answers': {
                    '✅': 'y',
                    '❌': 'n',
                    '❓': 'idk',
                    '👍': 'p',
                    '👎': 'pn'
                }
            }

            message = await interaction.response.send_message(embed=embed)
            msg = await message.original_response()
            
            for emoji in ['✅', '❌', '❓', '👍', '👎', '↩️', '🏁']:
                await msg.add_reaction(emoji)
                
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Произошла ошибка при запуске игры: {str(e)}",
                    color="RED"
                ),
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or user.id not in self.games:
            return

        game = self.games[user.id]
        aki = game['aki']

        if str(reaction.emoji) == '🏁':
            if aki.progression >= 80:
                embed = create_embed(
                    title="🧞‍♂️ Я думаю, это...",
                    description=f"**{aki.name}**\n{aki.description}\n\n"
                              f"Я уверен на {round(aki.progression)}%",
                    image=aki.photo,
                    color="GREEN"
                )
            else:
                embed = create_embed(
                    description="Игра завершена! Я не смог угадать 😢",
                    color="RED"
                )
            
            del self.games[user.id]
            await reaction.message.edit(embed=embed)
            await reaction.message.clear_reactions()
            return

        if str(reaction.emoji) == '↩️':
            try:
                result = aki.go_back()
                embed = create_embed(
                    title="🧞‍♂️ Акинатор",
                    description=f"**Вопрос #{aki.step + 1}**\n{aki.question}",
                    color="BLUE"
                )
                await reaction.message.edit(embed=embed)
            except Exception as e:
                pass
            await reaction.remove(user)
            return

        if str(reaction.emoji) in game['answers']:
            answer = game['answers'][str(reaction.emoji)]
            try:
                result = aki.post_answer(answer)
                
                if aki.name:  # Если получен ответ с предположением
                    embed = create_embed(
                        title="🧞‍♂️ Я думаю, это...",
                        description=f"**{aki.name}**\n{aki.description}\n\n"
                                  f"Я уверен на {round(aki.progression)}%",
                        image=aki.photo,
                        color="GREEN"
                    )
                    
                    del self.games[user.id]
                    await reaction.message.edit(embed=embed)
                    await reaction.message.clear_reactions()
                else:
                    embed = create_embed(
                        title="🧞‍♂️ Акинатор",
                        description=f"**Вопрос #{aki.step + 1}**\n{aki.question}",
                        color="BLUE"
                    )
                    await reaction.message.edit(embed=embed)
                    await reaction.remove(user)
                    
            except Exception as e:
                embed = create_embed(
                    description=f"Произошла ошибка в игре: {str(e)}",
                    color="RED"
                )
                del self.games[user.id]
                await reaction.message.edit(embed=embed)
                await reaction.message.clear_reactions()

async def setup(bot):
    await bot.add_cog(Akinator(bot))