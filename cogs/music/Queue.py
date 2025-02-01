import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="queue", description="Показать очередь воспроизведения")
    async def queue(self, interaction: discord.Interaction):
        """Показать очередь воспроизведения"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.followup.send(
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
            await interaction.followup.send(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Не удалось получить информацию об очереди!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        current = state.current
        if not current:
            await interaction.followup.send(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Не удалось получить информацию о текущем треке!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Создаем эмбед с очередью
        embed=Embed(
            title=f"{EMOJIS['QUEUE']} Очередь воспроизведения",
            color="BLUE"
        )

        # Добавляем информацию о текущем треке
        embed.add_field(
            name=f"{EMOJIS['MUSIC']} Сейчас играет",
            value=(
                f"**[{current.title}]({current.uri})**\n"
                f"{EMOJIS['TIME']} Длительность: `{current.format_duration()}`\n"
                f"{EMOJIS['USER']} Запросил: {current.requester.mention if current.requester else 'Неизвестно'}"
            ),
            inline=False
        )

        # Если есть треки в очереди
        if not state.songs.empty():
            upcoming = []
            position = 1
            queue_list = state.songs._queue.copy()  # Получаем копию очереди

            for song in queue_list:
                upcoming.append(
                    f"`{position}.` **[{song.title}]({song.uri})**\n"
                    f"{EMOJIS['TIME']} `{song.format_duration()}` | "
                    f"{EMOJIS['USER']} {song.requester.mention if song.requester else 'Неизвестно'}"
                )
                position += 1

            # Разбиваем на страницы, если треков много
            if len(upcoming) > 10:
                upcoming = upcoming[:10]
                upcoming.append(f"\n{EMOJIS['INFO']} И еще {len(queue_list) - 10} треков...")

            embed.add_field(
                name=f"{EMOJIS['PLAYLIST']} В очереди ({len(queue_list)} треков)",
                value="\n".join(upcoming) if upcoming else "Очередь пуста",
                inline=False
            )
        else:
            embed.add_field(
                name=f"{EMOJIS['PLAYLIST']} В очереди",
                value="Очередь пуста",
                inline=False
            )

        # Добавляем информацию о повторе
        embed.add_field(
            name=f"{EMOJIS['SETTINGS']} Настройки",
            value=(
                f"{EMOJIS['REPEAT']} Повтор: {'Включен' if state.loop else 'Выключен'}\n"
                f"{EMOJIS['VOLUME']} Громкость: {player.volume}%"
            ),
            inline=False
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Queue(bot)) 