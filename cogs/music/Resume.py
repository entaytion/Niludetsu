import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class Resume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="resume", description="Продолжить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        """Продолжить воспроизведение"""
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

        if not player.paused:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Музыка уже играет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        await player.resume()
        song = self.music.get_current_song(interaction.guild_id)

        embed = create_embed(
            title=f"{EMOJIS['PLAY']} Воспроизведение",
            description=f"**[{song.title}]({song.uri})** снова играет",
            color="GREEN"
        )
        embed.set_footer(text=f"Запросил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Resume(bot)) 