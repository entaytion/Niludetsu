import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from enum import Enum

class RepeatMode(Enum):
    OFF = 0
    SINGLE = 1
    QUEUE = 2

class Repeat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)
        self._repeat_modes = {}  # Словарь для хранения режима повтора для каждого сервера

    def get_repeat_mode(self, guild_id: int) -> RepeatMode:
        """Получает режим повтора для сервера"""
        return self._repeat_modes.get(guild_id, RepeatMode.OFF)

    def set_repeat_mode(self, guild_id: int, mode: RepeatMode):
        """Устанавливает режим повтора для сервера"""
        self._repeat_modes[guild_id] = mode

    @app_commands.command(name="repeat", description="Включить/выключить повтор текущего трека")
    async def repeat(self, interaction: discord.Interaction):
        """Включить/выключить повтор текущего трека"""
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

        # Переключаем режим повтора
        state.loop = not state.loop
        song = self.music.get_current_song(interaction.guild_id)

        embed=Embed(
            title=f"{EMOJIS['REPEAT']} Повтор {'включен' if state.loop else 'выключен'}",
            color="GREEN" if state.loop else "RED"
        )

        if song:
            embed.add_field(
                name=f"{EMOJIS['MUSIC']} Текущий трек",
                value=f"**[{song.title}]({song.uri})**\n"
                      f"{EMOJIS['TIME']} Длительность: `{song.format_duration()}`",
                inline=False
            )

        embed.set_footer(text=f"{'Теперь трек будет повторяться' if state.loop else 'Повтор отключен'} • {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Repeat(bot)) 