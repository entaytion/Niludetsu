import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
import random

class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="shuffle", description="Перемешать очередь воспроизведения")
    async def shuffle(self, interaction: discord.Interaction):
        """Перемешать очередь воспроизведения"""
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

        state = self.music.get_voice_state(interaction.guild)
        if not state:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Не удалось получить информацию об очереди!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if state.songs.empty():
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="В очереди нет треков для перемешивания!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Перемешиваем очередь
        queue_list = list(state.songs._queue)
        random.shuffle(queue_list)
        state.songs._queue.clear()
        for song in queue_list:
            await state.songs.put(song)

        embed = create_embed(
            title=f"{EMOJIS['SHUFFLE']} Очередь перемешана",
            description=f"Перемешано `{len(queue_list)}` треков",
            color="BLUE"
        )

        # Показываем первые 5 треков новой очереди
        if queue_list:
            tracks_list = []
            for i, song in enumerate(queue_list[:5], 1):
                tracks_list.append(
                    f"`{i}.` **[{song.title}]({song.uri})**\n"
                    f"{EMOJIS['USER']} {song.requester.mention if song.requester else 'Неизвестно'}"
                )
            
            if len(queue_list) > 5:
                tracks_list.append(f"\n{EMOJIS['INFO']} И еще {len(queue_list) - 5} треков...")

            embed.add_field(
                name=f"{EMOJIS['PLAYLIST']} Новая очередь",
                value="\n".join(tracks_list),
                inline=False
            )

        embed.set_footer(text=f"Перемешал: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Shuffle(bot)) 