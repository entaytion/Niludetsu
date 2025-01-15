import discord
from discord.ext import commands
from utils import create_embed, get_user, save_user, FOOTER_ERROR, FOOTER_SUCCESS

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="balance", description="Управление балансом пользователя")
    @discord.app_commands.describe(user="Пользователь для управления балансом (опционально)",
                                   action="Действие с балансом (set, add, del)",
                                   amount="Сумма для изменения баланса (опционально)")
    async def balance(self, interaction: discord.Interaction,
                      user: discord.Member = None,
                      action: str = None, 
                      amount: int = None):
        user = user or interaction.user

        # Проверка, является ли пользователь ботом
        if user.bot and user.id != 1264591814208262154:
            await interaction.response.send_message("Вы не можете использовать эту команду на ботов.")
            return

        user_id = str(user.id)
        user_data = get_user(self.bot, user_id)

        if action is None:
            if user_data:
                balance = user_data.get('balance', 0)
                deposit = user_data.get('deposit', 0)
                embed = create_embed(
                    description=f"<:aeOutlineDot:1266066158029770833> **Наличные**: {balance} <:aeMoney:1266066622561517781>\n<:aeOutlineDot:1266066158029770833> **В банке:** {deposit} <:aeMoney:1266066622561517781>",
                    author={'name': f"Баланс пользователя {user.name}:", 'icon_url': user.avatar.url})
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Пользователь не найден.")
            return

        # Проверка прав
        if interaction.user.id != 636570363605680139:
            embed = create_embed(
                description="У вас нет прав для выполнения этой команды.",
                footer=FOOTER_ERROR)
            await interaction.response.send_message(embed=embed)
            return

        # Проверка указания суммы
        if amount is None and action in ["set", "add", "del"]:
            embed = create_embed(
                description="Не указана сумма для изменения баланса.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)
            return

        # Выполнение действий с балансом
        if action == "set":
            user_data['balance'] = amount
            save_user(user_id, user_data)
            embed = create_embed(
                title="Баланс обновлён.",
                description=f"Теперь баланс {user.mention} стал {amount} <:aeMoney:1266066622561517781>.",
                footer=FOOTER_SUCCESS
            )
            await interaction.response.send_message(embed=embed)

        elif action == "add":
            user_data['balance'] += amount
            save_user(user_id, user_data)
            embed = create_embed(
                title="Баланс обновлён.",
                description=f"Теперь на баланс {user.mention} добавлено {amount} <:aeMoney:1266066622561517781>.",
                footer=FOOTER_SUCCESS
            )
            await interaction.response.send_message(embed=embed)

        elif action == "del":
            user_data['balance'] -= amount
            save_user(user_id, user_data)
            embed = create_embed(
                title="Баланс обновлён.",
                description=f"Теперь с баланса {user.mention} снято {amount} <:aeMoney:1266066622561517781>.",
                footer=FOOTER_SUCCESS
            )
            await interaction.response.send_message(embed=embed)

        else:
            embed = create_embed(
                description="Произошла какая-то мистическая ошибка, о которой даже не знает разработчик.",
                footer=FOOTER_ERROR
            )
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Balance(bot))
