import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class Karaoke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)
        self._karaoke_enabled = {}  # Словарь для хранения состояния эффекта для каждого сервера

    def is_karaoke_enabled(self, guild_id: int) -> bool:
        """Проверяет, включен ли эффект karaoke для сервера"""
        return self._karaoke_enabled.get(guild_id, False)

    def set_karaoke(self, guild_id: int, enabled: bool):
        """Устанавливает состояние эффекта karaoke для сервера"""
        self._karaoke_enabled[guild_id] = enabled

    @app_commands.command(name="karaoke", description="Включить/выключить эффект Караоке")
    async def karaoke(self, interaction: discord.Interaction):
        """Включить/выключить эффект Караоке"""
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
        enabled = not self.is_karaoke_enabled(guild_id)
        self.set_karaoke(guild_id, enabled)

        # Применяем эффект
        filters = player.filters
        if enabled:
            filters.karaoke.set(
                level=1.0,
                mono_level=1.0,
                filter_band=220.0,
                filter_width=100.0
            )
        else:
            filters.karaoke.reset()
        await player.set_filters(filters)

        song = self.music.get_current_song(guild_id)

        embed=Embed(
            title=f"{EMOJIS['KARAOKE']} Эффект Караоке",
            description=f"Эффект Караоке **{'включен' if enabled else 'выключен'}**",
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
                    f"**Уровень:** `100%`\n"
                    f"**Моно уровень:** `100%`\n"
                    f"**Частота фильтра:** `220 Hz`\n"
                    f"**Ширина фильтра:** `100 Hz`"
                ),
                inline=False
            )

        embed.set_footer(text=f"{'Эффект применен' if enabled else 'Эффект отключен'} • {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Karaoke(bot)) 