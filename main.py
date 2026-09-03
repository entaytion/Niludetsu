import asyncio, os, time

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from Niludetsu import (
    config, settings, database, logger, Embed,
    AccessGuard, QuestTracker, LevelTracker
)
from Niludetsu.tools.Errors import ErrorHandler
from Niludetsu.tools.Loader import Loader
from Niludetsu.config_manager import ConfigManager
from web.bot import set_bot

intents = discord.Intents.all()
async def get_prefix(bot, message):
    if message.guild is None:
        return ["!"]
    controller: AccessGuard | None = getattr(bot, "access", None)
    if controller:
        return controller.prefixes_for(message.guild.id)
    if message.guild.id == config.SERVERS["MAIN_ID"]:
        return config.PREFIX["MAIN_SERVER"]
    return config.PREFIX["OTHER_SERVER"]

class NiludetsuBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree.on_error = self._on_app_command_error
        self._status_task: asyncio.Task | None = None
        self.http_session: aiohttp.ClientSession | None = None

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
            
        if isinstance(error, commands.UserInputError):
            embed = Embed.error(title="❌ Ошибка ввода", description=str(error))
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException:
                pass
            return

        command_name = ctx.command.qualified_name if ctx.command else "unknown"
        await self._report_error(f"command: {command_name}", error, None, ctx=ctx)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_value is None:
            return
        await self._report_error(f"event: {event_method}", exc_value, event_method)

    async def _report_error(
        self,
        context_label: str,
        error: Exception,
        origin_hint=None,
        ctx: commands.Context = None,
        interaction: discord.Interaction = None
    ) -> None:
        logger.exception(f"Error in {context_label}: {error}")

        import traceback
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_text = "".join(tb_lines)

        bugs_channel_id = getattr(config, "BUGS_CHANNEL_ID", None)
        if bugs_channel_id:
            try:
                channel = self.get_channel(bugs_channel_id)
                if not channel:
                    channel = await self.fetch_channel(bugs_channel_id)
                if channel:
                    user_info = None
                    if ctx:
                        user_info = f"{ctx.author} (`{ctx.author.id}`)"
                    elif interaction:
                        user_info = f"{interaction.user} (`{interaction.user.id}`)"

                    embed = Embed.error(
                        title=f"Ошибка: {context_label}",
                        description=f"**Исключение:** `{type(error).__name__}: {error}`"
                    )
                    if user_info:
                        embed.add_field(name="Вызвал", value=user_info, inline=True)
                    if ctx and ctx.guild:
                        embed.add_field(name="Сервер", value=f"{ctx.guild.name} (`{ctx.guild.id}`)", inline=True)
                    elif interaction and interaction.guild:
                        embed.add_field(name="Сервер", value=f"{interaction.guild.name} (`{interaction.guild.id}`)", inline=True)

                    tb_snippet = tb_text[-1800:] if len(tb_text) > 1800 else tb_text
                    embed.add_field(name="Traceback", value=f"```py\n{tb_snippet}\n```", inline=False)
                    await channel.send(embed=embed)
            except Exception as report_exc:
                logger.error(f"Failed to send error report to bugs channel: {report_exc}")

        user_embed = Embed.error(
            title="Произошла непредвиденная ошибка",
            description="Информация об ошибке была отправлена разработчикам."
        )
        try:
            if interaction:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=user_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=user_embed, ephemeral=True)
            elif ctx:
                await ctx.reply(embed=user_embed, ephemeral=True)
        except Exception:
            pass

    async def setup_hook(self):
        self.error_handler = ErrorHandler(self)
        self.db = database
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20)
        )

        await settings.load()

        self.config_manager = ConfigManager(self)
        await self.config_manager.load_all()
        await self.db.setup_tables()

        self.access = AccessGuard(self)
        self.command_manager = self.access
        self.permissions = settings

        from Niludetsu.moderation.manager import ModerationManager
        self.moderation_manager = ModerationManager(self)
        self.moderation_manager.start_expire_system()

        self.loader = Loader(self, command_dirs=["commands"])
        await self.loader.load_everything()
        await self.access.bootstrap()

        self.quest_tracker = QuestTracker(self)
        self.level_tracker = LevelTracker(settings.SERVERS["MAIN_ID"], config_manager=self.config_manager)

        for category in self.command_manager.get_categories():
            self.command_manager.set_category_enabled(settings.SERVERS["MAIN_ID"], category, True)

        self._web_server = None
        self._web_task = asyncio.create_task(self._run_web_server(), name="web-server")

    async def _run_web_server(self) -> None:
        import uvicorn
        from web.app import app as web_app
        from web.config import HOST, PORT

        set_bot(self)
        cfg = uvicorn.Config(
            web_app,
            host=HOST,
            port=PORT,
            loop="asyncio",
            log_level="info",
        )
        self._web_server = uvicorn.Server(cfg)
        logger.info("🌐 Web dashboard starting on {}:{}", HOST, PORT)
        await self._web_server.serve()

    async def _on_app_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        from discord import app_commands
        if isinstance(error, app_commands.TransformerError) or isinstance(error, app_commands.CheckFailure):
            embed = Embed.error(title="❌ Ошибка команды", description=str(error))
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.HTTPException:
                pass
            return

        command_name = interaction.command.qualified_name if interaction.command else "unknown"
        await self._report_error(f"interaction: {command_name}", error, None, interaction=interaction)

    async def update_status(self):
        while not self.is_closed():
            try:
                main_guild = self.get_guild(settings.SERVERS["MAIN_ID"])
                if main_guild:
                    member_count = main_guild.member_count
                    await self.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name=f"{member_count:,} nullther's",
                        )
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                await self._report_error("background: update_status", exc, "update_status")
            await asyncio.sleep(300)

    async def on_ready(self):
        logger.success("✅ Бот {} успешно запущен!", self.user)
        if self._status_task is None or self._status_task.done():
            self._status_task = asyncio.create_task(self.update_status())

    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if not self.access.can_use_prefix_command(message.guild.id):
            return

        prefixes = await self.command_prefix(self, message)
        used_prefix = next((p for p in prefixes if message.content.startswith(p)), None)
        if used_prefix:
            command_name = message.content[len(used_prefix):].split(" ")[0]
            command = self.get_command(command_name)

            if not self.command_manager.is_command_allowed(message.guild.id, command_name):
                await message.add_reaction("💢")
                await asyncio.sleep(2)
                try:
                    await message.delete()
                except Exception:
                    pass
                return

            await self.process_commands(message)
            return

        if message.guild.id == settings.SERVERS["MAIN_ID"]:
            asyncio.create_task(
                self.quest_tracker.on_message(str(message.guild.id), str(message.author.id))
            )

    async def close(self) -> None:
        if self._status_task and not self._status_task.done():
            self._status_task.cancel()
            try:
                await self._status_task
            except asyncio.CancelledError:
                pass

        if self._web_server:
            self._web_server.should_exit = True
        if self._web_task and not self._web_task.done():
            self._web_task.cancel()
            try:
                await self._web_task
            except (asyncio.CancelledError, Exception):
                pass

        if self.http_session and not self.http_session.closed:
            await self.http_session.close()

        if hasattr(self, "db"):
            await self.db.close()

        await super().close()

allowed = discord.AllowedMentions(users=True, everyone=False, roles=True)
bot = NiludetsuBot(command_prefix=get_prefix, intents=intents, allowed_mentions=allowed)
bot.start_time = time.time()
load_dotenv()
try:
    bot.run(os.getenv("MAIN_TOKEN"))
except KeyboardInterrupt:
    pass
finally:
    pass
