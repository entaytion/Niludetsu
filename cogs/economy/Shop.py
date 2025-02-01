import discord
from discord import Interaction
from discord.ext import commands
from Niludetsu.database import Database
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import math

ITEMS_PER_PAGE = 5  # Количество ролей на одной странице

class RoleSelect(discord.ui.Select):
    def __init__(self, roles: List[dict], guild: discord.Guild):
        self.guild = guild
        options = [
            discord.SelectOption(
                label=f"{role['price']}💰 {guild.get_role(int(role['role_id'])).name}",
                value=role['role_id'],
                description=role['description'][:100] if role['description'] else None
            ) for role in roles if guild.get_role(int(role['role_id']))
        ]
        super().__init__(
            placeholder="Выберите роль для покупки...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.roles = {role['role_id']: role for role in roles}

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        role_data = self.roles[role_id]
        
        # Создаем окно подтверждения
        confirm = discord.ui.Button(label="Подтвердить", style=discord.ButtonStyle.green)
        cancel = discord.ui.Button(label="Отменить", style=discord.ButtonStyle.red)
        
        async def confirm_callback(btn_interaction):
            # Проверяем баланс пользователя
            user_data = await self.view.db.ensure_user(btn_interaction.user.id)

            # Проверяем только баланс, без учета депозита
            if user_data['balance'] < role_data['price']:
                await btn_interaction.response.send_message(
                    embed=Embed(
                        description=f"❌ У вас недостаточно средств в балансе! Необходимо: {role_data['price']}💰\nВаш баланс: {user_data['balance']}💰",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            # Покупаем роль
            role = btn_interaction.guild.get_role(int(role_id))
            if not role:
                await btn_interaction.response.send_message(
                    embed=Embed(
                        description="❌ Роль не найдена!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return
                
            # Снимаем деньги только с баланса
            new_balance = user_data['balance'] - role_data['price']
            await self.view.db.update("users", 
                where={"user_id": str(btn_interaction.user.id)},
                values={"balance": new_balance}
            )
            
            # Выдаем роль
            await btn_interaction.user.add_roles(role)
            
            # Обновляем количество покупок
            await self.view.db.update("shop_roles",
                where={"role_id": role_id},
                values={"purchases": role_data['purchases'] + 1}
            )
            
            await btn_interaction.response.send_message(
                embed=Embed(
                    description=f"✅ Вы успешно приобрели роль {role.mention} за {role_data['price']}💰\nОстаток баланса: {new_balance}💰",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        async def cancel_callback(btn_interaction):
            await btn_interaction.response.send_message(
                embed=Embed(
                    description="❌ Покупка отменена",
                    color="RED"
                ),
                ephemeral=True
            )
            
        confirm.callback = confirm_callback
        cancel.callback = cancel_callback
        
        view = discord.ui.View()
        view.add_item(confirm)
        view.add_item(cancel)
        
        role = interaction.guild.get_role(int(role_id))
        await interaction.response.send_message(
            embed=Embed(
                title="🛒 Подтверждение покупки",
                description=f"Вы собираетесь купить роль {role.mention} за {role_data['price']}💰\n\n"
                          f"Описание: {role_data['description']}\n"
                          f"Куплено раз: {role_data['purchases']}",
                color="BLUE"
            ),
            view=view,
            ephemeral=True
        )

class ShopView(discord.ui.View):
    def __init__(self, roles: List[dict], db: Database, guild: discord.Guild, page: int = 0):
        super().__init__()
        self.roles = roles
        self.db = db
        self.guild = guild
        self.page = page
        self.max_pages = math.ceil(len(roles) / ITEMS_PER_PAGE)
        
        # Добавляем селект с ролями для текущей страницы
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_roles = roles[start_idx:end_idx]
        if page_roles:
            self.add_item(RoleSelect(page_roles, guild))
            
        # Добавляем кнопки навигации
        self.prev_button = discord.ui.Button(
            label="◀",
            style=discord.ButtonStyle.secondary,
            disabled=(page == 0),
            custom_id="prev"
        )
        self.next_button = discord.ui.Button(
            label="▶",
            style=discord.ButtonStyle.secondary,
            disabled=(page >= self.max_pages - 1),
            custom_id="next"
        )
        
        self.prev_button.callback = self.prev_button_callback
        self.next_button.callback = self.next_button_callback
        
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    async def prev_button_callback(self, interaction: discord.Interaction):
        await self.show_page(interaction, self.page - 1)

    async def next_button_callback(self, interaction: discord.Interaction):
        await self.show_page(interaction, self.page + 1)

    async def show_page(self, interaction: discord.Interaction, page: int):
        self.page = page
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_roles = self.roles[start_idx:end_idx]
        
        embed = Embed(title="🛍️ Магазин ролей")
        for role in page_roles:
            discord_role = interaction.guild.get_role(int(role['role_id']))
            if discord_role:
                embed.add_field(
                    name=f"{role['price']}💰 {discord_role.name}",
                    value=f"Описание: {role['description']}\nКуплено: {role['purchases']} раз",
                    inline=False
                )
        
        embed.set_footer(text=f"Страница {page + 1}/{self.max_pages}")
        
        view = ShopView(self.roles, self.db, interaction.guild, page)
        await interaction.response.edit_message(embed=embed, view=view)

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="shop", description="Открыть магазин ролей")
    async def shop(self, interaction: discord.Interaction):
        # Получаем все роли из магазина
        roles = await self.db.fetch_all(
            "SELECT * FROM shop_roles ORDER BY price ASC"
        )
        
        if not roles:
            await interaction.response.send_message(
                embed=Embed(
                    description="❌ В магазине пока нет ролей!",
                    color="RED"
                ),
                ephemeral=True
            )
            return
            
        # Создаем начальное сообщение с первой страницей
        embed = Embed(title="🛍️ Магазин ролей")
        page_roles = roles[:ITEMS_PER_PAGE]
        
        for role in page_roles:
            discord_role = interaction.guild.get_role(int(role['role_id']))
            if discord_role:
                embed.add_field(
                    name=f"{role['price']}💰 {discord_role.name}",
                    value=f"Описание: {role['description']}\nКуплено: {role['purchases']} раз",
                    inline=False
                )
                
        embed.set_footer(text=f"Страница 1/{math.ceil(len(roles) / ITEMS_PER_PAGE)}")
        
        view = ShopView(roles, self.db, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Shop(bot))
