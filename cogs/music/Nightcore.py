import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class Nightcore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)
        self._nightcore_enabled = {}  # Словарь для хранения состояния эффекта для каждого сервера

    def is_nightcore_enabled(self, guild_id: int) -> bool:
        """Проверяет, включен ли эффект nightcore для сервера"""
        return self._nightcore_enabled.get(guild_id, False)

    def set_nightcore(self, guild_id: int, enabled: bool):
        """Устанавливает состояние эффекта nightcore для сервера"""
        self._nightcore_enabled[guild_id] = enabled

    @app_commands.command(name="nightcore", description="Включить/выключить эффект Nightcore")
    async def nightcore(self, interaction: discord.Interaction):
        """Включить/выключить эффект Nightcore"""
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

        # Переключаем состояние эффекта
        guild_id = interaction.guild_id
        enabled = not self.is_nightcore_enabled(guild_id)
        self.set_nightcore(guild_id, enabled)

        # Применяем эффект
        filters = player.filters
        if enabled:
            filters.timescale.set(speed=1.2, pitch=1.2, rate=1.0)
        else:
            filters.timescale.reset()
        await player.set_filters(filters)

        song = self.music.get_current_song(guild_id)

        embed=Embed(
            title=f"{EMOJIS['EFFECT']} Эффект Nightcore",
            description=f"Эффект Nightcore **{'включен' if enabled else 'выключен'}**",
            color="GREEN" if enabled else "RED"
        )

        if song:
            embed.add_field(
                name=f"{EMOJIS['MUSIC']} Текущий трек",
                value=f"**[{song.title}]({song.uri})**\n"
                      f"{EMOJIS['TIME']} Длительность: `{song.format_duration()}`",
                inline=False
            )

        if enabled:
            embed.add_field(
                name=f"{EMOJIS['SETTINGS']} Настройки эффекта",
                value=(
                    f"**Скорость:** `120%`\n"
                    f"**Тональность:** `120%`\n"
                    f"**Частота:** `100%`"
                ),
                inline=False
            )

        embed.set_footer(text=f"{'Эффект применен' if enabled else 'Эффект отключен'} • {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Nightcore(bot)) 