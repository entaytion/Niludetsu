import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database

class Divorce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @discord.app_commands.command(name="divorce", description="Развестись с текущим партнером")
    async def divorce(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = await self.db.get_row("users", user_id=user_id)

        if not user_data:
            user_data = await self.db.insert("users", {
                'user_id': user_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'spouse': None
            })

        if not user_data.get('spouse'):
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не состоите в браке!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Получаем данные партнера
        spouse_id = user_data['spouse']
        spouse_data = await self.db.get_row("users", user_id=spouse_id)
        spouse = interaction.guild.get_member(int(spouse_id))

        # Создаем кнопки подтверждения
        view = discord.ui.View(timeout=60)
        confirm_button = discord.ui.Button(label="Подтвердить", style=discord.ButtonStyle.red, custom_id="confirm")
        cancel_button = discord.ui.Button(label="Отменить", style=discord.ButtonStyle.grey, custom_id="cancel")

        async def confirm_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message(
                    embed=Embed(
                        description="Это не ваш развод!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            # Разводим пользователей
            await self.db.update(
                "users",
                where={"user_id": user_id},
                values={"spouse": None}
            )
            await self.db.update(
                "users",
                where={"user_id": spouse_id},
                values={"spouse": None}
            )

            await button_interaction.message.edit(
                embed=Embed(
                    title="💔 Развод оформлен",
                    description=f"{interaction.user.mention} и {spouse.mention if spouse else 'партнер'} больше не в браке.",
                    color="RED"
                ),
                view=None
            )

        async def cancel_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message(
                    embed=Embed(
                        description="Это не ваш развод!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            await button_interaction.message.edit(
                embed=Embed(
                    description=f"{interaction.user.mention} отменил(а) развод.",
                    color="GREEN"
                ),
                view=None
            )

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Отправляем сообщение с подтверждением
        await interaction.response.send_message(
            embed=Embed(
                title="💔 Подтверждение развода",
                description=f"{interaction.user.mention}, вы уверены, что хотите развестись с {spouse.mention if spouse else 'партнером'}?",
                color="BLUE"
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(Divorce(bot)) 