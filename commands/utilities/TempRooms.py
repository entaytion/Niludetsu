import asyncio
import discord
from discord.ext import commands, tasks
from Niludetsu import config, logger
from Niludetsu.locale import _
from Niludetsu.temprooms.service import TempRoomService
from Niludetsu.temprooms.views import TempRoomActions

class TempRooms(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.service = TempRoomService(bot)
        self.actions_view = TempRoomActions(self.service)
        self.cleanup_lock = asyncio.Lock()
        self.cleanup_loop.start()


    async def cog_load(self) -> None:
        await self._attach_view_message()

    async def cog_unload(self) -> None:
        self.cleanup_loop.cancel()
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

        self.bot.add_view(self.actions_view, message_id=message.id)
        try:
            await message.edit(view=self.actions_view)
        except Exception:
            pass


    @tasks.loop(seconds=30)
    async def cleanup_loop(self) -> None:
        await self._cleanup_all_empty(reason="Фоновая очистка пустых комнат")

    @cleanup_loop.before_loop
    async def before_cleanup_loop(self) -> None:
        await self.bot.wait_until_ready()

    async def _cleanup_all_empty(self, reason: str = "Очистка пустых временных комнат") -> None:
        try:
            category_id = getattr(config, "TEMPROOM_CATEGORY", None)
            lobby_id = getattr(config, "TEMPROOM_VOICE", None)
            if not category_id:
                return

            main_guild_id = config.SERVERS.get("MAIN_ID")
            guild = self.bot.get_guild(main_guild_id)
            if not guild:
                return

            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                return

            for channel in category.voice_channels:
                if channel.id == lobby_id:
                    continue
                if len(channel.members) == 0:
                    room = await self.service.get_room(channel.id)
                    is_temp = (room is not None) or (await self.service.repo.is_temp_channel(str(channel.id)))
                    if is_temp:
                        async with self.cleanup_lock:
                            if len(channel.members) == 0:
                                await self.service.delete_temp_room(channel, reason=reason)
        except Exception as e:
            logger.error(f"[TempRooms] Ошибка при очистке комнат: {e}")


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._attach_view_message()
        await self._cleanup_all_empty(reason="Очистка зависших каналов при запуске")

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

        if after.channel and after.channel.id == lobby_id:
            try:
                await self.service.create_temp_room(member)
            except Exception as exc:  # noqa: BLE001
                await member.send(t("utilities", "temproom_create_error", error=exc))
            return

        if before.channel and before.channel != after.channel:
            await self._maybe_cleanup_channel(before.channel)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self._cleanup_all_empty(reason="Очистка после выхода участника")

    async def _maybe_cleanup_channel(self, channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.VoiceChannel):
            return
        lobby_id = getattr(config, "TEMPROOM_VOICE", None)
        if channel.id == lobby_id:
            return

        room = await self.service.get_room(channel.id)
        is_temp = (room is not None) or (await self.service.repo.is_temp_channel(str(channel.id)))
        if not is_temp:
            return

        await asyncio.sleep(1.5)

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

    @commands.command(name="temproom-setup")
    @commands.is_owner()
    async def temproom_setup(self, ctx: commands.Context) -> None:
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
