import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="leave", description="Отключить бота от голосового канала")
    async def leave(self, interaction: discord.Interaction):
        """Отключить бота от голосового канала"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        state = self.music.get_voice_state(interaction.guild)
        if not state:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Бот не подключен к голосовому каналу!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        channel = player.channel
        await state.stop()

        embed = create_embed(
            title=f"{EMOJIS['LEAVE']} Отключение",
            description=f"Бот отключен от канала {channel.mention}",
            color="BLUE"
        )
        embed.set_footer(text=f"Отключил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot)) 