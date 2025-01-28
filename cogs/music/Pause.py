import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Pause(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="pause", description="Поставить музыку на паузу")
    async def pause(self, interaction: discord.Interaction):
        """Поставить музыку на паузу"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Сейчас ничего не играет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if player.paused:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Музыка уже на паузе!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        await player.pause()
        song = self.music.get_current_song(interaction.guild_id)

        embed = create_embed(
            title=f"{EMOJIS['PAUSE']} Пауза",
            description=f"**[{song.title}]({song.uri})** поставлен на паузу",
            color="YELLOW"
        )
        embed.set_footer(text=f"Запросил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pause(bot)) 