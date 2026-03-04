"""
Менеджер музыкальной системы.
Централизованное управление воспроизведением музыки.
"""
import discord, os, wavelink
from dotenv import load_dotenv
from Niludetsu.tools.Embed import Embed
from typing import Optional, Dict

class Song:
    """Класс, представляющий песню"""
    def __init__(self, track: wavelink.Playable, requester: discord.Member = None):
        self.track = track
        self.title = track.title
        self.author = track.author
        self.duration = track.length
        self.uri = track.uri
        self.is_stream = track.is_stream
        self.thumbnail = track.artwork_url if hasattr(track, 'artwork_url') else None
        self.requester = requester
        self.start_time = None

    def format_duration(self) -> str:
        """Форматирует длительность трека"""
        if self.is_stream:
            return "🔴 LIVE"
        minutes = self.duration // 60000
        seconds = (self.duration % 60000) // 1000
        return f"{minutes}:{seconds:02d}"

class VoiceState:
    """Класс для управления состоянием голосового подключения"""
    def __init__(self, bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.current: Optional[Song] = None
        self.voice: Optional[wavelink.Player] = None
        self._loop = False
        self._volume = 100
        self.skip_votes = set()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: int):
        self._volume = value
        if self.voice:
            self.voice.volume = value

    def is_playing(self):
        if self.voice:
            return self.voice.is_playing()
        return False

    async def stop(self):
        """Остановка воспроизведения"""
        if self.voice:
            await self.voice.disconnect()
            self.voice = None
        self.current = None

    @property
    def queue(self):
        """Получить очередь треков"""
        if self.voice:
            return self.voice.queue
        return None

