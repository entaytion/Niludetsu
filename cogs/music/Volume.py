import discord
from discord import app_commands
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @app_commands.command(name="volume", description="Изменить громкость музыки (0-150%)")
    @app_commands.describe(volume="Уровень громкости от 0 до 150")
    async def volume(self, interaction: discord.Interaction, volume: int):
        await interaction.response.defer()
        
        try:
            player = await self.core.get_player(interaction)
            if not player or not player.is_playing():
                await interaction.followup.send(
                    embed=create_embed(
                        description="Сейчас ничего не играет!"
                    )
                )
                return

            # Проверяем диапазон громкости
            if not 0 <= volume <= 150:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Громкость должна быть от 0 до 150%!"
                    )
                )
                return

            # Устанавливаем новую громкость
            await player.set_volume(volume)
            
            # Создаем эмбед с информацией
            embed = create_embed(
                title="🔊 Громкость изменена",
                description=f"Установлена громкость: **{volume}%**"
            )
            
            # Добавляем индикатор громкости
            if volume == 0:
                indicator = "🔇"
            elif volume < 30:
                indicator = "🔈"
            elif volume < 70:
                indicator = "🔉"
            else:
                indicator = "🔊"
            
            # Добавляем визуальную шкалу громкости
            bars = int((volume / 150) * 10)
            volume_bar = "▰" * bars + "▱" * (10 - bars)
            embed.add_field(
                name=f"{indicator} Уровень громкости:",
                value=f"```{volume_bar}```",
                inline=False
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in volume command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!"
                )
            )

async def setup(bot):
    await bot.add_cog(Volume(bot)) 