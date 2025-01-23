import discord
from discord.ext import commands
import wavelink
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS
import json

with open('config/config.json', 'r') as f:
    LAVALINK_SERVER = json.load(f)['LAVALINK']

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.node = None
        self.repeating = {}
        self.nightcore_enabled = {}
        bot.loop.create_task(self.connect_nodes())
        
        bot.event(self.on_wavelink_track_end)
        bot.event(self.on_wavelink_track_start)
        bot.event(self.on_voice_state_update)

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

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """Обработчик окончания трека"""
        player = payload.player
        
        if not player:
            return
        
        if self.repeating.get(player.guild.id):
            await player.play(payload.track)
            return
        
        if player.queue:
            next_track = await player.queue.get_wait()
            await player.play(next_track)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Обработчик начала трека"""
        player = payload.player
        track = payload.track
        
        if not player or not track:
            return
        
        embed = create_embed(
            title="🎵 Сейчас играет:",
            description=f"**{track.title}**\nИсполнитель: {track.author}",
            footer=FOOTER_SUCCESS
        )
        
        if hasattr(player, 'home'):
            await player.home.send(embed=embed)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Обработчик изменения голосового канала"""
        if member.bot:  
            return
        
        player = wavelink.Pool.get_node().get_player(member.guild.id)
        if not player:
            return
        
        if not player.channel:
            return
        
        channel_members = len([m for m in player.channel.members if not m.bot])
        if channel_members == 0:
            await player.disconnect()
            if hasattr(player, 'home'):
                await player.home.send(
                    embed=create_embed(
                        description="Все вышли из канала. Отключаюсь...",
                        footer=FOOTER_SUCCESS
                    )
                )

async def setup(bot):
    await bot.add_cog(Core(bot)) 