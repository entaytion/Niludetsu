import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis, MarriageManager, AdoptionManager

from typing import Optional

class AdoptionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.adoption = AdoptionManager()
        self.marriages = MarriageManager()

    @commands.hybrid_command(name="adopt", description="Усыновить пользователя")
    @app_commands.describe(member="👤 Кого хотите усыновить")
    async def adopt(self, ctx: commands.Context, member: discord.Member) -> None:
        guild_id = str(ctx.guild.id)
        parent_id = str(ctx.author.id)
        target_id = str(member.id)

        if member.bot or target_id == parent_id:
            await ctx.reply(f"{Emojis.ERROR} Нельзя усыновить себя или бота!", ephemeral=True)
            return

        marriage = await self.marriages.fetch_marriage(guild_id, parent_id)
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} Сначала найдите вторую половинку!", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == parent_id else marriage["partner_b_id"]
        if target_id == partner_id:
            await ctx.reply(f"{Emojis.ERROR} Ваш партнёр уже полноценный родитель.", ephemeral=True)
            return

        proposal = AdoptionView(member)
        embed = Embed(
            title="Предложение усыновления",
            description=f"Семья {ctx.author.mention} и {ctx.guild.get_member(int(partner_id)).mention} "
                        f"хочет принять {member.mention}. Согласен?",
            color=Colors.PRIMARY,
        )
        message = await ctx.reply(member.mention, embed=embed, view=proposal, mention_author=False)
        await proposal.wait()

        if proposal.value is None:
            await message.edit(content="⏱️ Время вышло.", view=None)
            return
        if not proposal.value:
            await message.edit(content=f"❌ {member.mention} отказался.", view=None)
            return

        try:
            await self.adoption.add_child(guild_id, parent_id, target_id)
        except RuntimeError as exc:
            mapping = {
                "no_marriage": "❌ Сначала женитесь!",
                "already_child": "❌ Этот пользователь уже состоит в другой семье.",
            }
            await ctx.reply(mapping.get(str(exc), "❌ Что-то пошло не так."), ephemeral=True)
            return

        success = Embed(
            title="Поздравляем!",
            description=f"{member.mention} теперь часть семьи!",
            color=Colors.SUCCESS,
        )
        await message.edit(content=None, embed=success, view=None)

    @commands.hybrid_command(name="release", description="Отпустить усыновлённого пользователя")
    @app_commands.describe(member="👤 Кого отпустить из семьи")
    async def release(self, ctx: commands.Context, member: discord.Member) -> None:
        guild_id = str(ctx.guild.id)
        parent_id = str(ctx.author.id)

        marriage = await self.marriages.fetch_marriage(guild_id, parent_id)
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} Вы не состоите в браке!", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == parent_id else marriage["partner_b_id"]
        target_id = str(member.id)

        children = await self.marriages.children(marriage["id"])
        if not any(str(child["user_id"]) == target_id for child in children):
            await ctx.reply(f"{Emojis.ERROR} Этот пользователь не часть вашей семьи.", ephemeral=True)
            return

        await self.adoption.remove_child(guild_id, parent_id, target_id)

        embed = Embed(
            title="Семья распрощалась",
            description=f"{member.mention} больше не числится в семье {ctx.author.mention} и {ctx.guild.get_member(int(partner_id)).mention}.",
            color=Colors.WARNING,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="children", description="Посмотреть усыновлённых")
    @app_commands.describe(member="👥 Чью семью показать")
    async def children(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        target = member or ctx.author
        guild_id = str(ctx.guild.id)

        marriage = await self.marriages.fetch_marriage(guild_id, str(target.id))
        if not marriage:
            await ctx.reply(f"{Emojis.ERROR} Эта пара пока без брака.", ephemeral=True)
            return

        partner_id = marriage["partner_a_id"] if marriage["partner_b_id"] == str(target.id) else marriage["partner_b_id"]
        partner = ctx.guild.get_member(int(partner_id))
        kids = await self.marriages.children(marriage["id"])

        if not kids:
            await ctx.reply("У этой семьи пока нет усыновлённых.", ephemeral=True)
            return

        mentions = []
        for row in kids:
            child = ctx.guild.get_member(int(row["user_id"]))
            if child:
                mentions.append(child.mention)

        embed = Embed(
            title=f"Семья {target.display_name}",
            description=f"Партнёр: {partner.mention if partner else 'не найден'}\n"
                        f"Усыновлённых: **{len(mentions)}**",
            color=Colors.PRIMARY,
        )
        embed.add_field(name="👶 Дети", value="\n".join(mentions), inline=False)
        await ctx.reply(embed=embed)

class AdoptionView(discord.ui.View):
    def __init__(self, target: discord.Member):
        super().__init__(timeout=60)
        self.target = target
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("Это решение не для тебя!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Согласиться", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Отказаться", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(AdoptionCog(bot))

