import discord
from discord.ext import commands
import wavelink
from utils import create_embed
from .Core import Core

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.core = None
        
    async def cog_load(self):
        self.core = self.bot.get_cog('Core')

    @discord.app_commands.command(name="queue", description="Просмотр очереди треков")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            player: wavelink.Player = wavelink.Pool.get_node().get_player(interaction.guild.id)
            if not player or not player.connected:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Я не подключен к голосовому каналу!"
                    )
                )
                return

            current = player.current
            tracks = list(player.queue)

            if not current and not tracks:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Очередь пуста!"
                    )
                )
                return

            queue_text = []
            
            if current:
                queue_text.append(f"**Сейчас играет:** {current.title}")
            
            if tracks:
                queue_text.append("\n**В очереди:**")
                for i, track in enumerate(tracks, 1):
                    queue_text.append(f"**{i}.** {track.title}")
                    if i >= 10:  
                        remaining = len(tracks) - 10
                        if remaining > 0:
                            queue_text.append(f"\nИ еще {remaining} треков...")
                        break

            await interaction.followup.send(
                embed=create_embed(
                    title="🎵 Очередь треков:",
                    description="\n".join(queue_text)
                )
            )
        except Exception as e:
            print(f"Error in queue command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при получении очереди!"
                )
            )

async def setup(bot):
    await bot.add_cog(Queue(bot)) 