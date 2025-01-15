import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload", description="Перезагрузить команду или все команды")
    @app_commands.describe(extension="Имя расширения для перезагрузки (опционально)")
    @commands.is_owner()  # Только владелец бота может использовать эту команду
    async def reload(self, interaction: discord.Interaction, extension: str = None):
        if extension is None:
            # Перезагружаем все расширения
            for ext in list(self.bot.extensions):
                self.bot.reload_extension(ext)
            embed = create_embed(
                description="Все команды были успешно перезагружены!",
                footer=FOOTER_SUCCESS
            )
            await interaction.response.send_message(embed=embed)
        else:
            # Перезагружаем конкретное расширение
            try:
                self.bot.reload_extension(f"cogs.{extension}")
                embed = create_embed(
                    description=f"Команда `{extension}` была успешно перезагружена!",
                    footer=FOOTER_SUCCESS
                )
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                embed = create_embed(
                    description=f"Ошибка при перезагрузке команды `{extension}`: {str(e)}",
                    footer=FOOTER_ERROR
                )
                await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Reload(bot))
