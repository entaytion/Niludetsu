import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.database import Database

class Marry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.proposals = {}

    @discord.app_commands.command(name="marry", description="Сделать предложение пользователю")
    @discord.app_commands.describe(member="Пользователь, которому вы хотите сделать предложение")
    async def marry(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете жениться на самом себе!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                embed=Embed(
                    description="Вы не можете жениться на боте!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Проверяем, не женаты ли уже пользователи
        author_id = str(interaction.user.id)
        target_id = str(member.id)

        author_data = await self.db.get_row("users", user_id=author_id)
        target_data = await self.db.get_row("users", user_id=target_id)

        if not author_data:
            author_data = await self.db.insert("users", {
                'user_id': author_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'spouse': None
            })

        if not target_data:
            target_data = await self.db.insert("users", {
                'user_id': target_id,
                'balance': 0,
                'deposit': 0,
                'xp': 0,
                'level': 1,
                'roles': '[]',
                'spouse': None
            })

        if author_data.get('spouse'):
            spouse = interaction.guild.get_member(int(author_data['spouse']))
            await interaction.response.send_message(
                embed=Embed(
                    description=f"Вы уже состоите в браке с {spouse.mention if spouse else 'кем-то'}!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if target_data.get('spouse'):
            spouse = interaction.guild.get_member(int(target_data['spouse']))
            await interaction.response.send_message(
                embed=Embed(
                    description=f"{member.mention} уже состоит в браке с {spouse.mention if spouse else 'кем-то'}!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        # Создаем кнопки
        view = discord.ui.View(timeout=60)
        accept_button = discord.ui.Button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept")
        decline_button = discord.ui.Button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="decline")

        async def accept_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != member.id:
                await button_interaction.response.send_message(
                    embed=Embed(
                        description="Это не ваше предложение!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            # Регистрируем брак
            await self.db.update(
                "users",
                where={"user_id": author_id},
                values={"spouse": target_id}
            )
            await self.db.update(
                "users",
                where={"user_id": target_id},
                values={"spouse": author_id}
            )

            await button_interaction.message.edit(
                embed=Embed(
                    title="💒 Свадьба!",
                    description=f"💝 {interaction.user.mention} и {member.mention} теперь в браке!",
                    color="GREEN"
                ),
                view=None
            )

        async def decline_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id != member.id:
                await button_interaction.response.send_message(
                    embed=Embed(
                        description="Это не ваше предложение!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            await button_interaction.message.edit(
                embed=Embed(
                    description=f"{member.mention} отклонил(а) предложение {interaction.user.mention}",
                    color="RED"
                ),
                view=None
            )

        accept_button.callback = accept_callback
        decline_button.callback = decline_callback
        view.add_item(accept_button)
        view.add_item(decline_button)

        # Отправляем предложение
        await interaction.response.send_message(
            embed=Embed(
                title="💍 Предложение руки и сердца",
                description=f"{interaction.user.mention} делает предложение {member.mention}!",
                color="BLUE"
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(Marry(bot)) 