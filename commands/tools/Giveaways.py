import asyncio, discord
from discord import app_commands
from discord.ext import commands, tasks
from Niludetsu.giveaways import GiveawayManager
from Niludetsu.giveaways.ui import GiveawayConfigurator, GiveawayParticipationView
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService

_time = TimeService()

class Giveaways(commands.Cog):
    """Команды и фоновые задачи для розыгрышей."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = GiveawayManager(bot)
        asyncio.create_task(self.manager.setup_database())
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(GiveawayParticipationView())

    @tasks.loop(seconds=5)
    async def check_giveaways(self):
        if not self.manager.active:
            return  # никаких запросов к Supabase, пока новых розыгрышей нет

        now = _time.now()
        due = await self.manager.repo.get_due()

        for giveaway in due:
            giveaway_id = giveaway["giveaway_id"]
            await self.manager.end_giveaway(giveaway_id)

        for giveaway_id, meta in list(self.manager.active.items()):
            if meta["end_time"] <= now:
                await self.manager.end_giveaway(giveaway_id)

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    giveaway_group = app_commands.Group(
        name="giveaway",
        description="🎉 Управление розыгрышами",
        guild_only=True,
    )

    @giveaway_group.command(name="create", description="🥳 Создать новый розыгрыш")
    async def giveaway_create(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Ты не админ, иди нахуй!", ephemeral=True)
            return

        view = GiveawayConfigurator(self, interaction.guild, interaction.user)
        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True,
        )
        view.message = await interaction.original_response()

    @giveaway_group.command(name="reroll", description="🎉 Перерозыгрыш завершённого розыгрыша")
    @app_commands.describe(giveaway_id="ID розыгрыша (из базы)")
    @app_commands.default_permissions(administrator=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, giveaway_id: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Ты не админ, иди нахуй!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            winners = await self.manager.reroll(giveaway_id)
        except ValueError as err:
            await interaction.followup.send(embed=Embed.error(description=str(err)))
            return

        if not winners:
            await interaction.followup.send(embed=Embed.warning(description="Победителей выбрать не удалось."))
            return

        description = "\n".join(f"🎉 {member.mention}" for member in winners)
        await interaction.followup.send(
            embed=Embed.success(
                title="✨ Перерозыгрыш завершён!",
                description=description,
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))

