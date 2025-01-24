import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class NowPlaying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="np", description="Показать текущий трек")
    async def nowplaying(self, interaction: discord.Interaction):
        await interaction.response.defer()

        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player or not player.playing:
            await interaction.followup.send(
                embed=create_embed(
                    description="Сейчас ничего не играет!"
                )
            )
            return

        track = player.current
        if not track:
            await interaction.followup.send(
                embed=create_embed(
                    description="Не удалось получить информацию о треке!"
                )
            )
            return

        current_time = int(player.position / 1000)  
        total_time = int(track.length / 1000)  

        progress_segments = 9
        if total_time > 0:
            progress = "▬" * (current_time * progress_segments // total_time)
        else:
            progress = "▬" * progress_segments
        progress += "⏺️"
        remaining_segments = progress_segments - len(progress) + 1
        if remaining_segments > 0:
            progress += "▬" * remaining_segments

        def format_time(seconds):
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            return f"{minutes:02}:{seconds:02}"

        embed = create_embed(
            title="🎵 Сейчас играет:",
            description=f"**{track.title}**\nИсполнитель: {track.author}"
        )
        embed.add_field(
            name="🔊 Прогресс:",
            value=f"{progress}\n⏱️ {format_time(current_time)} / {format_time(total_time)}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NowPlaying(bot)) 