import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class SettingsButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str, emoji: str):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=label,
            custom_id=custom_id,
            emoji=emoji
        )

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == "automod_settings":
            automod_cog = interaction.client.get_cog("AutoModSettings")
            if automod_cog:
                await automod_cog.automod_settings(interaction)

class SettingsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(SettingsButton("Автомодерация", "automod_settings", "🛡️"))

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="settings", aliases=["config"])
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Настройки бота"""
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройки бота",
            description="Выберите категорию настроек:",
            color="BLUE"
        )
        
        view = SettingsView()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Settings(bot)) 