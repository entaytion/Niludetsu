import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class NowPlaying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="np", description="Показать текущий трек")
    async def np(self, interaction: discord.Interaction):
        """Показать текущий трек"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.followup.send(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Сейчас ничего не играет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        song = self.music.get_current_song(interaction.guild_id)
        if not song:
            await interaction.followup.send(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Не удалось получить информацию о треке!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Форматируем длительность и прогресс
        position = player.position
        
        if song.is_stream:
            progress = f"{EMOJIS['LIVE']} LIVE"
        else:
            current_min = position // 60000
            current_sec = (position % 60000) // 1000
            total_min = song.duration // 60000
            total_sec = (song.duration % 60000) // 1000
            progress = f"`{current_min}:{current_sec:02d}` - `{total_min}:{total_sec:02d}`"

        # Создаем эмбед с информацией о треке
        embed = create_embed(
            title=f"{EMOJIS['MUSIC']} Сейчас играет",
            description=f"**[{song.title}]({song.uri})**\n{EMOJIS['ARTIST']} **Автор:** {song.author}",
            color="BLUE"
        )

        embed.add_field(
            name=f"{EMOJIS['TIME']} Прогресс",
            value=progress,
            inline=True
        )
        embed.add_field(
            name=f"{EMOJIS['USER']} Запросил",
            value=song.requester.mention if song.requester else "Неизвестно",
            inline=True
        )

        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)

        embed.set_footer(text=f"Громкость: {player.volume}%")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NowPlaying(bot)) 