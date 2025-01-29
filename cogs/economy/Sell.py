import discord
from discord import Interaction
from discord.ext import commands
from Niludetsu.utils.database import get_user, save_user, get_role_by_id, get_user_roles, remove_role_from_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from typing import List

class Sell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def role_autocomplete(self, interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[int]]:
        user_id = str(interaction.user.id)
        user_roles = get_user_roles(user_id)
        choices = []
        
        for role_id in user_roles:
            role_data = get_role_by_id(role_id)
            if role_data:
                name = f"{role_data['name']} (ID: {role_id})"
                if not current or current.lower() in name.lower():
                    choices.append(discord.app_commands.Choice(name=name, value=role_id))
        
        return choices[:25]

    @discord.app_commands.command(name="sell", description="Продажа ролей в инвентаре")
    @discord.app_commands.describe(id_role="Выберите роль для продажи")
    @discord.app_commands.autocomplete(id_role=role_autocomplete)
    async def sell(self, interaction: Interaction, id_role: int = None):
        user_id = str(interaction.user.id)
        guild = interaction.guild
        member = interaction.user
        
        if id_role is None:
            user_roles = get_user_roles(user_id)
            if not user_roles:
                embed = create_embed(
                    description="У вас нет ролей, которые можно продать.",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            roles_data = []
            for role_id in user_roles:
                role_data = get_role_by_id(role_id)
                if role_data:
                    roles_data.append(role_data)

            embed = create_embed(
                title="Продажа ролей",
                description="Вот роли, которые вы можете продать:\n\n" + "\n".join([
                    f"{EMOJIS['DOT']} **{role['name']}** | {int(role['balance'] * 0.70):,} {EMOJIS['MONEY']}\n🔑 **ID роли:** `{role['role_id']}`\n"
                    for role in roles_data
                ]),
                color="BLUE"
            )
            await interaction.response.send_message(embed=embed)
            return

        role = get_role_by_id(id_role)
        if role is None:
            embed = create_embed(
                description="Роль не найдена!",
                color="RED"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user_roles = get_user_roles(user_id)
        if id_role not in user_roles:
            embed = create_embed(
                description="У вас нет этой роли!",
                color="RED"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        sale_price = int(role['balance'] * 0.70)  # 70% от цены роли
        bot_profit = role['balance'] - sale_price  # 30% в казну сервера

        user_data = get_user(user_id)
        user_data['balance'] = user_data.get('balance', 0) + sale_price
        save_user(user_id, user_data)

        bot_id = '1264591814208262154'  # ID бота
        bot_data = get_user(bot_id)
        bot_data['balance'] = bot_data.get('balance', 0) + bot_profit
        save_user(bot_id, bot_data)

        role_obj = guild.get_role(role['discord_role_id'])
        if role_obj:
            await member.remove_roles(role_obj, reason="Sold role")
            remove_role_from_user(user_id, id_role)
            
            embed = create_embed(
                title="Роль продана!",
                description=f"Вы продали роль **{role['name']}** за {sale_price:,} {EMOJIS['MONEY']}\n"
                          f"Ваш новый баланс: {user_data['balance']:,} {EMOJIS['MONEY']}\n"
                          f"С продажи роли, 30% отправляется в **казну сервера**",
                color="GREEN"
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = create_embed(
                description="Роль не найдена на сервере.",
                color="RED"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Sell(bot))
