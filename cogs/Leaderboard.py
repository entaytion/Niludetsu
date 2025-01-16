import discord
from discord.ext import commands
from discord import Interaction
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS, EMOJIS
from typing import Literal

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="leaderboard", description="Показать топ пользователей")
    @discord.app_commands.describe(category="Категория для сортировки")
    async def leaderboard(self, interaction: Interaction, category: Literal['level', 'money']):
        await interaction.response.defer()

        bot_id = '1264591814208262154'
        bot_balance = get_user(self.bot, bot_id)

        # Проверка, есть ли данные о боте
        if bot_balance is None:
            await interaction.followup.send("Не удалось получить баланс для бота. Попробуйте позже.", ephemeral=True)
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
        else:
            await interaction.followup.send("Категория не найдена.", ephemeral=True)
            return

        # Создаем embed с рейтингом
        embed = create_embed(
            title=f"Рейтинг по {value_title} пользователей",
            footer={
                "text": f"Вы на {next((i + 1 for i, (member_id, _) in enumerate(sorted_users) if member_id == interaction.user.id), 'не найден')}-м месте.",
                "icon_url": interaction.user.avatar.url
            }
        )

        # Если категория "money", добавляем информацию о балансе бота
        if category == "money":
            treasury_info = f"{EMOJIS['DOT']} Баланс: **`{bot_balance['balance']}`** {EMOJIS['MONEY']}"
            embed.add_field(name="Казна сервера", value=treasury_info, inline=False)

        # Добавляем топ-10 пользователей в embed
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

        await interaction.followup.send(embed=embed)

    async def get_member_mention(self, user_id, guild_id):
        guild = self.bot.get_guild(guild_id)
        member = guild.get_member(user_id)
        if member:
            return f"{member.display_name} ({member.mention})"
        else:
            return f"<@{user_id}>"

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
