import discord
from discord.ext import commands
from utils import get_user, save_user, create_embed
from datetime import datetime

class Marry(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.proposals = {}  # Зберігаємо активні пропозиції

    @discord.app_commands.command(name="marry", description="Выйти замуж / жениться за кого-то")
    @discord.app_commands.describe(user="Пользователь, которому вы хотите сделать предложение")
    async def marry(self, interaction: discord.Interaction, user: discord.Member):
        if user.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете пожениться с ботом!"
                )
            )
            return

        if user.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете пожениться сами с собой!"
                )
            )
            return

        author_data = get_user(self.client, str(interaction.user.id))
        target_data = get_user(self.client, str(user.id))

        if not author_data or not target_data:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Оба пользователя должны быть зарегистрированы!"
                )
            )
            return

        if author_data.get('spouse'):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы уже женаты!"
                )
            )
            return

        if target_data.get('spouse'):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Этот пользователь уже женат!"
                )
            )
            return

        # Створюємо кнопки для відповіді
        class MarryButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != user.id:
                    await button_interaction.response.send_message("Это не ваше предложение!")
                    return
                self.value = True
                self.stop()
                for item in self.children:
                    item.disabled = True
                await button_interaction.response.edit_message(view=self)

            @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red)
            async def decline(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != user.id:
                    await button_interaction.response.send_message("Это не ваше предложение!")
                    return
                self.value = False
                self.stop()
                for item in self.children:
                    item.disabled = True
                await button_interaction.response.edit_message(view=self)

        view = MarryButtons()
        await interaction.response.send_message(
            embed=create_embed(
                title="💍 Предложение руки и сердца",
                description=f"{interaction.user.mention} делает предложение {user.mention}!\n"
                           f"У вас есть 60 секунд, чтобы ответить."
            ),
            view=view
        )

        # Чекаємо на відповідь
        await view.wait()

        if view.value is None:
            await interaction.edit_original_response(
                embed=create_embed(
                    description="Время на ответ вышло!"
                ),
                view=None
            )
        elif view.value:
            # Одружуємо користувачів
            author_data = get_user(self.client, str(interaction.user.id))
            target_data = get_user(self.client, str(user.id))
            
            # Встановлюємо дані про шлюб
            marriage_date = datetime.now().isoformat()
            joint_balance = (author_data.get('balance', 0) + target_data.get('balance', 0)) // 2
            
            # Оновлюємо дані першого користувача
            author_data.update({
                'spouse': str(user.id),
                'marriage_date': marriage_date,
                'balance': joint_balance
            })
            
            # Оновлюємо дані другого користувача
            target_data.update({
                'spouse': str(interaction.user.id),
                'marriage_date': marriage_date,
                'balance': joint_balance
            })
            
            # Зберігаємо зміни
            save_user(str(interaction.user.id), author_data)
            save_user(str(user.id), target_data)
            
            await interaction.edit_original_response(
                embed=create_embed(
                    title="💑 Поздравляем молодых!",
                    description=f"{interaction.user.mention} и {user.mention} теперь женаты!\n"
                               f"Ваш общий банк: {joint_balance} <:aeMoney:1266066622561517781>"
                ),
                view=None
            )
        else:
            await interaction.edit_original_response(
                embed=create_embed(
                    description=f"{user.mention} отклонил(а) предложение {interaction.user.mention}!"
                ),
                view=None
            )

async def setup(client):
    await client.add_cog(Marry(client)) 