import discord
from discord.ext import commands
from utils import get_user, save_user, create_embed, FOOTER_SUCCESS, FOOTER_ERROR

class Divorce(commands.Cog):
    def __init__(self, client):
        self.client = client

    @discord.app_commands.command(name="divorce", description="Развестись с текущим партнером")
    async def divorce(self, interaction: discord.Interaction):
        user_data = get_user(self.client, str(interaction.user.id))
        
        if not user_data:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не зарегистрированы в системе!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        if not user_data.get('spouse'):
            await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не женаты!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            return

        # Получаем данные партнера
        spouse_id = user_data['spouse']
        spouse_data = get_user(self.client, spouse_id)
        
        if not spouse_data:
            # Если партнера не найдено, просто удаляем запись о браке
            user_data.update({
                'spouse': None,
                'marriage_date': None
            })
            save_user(str(interaction.user.id), user_data)
            await interaction.response.send_message(
                embed=create_embed(
                    description="Развод оформлен.",
                    footer=FOOTER_SUCCESS
                )
            )
            return

        # Разделяем общий банк
        total_balance = user_data.get('balance', 0)
        half_balance = total_balance // 2
        
        # Обновляем данные первого пользователя
        user_data.update({
            'spouse': None,
            'marriage_date': None,
            'balance': half_balance
        })
        
        # Обновляем данные второго пользователя
        spouse_data.update({
            'spouse': None,
            'marriage_date': None,
            'balance': half_balance
        })
        
        # Сохраняем изменения
        save_user(str(interaction.user.id), user_data)
        save_user(spouse_id, spouse_data)
        
        # Получаем объект пользователя партнера
        spouse_member = interaction.guild.get_member(int(spouse_id))
        spouse_mention = spouse_member.mention if spouse_member else "бывший партнер"
        
        await interaction.response.send_message(
            embed=create_embed(
                title="💔 Развод оформлен",
                description=f"{interaction.user.mention} разводится с {spouse_mention}.\n"
                           f"Банк разделен поровну: по {half_balance} <:aeMoney:1266066622561517781>",
                footer=FOOTER_SUCCESS
            )
        )

async def setup(client):
    await client.add_cog(Divorce(client)) 