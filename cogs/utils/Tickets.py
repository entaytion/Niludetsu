import discord
from discord.ext import commands
from discord import app_commands
import yaml
import asyncio
from datetime import datetime
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.primary, emoji="📩", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Загружаем конфигурацию
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        with open('config/tickets.yaml', 'r', encoding='utf-8') as f:
            ticket_data = yaml.safe_load(f) or {
                "ticket_counter": 0,
                "active_tickets": {},
                "closed_tickets": {},
                "ratings": {}
            }

        # Получаем необходимые ID
        category_id = int(config['tickets']['category'])
        support_role_id = int(config['tickets']['support_role'])
        
        # Проверяем, нет ли уже открытого тикета
        category = interaction.guild.get_channel(category_id)
        existing_ticket = discord.utils.get(category.text_channels, 
                                          topic=f"User ID: {interaction.user.id}")
        
        if existing_ticket:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="У вас уже есть открытый тикет!"
                ),
                ephemeral=True
            )

        # Увеличиваем счетчик тикетов
        ticket_data["ticket_counter"] += 1
        ticket_number = ticket_data["ticket_counter"]

        # Создаём канал тикета
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.get_role(support_role_id): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            category=category,
            topic=f"User ID: {interaction.user.id}",
            overwrites=overwrites
        )

        # Сохраняем информацию о тикете
        ticket_info = {
            "number": ticket_number,
            "user_id": interaction.user.id,
            "guild_id": interaction.guild.id,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "last_activity": datetime.now().isoformat(),
            "added_users": []
        }
        ticket_data["active_tickets"][str(channel.id)] = ticket_info

        with open('config/tickets.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(ticket_data, f, default_flow_style=False, allow_unicode=True)

        # Отправляем сообщение в канал тикета
        embed = create_embed(
            title=f"Тикет #{ticket_number}",
            description=f"Здравствуйте, {interaction.user.mention}!\nОпишите вашу проблему, и команда поддержки скоро вам поможет."
        )
        
        view = TicketControlView()
        await channel.send(
            content=f"{interaction.user.mention} {interaction.guild.get_role(support_role_id).mention}",
            embed=embed,
            view=view
        )

        # Отправляем подтверждение создания тикета
        await interaction.response.send_message(
            embed=create_embed(
                description=f"Ваш тикет #{ticket_number} создан: {channel.mention}"
            ),
            ephemeral=True
        )

        # Логируем создание тикета
        logs_channel = interaction.guild.get_channel(int(config['tickets']['logs_channel']))
        if logs_channel:
            log_embed = create_embed(
                title=f"Тикет #{ticket_number} создан",
                description=f"**Пользователь:** {interaction.user.mention}\n**Канал:** {channel.mention}"
            )
            await logs_channel.send(embed=log_embed)

class RatingView(discord.ui.View):
    def __init__(self, ticket_id: int):
        super().__init__(timeout=300)
        self.ticket_id = ticket_id

    @discord.ui.button(label="1", style=discord.ButtonStyle.red, custom_id="rate_1")
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rate(interaction, 1)

    @discord.ui.button(label="2", style=discord.ButtonStyle.gray, custom_id="rate_2")
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rate(interaction, 2)

    @discord.ui.button(label="3", style=discord.ButtonStyle.gray, custom_id="rate_3")
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rate(interaction, 3)

    @discord.ui.button(label="4", style=discord.ButtonStyle.gray, custom_id="rate_4")
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rate(interaction, 4)

    @discord.ui.button(label="5", style=discord.ButtonStyle.green, custom_id="rate_5")
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rate(interaction, 5)

    async def rate(self, interaction: discord.Interaction, rating: int):
        with open('config/tickets.yaml', 'r', encoding='utf-8') as f:
            ticket_data = yaml.safe_load(f)
        
        ticket_data["ratings"][str(self.ticket_id)] = rating
        
        with open('config/tickets.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(ticket_data, f, default_flow_style=False, allow_unicode=True)

        await interaction.response.send_message(
            embed=create_embed(
                description=f"Спасибо за оценку! Вы поставили {rating} звезд."
            ),
            ephemeral=True
        )
        self.stop()

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        with open('config/tickets.yaml', 'r', encoding='utf-8') as f:
            ticket_data = yaml.safe_load(f)
            
            # Проверяем права на закрытие тикета
            support_role_id = int(config['tickets']['support_role'])
            if not interaction.user.get_role(support_role_id) and not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="У вас нет прав на закрытие тикета!"
                    ),
                    ephemeral=True
                )

            # Перемещаем тикет в закрытые
            ticket_id = str(interaction.channel.id)
            if ticket_id in ticket_data["active_tickets"]:
                ticket_info = ticket_data["active_tickets"].pop(ticket_id)
                ticket_info["closed_at"] = datetime.now().isoformat()
                ticket_info["closed_by"] = interaction.user.id
                ticket_data["closed_tickets"][ticket_id] = ticket_info
                
                with open('config/tickets.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(ticket_data, f, default_flow_style=False, allow_unicode=True)

        await interaction.response.send_message(
            embed=create_embed(
                description="Тикет будет закрыт через 5 секунд..."
            )
        )

        # Отправляем форму оценки создателю тикета
        user = interaction.guild.get_member(ticket_info["user_id"])
        if user:
            rating_embed = create_embed(
                title="Оцените качество поддержки",
                description="Пожалуйста, оцените качество поддержки от 1 до 5"
            )
            try:
                await user.send(embed=rating_embed, view=RatingView(interaction.channel.id))
            except:
                pass

        # Логируем закрытие тикета
        logs_channel = interaction.guild.get_channel(int(config['tickets']['logs_channel']))
        if logs_channel:
            log_embed = create_embed(
                title=f"Тикет #{ticket_info['number']} закрыт",
                description=f"**Канал:** {interaction.channel.name}\n**Закрыт модератором:** {interaction.user.mention}"
            )
            await logs_channel.send(embed=log_embed)

        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Добавить участника", style=discord.ButtonStyle.green, emoji="👥", custom_id="add_member")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddMemberModal()
        await interaction.response.send_modal(modal)

class AddMemberModal(discord.ui.Modal, title="Добавить участника"):
    user_id = discord.ui.TextInput(
        label="ID пользователя",
        placeholder="Введите ID пользователя...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            user = interaction.guild.get_member(user_id)
            
            if not user:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Пользователь не найден!"
                    ),
                    ephemeral=True
                )

            # Обновляем права доступа
            await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)

            # Обновляем данные тикета
            with open('config/tickets.yaml', 'r', encoding='utf-8') as f:
                ticket_data = yaml.safe_load(f)
                
            ticket_id = str(interaction.channel.id)
            if ticket_id in ticket_data["active_tickets"]:
                if user_id not in ticket_data["active_tickets"][ticket_id]["added_users"]:
                    ticket_data["active_tickets"][ticket_id]["added_users"].append(user_id)
                
                with open('config/tickets.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(ticket_data, f, default_flow_style=False, allow_unicode=True)

            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Пользователь {user.mention} добавлен в тикет!"
                )
            )
        except ValueError:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Неверный формат ID!"
                ),
                ephemeral=True
            )

