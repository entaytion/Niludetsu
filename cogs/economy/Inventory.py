import discord
from discord.ext import commands
from utils import create_embed, get_user, get_user_roles, get_role_by_id, EMOJIS

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="inventory", description="Показать ваши купленные роли")
    async def inventory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            user_data = get_user(self.bot, user_id)
            if not user_data.get('roles'):
                await interaction.followup.send(
                    embed=create_embed(
                        description="У вас нет купленных ролей!"
                    )
                )
                return

            user_roles = get_user_roles(user_id)
            if not user_roles:
                await interaction.followup.send(
                    embed=create_embed(
                        description="У вас нет купленных ролей!"
                    )
                )
                return

            embed = create_embed(
                title=f"🎒 Инвентарь {interaction.user.name}",
                description="Ваши купленные роли:"
            )

            for role_id in user_roles:
                role_data = get_role_by_id(role_id)
                if role_data:
                    embed.add_field(
                        name=f"{role_data['name']}",
                        value=f"💰 Стоимость: {role_data['balance']} {EMOJIS['MONEY']}\n📝 Описание: {role_data['description']}\n🔑 ID роли: `{role_data['role_id']}`",
                        inline=False
                    )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in inventory command: {e}")
            await interaction.followup.send(
                embed=create_embed(
                    description="Произошла ошибка при получении инвентаря!"
                )
            )

async def setup(bot):
    await bot.add_cog(Inventory(bot))