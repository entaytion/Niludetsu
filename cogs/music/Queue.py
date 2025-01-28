import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="queue", description="Показать очередь воспроизведения")
    async def queue(self, interaction: discord.Interaction):
        """Показать очередь воспроизведения"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.queue:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Очередь воспроизведения пуста!"
                ),
                ephemeral=True
            )
            return

        # Создаем список треков
        queue_list = []
        for i, track in enumerate(player.queue, start=1):
            queue_list.append(f"`{i}.` **{track.title}** - {track.author}")
            if i >= 10:  # Показываем только первые 10 треков
                break

        # Добавляем информацию о количестве оставшихся треков
        remaining = len(player.queue) - len(queue_list)
        if remaining > 0:
            queue_list.append(f"\n*...и еще {remaining} треков*")

        embed = create_embed(
            title="🎵 Очередь воспроизведения",
            description="\n".join(queue_list)
        )

        if player.current:
            embed.add_field(
                name="Сейчас играет:",
                value=f"**{player.current.title}** - {player.current.author}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Queue(bot)) 