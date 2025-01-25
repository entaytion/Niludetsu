import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Play(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="play", description="Воспроизвести музыку")
    @discord.app_commands.describe(query="Поисковый запрос для музыки")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы должны находиться в голосовом канале!"
                )
            )
            return

        await interaction.response.defer(thinking=True)

        if not self.core.node or not wavelink.Pool.get_node():
            await interaction.followup.send(
                embed=create_embed(
                    description="Музыкальный сервер недоступен. Попробуйте позже!"
                )
            )
            return

        player = await self.core.get_player(interaction)
        if not player:
            await interaction.followup.send(
                embed=create_embed(
                    description="Ошибка подключения к голосовому каналу!"
                )
            )
            return

        if not hasattr(player, 'home'):
            player.home = interaction.channel

        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                await interaction.followup.send(
                    embed=create_embed(
                        description="По вашему запросу ничего не найдено!"
                    )
                )
                return

            track = tracks[0]

            if player.playing:
                player.queue.put(track)
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎶 Добавлено в очередь:",
                        description=f"**{track.title}**\nЗапросил: {interaction.user.mention}"
                    )
                )
            else:
                await player.play(track)
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎵 Сейчас играет:",
                        description=f"**{track.title}**\nЗапросил: {interaction.user.mention}"
                    )
                )
        except Exception as e:
            print(f"Error in play command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при воспроизведении трека!"
                )
            )

async def setup(bot):
    await bot.add_cog(Play(bot))