class MusicManager:
    """Менеджер музыкальной системы"""

    _instance = None
    _initialized = False

    def __new__(cls, bot):
        if cls._instance is None:
            cls._instance = super(MusicManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, bot):
        if not self._initialized:
            self.bot = bot
            self.voice_states: Dict[int, VoiceState] = {}
            self._current_songs: Dict[int, Song] = {}
            self._text_channels: Dict[int, discord.TextChannel] = {}
            self._nightcore_enabled: Dict[int, bool] = {}
            self.wavelink_node = None
            self._node_connected = False

            # Загружаем конфиг Lavalink
            load_dotenv()
            self.lavalink_config = {
                'host': os.getenv('LAVALINK_HOST'),
                'port': os.getenv('LAVALINK_PORT'),
                'password': os.getenv('LAVALINK_PASSWORD'),
                'identifier': os.getenv('LAVALINK_IDENTIFIER'),
                'secure': os.getenv('LAVALINK_SECURE', 'false').lower() == 'true'
            }

            # Инициализируем подключение
            if not hasattr(self, '_connect_task'):
                self._connect_task = bot.loop.create_task(self.connect_nodes())

            # Регистрируем события
            if not hasattr(self, '_event_registered'):
                bot.event(self.on_voice_state_update)
                bot.event(self.on_wavelink_track_end)
                bot.event(self.on_wavelink_track_exception)
                bot.event(self.on_wavelink_track_stuck)
                self._event_registered = True

            MusicManager._initialized = True

    async def connect_nodes(self):
        """Подключение к серверу Lavalink"""
        await self.bot.wait_until_ready()

        if self._node_connected:
            return

        self.wavelink_node = wavelink.Node(
            uri=f"{'ws' if not self.lavalink_config['secure'] else 'wss'}://{self.lavalink_config['host']}:{self.lavalink_config['port']}",
            password=self.lavalink_config['password'],
            identifier=self.lavalink_config['identifier']
        )

        await wavelink.Pool.connect(nodes=[self.wavelink_node], client=self.bot)
        self._node_connected = True
        print("[MusicManager] Подключено к Lavalink")

    def get_voice_state(self, guild: discord.Guild) -> VoiceState:
        """Получение состояния голосового подключения"""
        state = self.voice_states.get(guild.id)
        if not state:
            state = VoiceState(self.bot, guild)
            self.voice_states[guild.id] = state
        return state

    def get_current_song(self, guild_id: int) -> Optional[Song]:
        """Получить текущий трек"""
        return self._current_songs.get(guild_id)

    def set_current_song(self, guild_id: int, song: Optional[Song]):
        """Установить текущий трек"""
        if song is None:
            self._current_songs.pop(guild_id, None)
        else:
            self._current_songs[guild_id] = song

    def set_text_channel(self, guild_id: int, channel: discord.TextChannel):
        """Сохранить текстовый канал"""
        self._text_channels[guild_id] = channel

    def get_text_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """Получить текстовый канал"""
        return self._text_channels.get(guild_id)

    async def join_voice(self, ctx_or_interaction) -> Optional[wavelink.Player]:
        """Подключение к голосовому каналу"""
        # Определяем тип (Context или Interaction)
        if hasattr(ctx_or_interaction, 'author'):
            user = ctx_or_interaction.author
            guild = ctx_or_interaction.guild
        else:
            user = ctx_or_interaction.user
            guild = ctx_or_interaction.guild

        if not user.voice:
            error_embed = Embed.error(description="Вы должны находиться в голосовом канале!")
            if hasattr(ctx_or_interaction, 'followup'):
                await ctx_or_interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=error_embed)
            return None

        channel = user.voice.channel
        player = wavelink.Pool.get_node().get_player(guild.id)

        if not player:
            player = await channel.connect(cls=wavelink.Player, timeout=60.0)
        elif player.channel.id != channel.id:
            await player.move_to(channel)

        return player

    async def ensure_voice(self, ctx_or_interaction) -> Optional[wavelink.Player]:
        """Проверка и подключение к голосовому каналу"""
        player = await self.join_voice(ctx_or_interaction)
        if not player:
            return None

        if not player._connected:
            error_embed = Embed.error(description="Не удалось подключиться к голосовому каналу!")
            if hasattr(ctx_or_interaction, 'followup'):
                await ctx_or_interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=error_embed)
            return None

        return player

    async def search_track(self, query: str) -> Optional[wavelink.Playable]:
        """Поиск трека с поддержкой разных источников"""
        search_query = query

        # YouTube
        if 'youtube.com/' in query or 'youtu.be/' in query:
            if 'youtube.com/watch?v=' in query:
                video_id = query.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in query:
                video_id = query.split('youtu.be/')[1].split('?')[0]
            else:
                video_id = None

            if video_id:
                search_query = f"https://youtube.com/watch?v={video_id}"

            tracks = await wavelink.Playable.search(search_query, source="ytsearch")

        # Spotify
        elif 'spotify.com/' in query:
            tracks = await wavelink.Playable.search(query, source="spsearch")

        # SoundCloud
        elif 'soundcloud.com/' in query:
            tracks = await wavelink.Playable.search(query, source="scsearch")

        else:
            # Последовательный поиск по источникам
            tracks = await wavelink.Playable.search(query, source="ytsearch")
            if not tracks:
                tracks = await wavelink.Playable.search(query, source="scsearch")
            if not tracks:
                tracks = await wavelink.Playable.search(query, source="ytmsearch")

        if not tracks:
            return None

        track = tracks[0]

        # Проверка доступности
        if not track.uri or getattr(track, 'is_failed', False):
            if len(tracks) > 1:
                for alt_track in tracks[1:]:
                    if alt_track.uri and not getattr(alt_track, 'is_failed', False):
                        return alt_track
            return None

        return track

    async def play_song(self, ctx_or_interaction, query: str):
        """Воспроизведение трека"""
        # Defer response
        if hasattr(ctx_or_interaction, 'response'):
            await ctx_or_interaction.response.defer()

        player = await self.ensure_voice(ctx_or_interaction)
        if not player:
            return

        if not self._node_connected:
            error_embed = Embed.error(description="Сервер музыки недоступен. Попробуйте позже.")
            if hasattr(ctx_or_interaction, 'followup'):
                await ctx_or_interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=error_embed)
            return

        track = await self.search_track(query)
        if not track:
            error_embed = Embed.error(description="По вашему запросу ничего не найдено!")
            if hasattr(ctx_or_interaction, 'followup'):
                await ctx_or_interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=error_embed)
            return

        user = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
        guild = ctx_or_interaction.guild
        channel = ctx_or_interaction.channel

        song = Song(track, user)
        state = self.get_voice_state(guild)

        if player.playing:
            await player.queue.put_wait(track)
            embed = Embed.success(
                title="🎵 Добавлено в очередь",
                description=f"**[{track.title}]({track.uri})**\nДлительность: {song.format_duration()}",
                thumbnail_url=song.thumbnail
            )
        else:
            await player.play(track)
            state.current = song
            self.set_current_song(guild.id, song)
            embed = Embed.success(
                title="🎵 Сейчас играет",
                description=f"**[{track.title}]({track.uri})**\nДлительность: {song.format_duration()}",
                thumbnail_url=song.thumbnail
            )

        self.set_text_channel(guild.id, channel)

        if hasattr(ctx_or_interaction, 'followup'):
            await ctx_or_interaction.followup.send(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    def is_nightcore_enabled(self, guild_id: int) -> bool:
        """Проверяет, включен ли nightcore"""
        return self._nightcore_enabled.get(guild_id, False)

    def set_nightcore(self, guild_id: int, enabled: bool):
        """Устанавливает состояние nightcore"""
        self._nightcore_enabled[guild_id] = enabled

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Обработчик изменений в голосовых каналах"""
        if member.id == self.bot.user.id:
            return

        if not before.channel:
            return

        voice_client = before.channel.guild.voice_client
        if not voice_client or not voice_client.channel:
            return

        members = [m for m in voice_client.channel.members if not m.bot]

        if not members:
            player = wavelink.Pool.get_node().get_player(voice_client.guild.id)
            if player:
                await player.disconnect()
                text_channel = self.get_text_channel(voice_client.guild.id)
                if text_channel:
                    await text_channel.send(
                        embed=Embed.info(
                            description=f"👋 Бот покинул канал {voice_client.channel.name}, так как все пользователи вышли"
                        )
                    )

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Обработчик окончания трека"""
        if not payload or not payload.player:
            return

        guild_id = payload.player.guild.id if payload.player.guild else None
        if not guild_id:
            return

        text_channel = self.get_text_channel(guild_id)
        if not text_channel:
            return

        state = self.get_voice_state(payload.player.guild)
        if not state:
            return

        state.current = None
        self.set_current_song(guild_id, None)

        if not payload.player.queue.is_empty:
            next_track = await payload.player.queue.get_wait()
            await payload.player.play(next_track)
            state.current = Song(next_track, None)
            self.set_current_song(guild_id, state.current)

            if payload.reason == "finished":
                await text_channel.send(
                    embed=Embed.info(
                        title="🎵 Сейчас играет",
                        description=f"**{next_track.title}**\nДлительность: {state.current.format_duration()}"
                    )
                )
        else:
            if payload.reason == "finished":
                await text_channel.send(
                    embed=Embed.info(
                        title="🎵 Очередь завершена",
                        description="Все треки воспроизведены"
                    )
                )

    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Обработчик ошибок трека"""
        guild_id = payload.player.guild.id
        channel = self.get_text_channel(guild_id)

        error_message = f"Произошла ошибка при воспроизведении трека:\n**{payload.track.title}**"

        if hasattr(payload, 'error'):
            error_message += f"\nДетали: ```{payload.error}```"

        if channel:
            await channel.send(embed=Embed.error(description=error_message))

        print(f"[MusicManager] Track Exception - Guild: {guild_id}, Track: {payload.track.title}")

    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload):
        """Обработчик зависания трека"""
        guild_id = payload.player.guild.id
        channel = self.get_text_channel(guild_id)

        if channel:
            await channel.send(embed=Embed.warning(description=f"Трек зависает:\n**{payload.track.title}**"))

