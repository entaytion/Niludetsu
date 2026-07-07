import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, MarriageManager, AdoptionManager
from Niludetsu.locale import _, DEFAULT_LOCALE

from typing import Optional

M = DEFAULT_LOCALE.get("marriage", {})

class AdoptionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.adoption = AdoptionManager()
        self.marriages = MarriageManager()

    @commands.hybrid_command(name="adopt", description="Усыновить пользователя")
    @app_commands.describe(member="👤 Кого хотите усыновить")
    async def adopt(self, ctx: commands.Context, member: discord.Member) -> None:
        t = _(ctx=ctx)
        guild_id = str(ctx.guild.id)
        parent_id = str(ctx.author.id)
        target_id = str(member.id)

        if member.bot or target_id == parent_id:
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'adopt_bot_self_error')}", ephemeral=True)
            return

        marriage = await self.marriages.fetch_marriage(guild_id, parent_id)
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'adopt_no_marriage')}", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == parent_id else marriage["partner_b_id"]
        if target_id == partner_id:
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'adopt_partner_is_parent')}", ephemeral=True)
            return

        proposal = AdoptionView(member, t)
        embed = Embed(
            title=t("marriage", "adopt_title"),
            description=t("marriage", "adopt_desc", author=ctx.author.mention, partner=ctx.guild.get_member(int(partner_id)).mention, target=member.mention),
            color=Colors.PRIMARY,
        )
        message = await ctx.reply(member.mention, embed=embed, view=proposal, mention_author=False)
        await proposal.wait()

        if proposal.value is None:
            await message.edit(content=t("marriage", "adopt_timeout"), view=None)
            return
        if not proposal.value:
            await message.edit(content=t("marriage", "adopt_rejected", target=member.mention), view=None)
            return

        try:
            await self.adoption.add_child(guild_id, parent_id, target_id)
        except RuntimeError as exc:
            mapping = {
                "no_marriage": t("marriage", "adopt_error_no_marriage"),
                "already_child": t("marriage", "adopt_error_already_child"),
            }
            await ctx.reply(mapping.get(str(exc), t("marriage", "adopt_error_unknown")), ephemeral=True)
            return

        success = Embed(
            title=t("marriage", "adopt_success_title"),
            description=t("marriage", "adopt_success_desc", target=member.mention),
            color=Colors.SUCCESS,
        )
        await message.edit(content=None, embed=success, view=None)

    @commands.hybrid_command(name="release", description="Отпустить усыновлённого пользователя")
    @app_commands.describe(member="👤 Кого отпустить из семьи")
    async def release(self, ctx: commands.Context, member: discord.Member) -> None:
        t = _(ctx=ctx)
        guild_id = str(ctx.guild.id)
        parent_id = str(ctx.author.id)

        marriage = await self.marriages.fetch_marriage(guild_id, parent_id)
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'release_not_married')}", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == parent_id else marriage["partner_b_id"]
        target_id = str(member.id)

        children = await self.marriages.children(marriage["id"])
        if not any(str(child["user_id"]) == target_id for child in children):
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'release_not_family')}", ephemeral=True)
            return

        await self.adoption.remove_child(guild_id, parent_id, target_id)

        embed = Embed(
            title=t("marriage", "release_title"),
            description=t("marriage", "release_desc", target=member.mention, author=ctx.author.mention, partner=ctx.guild.get_member(int(partner_id)).mention),
            color=Colors.WARNING,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="children", description="Посмотреть усыновлённых")
    @app_commands.describe(member="👥 Чью семью показать")
    async def children(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        t = _(ctx=ctx)
        target = member or ctx.author
        guild_id = str(ctx.guild.id)

        marriage = await self.marriages.fetch_marriage(guild_id, str(target.id))
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} {t('marriage', 'children_no_marriage')}", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == str(target.id) else marriage["partner_b_id"]
        partner = ctx.guild.get_member(int(partner_id))
        kids = await self.marriages.children(marriage["id"])

        if not kids:
            await ctx.reply(t("marriage", "children_empty"), ephemeral=True)
            return

        mentions = []
        for row in kids:
            child = ctx.guild.get_member(int(row["user_id"]))
            if child:
                mentions.append(child.mention)

        embed = Embed(
            title=t("marriage", "children_title", user_name=target.display_name),
            description=t("marriage", "children_desc", partner=partner.mention if partner else "не найден", count=len(mentions)),
            color=Colors.PRIMARY,
        )
        embed.add_field(name=t("marriage", "children_label"), value="\n".join(mentions), inline=False)
        await ctx.reply(embed=embed)

class AdoptionView(discord.ui.View):
    def __init__(self, target: discord.Member, t):
        super().__init__(timeout=60)
        self.target = target
        self.value: Optional[bool] = None
        self.t = t

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(self.t("marriage", "propose_not_for_you"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label=M.get("button_accept", "Согласиться"), style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label=M.get("button_decline", "Отказаться"), style=discord.ButtonStyle.danger, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(AdoptionCog(bot))
