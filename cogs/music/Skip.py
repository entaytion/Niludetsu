import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

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
                    title=f"{EMOJIS['ERROR']} Ошибка",
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
                    title=f"{EMOJIS['ERROR']} Ошибка",
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
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Не удалось получить информацию о текущем треке!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Пропускаем текущий трек
        await player.stop()

        embed=Embed(
            title=f"{EMOJIS['SKIP']} Трек пропущен",
            description=f"**[{current.title}]({current.uri})** пропущен",
            color="BLUE"
        )
        
        # Если есть следующий трек в очереди
        if not state.songs.empty():
            next_song = state.songs._queue[0]
            embed.add_field(
                name=f"{EMOJIS['NEXT']} Следующий трек",
                value=f"**[{next_song.title}]({next_song.uri})**\n"
                      f"{EMOJIS['USER']} Запросил: {next_song.requester.mention if next_song.requester else 'Неизвестно'}",
                inline=False
            )

        embed.set_footer(text=f"Пропустил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Skip(bot)) 