"""
Основной модуль для работы с музыкой.
Предоставляет базовые классы и функции для воспроизведения музыки.
"""

import discord
from discord.ext import commands
import wavelink
from Niludetsu.utils.embed import Embed
from typing import Optional, Union
import asyncio
import os
from dotenv import load_dotenv

class Song:
    """Класс, представляющий песню"""
    def __init__(self, track: wavelink.Playable, requester: discord.Member = None):
        self.track = track
        self.title = track.title
        self.author = track.author
        self.duration = track.length  # Используем length вместо duration
        self.uri = track.uri
        self.is_stream = track.is_stream
        self.thumbnail = track.artwork_url if hasattr(track, 'artwork_url') else None
        self.requester = requester
        self.start_time = None

    def format_duration(self) -> str:
        """Форматирует длительность трека"""
        if self.is_stream:
            return "🔴 LIVE"
        minutes = self.duration // 60000  # конвертируем миллисекунды в минуты
        seconds = (self.duration % 60000) // 1000  # остаток в секундах
        return f"{minutes}:{seconds:02d}"

class VoiceState:
    """Класс для управления состоянием голосового подключения"""
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.current: Optional[Song] = None
        self.voice: Optional[wavelink.Player] = None
        self.next = asyncio.Event()
        self.songs = asyncio.Queue()
        self.exists = True
        self._loop = False
        self._volume = 100
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    async def audio_player_task(self):
        """Задача для воспроизведения музыки"""
        while self.exists:
            self.next.clear()
            if not self._loop:
                try:
                    async with asyncio.timeout(180):  # 3 минуты
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    await self.stop()
                    self.exists = False
                    return

            self.voice.play(self.current.track)
            await self.next.wait()

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
        self.exists = False
        self.current = None
        self.songs = asyncio.Queue()

