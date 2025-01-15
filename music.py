import discord
from discord.ext import commands
import wavelink
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS
import json

with open('lavalink_config.json', 'r') as f:
    LAVALINK_SERVER = json.load(f)
    
import random

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.node = None
        self.repeating = {}  # Для хранения состояния повторения треков
        bot.loop.create_task(self.connect_nodes())
        
        # Добавляем обработчики событий
        bot.event(self.on_wavelink_track_end)
        bot.event(self.on_wavelink_track_start)

    async def connect_nodes(self):
        """Подключение к серверу Lavalink"""
        await self.bot.wait_until_ready()
        self.node = wavelink.Node(
            uri=f"{'ws' if not LAVALINK_SERVER['secure'] else 'wss'}://{LAVALINK_SERVER['host']}:{LAVALINK_SERVER['port']}",
            password=LAVALINK_SERVER['password'],
            identifier=LAVALINK_SERVER['identifier']
        )
        await wavelink.Pool.connect(nodes=[self.node], client=self.bot)
        print("Music node connected successfully!")

    async def get_player(self, interaction: discord.Interaction) -> wavelink.Player | None:
        """Получение или создание плеера для сервера"""
        try:
            player = wavelink.Pool.get_node().get_player(interaction.guild.id)
            if player:
                return player
            return await interaction.user.voice.channel.connect(cls=wavelink.Player)
        except Exception as e:
            print(f"Error getting/creating player: {e}")
            return None

    async def is_connected(self, interaction: discord.Interaction) -> wavelink.Player | None:
        """Проверка подключения к голосовому каналу и получение плеера."""
        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player or not player.is_connected():
            await interaction.response.send_message(
                embed=create_embed(
                    description="Я не подключен к голосовому каналу!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return None
        return player

    async def is_playing(self, interaction: discord.Interaction) -> wavelink.Player | None:
        """Проверка, что сейчас что-то играет."""
        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player or not player.is_connected():
            await interaction.response.send_message(
                embed=create_embed(
                    description="Я не подключен к голосовому каналу!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return None
        if not player.playing:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Сейчас ничего не играет!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return None
        return player

    @discord.app_commands.command(name="play", description="Воспроизвести музыку")
    @discord.app_commands.describe(query="Поисковый запрос для музыки")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы должны находиться в голосовом канале!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)

        if not self.node or not wavelink.Pool.get_node():
            await interaction.followup.send(
                embed=create_embed(
                    description="Музыкальный сервер недоступен. Попробуйте позже!",
                    footer=FOOTER_ERROR
                )
            )
            return

        player = await self.get_player(interaction)
        if not player:
            await interaction.followup.send(
                embed=create_embed(
                    description="Ошибка подключения к голосовому каналу!",
                    footer=FOOTER_ERROR
                )
            )
            return

        # Сохраняем канал для отправки уведомлений
        if not hasattr(player, 'home'):
            player.home = interaction.channel

        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                await interaction.followup.send(
                    embed=create_embed(
                        description="По вашему запросу ничего не найдено!",
                        footer=FOOTER_ERROR
                    )
                )
                return

            track = tracks[0]

            if player.playing:
                player.queue.put(track)
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎶 Добавлено в очередь:",
                        description=f"**{track.title}**\nЗапросил: {interaction.user.mention}",
                        footer=FOOTER_SUCCESS
                    )
                )
            else:
                await player.play(track)
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎵 Сейчас играет:",
                        description=f"**{track.title}**\nЗапросил: {interaction.user.mention}",
                        footer=FOOTER_SUCCESS
                    )
                )
        except Exception as e:
            print(f"Error in play command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при воспроизведении трека!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="np", description="Показать текущий трек")
    async def nowplaying(self, interaction: discord.Interaction):
        await interaction.response.defer()

        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player or not player.playing:
            await interaction.followup.send(
                embed=create_embed(
                    description="Сейчас ничего не играет!",
                    footer=FOOTER_ERROR
                )
            )
            return

        track = player.current
        if not track:
            await interaction.followup.send(
                embed=create_embed(
                    description="Не удалось получить информацию о треке!",
                    footer=FOOTER_ERROR
                )
            )
            return

        current_time = int(player.position / 1000)  # Конвертируем в секунды
        total_time = int(track.length / 1000)  # Конвертируем в секунды

        progress_segments = 9
        if total_time > 0:
            progress = "▬" * (current_time * progress_segments // total_time)
        else:
            progress = "▬" * progress_segments
        progress += "⏺️"
        remaining_segments = progress_segments - len(progress) + 1
        if remaining_segments > 0:
            progress += "▬" * remaining_segments

        def format_time(seconds):
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            return f"{minutes:02}:{seconds:02}"

        embed = create_embed(
            title="🎵 Сейчас играет:",
            description=f"**{track.title}**\nИсполнитель: {track.author}",
            footer=FOOTER_SUCCESS
        )
        embed.add_field(
            name="🔊 Прогресс:",
            value=f"{progress}\n⏱️ {format_time(current_time)} / {format_time(total_time)}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        player = await self.is_playing(interaction)
        if not player:
            return

        await interaction.response.defer()

        try:
            await player.stop()
            await interaction.followup.send(
                embed=create_embed(
                    description="Трек пропущен!",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in skip command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при пропуске трека!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="queue", description="Просмотр очереди треков")
    async def queue(self, interaction: discord.Interaction):
        # Получаем плеер
        player: wavelink.Player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player or not player.connected:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Я не подключен к голосовому каналу!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            current = player.current
            tracks = list(player.queue)

            if not current and not tracks:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Очередь пуста!",
                        footer=FOOTER_ERROR
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
                    if i >= 10:  # Показываем только первые 10 треков
                        remaining = len(tracks) - 10
                        if remaining > 0:
                            queue_text.append(f"\nИ еще {remaining} треков...")
                        break

            await interaction.followup.send(
                embed=create_embed(
                    title="🎵 Очередь треков:",
                    description="\n".join(queue_text),
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in queue command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при получении очереди!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="leave", description="Отключить бота от голосового канала")
    async def leave(self, interaction: discord.Interaction):
        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if player and player.is_connected():
            await player.disconnect()
            embed = create_embed(
                description="Отключился от голосового канала.",
                footer=FOOTER_SUCCESS
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = create_embed(
                description="Я не подключен к голосовому каналу.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="pause", description="Поставить музыку на паузу")
    async def pause(self, interaction: discord.Interaction):
        player = await self.is_playing(interaction)
        if not player:
            return

        await interaction.response.defer()

        try:
            await player.pause(not player.paused)
            status = "поставлена на паузу" if player.paused else "возобновлена"
            
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Музыка {status}.",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in pause command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="repeat", description="Повторить текущий трек")
    async def repeat(self, interaction: discord.Interaction):
        player = await self.is_playing(interaction)
        if not player:
            return

        await interaction.response.defer()

        try:
            guild_id = interaction.guild.id
            self.repeating[guild_id] = not self.repeating.get(guild_id, False)
            status = "включено" if self.repeating[guild_id] else "отключено"
            
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Повторение трека {status}.",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in repeat command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="shuffle", description="Перемешать очередь треков")
    async def shuffle(self, interaction: discord.Interaction):
        player = await self.is_connected(interaction)
        if not player:
            return

        if not player.queue: # Используем более питоновский способ проверки пустой очереди
            await interaction.response.send_message(
                embed=create_embed(
                    description="Очередь пуста, нечего перемешивать!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        queue_list = list(player.queue)
        random.shuffle(queue_list)
        player.queue.clear()
        for track in queue_list:
            player.queue.put(track)

        await interaction.response.send_message(
            embed=create_embed(
                description="Очередь треков перемешана.",
                footer=FOOTER_SUCCESS
            )
        )

    @discord.app_commands.command(name="resume", description="Продолжить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        player = await self.is_connected(interaction)
        if not player:
            return

        await interaction.response.defer()

        try:
            await player.resume()
            await interaction.followup.send(
                embed=create_embed(
                    description="Воспроизведение продолжено.",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in resume command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка!",
                    footer=FOOTER_ERROR
                )
            )

    @discord.app_commands.command(name="nightcore", description="Включить/выключить эффект Nightcore")
    async def nightcore(self, interaction: discord.Interaction):
        player = await self.is_connected(interaction)
        if not player:
            return

        await interaction.response.defer()

        try:
            filters = player.filters
            
            # Проверяем, включен ли уже эффект
            if filters.timescale.speed == 1.2:  # Если эффект включен
                # Сбрасываем фильтры
                filters.reset()
                status = "выключен"
            else:
                # Устанавливаем эффект
                filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
                status = "включен"

            await player.set_filters(filters)
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Эффект Nightcore {status}!",
                    footer=FOOTER_SUCCESS
                )
            )
        except Exception as e:
            print(f"Error in nightcore command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при установке эффекта!",
                    footer=FOOTER_ERROR
                )
            )

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """Обработчик окончания трека"""
        player = payload.player
        
        if not player:
            return
            
        # Проверяем повтор
        if self.repeating.get(player.guild.id):
            await player.play(payload.track)
            return
            
        # Проверяем очередь
        if player.queue:
            next_track = await player.queue.get_wait()
            await player.play(next_track)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Обработчик начала трека"""
        player = payload.player
        track = payload.track
        
        if not player or not track:
            return
            
        # Создаем embed с информацией о треке
        embed = create_embed(
            title="🎵 Сейчас играет:",
            description=f"**{track.title}**\nИсполнитель: {track.author}",
            footer=FOOTER_SUCCESS
        )
        
        # Отправляем сообщение в тот же канал
        if hasattr(player, 'home'):
            await player.home.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))