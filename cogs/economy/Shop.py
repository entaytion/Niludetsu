import discord
from discord import Interaction
from discord.ext import commands
from utils import load_roles, get_user, save_user, create_embed, FOOTER_SUCCESS, FOOTER_ERROR

class Shop(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="shop", description="Магазин сервера")
    @discord.app_commands.describe(id_role="Выбор роли") 
    async def shop(self,
                   interaction: Interaction,
                   id_role: int = None):
        try:
            user_id = str(interaction.user.id)

            if id_role is None:
                roles = load_roles()

                embed = create_embed(
                    title="Магазин",
                    description="Основной список ролей (бета-тест):\n\n" + "\n".join([
                        f"<:aeOutlineDot:1266066158029770833> **{role['name']}** | {role['balance']} <:aeMoney:1266066622561517781>\n{role['description']}\n**Чтобы купить роль, напишите:** `/shop id_role:{role['role_id']}`\n"
                        for role in roles
                    ])
                )
                await interaction.response.send_message(embed=embed)
            else:
                roles = load_roles()

                role = next((r for r in roles if r["role_id"] == id_role), None)

                if role is None:
                    await interaction.response.send_message(
                        embed=create_embed(
                            description="Роль не найдена.",
                            footer=FOOTER_ERROR
                        )
                    )
                    return

                guild = interaction.guild
                if not guild:
                    await interaction.response.send_message("Сервер не найден.")
                    return

                user_data = get_user(self.client, user_id)

                if user_data['balance'] < role['balance']:
                    embed = create_embed(
                        description="Недостаточно средств для покупки.",
                        footer=FOOTER_ERROR
                    )
                    await interaction.response.send_message(embed=embed)
                    return

                user_data['balance'] -= role['balance']
                save_user(user_id, user_data)

                role_obj_id = role['discord_role_id']
                member = interaction.user
                role_obj = guild.get_role(role_obj_id)
                if role_obj:
                    await member.add_roles(role_obj, reason="Buy from shop")
                    embed = create_embed(
                        description="Вы купили роль! Ваш баланс: " + str(user_data['balance']) + " <:aeMoney:1266066622561517781>.",
                        footer=FOOTER_SUCCESS
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(
                        embed=create_embed(
                            description="Роль не найдена на сервере.",
                            footer=FOOTER_ERROR
                        )
                    )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Произошла ошибка при выполнении команды.",
                    footer=FOOTER_ERROR
                )
            )

async def setup(client):
    await client.add_cog(Shop(client))
