import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.music import Music
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music = Music(bot)

    @app_commands.command(name="volume", description="Изменить громкость (0-150)")
    @app_commands.describe(volume="Уровень громкости (0-150)")
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 150]):
        """Изменить громкость"""
        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        if not player.playing:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Сейчас ничего не играет!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Устанавливаем новую громкость
        await player.set_volume(volume)
        song = self.music.get_current_song(interaction.guild_id)

        # Определяем эмодзи громкости
        if volume == 0:
            volume_emoji = Emojis.VOLUME_MUTE
        elif volume < 50:
            volume_emoji = Emojis.VOLUME_LOW
        elif volume < 100:
            volume_emoji = Emojis.VOLUME_MEDIUM
        else:
            volume_emoji = Emojis.VOLUME_HIGH

        embed=Embed(
            title=f"{volume_emoji} Громкость изменена",
            description=f"Новая громкость: `{volume}%`",
            color="BLUE"
        )

        if song:
            embed.add_field(
                name=f"{Emojis.MUSIC} Текущий трек",
                value=f"**[{song.title}]({song.uri})**",
                inline=False
            )

        embed.set_footer(text=f"Изменил: {interaction.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Volume(bot)) 