class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="setup", description="Настроить панель тикетов")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        channel_id = int(config['tickets']['panel']['channel'])
        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="Канал для панели тикетов не найден!",
                    color='RED'
                ),
                ephemeral=True
            )

        embed = create_embed(
            title="📩 Система тикетов",
            description="Нажмите на кнопку ниже, чтобы создать тикет и связаться с командой поддержки.",
            color='BLUE'
        )

        view = TicketView()
        await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            embed=create_embed(
                description="Панель тикетов успешно настроена!",
                color='GREEN'
            ),
            ephemeral=True
        )

    @app_commands.command(name="stats", description="Показать статистику тикетов")
    @app_commands.default_permissions(administrator=True)
    async def stats(self, interaction: discord.Interaction):
        with open('config/tickets.yaml', 'r', encoding='utf-8') as f:
            ticket_data = yaml.safe_load(f)

        total_tickets = ticket_data["ticket_counter"]
        active_tickets = len(ticket_data["active_tickets"])
        closed_tickets = len(ticket_data["closed_tickets"])
        
        # Подсчет средней оценки
        ratings = ticket_data["ratings"].values()
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        embed = create_embed(
            title="📊 Статистика тикетов",
            color='BLUE'
        )
        embed.add_field(name="Всего тикетов", value=str(total_tickets), inline=True)
        embed.add_field(name="Активные тикеты", value=str(active_tickets), inline=True)
        embed.add_field(name="Закрытые тикеты", value=str(closed_tickets), inline=True)
        embed.add_field(name="Средняя оценка", value=f"{avg_rating:.1f}⭐", inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot)) 