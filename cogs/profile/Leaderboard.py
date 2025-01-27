import discord
from discord.ext import commands
from discord import Interaction, ButtonStyle
from discord.ui import Button, View
from utils import create_embed, get_user, save_user, EMOJIS, DB_PATH
from typing import Literal
import sqlite3

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
        try:
            for item in self.children:
                item.disabled = True
            await self.original_interaction.edit_original_response(view=self)
        except Exception as e:
            print(f"Error in on_timeout: {e}")

    async def show_reputation_embed(self, interaction: Interaction, sorted_users, rep_type):
        try:
            embed = create_embed(
                title=f"Рейтинг по {rep_type} репутации",
                footer={
                    "text": f"Вы на {next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), 'не найдено')}-м месте.",
                    "icon_url": interaction.user.avatar.url
                }
            )
            
            for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
                member_mention = await self.cog.get_member_mention(member_id, interaction.guild.id)
                rep = user_data.get('reputation', 0)
                emoji = "⬆️" if rep >= 0 else "⬇️"
                embed.add_field(
                    name=f"{i}. {member_mention}",
                    value=f"Репутация: **`{rep}`** {emoji}",
                    inline=False
                )
                
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Error in show_reputation_embed: {e}")

    @discord.ui.button(label="Топ положительной репутации", style=ButtonStyle.green)
    async def positive_button(self, interaction: Interaction, button: Button):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, reputation FROM users ORDER BY reputation DESC")
                sorted_users = [(int(row[0]), {'reputation': row[1]}) for row in cursor.fetchall()]
            await self.show_reputation_embed(interaction, sorted_users, "положительной")
        except Exception as e:
            print(f"Error in positive_button: {e}")
        
    @discord.ui.button(label="Топ отрицательной репутации", style=ButtonStyle.red)
    async def negative_button(self, interaction: Interaction, button: Button):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, reputation FROM users ORDER BY reputation ASC")
                sorted_users = [(int(row[0]), {'reputation': row[1]}) for row in cursor.fetchall()]
            await self.show_reputation_embed(interaction, sorted_users, "отрицательной")
        except Exception as e:
            print(f"Error in negative_button: {e}")

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="leaderboard", description="Показать топ пользователей")
    @discord.app_commands.describe(category="Категория для сортировки")
    async def leaderboard(self, interaction: Interaction, category: Literal['level', 'money', 'reputation']):
        try:
            await interaction.response.defer()

            bot_id = '1264591814208262154'
            bot_balance = get_user(self.bot, bot_id)

            if bot_balance is None:
                await interaction.followup.send("Не удалось получить баланс бота. Попробуйте позже.")
                return

            users = {}
            for member in interaction.guild.members:
                if str(member.id) == bot_id:
                    continue
                user_data = get_user(self.bot, str(member.id))
                if user_data:
                    users[member.id] = user_data

            if category == "level":
                sorted_users = sorted(users.items(), key=lambda x: (x[1].get('level', 0), x[1].get('xp', 0)), reverse=True)
                value_title = "уровню"
            elif category == "money":
                sorted_users = sorted(users.items(), key=lambda x: (x[1].get('balance', 0) + x[1].get('deposit', 0)), reverse=True)
                value_title = "деньгам"
            elif category == "reputation":
                view = ReputationView(self, users, interaction)
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT user_id, reputation FROM users ORDER BY reputation DESC")
                    sorted_users = [(int(row[0]), {'reputation': row[1]}) for row in cursor.fetchall()]
                value_title = "репутации"
            else:
                await interaction.followup.send("Категория не найдена.")
                return

            embed = create_embed(
                title=f"Рейтинг по {value_title} пользователей",
                footer={
                    "text": f"Вы на {next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), 'не найдено')}-м месте.",
                    "icon_url": interaction.user.avatar.url
                }
            )

            if category == "money":
                treasury_info = f"{EMOJIS['DOT']} Баланс: **`{bot_balance['balance']}`** {EMOJIS['MONEY']}"
                embed.add_field(name="Казна сервера", value=treasury_info, inline=False)

            for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
                member_mention = await self.get_member_mention(member_id, interaction.guild.id)
                if category == "money":
                    total_amount = user_data['balance'] + user_data['deposit']
                    embed.add_field(
                        name=f"{i}. {member_mention}",
                        value=f"Наличные: **`{user_data['balance']}`** {EMOJIS['MONEY']} | Банк: **`{user_data['deposit']}`** {EMOJIS['MONEY']} | Всего: **`{total_amount}`** {EMOJIS['MONEY']}",
                        inline=False
                    )
                elif category == "level":
                    embed.add_field(
                        name=f"{i}. {member_mention}",
                        value=f"Уровень: **`{user_data['level']}`** | XP: **`{user_data['xp']}`**",
                        inline=False
                    )
                elif category == "reputation":
                    rep = user_data.get('reputation', 0)
                    emoji = "⬆️" if rep >= 0 else "⬇️"
                    embed.add_field(
                        name=f"{i}. {member_mention}",
                        value=f"Репутация: **`{rep}`** {emoji}",
                        inline=False
                    )

            if category == "reputation":
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Error in leaderboard command: {e}")

    async def get_member_mention(self, user_id, guild_id):
        try:
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(user_id)
            if member:
                return f"{member.display_name} ({member.mention})"
            else:
                return f"<@{user_id}>"
        except Exception as e:
            print(f"Error in get_member_mention: {e}")
            return f"<@{user_id}>"

async def setup(bot):
    try:
        await bot.add_cog(Leaderboard(bot))
    except Exception as e:
        print(f"Error in setup: {e}")
