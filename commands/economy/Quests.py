import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import QuestManager, Embed, Emojis, Colors

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = QuestManager()

    @commands.hybrid_command(name="quests", aliases=("квесты", "q"), description="Посмотреть активные квесты")
    @app_commands.describe(page="Страница (1 - ежедневные, 2 - еженедельные)")
    async def quests(self, ctx, page: int = 1):
        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        quests = await self.manager.get_user_quests(uid, gid, page)
        
        title = "Ежедневные квесты" if page == 1 else "Еженедельные квесты"
        embed = Embed.info(title=f"{title}")
        
        if not quests:
            embed.description = "Квестов пока нет, заходите позже!"
        else:
            for p in quests:
                q = p.quest
                status = "✅" if p.completed else "⏳"
                if p.reward_claimed: status = "💰"
                
                bar = f"[{'🟩' * int(p.progress/q['goal']*10)} {'⬛' * (10-int(p.progress/q['goal']*10))}]"
                embed.add_field(
                    name=f"{status} {q['name']}",
                    value=f"{q['description']}\n{bar} **{p.progress}/{q['goal']}**\nНаграда: **{q['reward']:,}** {Emojis.MONEY}",
                    inline=False
                )

        view = QuestActionsView(self.manager, uid, gid, quests) if quests else None
        await ctx.reply(embed=embed, view=view)

class QuestActionsView(discord.ui.View):
    def __init__(self, manager, uid, gid, quests):
        super().__init__(timeout=120)
        self.manager, self.uid, self.gid = manager, uid, gid
        
        claimable = [p for p in quests if p.completed and not p.reward_claimed]
        if claimable:
            btn = discord.ui.Button(label="Забрать награды", style=discord.ButtonStyle.success, emoji="💰")
            btn.callback = self._claim_all
            self.add_item(btn)

    async def _claim_all(self, i):
        if str(i.user.id) != self.uid: return
        
        quests = await self.manager.get_claimable_quests(self.uid, self.gid)
        if not quests: return await i.response.send_message("Нет наград для получения!", ephemeral=True)
        
        msgs = []
        for p in quests:
            ok, msg = await self.manager.claim_reward(self.uid, self.gid, p.quest["key"])
            if ok: msgs.append(msg)
            
        await i.response.send_message("\n".join(msgs) if msgs else "Ошибочка вышла.", ephemeral=True)
        self.stop()

async def setup(bot): await bot.add_cog(Quests(bot))
