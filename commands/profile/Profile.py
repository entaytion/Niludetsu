import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from Niludetsu.achievements.manager import AchievementsManager
from Niludetsu.database.supabase_database import database
from Niludetsu.profile.image import ProfileGenerator
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Discord import resolve_member
from typing import Optional
class Profile(commands.Cog):
    """Команды профиля"""

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.generator = ProfileGenerator()
        self.achievements = AchievementsManager()

    @app_commands.command(name="profile", description="🖼️ Посмотреть профиль пользователя")
    @app_commands.describe(user="👤 Пользователь (по умолчанию — вы)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Показывает профиль пользователя"""
        await interaction.response.defer()

        target = user or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)

        bundle = await self.db.ensure_user(user_id, guild_id)

        profile = bundle.get("profile", {})
        economy = bundle.get("economy", {})

        analytics = bundle.get("analytics", {})

        marriage = await self.db.get_active_marriage(guild_id, user_id)
        partner = None

        if marriage:
            partner_id = await self.db.get_marriage_partner(marriage, user_id)
            partner = await resolve_member(interaction.client, partner_id, guild_id)
            if isinstance(partner, discord.User):
                # We need a user object for display, resolve_member gives User or Member
                pass

        achievements_data = await self.achievements.get_user_summary(guild_id, user_id)
        achievements_count = sum(1 for ach in achievements_data.values() if ach.get("unlocked"))

        image_bytes = await self.generator.generate(
            user=target,
            profile=profile,
            economy=economy,
            analytics=analytics,
            marriage=marriage,
            partner=partner,
            achievements_count=achievements_count
        )

        if not image_bytes:
            await interaction.followup.send(
                embed=Embed.error(description="Не удалось создать изображение профиля"),
                ephemeral=True
            )
            return

        file = discord.File(BytesIO(image_bytes), filename="profile.jpg")

        view = ProfileActionsView(self, target) if target.id == interaction.user.id else None

        if view:
            await interaction.followup.send(file=file, view=view)
        else:
            await interaction.followup.send(file=file)

class ProfileActionsView(discord.ui.View):
    """View с кнопками действий профиля"""

    def __init__(self, cog: "Profile", user: discord.Member):
        super().__init__(timeout=300)
        self.cog = cog
        self.user = user

    @discord.ui.button(label="Достижения", emoji="🏆", style=discord.ButtonStyle.gray)
    async def achievements_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Показывает достижения"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                embed=Embed.error(description="Это не ваш профиль!"),
                ephemeral=True
            )
            return

        # Получаем достижения через cog
        summary = await self.cog.achievements.get_user_summary(
            str(interaction.guild_id),
            str(self.user.id)
        )

        # Создаём embed
        embed = Embed.info(title=f"🏆 Достижения {self.user.display_name}")
        embed.set_thumbnail(url=self.user.display_avatar.url)

        for ach_id, data in summary.items():
            status = "✅" if data["unlocked"] else "❌"
            unlock_time = f"\n🕒 Получено: {data['unlocked_at']}" if data["unlocked"] else ""

            embed.add_field(
                name=f"{status} {data['name']}",
                value=f"{data['icon']} {data['description']}\n💰 Награда: **{data['reward']}**{unlock_time}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profile(bot))

