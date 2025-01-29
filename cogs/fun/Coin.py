import discord
from discord.ext import commands
import random
import asyncio
from Niludetsu.utils.embed import create_embed

class Coin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.coin_frames = [
            "( ﾟ◡ﾟ)/⌒🪙",
            "( ﾟ◡ﾟ)/  ⌒🪙",
            "( ﾟ◡ﾟ)/    ⌒🪙",
            "( ﾟ◡ﾟ)/      🪙",
            "( ﾟ◡ﾟ)/    ✨🪙",
            "( ﾟ◡ﾟ)/  ✨🪙",
            "( ﾟ◡ﾟ)/✨🪙",
        ]

    @discord.app_commands.command(name="coin", description="Подбросить монетку")
    async def coin(self, interaction: discord.Interaction):
        # Отправляем начальное сообщение
        embed = create_embed(
            title="🪙 Подбрасываю монетку...",
            description=self.coin_frames[0],
            color="BLUE"
        )
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Анимация подбрасывания
        for frame in self.coin_frames[1:]:
            embed.description = frame
            await message.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Определяем результат
        result = random.choice(["Орёл", "Решка"])
        
        # Показываем результат
        final_embed = create_embed(
            title="🪙 Результат броска",
            description=f"( ﾟ◡ﾟ)/ 🪙\n\n**Выпало:** {result}",
            color="GREEN"
        )
        await message.edit(embed=final_embed)

async def setup(bot):
    await bot.add_cog(Coin(bot))