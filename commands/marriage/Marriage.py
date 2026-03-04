import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, Time, send, defer
from Niludetsu.achievements.manager import AchievementsManager
from Niludetsu.database.supabase_database import database
from Niludetsu.economy.manager import EconomyManager
from Niludetsu.marriage.marriage_manager import MarriageManager
from typing import Optional

_time = Time()

class MarriageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.marriages = MarriageManager(self.db)
        self.economy = EconomyManager(self.db)
        self.achievements = AchievementsManager()

    @commands.hybrid_command(name="marry", description="💍 Сделать предложение пользователю")
    @app_commands.describe(member="Пользователь, которому вы хотите сделать предложение")
    async def marry(self, ctx: commands.Context, member: discord.Member) -> None:
        await defer(ctx, ephemeral=False, thinking=True)

        proposer_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        target_id = str(member.id)

        if member.bot:
            await send(ctx, f"{Emojis.ERROR} Нельзя жениться на боте!", ephemeral=True)
            return
        if proposer_id == target_id:
            await send(ctx, f"{Emojis.ERROR} Сам на себе женишься? Жизнь — не Dark Souls!", ephemeral=True)
            return

        await self.db.ensure_user(proposer_id, guild_id)
        await self.db.ensure_user(target_id, guild_id)

        for uid in (proposer_id, target_id):
            marriage = await self.marriages.fetch_marriage(guild_id, uid)
            if marriage:
                if uid == proposer_id:
                    await send(ctx, f"{Emojis.ERROR} Вы уже состоите в браке!", ephemeral=True)
                else:
                    await send(ctx, f"{Emojis.ERROR} Этот пользователь уже состоит в браке!", ephemeral=True)
                return

        view = MarriageProposalView(member)
        embed = Embed(
            title="💝 Предложение руки и сердца",
            description=f"{ctx.author.mention} делает предложение {member.mention}.\n"
                        "У тебя есть **60 секунд** на ответ.",
            color=Colors.PRIMARY,
        )

        message = await send(ctx, member.mention, embed=embed, view=view)
        if message is None:
            return
        await view.wait()

        if view.value is None:
            await message.edit(content="⏱️ Время истекло.", view=None)
            return
        if not view.value:
            await message.edit(content=f"💔 {member.mention} отказался.", view=None)
            return

        marriage = await self.marriages.create_marriage(guild_id, proposer_id, target_id)
        await self.marriages.sync_spousal_flags(guild_id, marriage, enabled=True)

        await self.db.update_record(
            "user_economy",
            {"user_id": proposer_id, "guild_id": guild_id},
            {"spousal_enabled": True},
        )
        await self.db.update_record(
            "user_economy",
            {"user_id": target_id, "guild_id": guild_id},
            {"spousal_enabled": True},
        )

        success = Embed(
            title="💞 Поздравляем!",
            description=f"{ctx.author.mention} и {member.mention} теперь в браке.",
            color=Colors.SUCCESS,
        )
        success.add_field(name="📅 Дата свадьбы", value=_time.format_datetime(marriage["married_at"]))
        await message.edit(content=None, embed=success, view=None)
        await self.achievements.unlock(guild_id, proposer_id, "first_marriage", channel=ctx.channel)
        await self.achievements.unlock(guild_id, target_id, "first_marriage", channel=ctx.channel)

    @commands.hybrid_command(name="divorce", description="💔 Развестись с текущим партнером")
    async def divorce(self, ctx: commands.Context) -> None:
        await defer(ctx, ephemeral=True, thinking=True)

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        marriage = await self.marriages.fetch_marriage(guild_id, user_id)
        if not marriage:
            await send(ctx, embed=Embed.error(description=f"{Emojis.ERROR} Вы ещё не в браке!"), ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == user_id else marriage["partner_b_id"]

        balance = await self.marriages.unify_spousal_balance(guild_id, marriage)
        share = balance // 2

        for uid in (user_id, partner_id):
            await self.economy.add_money(uid, guild_id, share, share_spousal=False)

        await self.marriages.clear_spousal_balance(guild_id, marriage)
        await self.marriages.sync_spousal_flags(guild_id, marriage, enabled=False)
        await self.marriages.finish_marriage(marriage["id"], status="divorced")

        embed = Embed(
            title="💔 Развод оформлен",
            description=(
                f"Семейный счёт **{balance:,} {Emojis.MONEY}** разделён поровну — "
                f"по **{share:,} {Emojis.MONEY}** каждому."
            ),
            color=Colors.ERROR,
        )

        kids = await self.marriages.children(marriage["id"])
        if kids:
            embed.add_field(
                name="👶 Дети",
                value=f"{len(kids)} ребёнок(ов) были освобождены из семьи.",
                inline=False,
            )

        await send(ctx, embed=embed, ephemeral=False)

    @commands.hybrid_command(name="relations", description="🏡 Посмотреть информацию о браке")
    @app_commands.describe(member="Чьи отношения посмотреть")
    async def relations(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        await defer(ctx, ephemeral=True, thinking=True)

        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        marriage = await self.marriages.fetch_marriage(guild_id, str(target.id))
        if not marriage:
            text = "Вы не состоите в браке!" if target == ctx.author else f"{target.display_name} пока свободен(а)."
            await send(ctx, f"{Emojis.ERROR} {text}", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == str(target.id) else marriage["partner_b_id"]
        partner = ctx.guild.get_member(int(partner_id))
        if not partner:
            await send(ctx, f"{Emojis.ERROR} Партнёр не найден на сервере!", ephemeral=True)
            return

        married_at = _time.ensure_datetime(marriage["married_at"])
        duration = _time.diff(married_at)
        together = f"{duration.days} дн. {duration.hours} ч. {duration.minutes} мин."

        embed = Embed(
            title="💝 Информация о браке",
            description=(
                f"Пара: **{target.display_name} × {partner.display_name}**\n"
                f"Вместе: **{together}**"
            ),
            color=Colors.PRIMARY,
        )
        embed.add_field(
            name="📅 Дата свадьбы",
            value=_time.format_datetime(married_at),
            inline=True,
        )
        family_balance = await self.marriages.unify_spousal_balance(guild_id, marriage)
        embed.add_field(
            name="💰 Семейный счёт",
            value=f"{family_balance:,} {Emojis.MONEY}",
            inline=True,
        )
        children = await self.marriages.children(marriage["id"]) or []

        mentions = []
        for row in children:
            child = ctx.guild.get_member(int(row["user_id"]))
            if child:
                mentions.append(child.mention)
        if mentions:
            embed.add_field(
                name=f"👨‍👩‍👧 Дети ({len(mentions)})",
                value=", ".join(mentions),
                inline=False,
            )
        embed.set_thumbnail(url=partner.display_avatar.url)
        await send(ctx, embed=embed, ephemeral=False)

class MarriageProposalView(discord.ui.View):
    def __init__(self, target: discord.Member):
        super().__init__(timeout=60)
        self.target = target
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message(f"{Emojis.ERROR} Это предложение не для тебя!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Согласиться", style=discord.ButtonStyle.success, emoji="💍")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Отказаться", style=discord.ButtonStyle.danger, emoji="💔")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(MarriageCog(bot))

