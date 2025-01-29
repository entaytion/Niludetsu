import discord
from discord.ext import commands
from discord import Interaction, ButtonStyle
from discord.ui import Button, View
from Niludetsu.utils.database import DB_PATH
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
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
                title=f"{EMOJIS['LEADERBOARD']} Рейтинг по {rep_type} репутации",
                description=f"{EMOJIS['INFO']} Показаны топ-10 пользователей",
                color="BLUE",
                footer={
                    "text": f"Вы на {next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), 'не найдено')}-м месте.",
                    "icon_url": interaction.user.avatar.url
                }
            )
            
            for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
                member_mention = await self.cog.get_member_mention(member_id, interaction.guild.id)
                rep = user_data.get('reputation', 0)
                emoji = f"{EMOJIS['UP']}" if rep >= 0 else f"{EMOJIS['DOWN']}"
                embed.add_field(
                    name=f"{EMOJIS['RANK']} #{i}. {member_mention}",
                    value=f"{EMOJIS['REPUTATION']} Репутация: **`{rep}`** {emoji}",
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

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                if category == "level":
                    cursor.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC")
                    sorted_users = [(int(row[0]), {'level': row[1], 'xp': row[2]}) for row in cursor.fetchall()]
                    value_title = f"{EMOJIS['LEVEL']} уровню"
                elif category == "money":
                    cursor.execute("SELECT user_id, balance, deposit FROM users ORDER BY (balance + deposit) DESC")
                    sorted_users = [(int(row[0]), {'balance': row[1], 'deposit': row[2]}) for row in cursor.fetchall()]
                    value_title = f"{EMOJIS['MONEY']} деньгам"
                elif category == "reputation":
                    view = ReputationView(self, None, interaction)
                    cursor.execute("SELECT user_id, reputation FROM users ORDER BY reputation DESC")
                    sorted_users = [(int(row[0]), {'reputation': row[1]}) for row in cursor.fetchall()]
                    value_title = f"{EMOJIS['REPUTATION']} репутации"
                else:
                    await interaction.followup.send(
                        embed=create_embed(
                            title=f"{EMOJIS['ERROR']} Ошибка",
                            description="Категория не найдена.",
                            color="RED"
                        )
                    )
                    return

            # Фильтруем пользователей, которые есть на сервере
            guild_member_ids = [member.id for member in interaction.guild.members]
            sorted_users = [(user_id, data) for user_id, data in sorted_users if user_id in guild_member_ids]

            if not sorted_users:
                await interaction.followup.send(
                    embed=create_embed(
                        title=f"{EMOJIS['INFO']} Информация",
                        description="Нет данных для отображения.",
                        color="BLUE"
                    )
                )
                return

            embed = create_embed(
                title=f"{EMOJIS['LEADERBOARD']} Рейтинг по {value_title}",
                description=f"{EMOJIS['INFO']} Показаны топ-10 пользователей",
                color="BLUE"
            )

            # Добавляем позицию пользователя в footer
            user_position = next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), None)
            if user_position:
                embed.set_footer(text=f"Вы на {user_position}-м месте", icon_url=interaction.user.avatar.url)
            else:
                embed.set_footer(text="Вы пока не участвуете в рейтинге", icon_url=interaction.user.avatar.url)

            for i, (member_id, user_data) in enumerate(sorted_users[:10], start=1):
                member_mention = await self.get_member_mention(member_id, interaction.guild.id)
                
                if category == "money":
                    balance = user_data.get('balance', 0)
                    deposit = user_data.get('deposit', 0)
                    total = balance + deposit
                    embed.add_field(
                        name=f"{EMOJIS['RANK']} #{i}. {member_mention}",
                        value=f"{EMOJIS['CASH']} Наличные: **`{balance:,}`** {EMOJIS['MONEY']}\n"
                              f"{EMOJIS['BANK']} Банк: **`{deposit:,}`** {EMOJIS['MONEY']}\n"
                              f"{EMOJIS['TOTAL']} Всего: **`{total:,}`** {EMOJIS['MONEY']}",
                        inline=False
                    )
                elif category == "level":
                    level = user_data.get('level', 0)
                    xp = user_data.get('xp', 0)
                    embed.add_field(
                        name=f"{EMOJIS['RANK']} #{i}. {member_mention}",
                        value=f"{EMOJIS['LEVEL']} Уровень: **`{level}`**\n"
                              f"{EMOJIS['XP']} XP: **`{xp:,}`**",
                        inline=False
                    )
                elif category == "reputation":
                    rep = user_data.get('reputation', 0)
                    emoji = f"{EMOJIS['UP']}" if rep >= 0 else f"{EMOJIS['DOWN']}"
                    embed.add_field(
                        name=f"{EMOJIS['RANK']} #{i}. {member_mention}",
                        value=f"{EMOJIS['REPUTATION']} Репутация: **`{rep}`** {emoji}",
                        inline=False
                    )

            if category == "reputation":
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in leaderboard command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Произошла ошибка при получении данных рейтинга.",
                    color="RED"
                )
            )

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
