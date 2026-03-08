import asyncio, discord, os, time
from cogs.customization.Banner import Banner
from discord.ext import commands
from dotenv import load_dotenv
from Niludetsu import config
from Niludetsu.database.supabase_database import database
from Niludetsu.logging import logger
from Niludetsu.tools.AccessControl import AccessGuard
from Niludetsu.tools.Errors import setup_error_handling
from Niludetsu.tools.Loader import Loader
from Niludetsu.tools.Embed import Embed
from Niludetsu.quests.tracker import QuestTracker

intents = discord.Intents.all()
async def get_prefix(bot, message):
    controller: AccessGuard | None = getattr(bot, "access", None)
    guild_id = message.guild.id if message.guild else None
    if controller:
        return controller.prefixes_for(guild_id)
    if guild_id == config.SERVERS["MAIN_ID"]:
        return config.PREFIX["MAIN_SERVER"]
    return config.PREFIX["OTHER_SERVER"]

class NiludetsuBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree.on_error = self._on_app_command_error

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
            
        # Игнорируем обычные юзерские ошибки (например, неверный аргумент, юзер не найден)
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
        reporter = getattr(self, "bug_report_logger", None)
        if reporter is None:
            logger.error(f"Error in {context_label}: {error}")
            return

        contextual = reporter.ensure_contextual(
            error,
            context_label=context_label,
            origin_hint=origin_hint,
        )

        guild = None
        if ctx:
            guild = ctx.guild
        elif interaction:
            guild = interaction.guild

        channel = await reporter.resolve_channel(guild)
        if not channel:
            logger.error(f"Cannot find bugs channel for error: {error}")
            return

        try:
            if ctx:
                await reporter.log_command_error(channel, ctx, contextual)
            elif interaction:
                await reporter.log_app_command_error(channel, interaction, contextual)
            else:
                import traceback
                tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                paste_url = await reporter._create_paste(
                    title=f"Event error: {context_label}",
                    content=f"=== EVENT ERROR REPORT ===\nContext: {context_label}\nException: {type(error).__name__}: {error}\n\n Traceback:\n{tb_text}"
                )
                await reporter._send_channel_message(
                    channel,
                    header=f"Ошибка события `{context_label}`",
                    user=None,
                    extra=paste_url,
                    raw_error=error,
                )
        except Exception as e:
            logger.exception(f"Failed to report error: {e}")

    async def setup_hook(self):
        await setup_error_handling(self)
        self.db = database
        self.db.set_bot(self)

        self.access = AccessGuard(self)
        self.command_manager = self.access
        self.permissions = config

        from Niludetsu.moderation.manager import ModerationManager
        self.moderation_manager = ModerationManager(self)
        self.moderation_manager.start_expire_system()

        self.loader = Loader(self, command_dirs=["commands", "cogs"])
        await self.loader.load_everything()
        await self.access.bootstrap()

        self.banner = Banner(self)
        await self.banner.cog_load()

        self.quest_tracker = QuestTracker(self)

        for category in self.command_manager.get_categories():
            self.command_manager.set_category_enabled(config.SERVERS["MAIN_ID"], category, True)

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
        while True:
            try:
                main_guild = self.get_guild(config.SERVERS["MAIN_ID"])
                if main_guild:
                    member_count = main_guild.member_count
                    await self.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name=f"на {member_count:,} участников Æther 🖤",
                        )
                    )
            except Exception as exc:
                await self._report_error("background: update_status", exc, "update_status")
            await asyncio.sleep(300)

    async def on_ready(self):
        logger.success("✅ Бот {} успешно запущен!", self.user)
        asyncio.create_task(self.update_status())

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

        if level_system and message.guild.id == config.SERVERS["MAIN_ID"]:
            await level_system.process_message(message)

        # Quest tracking (only MAIN_ID)
        if message.guild.id == config.SERVERS["MAIN_ID"]:
            asyncio.create_task(
                self.quest_tracker.on_message(str(message.guild.id), str(message.author.id))
            )

bot = NiludetsuBot(command_prefix=get_prefix, intents=intents)
bot.start_time = time.time()
load_dotenv()
level_system = None
bot.run(os.getenv("MAIN_TOKEN"))
