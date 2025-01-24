import discord
from discord import Interaction
from discord.ext import commands
from utils import load_roles, get_user, save_user, create_embed, count_role_owners, add_role_to_user, get_user_roles, EMOJIS

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
                description = "Основной список ролей:\n\n"
                
                for role in roles:
                    owners = count_role_owners(role['role_id'])
                    description += f"{EMOJIS['DOT']} **{role['name']}** | {role['balance']} {EMOJIS['MONEY']}\n"
                    description += f"{role['description']}\n"
                    description += f"👥 **Владельцев:** {owners}\n"
                    description += f"🔑 **ID роли:** `{role['role_id']}`\n\n"
                
                embed = create_embed(
                    title="Магазин",
                    description=description
                )
                await interaction.response.send_message(embed=embed)
                return

            # Покупка роли
            roles = load_roles()
            role = next((r for r in roles if r["role_id"] == id_role), None)

            if role is None:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Роль не найдена."
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
                    description="Недостаточно средств для покупки."
                )
                await interaction.response.send_message(embed=embed)
                return

            # Перевірка чи є вже роль у користувача
            user_roles = get_user_roles(user_id)
            if id_role in user_roles:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="У вас уже есть эта роль!"
                    )
                )
                return

            # Додаємо роль користувачу
            role_obj = guild.get_role(role['discord_role_id'])
            if role_obj:
                # Спочатку знімаємо гроші і додаємо Discord роль
                user_data['balance'] -= role['balance']
                await interaction.user.add_roles(role_obj, reason="Buy from shop")
                
                # Оновлюємо роль в базі даних
                current_roles = user_data.get('roles', '')
                if current_roles:
                    new_roles = f"{current_roles},{id_role}"
                else:
                    new_roles = str(id_role)
                
                user_data['roles'] = new_roles
                save_user(user_id, user_data)

                embed = create_embed(
                    description=f"Вы купили роль! Ваш баланс: {user_data['balance']} {EMOJIS['MONEY']}."
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Роль не найдена на сервере."
                    )
                )

        except Exception as e:
            print(f"Error in shop command: {e}")
            await interaction.response.send_message(
                embed=create_embed(
                    description="Произошла ошибка при выполнении команды."
                )
            )

async def setup(client):
    await client.add_cog(Shop(client))
