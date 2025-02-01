import discord
from discord.ext import commands
from discord import Interaction, ButtonStyle
from discord.ui import Button, View
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from typing import Literal

class ReputationView(View):
    def __init__(self, cog, users, interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.users = users
        self.original_interaction = interaction
        
    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("Вы не можете использовать эти кнопки!")
            return False
        return True
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.original_interaction.edit_original_response(view=self)

    async def show_reputation_embed(self, interaction: Interaction, sorted_users, rep_type):
        embed=Embed(
            title=f"{EMOJIS['LEADERBOARD']} Рейтинг по {rep_type} репутации",
            description=f"{EMOJIS['INFO']} Показаны топ-10 пользователей",
            color="BLUE",
            footer={
                "text": f"Вы на {next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), 'не найдено')}-м месте.",
                "icon_url": interaction.user.display_avatar.url
            }
        )
        
        for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
            member_name = await self.cog.get_member_mention(member_id, interaction.guild.id)
            rep = user_data.get('reputation', 0)
            emoji = f"{EMOJIS['UP']}" if rep >= 0 else f"{EMOJIS['DOWN']}"
            embed.add_field(
                name=f"#{i}. {member_name}",
                value=f"Репутация: **{rep}** {emoji}",
                inline=False
            )
            
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Топ положительной репутации", style=ButtonStyle.green)
    async def positive_button(self, interaction: Interaction, button: Button):
        result = await self.cog.db.fetch_all(
            "SELECT user_id, reputation FROM users ORDER BY reputation DESC"
        )
        if not result:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="В базе данных нет записей о репутации пользователей.",
                    color="RED"
                ),
                ephemeral=True
            )
            return
        sorted_users = [(int(row['user_id']), {'reputation': row['reputation']}) for row in result]
        await self.show_reputation_embed(interaction, sorted_users, "положительной")
        
    @discord.ui.button(label="Топ отрицательной репутации", style=ButtonStyle.red)
    async def negative_button(self, interaction: Interaction, button: Button):
        result = await self.cog.db.fetch_all(
            "SELECT user_id, reputation FROM users ORDER BY reputation ASC"
        )
        if not result:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="В базе данных нет записей о репутации пользователей.",
                    color="RED"
                ),
                ephemeral=True
            )
            return
        sorted_users = [(int(row['user_id']), {'reputation': row['reputation']}) for row in result]
        await self.show_reputation_embed(interaction, sorted_users, "отрицательной")

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="leaderboard", description="Показать топ пользователей")
    @discord.app_commands.describe(category="Категория для сортировки")
    async def leaderboard(self, interaction: Interaction, category: Literal['level', 'money', 'reputation']):
        await interaction.response.defer()

        if category == "level":
            result = await self.db.fetch_all(
                "SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC"
            )
            if not result:
                await interaction.followup.send(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="В базе данных нет записей об уровнях пользователей.",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
            sorted_users = [(int(row['user_id']), {'level': row['level'], 'xp': row['xp']}) for row in result]
            value_title = f"{EMOJIS['LEVEL']} уровню"
        elif category == "money":
            result = await self.db.fetch_all(
                "SELECT user_id, balance, deposit FROM users ORDER BY (balance + deposit) DESC"
            )
            if not result:
                await interaction.followup.send(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="В базе данных нет записей о балансе пользователей.",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
            sorted_users = [(int(row['user_id']), {'balance': row['balance'], 'deposit': row['deposit']}) for row in result]
            value_title = f"{EMOJIS['MONEY']} деньгам"
        elif category == "reputation":
            result = await self.db.fetch_all(
                "SELECT user_id, reputation FROM users ORDER BY reputation DESC"
            )
            if not result:
                await interaction.followup.send(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка",
                        description="В базе данных нет записей о репутации пользователей.",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
            sorted_users = [(int(row['user_id']), {'reputation': row['reputation']}) for row in result]
            value_title = f"{EMOJIS['REPUTATION']} репутации"
            view = ReputationView(self, sorted_users, interaction)
            await interaction.followup.send(
                embed=await self.create_leaderboard_embed(interaction, sorted_users, value_title),
                view=view
            )
            return

        await interaction.followup.send(
            embed=await self.create_leaderboard_embed(interaction, sorted_users, value_title)
        )

    async def create_leaderboard_embed(self, interaction: Interaction, sorted_users, value_title):
        embed = Embed(
            title=f"{EMOJIS['LEADERBOARD']} Топ по {value_title}",
            description=f"{EMOJIS['INFO']} Показаны топ-10 пользователей",
            color="BLUE"
        )

        user_position = next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), None)
        if user_position:
            embed.set_footer(text=f"Вы на {user_position}-м месте", icon_url=interaction.user.display_avatar.url)
        else:
            embed.set_footer(text="Вы не найдены в списке", icon_url=interaction.user.display_avatar.url)

        for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
            member_name = await self.get_member_mention(member_id, interaction.guild.id)
            
            if 'level' in user_data:
                value = f"Уровень: **{user_data['level']}** (XP: {user_data['xp']})"
            elif 'balance' in user_data:
                total = user_data['balance'] + user_data['deposit']
                value = f"Всего: **{total:,}**\n(Баланс: {user_data['balance']:,}, Депозит: {user_data['deposit']:,})"
            else:
                rep = user_data['reputation']
                emoji = f"{EMOJIS['UP']}" if rep >= 0 else f"{EMOJIS['DOWN']}"
                value = f"Репутация: **{rep}** {emoji}"

            embed.add_field(
                name=f"#{i}. {member_name}",
                value=value,
                inline=False
            )

        return embed

    async def get_member_mention(self, user_id: int, guild_id: int) -> str:
        """Получить упоминание участника"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return f"Неизвестный пользователь"
            
        member = guild.get_member(user_id)
        if member:
            return f"{member.display_name}"
        else:
            try:
                user = await self.bot.fetch_user(user_id)
                return f"{user.name}"
            except:
                return f"Пользователь #{user_id}"

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
