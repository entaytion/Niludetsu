import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import g4f
import asyncio
import random
import platform
import sys

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Список доступных провайдеров
        self.providers = [
            g4f.Provider.ChatGptt,
            g4f.Provider.OIVSCode,
            g4f.Provider.Blackbox,
        ]
        self.current_provider_index = 0

    async def get_ai_response(self, prompt: str) -> str:
        """Получение ответа от ИИ через g4f"""
        # Используем текущий event loop
        for provider in self.providers:
            try:
                response = await asyncio.get_event_loop().run_in_executor(None, 
                    lambda: g4f.ChatCompletion.create(
                        model="gpt-4o",
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
                print(f"Error with provider {provider.__name__}: {str(e)}")
                continue
        
        return "Извините, не удалось получить ответ. Все доступные провайдеры временно недоступны. Попробуйте позже."

    @app_commands.command(name="ai", description="Спросить что-то у ИИ")
    @app_commands.describe(вопрос="Ваш вопрос к ИИ")
    async def ai(self, interaction: discord.Interaction, вопрос: str):
        """Команда для взаимодействия с ИИ"""
        await interaction.response.defer()
        
        try:
            response = await self.get_ai_response(вопрос)
            
            embed = create_embed(
                title="🤖 Ответ ИИ",
                description=response
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = create_embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка при обработке запроса: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(AI(bot)) 