import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils import create_embed
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

    @app_commands.command(name="repeat", description="Изменить режим повтора")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Выключить", value="off"),
        app_commands.Choice(name="Повтор трека", value="single"),
        app_commands.Choice(name="Повтор очереди", value="queue")
    ])
    async def repeat(self, interaction: discord.Interaction, mode: str = None):
        """Изменить режим повтора"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Сейчас ничего не играет!"
                ),
                ephemeral=True
            )
            return

        try:
            guild_id = interaction.guild_id
            current_mode = self.get_repeat_mode(guild_id)

            # Если режим не указан, переключаем между режимами
            if mode is None:
                if current_mode == RepeatMode.OFF:
                    new_mode = RepeatMode.SINGLE
                elif current_mode == RepeatMode.SINGLE:
                    new_mode = RepeatMode.QUEUE
                else:
                    new_mode = RepeatMode.OFF
            else:
                new_mode = {
                    "off": RepeatMode.OFF,
                    "single": RepeatMode.SINGLE,
                    "queue": RepeatMode.QUEUE
                }[mode]

            self.set_repeat_mode(guild_id, new_mode)

            if new_mode == RepeatMode.SINGLE:
                # Для повтора одного трека
                current_track = player.current
                if current_track:
                    await player.queue.put_wait(current_track)
                status = "повтор трека"
                emoji = "🔂"
            elif new_mode == RepeatMode.QUEUE:
                # Для повтора всей очереди
                status = "повтор очереди"
                emoji = "🔁"
            else:
                status = "выключен"
                emoji = "➡️"

            await interaction.followup.send(
                embed=create_embed(
                    description=f"{emoji} Режим повтора: {status}"
                )
            )
        except Exception as e:
            print(f"Error toggling repeat: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при изменении режима повтора!"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Repeat(bot)) 