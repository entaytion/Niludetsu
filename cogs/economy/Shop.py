import discord
from discord import Interaction
from discord.ext import commands
from Niludetsu.utils.database import get_user, save_user, get_roles, get_role_by_id, add_role_to_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="shop", description="Магазин ролей")
    @discord.app_commands.describe(
        action="Действие (list/buy)",
        role_id="ID роли для покупки"
    )
    async def shop(self, interaction: Interaction, action: str = "list", role_id: int = None):
        if action == "list":
            roles = get_roles()
            if not roles:
                embed = create_embed(
                    description="В магазине пока нет доступных ролей.",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            description = ["**Доступные роли:**\n"]
            for role in roles:
                description.append(
                    f"{EMOJIS['DOT']} **{role['name']}**\n"
                    f"💰 Цена: {role['balance']:,} {EMOJIS['MONEY']}\n"
                    f"📝 {role['description']}\n"
                    f"🔑 **ID роли:** `{role['role_id']}`\n"
                )

            embed = create_embed(
                title="Магазин ролей",
                description="\n".join(description),
                color="BLUE",
                footer={
                    'text': 'Для покупки используйте команду /shop buy <ID роли>'
                }
            )
            await interaction.response.send_message(embed=embed)
            return

        if action == "buy":
            if role_id is None:
                embed = create_embed(
                    description="Укажите ID роли для покупки.",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            role = get_role_by_id(role_id)
            if not role:
                embed = create_embed(
                    description="Роль с указанным ID не найдена.",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            user_id = str(interaction.user.id)
            user_data = get_user(user_id)

            if not user_data:
                user_data = {
                    'balance': 0,
                    'deposit': 0,
                    'xp': 0,
                    'level': 1,
                    'roles': '[]'
                }
                save_user(user_id, user_data)

            if user_data.get('balance', 0) < role['balance']:
                embed = create_embed(
                    description=f"У вас недостаточно средств.\n"
                              f"Цена роли: {role['balance']:,} {EMOJIS['MONEY']}\n"
                              f"Ваш баланс: {user_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Выполняем покупку
            user_data['balance'] = user_data.get('balance', 0) - role['balance']
            save_user(user_id, user_data)
            add_role_to_user(user_id, role_id)

            # Выдаем роль на сервере
            discord_role = interaction.guild.get_role(role['discord_role_id'])
            if discord_role:
                await interaction.user.add_roles(discord_role)

                embed = create_embed(
                    title="Покупка успешна!",
                    description=f"Вы купили роль **{role['name']}** за {role['balance']:,} {EMOJIS['MONEY']}\n"
                              f"Ваш текущий баланс: {user_data['balance']:,} {EMOJIS['MONEY']}",
                    color="GREEN"
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = create_embed(
                    description="Ошибка: роль не найдена на сервере.",
                    color="RED"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = create_embed(
                description="Неверное действие. Используйте list для просмотра или buy для покупки.",
                color="RED"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Shop(bot))
