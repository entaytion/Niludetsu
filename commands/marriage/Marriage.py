import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, Time, send, defer, AchievementsManager, EconomyManager, MarriageManager
from Niludetsu.locale import _, DEFAULT_LOCALE

from Niludetsu.database import database

from typing import Optional

_time = Time()
M = DEFAULT_LOCALE.get("marriage", {})

class MarriageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.marriages = MarriageManager(self.db)
        self.economy = EconomyManager(self.db)
        self.achievements = AchievementsManager()

    @commands.hybrid_command(name="marry", description="Сделать предложение пользователю")
    @app_commands.describe(member="Пользователь, которому вы хотите сделать предложение")
    async def marry(self, ctx: commands.Context, member: discord.Member) -> None:
        await defer(ctx, ephemeral=False, thinking=True)
        t = _(ctx=ctx)

        proposer_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        if member.bot:
            await send(ctx, f"{Emojis.ERROR} {t('marriage', 'propose_bot_error')}", ephemeral=True)
            return
        if proposer_id == target_id:
            await send(ctx, f"{Emojis.ERROR} {t('marriage', 'propose_self_error')}", ephemeral=True)
            return

        await self.db.ensure_record("users", user_id=proposer_id, guild_id=guild_id)
        await self.db.ensure_record("users", user_id=target_id, guild_id=guild_id)

        for uid in (proposer_id, target_id):
            marriage = await self.marriages.fetch_marriage(guild_id, uid)
            if marriage:
                if uid == proposer_id:
                    await send(ctx, f"{Emojis.ERROR} {t('marriage', 'propose_married_error')}", ephemeral=True)
                else:
                    await send(ctx, f"{Emojis.ERROR} {t('marriage', 'propose_target_married')}", ephemeral=True)
                return

        view = MarriageProposalView(member, t)
        embed = Embed(
            title=t("marriage", "propose_title"),
            description=t("marriage", "propose_desc", author=ctx.author.mention, target=member.mention),
            color=Colors.PRIMARY,
        )

        message = await send(ctx, member.mention, embed=embed, view=view)
        if message is None:
            return
        await view.wait()

        if view.value is None:
            await message.edit(content=t("marriage", "propose_timeout"), view=None)
            return
        if not view.value:
            await message.edit(content=t("marriage", "propose_rejected", target=member.mention), view=None)
            return

        marriage = await self.marriages.create_marriage(guild_id, proposer_id, target_id)
        
        await self.marriages.sync_spousal_flags(guild_id, marriage, enabled=True)

        success = Embed(
            title=t("marriage", "marry_success_title"),
            description=t("marriage", "marry_success_desc", author=ctx.author.mention, target=member.mention),
            color=Colors.SUCCESS,
        )
        success.add_field(name=t("marriage", "marry_date"), value=_time.format_datetime(marriage["married_at"]))
        await message.edit(content=None, embed=success, view=None)
        
        await self.achievements.unlock(guild_id, proposer_id, "first_marriage", channel=ctx.channel)
        await self.achievements.unlock(guild_id, target_id, "first_marriage", channel=ctx.channel)

    @commands.hybrid_command(name="divorce", description="Развестись с текущим партнером")
    async def divorce(self, ctx: commands.Context) -> None:
        await defer(ctx, ephemeral=True, thinking=True)
        t = _(ctx=ctx)

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        marriage = await self.marriages.fetch_marriage(guild_id, user_id)
        if not marriage:
            await send(ctx, embed=Embed.error(description=f"{Emojis.ERROR} {t('marriage', 'divorce_not_married')}"), ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == user_id else marriage["partner_b_id"]

        balance = await self.marriages.unify_spousal_balance(guild_id, marriage)
        share = balance // 2

        for uid in (user_id, partner_id):
            if share > 0:
                await self.economy.add_money(uid, guild_id, share, share_spousal=False)

        await self.marriages.clear_spousal_balance(guild_id, marriage)
        await self.marriages.sync_spousal_flags(guild_id, marriage, enabled=False)
        
        await self.db.close_marriage(marriage["id"], status="divorced")

        embed = Embed(
            title=t("marriage", "divorce_title"),
            description=t("marriage", "divorce_desc", balance=f"{balance:,} {Emojis.MONEY}", share=f"{share:,} {Emojis.MONEY}"),
            color=Colors.ERROR,
        )

        kids = await self.marriages.fetch_children(marriage["id"])
        if kids:
            embed.add_field(
                name=t("marriage", "divorce_children"),
                value=t("marriage", "divorce_children_desc", count=len(kids)),
                inline=False,
            )

        await send(ctx, embed=embed, ephemeral=False)

    @commands.hybrid_command(name="relations", description="Посмотреть информацию о браке")
    @app_commands.describe(member="Чьи отношения посмотреть")
    async def relations(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        await defer(ctx, ephemeral=True, thinking=True)
        t = _(ctx=ctx)

        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        marriage = await self.marriages.fetch_marriage(guild_id, str(target.id))
        if not marriage:
            text = t("marriage", "relations_not_married_self") if target == ctx.author else t("marriage", "relations_not_married_other", target=target.display_name)
            await send(ctx, f"{Emojis.ERROR} {text}", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == str(target.id) else marriage["partner_b_id"]
        partner = ctx.guild.get_member(int(partner_id))
        if not partner:
            await send(ctx, f"{Emojis.ERROR} {t('marriage', 'relations_partner_not_found')}", ephemeral=True)
            return

        married_at = _time.ensure_datetime(marriage["married_at"])
        duration = _time.diff(married_at)
        together = t("marriage", "together_format", days=duration.days, hours=duration.hours, minutes=duration.minutes)

        embed = Embed(
            title=t("marriage", "relations_title"),
            description=t("marriage", "relations_desc", user=target.display_name, partner=partner.display_name, together=together),
            color=Colors.PRIMARY,
        )
        embed.add_field(
            name=t("marriage", "marry_date"),
            value=_time.format_datetime(married_at),
            inline=True,
        )
        family_balance = await self.marriages.unify_spousal_balance(guild_id, marriage)
        embed.add_field(
            name=t("marriage", "relations_balance"),
            value=f"{family_balance:,} {Emojis.MONEY}",
            inline=True,
        )
        children = await self.marriages.fetch_children(marriage["id"]) or []

        mentions = []
        for row in children:
            child = ctx.guild.get_member(int(row["user_id"]))
            if child:
                mentions.append(child.mention)
        if mentions:
            embed.add_field(
                name=t("marriage", "relations_children", count=len(mentions)),
                value=", ".join(mentions),
                inline=False,
            )
        embed.set_thumbnail(url=partner.display_avatar.url)
        await send(ctx, embed=embed, ephemeral=False)

class MarriageProposalView(discord.ui.View):
    def __init__(self, target: discord.Member, t):
        super().__init__(timeout=60)
        self.target = target
        self.value: Optional[bool] = None
        self.t = t

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(f"{Emojis.ERROR} {self.t('marriage', 'propose_not_for_you')}", ephemeral=True)
            return False
        return True

    @discord.ui.button(label=M.get("button_accept", "Согласиться"), style=discord.ButtonStyle.success, emoji="💍")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label=M.get("button_decline", "Отказаться"), style=discord.ButtonStyle.danger, emoji="💔")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(MarriageCog(bot))
