import discord
from discord import Interaction
from discord.ext import commands
from utils import load_roles, get_user, save_user, create_embed, FOOTER_SUCCESS, FOOTER_ERROR

class Sell(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="sell", description="Продажа ролей в инвентаре")
    @discord.app_commands.describe(id_role="Выбор роли")
    async def sell(self,
                   interaction: Interaction,
                   id_role: int = None):
        user_id = str(interaction.user.id)
        guild = interaction.guild
        member = interaction.user
        user_roles = [r.id for r in member.roles]

        roles = load_roles()

        if id_role is None:
            roles_for_sale = [role for role in roles if role['discord_role_id'] in user_roles]

            if not roles_for_sale:
                embed = create_embed(
                    description="У вас нет ролей, которые можно продать.",
                    footer=FOOTER_ERROR
                )
                await interaction.response.send_message(embed=embed)
                return

            embed = create_embed(
                title="Продажа ролей",
                description="Вот роли, которые вы можете продать:\n\n" + "\n".join([ 
                    f"<:aeOutlineDot:1266066158029770833> **{role['name']}** | {int(role['balance'] * 0.90)} <:aeMoney:1266066622561517781>\n**Чтобы продать роль, напишите:** `/sell id_role:{role['role_id']}`\n"
                    for role in roles_for_sale
                ])
            )
            await interaction.response.send_message(embed=embed)
        else:
            role = next((r for r in roles if r["role_id"] == id_role), None)

            if role is None:
                embed = create_embed(
                    description="Роль не найдена!",
                    footer=FOOTER_ERROR
                )
                await interaction.response.send_message(embed=embed)
                return

            if role['discord_role_id'] not in user_roles:
                embed = create_embed(
                    description="Вы не имеете этой роли!",
                    footer=FOOTER_ERROR
                )
                await interaction.response.send_message(embed=embed)
                return

            sale_price = int(role['balance'] * 0.90)  # 90% від балансу ролі
            bot_profit = role['balance'] - sale_price  # 10% в казну сервера

            user_data = get_user(self.client, user_id)
            user_data['balance'] += sale_price
            save_user(user_id, user_data)

            bot_id = '1264591814208262154'  # ID бота
            bot_data = get_user(self.client, bot_id)
            bot_data['balance'] += bot_profit
            save_user(bot_id, bot_data)

            role_obj = guild.get_role(role['discord_role_id'])
            if role_obj:
                await member.remove_roles(role_obj, reason="Sold role")
                embed = create_embed(
                    title="Роль продана!",
                    description=f"Вы продали роль за {sale_price} <:aeMoney:1266066622561517781>. Ваш новый баланс: {user_data['balance']} <:aeMoney:1266066622561517781>.\nС продажи роли, 10% отправляется в **казну сервера**.",
                    footer=FOOTER_SUCCESS
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = create_embed(
                    description="Роль не найдена на сервере.",
                    footer=FOOTER_ERROR
                )
                await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Sell(client))
