"""
Основной модуль для работы с музыкой.
Предоставляет базовые классы и функции для воспроизведения музыки.
"""

import discord
from discord.ext import commands
import wavelink
from ..utils import create_embed
import yaml
from typing import Optional, Union
import asyncio

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
        try:
            return player.channel is not None and player.channel.id is not None
        except AttributeError:
            return False

    def __init__(self, bot: commands.Bot):
        if not self._initialized:
            self.bot = bot
            self.voice_states = {}
            self.wavelink_node = None
            self._node_connected = False
            self._connection_error_logged = False
            self.wavelink = wavelink  # Добавляем доступ к wavelink

            # Загружаем конфигурацию
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.lavalink_config = config.get('music', {}).get('lavalink', {})

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

        try:
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
            print("✅ Lavalink node connected successfully!")
            
        except wavelink.exceptions.InvalidNodeException:
            if not hasattr(self, '_connection_error_logged'):
                print("❌ Ошибка подключения к Lavalink: нет доступных нод")
                self._connection_error_logged = True
        except Exception as e:
            if not hasattr(self, '_connection_error_logged'):
                print(f"❌ Ошибка подключения к Lavalink: {str(e)}")
                self._connection_error_logged = True

    async def join_voice(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """Подключение к голосовому каналу"""
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Вы должны находиться в голосовом канале!"
                ),
                ephemeral=True
            )
            return None

        channel = interaction.user.voice.channel
        if not channel:
            return None

        try:
            player = wavelink.Pool.get_node().get_player(interaction.guild.id)
            if not player:
                player = await channel.connect(cls=wavelink.Player)
            elif player.channel.id != channel.id:
                await player.move_to(channel)
            return player
        except Exception as e:
            print(f"Error joining voice: {e}")
            return None

    async def ensure_voice(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        """Проверка и подключение к голосовому каналу"""
        player = await self.join_voice(interaction)
        if not player:
            return None

        if not player._connected:
            await interaction.response.send_message(
                embed=create_embed(
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

    async def play_song(self, interaction: discord.Interaction, query: str):
        """Воспроизведение песни"""
        # Сохраняем текстовый канал
        self.set_text_channel(interaction.guild_id, interaction.channel)
        
        # Сразу откладываем ответ
        await interaction.response.defer()

        player = await self.ensure_voice(interaction)
        if not player:
            return

        # Поиск трека
        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                await interaction.followup.send(
                    embed=create_embed(
                        description="❌ Ничего не найдено!"
                    ),
                    ephemeral=True
                )
                return

            track = tracks[0]
            # Создаем объект Song с информацией о запросившем
            song = Song(track, interaction.user)
            
            if player.playing:
                # Добавляем в очередь сам трек wavelink
                await player.queue.put_wait(track)
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎵 Добавлено в очередь",
                        description=f"**{track.title}**\nАвтор: {track.author}"
                    )
                )
            else:
                # Начинаем воспроизведение
                song.start_time = discord.utils.utcnow()
                await player.play(track)
                self.set_current_song(interaction.guild_id, song)  # Сохраняем информацию о текущем треке
                await interaction.followup.send(
                    embed=create_embed(
                        title="🎵 Сейчас играет",
                        description=f"**{track.title}**\nАвтор: {track.author}"
                    )
                )

        except Exception as e:
            print(f"Error playing song: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="❌ Произошла ошибка при воспроизведении!"
                ),
                ephemeral=True
            )

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
            try:
                player = wavelink.Pool.get_node().get_player(voice_client.guild.id)
                if player:
                    await player.disconnect()
                    # Получаем сохраненный текстовый канал
                    text_channel = self.get_text_channel(voice_client.guild.id)
                    if text_channel:
                        await text_channel.send(
                            embed=create_embed(
                                description=f"👋 Бот покинул канал {voice_client.channel.name}, так как все пользователи вышли"
                            )
                        )
            except Exception as e:
                print(f"Ошибка при отключении от канала: {e}")

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Обработчик окончания трека"""
        try:
            player = payload.player
            if not player:
                return

            guild_id = int(player.guild.id)
            current_song = self.get_current_song(guild_id)
            
            # Очищаем информацию о текущем треке
            self.set_current_song(guild_id, None)
            
            # Получаем режим повтора
            repeat_cog = self.bot.get_cog('Repeat')
            if repeat_cog:
                from cogs.music.Repeat import RepeatMode
                repeat_mode = repeat_cog.get_repeat_mode(guild_id)

                if repeat_mode == RepeatMode.SINGLE and current_song:
                    # Для режима повтора одного трека
                    await player.play(current_song.track)
                    self.set_current_song(guild_id, current_song)
                    return
            
            # Если есть следующий трек в очереди, воспроизводим его
            if not player.queue.is_empty:
                next_track = await player.queue.get_wait()
                next_song = Song(next_track, current_song.requester if current_song else None)
                await player.play(next_track)
                self.set_current_song(guild_id, next_song)

                # Если включен режим повтора очереди, добавляем текущий трек в конец
                if repeat_cog and repeat_mode == RepeatMode.QUEUE and current_song:
                    await player.queue.put_wait(current_song.track)
                
                # Отправляем сообщение о новом треке в сохраненный канал
                text_channel = self.get_text_channel(guild_id)
                if text_channel:
                    embed = create_embed(
                        title="🎵 Сейчас играет",
                        description=f"**{next_track.title}**\nАвтор: {next_track.author}"
                    )
                    try:
                        await text_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Ошибка при отправке сообщения о новом треке: {e}")
        except Exception as e:
            print(f"Ошибка в обработчике окончания трека: {e}")

    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Обработчик ошибок воспроизведения"""
        try:
            player = payload.player
            if not player:
                return
                
            if not player.queue.is_empty:
                next_track = await player.queue.get_wait()
                await player.play(next_track)
        except Exception as e:
            print(f"Ошибка в обработчике исключения трека: {e}")

    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload):
        """Обработчик зависания трека"""
        try:
            player = payload.player
            if not player:
                return
                
            if not player.queue.is_empty:
                next_track = await player.queue.get_wait()
                await player.play(next_track)
        except Exception as e:
            print(f"Ошибка в обработчике зависания трека: {e}") 