import discord
from discord.ext import commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import has_admin_role

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="balance", description="Управление балансом пользователя")
    @discord.app_commands.describe(
        user="Пользователь для управления балансом (опционально)",
        action="Действие с балансом (set, add, del)",
        amount="Сумма для изменения баланса (опционально)"
    )
    async def balance(self, interaction: discord.Interaction,
                     user: discord.Member = None,
                     action: str = None, 
                     amount: int = None):
        user = user or interaction.user

        # Проверка, является ли пользователь ботом
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете использовать эту команду на ботов.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        user_id = str(user.id)
        user_data = get_user(user_id)

        if action is None:
            if user_data:
                balance = user_data.get('balance', 0)
                deposit = user_data.get('deposit', 0)
                embed = create_embed(
                    description=f"{EMOJIS['DOT']} **Наличные**: {balance:,} {EMOJIS['MONEY']}\n"
                              f"{EMOJIS['DOT']} **В банке:** {deposit:,} {EMOJIS['MONEY']}",
                    author={'name': f"Баланс пользователя {user.name}:", 'icon_url': user.display_avatar.url},
                    color="DEFAULT"
                )
                await interaction.response.send_message(embed=embed)
            else:
                # Создаем нового пользователя с нулевым балансом
                user_data = {
                    'balance': 0,
                    'deposit': 0,
                    'xp': 0,
                    'level': 1,
                    'roles': '[]'
                }
                save_user(user_id, user_data)
                embed = create_embed(
                    description=f"{EMOJIS['DOT']} **Наличные**: 0 {EMOJIS['MONEY']}\n"
                              f"{EMOJIS['DOT']} **В банке:** 0 {EMOJIS['MONEY']}",
                    author={'name': f"Баланс пользователя {user.name}:", 'icon_url': user.display_avatar.url},
                    color="DEFAULT"
                )
                await interaction.response.send_message(embed=embed)
            return

        # Проверка прав администратора
        if not await has_admin_role()(interaction):
            await interaction.response.send_message(
                embed=create_embed(
                    description="У вас нет прав для выполнения этой команды.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверка указания суммы
        if amount is None and action in ["set", "add", "del"]:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Не указана сумма для изменения баланса.",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Если пользователя нет в базе, создаем запись
        if not user_data:
            user_data = {
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]'
            }

        # Выполнение действий с балансом
        if action == "set":
            user_data['balance'] = amount
            save_user(user_id, user_data)
            await interaction.response.send_message(
                embed=create_embed(
                    title="Баланс обновлён",
                    description=f"Теперь баланс {user.mention} стал {amount:,} {EMOJIS['MONEY']}",
                    color="GREEN"
                )
            )

        elif action == "add":
            user_data['balance'] = user_data.get('balance', 0) + amount
            save_user(user_id, user_data)
            await interaction.response.send_message(
                embed=create_embed(
                    title="Баланс обновлён",
                    description=f"На баланс {user.mention} добавлено {amount:,} {EMOJIS['MONEY']}",
                    color="GREEN"
                )
            )

        elif action == "del":
            current_balance = user_data.get('balance', 0)
            if current_balance < amount:
                await interaction.response.send_message(
                    embed=create_embed(
                        description=f"На балансе пользователя недостаточно средств.\n"
                                  f"Текущий баланс: {current_balance:,} {EMOJIS['MONEY']}",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            user_data['balance'] = current_balance - amount
            save_user(user_id, user_data)
            await interaction.response.send_message(
                embed=create_embed(
                    title="Баланс обновлён", 
                    description=f"С баланса {user.mention} снято {amount:,} {EMOJIS['MONEY']}",
                    color="GREEN"
                )
            )

async def setup(bot):
    await bot.add_cog(Balance(bot))