class Music:
    """Основной класс для работы с музыкой"""
    _instance = None
    _initialized = False
    _current_songs = {}  # Словарь для хранения текущих треков по guild_id
    _text_channels = {}  # Словарь для хранения текстовых каналов по guild_id

    def __new__(cls, bot: commands.Bot):
        if cls._instance is None:
            cls._instance = super(Music, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def check_player_connection(player) -> bool:
        """
        Проверяет подключение плеера к голосовому каналу
        
        Args:
            player: Объект плеера Lavalink
            
        Returns:
            bool: True если плеер подключен, False если нет
        """
        return player.channel is not None and player.channel.id is not None

    def __init__(self, bot: commands.Bot):
        if not self._initialized:
            self.bot = bot
            self.voice_states = {}
            self.wavelink_node = None
            self._node_connected = False
            self._connection_error_logged = False
            self.wavelink = wavelink  # Добавляем доступ к wavelink

            # Загружаем переменные окружения
            load_dotenv()
            self.lavalink_config = {
                'host': os.getenv('LAVALINK_HOST'),
                'port': os.getenv('LAVALINK_PORT'),
                'password': os.getenv('LAVALINK_PASSWORD'),
                'identifier': os.getenv('LAVALINK_IDENTIFIER'),
                'secure': os.getenv('LAVALINK_SECURE', 'false').lower() == 'true'
            }

            # Инициализируем подключение к Lavalink только один раз
            if not hasattr(self, '_connect_task'):
                self._connect_task = bot.loop.create_task(self.connect_nodes())
            
            # Добавляем слушатели событий только один раз
            if not hasattr(self, '_event_registered'):
                bot.event(self.on_voice_state_update)
                bot.event(self.on_wavelink_track_end)
                bot.event(self.on_wavelink_track_exception)
                bot.event(self.on_wavelink_track_stuck)
                self._event_registered = True

            Music._initialized = True

    def get_voice_state(self, guild: discord.Guild) -> VoiceState:
        """Получение состояния голосового подключения для сервера"""
        state = self.voice_states.get(guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, guild)
            self.voice_states[guild.id] = state
        return state

    async def connect_nodes(self):
        """Подключение к серверу Lavalink"""
        await self.bot.wait_until_ready()

        # Проверяем, есть ли уже активная нода
        if hasattr(self, '_node_connected') and self._node_connected:
            return

        self.wavelink_node = wavelink.Node(
            uri=f"{'ws' if not self.lavalink_config['secure'] else 'wss'}://{self.lavalink_config['host']}:{self.lavalink_config['port']}",
            password=self.lavalink_config['password'],
            identifier=self.lavalink_config['identifier']
        )
        
        await wavelink.Pool.connect(nodes=[self.wavelink_node], client=self.bot)
        self._node_connected = True

    async def join_voice(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """Подключение к голосовому каналу"""
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Вы должны находиться в голосовом канале!"
                ),
                ephemeral=True
            )
            return None

        channel = interaction.user.voice.channel
        if not channel:
            return None

        player = wavelink.Pool.get_node().get_player(interaction.guild.id)
        if not player:
            player = await channel.connect(cls=wavelink.Player)
        elif player.channel.id != channel.id:
            await player.move_to(channel)
        return player

    async def ensure_voice(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """Проверка и подключение к голосовому каналу"""
        player = await self.join_voice(interaction)
        if not player:
            return None

        if not player._connected:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ Не удалось подключиться к голосовому каналу!"
                ),
                ephemeral=True
            )
            return None

        return player

    def get_current_song(self, guild_id: int) -> Optional[Song]:
        """Получить текущий трек для сервера"""
        return self._current_songs.get(guild_id)

    def set_current_song(self, guild_id: int, song: Optional[Song]):
        """Установить текущий трек для сервера"""
        if song is None:
            self._current_songs.pop(guild_id, None)
        else:
            self._current_songs[guild_id] = song

    def set_text_channel(self, guild_id: int, channel: discord.TextChannel):
        """Сохраняет текстовый канал для гильдии"""
        self._text_channels[guild_id] = channel

    def get_text_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        """Получает текстовый канал для гильдии"""
        return self._text_channels.get(guild_id)

    async def search_track(self, query: str) -> Optional[wavelink.Playable]:
        """
        Поиск трека с поддержкой разных источников и проверкой доступности
        """
        search_query = query
        
        # Если это прямая ссылка на YouTube
        if 'youtube.com/' in query or 'youtu.be/' in query:
            # Пытаемся извлечь ID видео для прямого поиска
            if 'youtube.com/watch?v=' in query:
                video_id = query.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in query:
                video_id = query.split('youtu.be/')[1].split('?')[0]
            else:
                video_id = None
            
            if video_id:
                search_query = f"https://youtube.com/watch?v={video_id}"
            
            tracks = await wavelink.Playable.search(search_query, source="ytsearch")
        
        # Если это Spotify ссылка
        elif 'spotify.com/' in query:
            tracks = await wavelink.Playable.search(query, source="spsearch")
        
        # Если это SoundCloud ссылка
        elif 'soundcloud.com/' in query:
            tracks = await wavelink.Playable.search(query, source="scsearch")
        
        else:
            # Пробуем разные источники последовательно
            tracks = await wavelink.Playable.search(query, source="ytsearch")
            if not tracks:
                tracks = await wavelink.Playable.search(query, source="scsearch")
            if not tracks:
                # Пробуем поиск по YouTube Music
                tracks = await wavelink.Playable.search(query, source="ytmsearch")

        if not tracks:
            return None

        track = tracks[0]
        
        # Расширенная проверка доступности трека
        if not track.uri or getattr(track, 'is_failed', False):
            # Пробуем следующий трек из результатов
            if len(tracks) > 1:
                for alt_track in tracks[1:]:
                    if alt_track.uri and not getattr(alt_track, 'is_failed', False):
                        return alt_track
            return None

        return track

    async def play_song(self, interaction: discord.Interaction, query: str):
        """Воспроизведение песни"""
        # Сразу откладываем ответ
        await interaction.response.defer()
        
        # Проверяем подключение к голосовому каналу
        player = await self.ensure_voice(interaction)
        if not player:
            await interaction.followup.send(
                embed=Embed(
                    description="❌ Не удалось подключиться к голосовому каналу!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Поиск трека
        track = await self.search_track(query)
        if not track:
            await interaction.followup.send(
                embed=Embed(
                    description="❌ По вашему запросу ничего не найдено или контент недоступен!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        song = Song(track, interaction.user)

        # Получаем состояние голосового канала
        state = self.get_voice_state(interaction.guild)
        if not state:
            return

        # Начинаем воспроизведение
        if player.playing:
            # Добавляем в очередь
            await player.queue.put_wait(track)
            await state.songs.put(song)  # Синхронизируем с нашей очередью
            await interaction.followup.send(
                embed=Embed(
                    title="🎵 Добавлено в очередь",
                    description=f"**{track.title}**\nДлительность: {song.format_duration()}",
                    color="GREEN"
                )
            )
        else:
            # Воспроизводим сразу
            await player.play(track)
            state.current = song  # Устанавливаем текущий трек в состоянии
            self.set_current_song(interaction.guild_id, song)  # И в глобальном хранилище
            await interaction.followup.send(
                embed=Embed(
                    title="🎵 Сейчас играет",
                    description=f"**{track.title}**\nДлительность: {song.format_duration()}",
                    color="GREEN"
                )
            )
        
        self.set_text_channel(interaction.guild_id, interaction.channel)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Обработчик изменений в голосовых каналах"""
        if member.id == self.bot.user.id:
            return  # Игнорируем изменения состояния самого бота
            
        # Получаем текущий голосовой канал бота
        if not before.channel:
            return
            
        voice_client = before.channel.guild.voice_client
        if not voice_client or not voice_client.channel:
            return
            
        # Проверяем, остались ли в канале люди (кроме бота)
        members = [m for m in voice_client.channel.members if not m.bot]
        
        if not members:
            player = wavelink.Pool.get_node().get_player(voice_client.guild.id)
            if player:
                await player.disconnect()
                # Получаем сохраненный текстовый канал
                text_channel = self.get_text_channel(voice_client.guild.id)
                if text_channel:
                    await text_channel.send(
                        embed=Embed(
                            description=f"👋 Бот покинул канал {voice_client.channel.name}, так как все пользователи вышли"
                        )
                    )

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Обработчик события окончания трека"""
        if not payload or not payload.player:
            return
            
        guild_id = payload.player.guild.id if payload.player.guild else None
        if not guild_id:
            return
            
        # Получаем текстовый канал для этой гильдии
        text_channel = self.get_text_channel(guild_id)
        if not text_channel:
            return
            
        state = self.get_voice_state(payload.player.guild)
        
        if not state:
            return
            
        # Очищаем текущий трек
        state.current = None
        self.set_current_song(guild_id, None)
        
        # Если есть следующий трек в очереди
        if not state.songs.empty():
            next_song = await state.songs.get()
            await payload.player.play(next_song.track)
            state.current = next_song
            self.set_current_song(guild_id, next_song)
            
            await text_channel.send(
                embed=Embed(
                    title="🎵 Сейчас играет",
                    description=f"**{next_song.title}**\nДлительность: {next_song.format_duration()}",
                    color="BLUE"
                )
            )
        else:
            await text_channel.send(
                embed=Embed(
                    title="🎵 Очередь завершена",
                    description="Все треки воспроизведены",
                    color="BLUE"
                )
            )

    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Обработчик ошибок трека"""
        guild_id = payload.player.guild.id
        channel = self.get_text_channel(guild_id)
        
        if channel:
            await channel.send(
                embed=Embed(
                    title="❌ Ошибка воспроизведения",
                    description=f"Произошла ошибка при воспроизведении трека:\n**{payload.track.title}**",
                    color="RED"
                )
            )

    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload):
        """Обработчик зависания трека"""
        guild_id = payload.player.guild.id
        channel = self.get_text_channel(guild_id)
        
        if channel:
            await channel.send(
                embed=Embed(
                    title="⚠️ Проблема воспроизведения",
                    description=f"Трек зависает:\n**{payload.track.title}**",
                    color="YELLOW"
                )
            )