import discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu.music.manager import MusicManager
from Niludetsu.tools.Embed import Embed
from typing import Optional

class MusicSystem(commands.Cog):
    """Музыкальная система"""

    def __init__(self, bot):
        self.bot = bot
        self.music = MusicManager(bot)

    # ГРУППА КОМАНД ДЛЯ SLASH (/ music ...)

    music_group = app_commands.Group(name="music", description="🎵 Управление музыкой")

    @music_group.command(name="play", description="🎵 Воспроизвести музыку")
    @app_commands.describe(query="Название песни или URL")
    async def music_play(self, interaction: discord.Interaction, query: str):
        """Воспроизвести музыку"""
        await self.music.play_song(interaction, query)

    @music_group.command(name="pause", description="🎵 Поставить на паузу")
    async def music_pause(self, interaction: discord.Interaction):
        """Поставить на паузу"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        if player.paused:
            return await interaction.followup.send(
                embed=Embed.default(description="Музыка уже на паузе!"),
                ephemeral=True
            )

        await player.pause(True)
        song = self.music.get_current_song(interaction.guild_id)

        embed = Embed.success(
            title="⏸️ Пауза",
            description=f"**[{song.title}]({song.uri})** поставлен на паузу"
        )
        embed.set_footer(text=f"Запросил: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="resume", description="🎵 Продолжить воспроизведение")
    async def music_resume(self, interaction: discord.Interaction):
        """Продолжить воспроизведение"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        if not player.paused:
            return await interaction.followup.send(
                embed=Embed.default(description="Музыка уже играет!"),
                ephemeral=True
            )

        await player.pause(False)
        song = self.music.get_current_song(interaction.guild_id)

        embed = Embed.success(
            title="▶️ Воспроизведение",
            description=f"**[{song.title}]({song.uri})** снова играет"
        )
        embed.set_footer(text=f"Запросил: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="skip", description="🎵 Пропустить текущий трек")
    async def music_skip(self, interaction: discord.Interaction):
        """Пропустить текущий трек"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        state = self.music.get_voice_state(interaction.guild)
        current = state.current

        await player.stop()

        embed = Embed.success(
            title="⏭️ Трек пропущен",
            description=f"**[{current.title}]({current.uri})** пропущен"
        )
        embed.set_footer(text=f"Пропустил: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="stop", description="🎵 Остановить воспроизведение")
    async def music_stop(self, interaction: discord.Interaction):
        """Остановить воспроизведение"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player:
            return

        channel = player.channel
        await player.disconnect()
        self.music.set_current_song(interaction.guild.id, None)

        embed = Embed.success(
            title="⏹️ Остановка",
            description=f"Воспроизведение остановлено и бот отключен от {channel.mention}"
        )
        embed.set_footer(text=f"Остановил: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="volume", description="🎵 Изменить громкость")
    @app_commands.describe(volume="Уровень громкости (0-150)")
    async def music_volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 150]):
        """Изменить громкость"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        await player.set_volume(volume)
        song = self.music.get_current_song(interaction.guild_id)

        # Эмодзи громкости
        if volume == 0:
            volume_emoji = "🔇"
        elif volume < 50:
            volume_emoji = "🔉"
        elif volume < 100:
            volume_emoji = "🔊"
        else:
            volume_emoji = "📢"

        embed = Embed.success(
            title=f"{volume_emoji} Громкость изменена",
            description=f"Новая громкость: `{volume}%`"
        )

        if song:
            embed.add_field(
                name="🎵 Текущий трек",
                value=f"**[{song.title}]({song.uri})**",
                inline=False
            )

        embed.set_footer(text=f"Изменил: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="queue", description="🎵 Показать очередь")
    async def music_queue(self, interaction: discord.Interaction):
        """Показать очередь"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        state = self.music.get_voice_state(interaction.guild)
        current = state.current

        embed = Embed.success(title="🎵 Очередь воспроизведения")

        embed.add_field(
            name="▶️ Сейчас играет:",
            value=f"**[{current.title}]({current.uri})** ({current.format_duration()})",
            inline=False
        )

        if not player.queue.is_empty:
            queue_list = []
            queue_tracks = list(player.queue)[:10]

            for i, track in enumerate(queue_tracks, 1):
                duration = track.length // 1000
                minutes = duration // 60
                seconds = duration % 60
                queue_list.append(f"`{i}.` **[{track.title}]({track.uri})** ({minutes}:{seconds:02d})")

            remaining = len(player.queue) - 10
            queue_text = "\n".join(queue_list)
            if remaining > 0:
                queue_text += f"\n*И ещё {remaining} треков...*"

            embed.add_field(
                name="📜 В очереди:",
                value=queue_text,
                inline=False
            )
        else:
            embed.add_field(
                name="📜 В очереди:",
                value="*Очередь пуста*",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @music_group.command(name="nowplaying", description="🎵 Показать текущий трек")
    async def music_np(self, interaction: discord.Interaction):
        """Показать текущий трек"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        song = self.music.get_current_song(interaction.guild_id)
        if not song:
            return await interaction.followup.send(
                embed=Embed.default(description="Не удалось получить информацию о треке!"),
                ephemeral=True
            )

        position = player.position

        if song.is_stream:
            progress = "🔴 LIVE"
        else:
            current_min = position // 60000
            current_sec = (position % 60000) // 1000
            total_min = song.duration // 60000
            total_sec = (song.duration % 60000) // 1000
            progress = f"`{current_min}:{current_sec:02d}` - `{total_min}:{total_sec:02d}`"

        embed = Embed.success(
            title="🎵 Сейчас играет",
            description=f"**[{song.title}]({song.uri})**\n🎤 **Автор:** {song.author}",
            thumbnail_url=song.thumbnail
        )

        embed.add_field(name="⏰ Прогресс", value=progress, inline=True)
        embed.add_field(
            name="👤 Запросил",
            value=song.requester.mention if song.requester else "Неизвестно",
            inline=True
        )

        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)

        embed.set_footer(text=f"Громкость: {player.volume}%")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="shuffle", description="🎵 Перемешать очередь")
    async def music_shuffle(self, interaction: discord.Interaction):
        """Перемешать очередь"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        queue_list = []
        while not player.queue.is_empty:
            track = await player.queue.get_wait()
            queue_list.append(track)

        if not queue_list:
            return await interaction.followup.send(
                embed=Embed.default(description="В очереди нет треков!"),
                ephemeral=True
            )

        random.shuffle(queue_list)

        for track in queue_list:
            await player.queue.put_wait(track)

        embed = Embed.success(
            title="🔀 Очередь перемешана",
            description=f"Перемешано `{len(queue_list)}` треков"
        )
        embed.set_footer(text=f"Перемешал: {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="repeat", description="🎵 Включить/выключить повтор")
    async def music_repeat(self, interaction: discord.Interaction):
        """Включить/выключить повтор"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        state = self.music.get_voice_state(interaction.guild)
        state.loop = not state.loop
        song = self.music.get_current_song(interaction.guild_id)

        embed = Embed.success(
            title=f"🔁 Повтор {'включен' if state.loop else 'выключен'}"
        )

        if song:
            embed.add_field(
                name="🎵 Текущий трек",
                value=f"**[{song.title}]({song.uri})**\n⏰ Длительность: `{song.format_duration()}`",
                inline=False
            )

        embed.set_footer(text=f"{'Трек будет повторяться' if state.loop else 'Повтор отключен'} • {interaction.user}")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="nightcore", description="🎵 Включить/выключить эффект Nightcore")
    async def music_nightcore(self, interaction: discord.Interaction):
        """Включить/выключить nightcore"""
        await interaction.response.defer()

        player = await self.music.ensure_voice(interaction)
        if not player or not player.playing:
            return await interaction.followup.send(
                embed=Embed.default(description="Сейчас ничего не играет!"),
                ephemeral=True
            )

        guild_id = interaction.guild_id
        enabled = not self.music.is_nightcore_enabled(guild_id)
        self.music.set_nightcore(guild_id, enabled)

        filters = player.filters
        if enabled:
            filters.timescale.set(speed=1.2, pitch=1.2, rate=1.0)
        else:
            filters.timescale.reset()
        await player.set_filters(filters)

        song = self.music.get_current_song(guild_id)

        embed = Embed.success(
            title=f"✨ Эффект Nightcore {'включен' if enabled else 'выключен'}"
        )

        if song:
            embed.add_field(
                name="🎵 Текущий трек",
                value=f"**[{song.title}]({song.uri})**",
                inline=False
            )

        if enabled:
            embed.add_field(
                name="⚙️ Настройки эффекта",
                value="**Скорость:** `120%`\n**Тональность:** `120%`\n**Частота:** `100%`",
                inline=False
            )

        embed.set_footer(text=f"{'Эффект применен' if enabled else 'Эффект отключен'} • {interaction.user}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicSystem(bot))