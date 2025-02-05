import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        """Пропустить текущий трек"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Сейчас ничего не играет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        state = self.music.get_voice_state(interaction.guild)
        if not state:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Не удалось получить информацию о воспроизведении!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        current = state.current
        if not current:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Не удалось получить информацию о текущем треке!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Пропускаем текущий трек
        try:
            # Сохраняем информацию о текущем треке перед пропуском
            skipped_track = current
            
            # Останавливаем текущий трек
            await player.stop()
            
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Произошла ошибка при пропуске трека: {str(e)}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        embed = Embed(
            title=f"{Emojis.SKIP} Трек пропущен",
            description=f"**[{skipped_track.title}]({skipped_track.uri})** пропущен",
            color="BLUE"
        )

        # Показываем следующий трек, если он есть в очереди
        if not player.queue.is_empty:
            # Получаем все треки из очереди
            queue_tracks = []
            while not player.queue.is_empty:
                track = await player.queue.get_wait()
                queue_tracks.append(track)
            
            # Возвращаем все треки обратно в том же порядке
            for track in queue_tracks:
                await player.queue.put_wait(track)
            
            # Показываем первый трек
            if queue_tracks:
                embed.add_field(
                    name=f"{Emojis.NEXT} Следующий трек",
                    value=f"**[{queue_tracks[0].title}]({queue_tracks[0].uri})**",
                    inline=False
                )

        embed.set_footer(text=f"Пропустил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Skip(bot)) 