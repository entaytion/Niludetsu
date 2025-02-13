import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database
import asyncio
from typing import Optional

class ReasonModal(Modal):
    def __init__(self, title: str, callback):
        super().__init__(title=title)
        self.callback = callback
        
        self.reason_input = TextInput(
            label="Причина",
            placeholder="Опишите вашу проблему...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.reason_input)
        
    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.reason_input.value)

class TicketButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="create_ticket")
    async def create(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ReasonModal("Создание тикета", self.handle_ticket_create))
        
    async def handle_ticket_create(self, interaction: discord.Interaction, reason: str):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.handle_ticket_create(interaction, reason)

class TicketView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        
    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="У вас нет прав на закрытие этого тикета",
                    color="RED"
                ),
                ephemeral=True
            )

        await interaction.response.send_modal(ReasonModal("Закрытие тикета", self.handle_ticket_close))
        
    async def handle_ticket_close(self, interaction: discord.Interaction, reason: str):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.handle_ticket_close(interaction, reason)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self._initialize())
        
    async def _initialize(self):
        """Асинхронная инициализация"""
        await self.bot.wait_until_ready()
        await self.db.init()
        await self.setup_tickets_view()
        
    async def setup_tickets_view(self):
        """Настройка панели тикетов"""
        try:
            # Получаем настройки из базы данных
            settings = await self.db.fetch_all(
                "SELECT key, value FROM settings WHERE category = 'tickets'"
            )
            
            settings_dict = {row['key']: row['value'] for row in settings}

            channel_id = settings_dict.get('panel_channel')
            message_id = settings_dict.get('panel_message')
            
            if not channel_id:
                return
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            # Создаем эмбед
            embed = Embed(
                title="🎫 Система тикетов",
                description=(
                    "Нажмите на кнопку ниже, чтобы создать тикет.\n\n"
                    f"{Emojis.DOT} В тикете опишите вашу проблему\n"
                    f"{Emojis.DOT} Дождитесь ответа модератора\n"
                    f"{Emojis.DOT} Не создавайте несколько тикетов\n"
                    f"{Emojis.DOT} Не спамьте в тикетах"
                ),
                color="BLUE"
            )
            
            if message_id:
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.edit(embed=embed, view=TicketButton())
                    return
                except Exception as e:
                    print(f"Error editing message: {e}")
                    pass
                    
            # Создаем новое сообщение
            message = await channel.send(embed=embed, view=TicketButton())
            
            # Сохраняем ID сообщения
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value)
                VALUES ('tickets', 'panel_message', ?)
                """,
                str(message.id)
            )
            
        except Exception as e:
            print(f"❌ Ошибка при настройке панели тикетов: {e}")
            
    async def handle_ticket_create(self, interaction: discord.Interaction, reason: str):
        """Обработка создания тикета"""
        try:
            # Проверяем, есть ли уже открытый тикет
            existing_ticket = await self.db.fetch_one(
                """
                SELECT channel_id FROM tickets 
                WHERE user_id = ? AND guild_id = ? AND status = 'open'
                """,
                str(interaction.user.id), str(interaction.guild.id)
            )
            
            if existing_ticket:
                channel = interaction.guild.get_channel(int(existing_ticket['channel_id']))
                if channel:
                    return await interaction.response.send_message(
                        embed=Embed(
                            title=f"{Emojis.ERROR} Ошибка",
                            description=f"У вас уже есть открытый тикет: {channel.mention}",
                            color="RED"
                        ),
                        ephemeral=True
                    )

            # Получаем категорию для тикетов
            category_id = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'tickets' AND key = 'category'"
            )
            
            if not category_id:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Категория для тикетов не настроена",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            category = interaction.guild.get_channel(int(category_id['value']))
            if not category:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Категория для тикетов не найдена",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Создаем канал
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True
                )
            }
            
            # Добавляем права для модераторов
            mod_role_id = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'tickets' AND key = 'mod_role'"
            )
            
            if mod_role_id:
                mod_role = interaction.guild.get_role(int(mod_role_id['value']))
                if mod_role:
                    overwrites[mod_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        attach_files=True,
                        embed_links=True,
                        read_message_history=True,
                        manage_messages=True
                    )
                    
            channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Тикет создан пользователем {interaction.user}"
            )
            
            # Сохраняем тикет в базу данных
            await self.db.execute(
                """
                INSERT INTO tickets (channel_id, user_id, guild_id, reason, status)
                VALUES (?, ?, ?, ?, 'open')
                """,
                str(channel.id), str(interaction.user.id), str(interaction.guild.id), reason
            )
            
            # Отправляем сообщение в канал тикета
            embed = Embed(
                title="🎫 Новый тикет",
                description=(
                    f"{Emojis.DOT} **Пользователь:** {interaction.user.mention}\n"
                    f"{Emojis.DOT} **Причина:** {reason}\n\n"
                    "Модераторы скоро ответят на ваш тикет.\n"
                    "Для закрытия тикета нажмите на кнопку ниже."
                ),
                color="BLUE"
            )
            
            await channel.send(
                content=f"{interaction.user.mention}",
                embed=embed,
                view=TicketView(interaction.user.id)
            )
            
            # Отправляем подтверждение
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Тикет создан",
                    description=f"Ваш тикет: {channel.mention}",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании тикета: {e}")
            try:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Произошла ошибка при создании тикета",
                        color="RED"
                    ),
                    ephemeral=True
                )
            except discord.HTTPException:
                pass
            
    async def handle_ticket_close(self, interaction: discord.Interaction, reason: str):
        """Обработка закрытия тикета"""
        try:
            # Получаем информацию о тикете
            ticket = await self.db.fetch_one(
                """
                SELECT user_id FROM tickets 
                WHERE channel_id = ? AND guild_id = ? AND status = 'open'
                """,
                str(interaction.channel.id), str(interaction.guild.id)
            )
            
            if not ticket:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Этот канал не является тикетом!",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Обновляем статус тикета
            await self.db.execute(
                """
                UPDATE tickets 
                SET status = 'closed', closed_by = ?, closed_at = CURRENT_TIMESTAMP, close_reason = ?
                WHERE channel_id = ? AND guild_id = ? AND status = 'open'
                """,
                str(interaction.user.id), reason, str(interaction.channel.id), str(interaction.guild.id)
            )
            
            # Отправляем сообщение о закрытии
            embed = Embed(
                title="🔒 Тикет закрыт",
                description=(
                    f"{Emojis.DOT} **Модератор:** {interaction.user.mention}\n"
                    f"{Emojis.DOT} **Причина:** {reason}\n\n"
                    "Канал будет удален через 10 секунд."
                ),
                color="RED"
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Ждем 10 секунд и удаляем канал
            await asyncio.sleep(10)
            await interaction.channel.delete()
            
        except Exception as e:
            print(f"❌ Ошибка при закрытии тикета: {e}")
            try:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Произошла ошибка при закрытии тикета",
                        color="RED"
                    ),
                    ephemeral=True
                )
            except discord.HTTPException:
                pass
            
    @app_commands.command(name="tickets", description="Управление системой тикетов")
    @app_commands.describe(
        action="Действие (create/set)",
        message_id="ID сообщения с панелью тикетов",
        tickets_channel="ID канала для панели тикетов",
        category="ID категории для тикетов",
        mod_role="ID роли модераторов тикетов"
    )
    @commands.has_permissions(administrator=True)
    async def tickets_command(
        self, 
        interaction: discord.Interaction, 
        action: str,
        message_id: str = None,
        tickets_channel: str = None,
        category: str = None,
        mod_role: str = None
    ):
        """Команда для управления системой тикетов"""
        if action == "create":
            await self._handle_create_tickets(interaction, message_id, tickets_channel)
        elif action == "set":
            await self._handle_set_tickets(interaction, tickets_channel, category, mod_role)
        else:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Неверное действие. Используйте create или set",
                    color="RED"
                ),
                ephemeral=True
            )

    async def _handle_create_tickets(self, interaction: discord.Interaction, message_id: str, tickets_channel: str):
        """Обработка создания панели тикетов"""
        try:
            channel = interaction.guild.get_channel(int(tickets_channel))
            if not channel:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Канал не найден",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Создаем эмбед
            embed = Embed(
                title="🎫 Система тикетов",
                description=(
                    "Нажмите на кнопку ниже, чтобы создать тикет.\n\n"
                    f"{Emojis.DOT} В тикете опишите вашу проблему\n"
                    f"{Emojis.DOT} Дождитесь ответа модератора\n"
                    f"{Emojis.DOT} Не создавайте несколько тикетов\n"
                    f"{Emojis.DOT} Не спамьте в тикетах"
                ),
                color="BLUE"
            )
            
            # Пытаемся получить сообщение
            try:
                message = await channel.fetch_message(int(message_id))
                await message.edit(embed=embed, view=TicketButton())
            except discord.NotFound:
                message = await channel.send(embed=embed, view=TicketButton())
                
            # Сохраняем ID канала и сообщения
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value)
                VALUES 
                    ('tickets', 'panel_channel', ?),
                    ('tickets', 'panel_message', ?)
                """,
                str(channel.id), str(message.id)
            )
            
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Успешно",
                    description="Панель тикетов создана",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании панели тикетов: {e}")
            try:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Произошла ошибка при создании панели тикетов",
                        color="RED"
                    ),
                    ephemeral=True
                )
            except discord.HTTPException:
                pass

    async def _handle_set_tickets(self, interaction: discord.Interaction, tickets_channel: str = None, category: str = None, mod_role: str = None):
        try:
            # Сохраняем настройки
            if tickets_channel:
                await self.db.execute(
                    """
                    INSERT OR REPLACE INTO settings (category, key, value)
                    VALUES ('tickets', 'panel_channel', ?)
                    """,
                    tickets_channel
                )
                
            if category:
                await self.db.execute(
                    """
                    INSERT OR REPLACE INTO settings (category, key, value)
                    VALUES ('tickets', 'category', ?)
                    """,
                    category
                )
                
            if mod_role:
                await self.db.execute(
                    """
                    INSERT OR REPLACE INTO settings (category, key, value)
                    VALUES ('tickets', 'mod_role', ?)
                    """,
                    mod_role
                )
                
            # Обновляем панель
            await self.setup_tickets_view()
            
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Успешно",
                    description="Настройки тикетов обновлены",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при настройке тикетов: {e}")
            try:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Произошла ошибка при настройке тикетов",
                        color="RED"
                    ),
                    ephemeral=True
                )
            except discord.HTTPException:
                pass

async def setup(bot):
    await bot.add_cog(Tickets(bot)) 