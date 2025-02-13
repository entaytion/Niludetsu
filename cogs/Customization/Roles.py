import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    async def get_roles_from_db(self, category: str) -> list:
        """Получение ролей из базы данных"""
        try:
            roles = await self.db.fetch_all(
                "SELECT value FROM settings WHERE category = ? AND key = ?",
                'roles', category
            )
            return roles[0]['value'].split(',') if roles else []
        except Exception as e:
            print(f"❌ Ошибка при получении ролей: {e}")
            return []

    @app_commands.command(name="colors", description="Выбрать цветную роль")
    async def colors(self, interaction: discord.Interaction):
        """Команда для выбора цветной роли"""
        try:
            # Получаем цветные роли из базы данных
            color_roles = await self.get_roles_from_db("color_roles")
            
            if not color_roles:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Цветные роли не настроены",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Создаем список компонентов
            options = []
            for role_data in color_roles:
                role = interaction.guild.get_role(int(role_data['id']))
                if role:
                    options.append(
                        discord.SelectOption(
                            label=role_data['name'],
                            value=str(role.id),
                            emoji=role_data['emoji'],
                            description=f"Цвет: #{role_data['color']:06x}"
                        )
                    )

            # Создаем выпадающий список
            select = discord.ui.Select(
                placeholder="Выберите цвет",
                options=options,
                custom_id="color_role_select"
            )

            # Создаем View с кнопкой для сброса
            view = discord.ui.View()
            view.add_item(select)
            view.add_item(discord.ui.Button(
                label="Сбросить цвет",
                style=discord.ButtonStyle.danger,
                custom_id="reset_color"
            ))

            # Отправляем сообщение с компонентами
            await interaction.response.send_message(
                embed=Embed(
                    title="🎨 Выбор цветной роли",
                    description="Выберите цвет из списка ниже или нажмите кнопку для сброса",
                    color="BLUE"
                ),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )

    @app_commands.command(name="gender", description="Выбрать гендерную роль")
    async def gender(self, interaction: discord.Interaction):
        """Команда для выбора гендерной роли"""
        try:
            # Получаем гендерные роли из базы данных
            gender_roles = await self.get_roles_from_db("gender_roles")
            
            if not gender_roles:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Гендерные роли не настроены",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Создаем список компонентов
            options = []
            for role_data in gender_roles:
                role = interaction.guild.get_role(int(role_data['id']))
                if role:
                    options.append(
                        discord.SelectOption(
                            label=role_data['name'],
                            value=str(role.id),
                            emoji=role_data['emoji']
                        )
                    )

            # Создаем выпадающий список
            select = discord.ui.Select(
                placeholder="Выберите пол",
                options=options,
                custom_id="gender_role_select"
            )

            # Создаем View с кнопкой для сброса
            view = discord.ui.View()
            view.add_item(select)
            view.add_item(discord.ui.Button(
                label="Сбросить пол",
                style=discord.ButtonStyle.danger,
                custom_id="reset_gender"
            ))

            # Отправляем сообщение с компонентами
            await interaction.response.send_message(
                embed=Embed(
                    title="👥 Выбор пола",
                    description="Выберите пол из списка ниже или нажмите кнопку для сброса",
                    color="BLUE"
                ),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Обработчик взаимодействий с компонентами"""
        if not interaction.data:
            return

        try:
            custom_id = interaction.data.get("custom_id", "")
            
            if custom_id == "color_role_select":
                # Получаем выбранную роль
                role_id = interaction.data["values"][0]
                role = interaction.guild.get_role(int(role_id))
                
                if not role:
                    return await interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Роль не найдена",
                            color="RED"
                        ),
                        ephemeral=True
                    )

                # Получаем все цветные роли
                color_roles = await self.get_roles_from_db("color_roles")
                color_role_ids = [int(r['id']) for r in color_roles]
                
                # Удаляем старые цветные роли
                roles_to_remove = [r for r in interaction.user.roles if r.id in color_role_ids]
                if roles_to_remove:
                    await interaction.user.remove_roles(*roles_to_remove, reason="Смена цветной роли")

                # Выдаем новую роль
                await interaction.user.add_roles(role, reason="Выбор цветной роли")
                
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Роль обновлена",
                        description=f"Вам выдана роль {role.mention}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )

            elif custom_id == "reset_color":
                # Получаем все цветные роли
                color_roles = await self.get_roles_from_db("color_roles")
                color_role_ids = [int(r['id']) for r in color_roles]
                
                # Удаляем цветные роли
                roles_to_remove = [r for r in interaction.user.roles if r.id in color_role_ids]
                if roles_to_remove:
                    await interaction.user.remove_roles(*roles_to_remove, reason="Сброс цветной роли")
                    
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Роли сброшены",
                        description="Все цветные роли были удалены",
                        color="GREEN"
                    ),
                    ephemeral=True
                )

            elif custom_id == "gender_role_select":
                # Получаем выбранную роль
                role_id = interaction.data["values"][0]
                role = interaction.guild.get_role(int(role_id))
                
                if not role:
                    return await interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description="Роль не найдена",
                            color="RED"
                        ),
                        ephemeral=True
                    )

                # Получаем все гендерные роли
                gender_roles = await self.get_roles_from_db("gender_roles")
                gender_role_ids = [int(r['id']) for r in gender_roles]
                
                # Удаляем старые гендерные роли
                roles_to_remove = [r for r in interaction.user.roles if r.id in gender_role_ids]
                if roles_to_remove:
                    await interaction.user.remove_roles(*roles_to_remove, reason="Смена гендерной роли")

                # Выдаем новую роль
                await interaction.user.add_roles(role, reason="Выбор гендерной роли")
                
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Роль обновлена",
                        description=f"Вам выдана роль {role.mention}",
                        color="GREEN"
                    ),
                    ephemeral=True
                )

            elif custom_id == "reset_gender":
                # Получаем все гендерные роли
                gender_roles = await self.get_roles_from_db("gender_roles")
                gender_role_ids = [int(r['id']) for r in gender_roles]
                
                # Удаляем гендерные роли
                roles_to_remove = [r for r in interaction.user.roles if r.id in gender_role_ids]
                if roles_to_remove:
                    await interaction.user.remove_roles(*roles_to_remove, reason="Сброс гендерной роли")
                    
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Роли сброшены",
                        description="Все гендерные роли были удалены",
                        color="GREEN"
                    ),
                    ephemeral=True
                )

        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Roles(bot)) 