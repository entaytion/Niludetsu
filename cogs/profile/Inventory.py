import discord
from discord.ext import commands
from Niludetsu.utils.database import get_user, get_user_roles, get_role_by_id
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="inventory", description="Показать ваши купленные роли")
    async def inventory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            user_data = get_user(user_id)
            if not user_data.get('roles'):
                await interaction.followup.send(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Инвентарь пуст",
                        description="У вас нет купленных ролей!",
                        color="RED"
                    )
                )
                return

            user_roles = get_user_roles(user_id)
            if not user_roles:
                await interaction.followup.send(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Инвентарь пуст",
                        description="У вас нет купленных ролей!",
                        color="RED"
                    )
                )
                return

            embed = create_embed(
                title=f"{EMOJIS['INVENTORY']} Инвентарь {interaction.user.name}",
                description=f"{EMOJIS['ROLES']} Ваши купленные роли:",
                color="BLUE"
            )

            for role_id in user_roles:
                role_data = get_role_by_id(role_id)
                if role_data:
                    embed.add_field(
                        name=f"{EMOJIS['ROLE']} {role_data['name']}",
                        value=f"{EMOJIS['MONEY']} Стоимость: {role_data['balance']}\n{EMOJIS['DESCRIPTION']} Описание: {role_data['description']}\n{EMOJIS['ID']} ID роли: `{role_data['role_id']}`",
                        inline=False
                    )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in inventory command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Произошла ошибка при получении инвентаря!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Inventory(bot))