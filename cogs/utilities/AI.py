import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import g4f
import asyncio
import random

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Список доступних провайдерів
        self.providers = [
            g4f.Provider.AIChatFree,
            g4f.Provider.Blackbox,
            g4f.Provider.ChatGptt,
            g4f.Provider.PerplexityLabs
        ]

    async def get_ai_response(self, prompt: str) -> str:
        """Отримання відповіді від ШІ через g4f"""
        loop = asyncio.get_event_loop()
        
        # Перебираємо провайдерів, поки не отримаємо відповідь
        for provider in random.sample(self.providers, len(self.providers)):
            try:
                response = await loop.run_in_executor(None, 
                    lambda: g4f.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{
                            "role": "system",
                            "content": "Ты - полезный ассистент, который отвечает на русском языке."
                        }, {
                            "role": "user",
                            "content": prompt
                        }],
                        provider=provider
                    )
                )
                if response and isinstance(response, str):
                    return response
            except Exception as e:
                print(f"Error with provider {provider.__name__}: {e}")
                continue
        
        return "Извините, не удалось получить ответ. Попробуйте еще раз через несколько секунд."

    @app_commands.command(name="ai", description="Спросить что-то у ИИ")
    @app_commands.describe(вопрос="Ваш вопрос к ИИ")
    async def ai(self, interaction: discord.Interaction, вопрос: str):
        try:
            await interaction.response.defer()

            # Отправляем запрос к ИИ
            answer = await self.get_ai_response(вопрос)

            # Создаем эмбед с ответом
            embed = create_embed(
                title="🤖 Ответ ИИ",
                description=answer,
                footer={
                    "text": f"Спросил: {interaction.user.display_name}",
                    "icon_url": interaction.user.avatar.url if interaction.user.avatar else None
                }
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(AI(bot)) 