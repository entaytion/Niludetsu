import asyncio, discord
from discord.ext import commands
from Niludetsu import config
from Niludetsu.locale import _
from Niludetsu.temprooms.service import TempRoomService
from Niludetsu.temprooms.views import TempRoomActions

class TempRooms(commands.Cog):
    """Управление временными голосовыми каналами."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.service = TempRoomService(bot)
        self.actions_view = TempRoomActions(self.service)
        self.cleanup_lock = asyncio.Lock()

    # Жизненный цикл 

    async def cog_load(self) -> None:
        await self._attach_view_message()

    async def cog_unload(self) -> None:
        self.bot.remove_view(self.actions_view)

    async def _attach_view_message(self) -> None:
        message_id = getattr(config, "TEMPROOM_MESSAGE", None)
        channel_id = getattr(config, "TEMPROOM_CHANNEL", None)
        if not message_id or not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return

        # Зарегистрируем обработчик и обновим компоненты сообщения на актуальный вид
        self.bot.add_view(self.actions_view, message_id=message.id)
        try:
            await message.edit(view=self.actions_view)
        except Exception:
            pass

    # Слушатели 

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._attach_view_message()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        lobby_id = getattr(config, "TEMPROOM_VOICE", None)
        if not lobby_id:
            return

        t = _(guild_id=member.guild.id, bot=self.bot)

        # Создание канала при входе в лобби
        if after.channel and after.channel.id == lobby_id:
            try:
                await self.service.create_temp_room(member)
            except Exception as exc:  # noqa: BLE001
                await member.send(t("utilities", "temproom_create_error", error=exc))  # best-effort
            return

        # Удаляем пустые временные каналы
        if before.channel and not after.channel:
            await self._maybe_cleanup_channel(before.channel)

        # Обработка перехода между временными каналами
        if before.channel and before.channel != after.channel:
            await self._maybe_cleanup_channel(before.channel)

    async def _maybe_cleanup_channel(self, channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.VoiceChannel):
            return
        room = await self.service.get_room(channel.id)
        if not room:
            return
        if channel.members:
            return
        async with self.cleanup_lock:
            if channel.members:
                return
            await self.service.delete_temp_room(channel, reason="Temp room empty")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        if isinstance(channel, discord.VoiceChannel):
            await self.service.repo.deactivate_room(str(channel.id))
            self.service.invalidate_room(str(channel.id))
        if isinstance(channel, discord.TextChannel):
            rooms = await self.service.repo.db.where(
                "temprooms",
                filters=[
                    {"column": "thread_id", "value": str(channel.id)},
                    {"column": "active", "value": True},
                ],
            )
            for row in rooms:
                await self.service.repo.update_room(row["channel_id"], thread_id=None)

    # Команды 
    @commands.command(name="temproom-setup")
    @commands.is_owner()
    async def temproom_setup(self, ctx: commands.Context) -> None:
        """Создаёт панель управления и показывает ID для config.py."""
        t = _(ctx=ctx)
        channel = ctx.channel
        if not isinstance(channel, discord.TextChannel):
            await ctx.reply(t("utilities", "temproom_text_channel_only"), mention_author=False)
            return

        embed = discord.Embed(
            title=t("utilities", "temproom_setup_title"),
            description=t("utilities", "temproom_setup_desc"),
            colour=discord.Colour.blurple(),
        )
        message = await channel.send(embed=embed, view=self.actions_view)

        lobby = ctx.guild.get_channel(config.TEMPROOM_VOICE) if config.TEMPROOM_VOICE else None
        category = ctx.guild.get_channel(config.TEMPROOM_CATEGORY) if config.TEMPROOM_CATEGORY else None

        await ctx.reply(
            t(
                "utilities",
                "temproom_setup_done",
                channel_id=channel.id,
                message_id=message.id,
                category_id=category.id if category else "...",
                voice_id=lobby.id if lobby else "...",
            ),
            mention_author=False,
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TempRooms(bot))
