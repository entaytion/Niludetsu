import discord
from Niludetsu import AchievementsManager, Embed, Emojis
from Niludetsu.locale import _, DEFAULT_LOCALE
from discord import app_commands
from discord.ext import commands

from Niludetsu.database import database

from Niludetsu.tools.Discord import resolve_member

from typing import Optional

class Profile(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.achievements = AchievementsManager()

    def format_voice_duration(self, seconds: int) -> str:
        if seconds <= 0: return DEFAULT_LOCALE.get("profile", {}).get("voice_dur_minutes", "{count}м").format(count=0)
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        days = hours // 24
        hours = hours % 24
        
        day_key = DEFAULT_LOCALE.get("profile", {}).get("voice_dur_days", "{count}д")
        hour_key = DEFAULT_LOCALE.get("profile", {}).get("voice_dur_hours", "{count}ч")
        min_key = DEFAULT_LOCALE.get("profile", {}).get("voice_dur_minutes", "{count}м")
        parts = []
        if days > 0: parts.append(day_key.format(count=days))
        if hours > 0: parts.append(hour_key.format(count=hours))
        if minutes > 0 or not parts: parts.append(min_key.format(count=minutes))
        return " ".join(parts)

    @app_commands.command(name="profile", description="Посмотреть профиль пользователя")
    @app_commands.describe(user="👤 Пользователь (по умолчанию — вы)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        await interaction.response.defer()

        t = _(guild_id=interaction.guild_id, bot=self.bot)
        target = user or interaction.user
        gid, uid = str(interaction.guild_id), str(target.id)

        bundle = await self.db.get_user(uid, gid)
        prof, eco, stat = bundle["profile"], bundle["economy"], bundle["analytics"]
        
        marriage = bundle.get("marriage")
        partner_str = t("profile", "single")
        if marriage:
            p_id = marriage["partner_b_id"] if marriage["partner_a_id"] == uid else marriage["partner_a_id"]
            partner = await resolve_member(interaction.client, p_id, gid)
            partner_str = t("profile", "married", partner=partner.mention) if partner else t("profile", "married", partner=f"ID: {p_id}")

        ach_summary = await self.achievements.get_user_summary(gid, uid)
        ach_count = sum(1 for a in ach_summary.values() if a.get("unlocked"))

        embed = Embed.default(title=t("profile", "title", user_name=target.display_name))
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(
            name=t("profile", "field_level"),
            value=t("profile", "field_level_text", level=prof.get('level', 1), xp=f"{prof.get('experience', 0):,}", rep=prof.get('reputation', 0)),
            inline=True
        )
        embed.add_field(
            name=t("profile", "field_wallet"),
            value=t("profile", "field_wallet_text", balance=f"{eco.get('balance', 0):,}", currency=Emojis.MONEY, deposit=f"{eco.get('deposit', 0):,}"),
            inline=True
        )
        
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        
        embed.add_field(
            name=t("profile", "field_activity"),
            value=t("profile", "field_activity_text", messages=f"{stat.get('messages_total', 0):,}", voice=self.format_voice_duration(stat.get('voice_seconds', 0)), achievements=ach_count),
            inline=True
        )
        embed.add_field(
            name=t("profile", "field_family"),
            value=partner_str,
            inline=True
        )

        view = ProfileActionsView(self, target) if target.id == interaction.user.id else None
        await interaction.followup.send(embed=embed, view=view)

class ProfileActionsView(discord.ui.View):
    def __init__(self, cog: "Profile", user: discord.Member):
        super().__init__(timeout=300)
        self.cog = cog
        self.user = user

    @discord.ui.button(label=DEFAULT_LOCALE.get("profile", {}).get("profile_achievements_label", "Достижения"), emoji="🏆", style=discord.ButtonStyle.gray)
    async def achievements_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        t = _(guild_id=interaction.guild_id, bot=interaction.client)
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(embed=Embed.error(description=t("profile", "not_yours")), ephemeral=True)

        summary = await self.cog.achievements.get_user_summary(str(interaction.guild_id), str(self.user.id))
        embed = Embed.info(title=t("profile", "achievements_title", user_name=self.user.display_name))
        embed.set_thumbnail(url=self.user.display_avatar.url)

        for _, d in summary.items():
            status = "✅" if d["unlocked"] else "❌"
            embed.add_field(
                name=f"{status} {d['name']}",
                value=f"{d['icon']} {d['description']}\n{t('profile', 'achievements_reward', reward=d['reward'])}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profile(bot))
