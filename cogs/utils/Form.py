import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button, Select
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

class PositionSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Пиар-менеджер",
                description="Продвижение и реклама сервера", 
                emoji="📢",
                value="pr_manager"
            ),
            discord.SelectOption(
                label="Хелпер/Модератор",
                description="Поддержание порядка и помощь участникам",
                emoji="🛡️", 
                value="moderator"
            )
        ]
        super().__init__(
            placeholder="Выберите должность...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="position_select"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = PRManagerModal() if self.values[0] == "pr_manager" else ModeratorModal()
        await interaction.response.send_modal(modal)

class BaseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, emoji="📝", custom_id="submit_application")
    async def submit(self, interaction: discord.Interaction, button: Button):
        view = View(timeout=None)
        view.add_item(PositionSelect())
        await interaction.response.send_message("Выберите должность:", view=view, ephemeral=True)

class ApplicationButton(BaseButton):
    pass

class ReasonModal(Modal):
    def __init__(self, title: str, callback):
        super().__init__(title=title)
        self.callback = callback
        
        self.reason = TextInput(
            label="Причина",
            placeholder="Укажите причину принятия/отказа (необязательно)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.reason.value)

class BaseApplicationModal(Modal):
    def __init__(self, title: str):
        super().__init__(title=title)
        
        self.fields = {}
        
        self.fields['personal_info'] = TextInput(
            label="Личная информация",
            placeholder="Ваше имя, возраст, часовой пояс",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        self.fields['motivation'] = TextInput(
            label="Мотивация",
            placeholder="Почему вы хотите присоединиться к команде?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        self.fields['availability'] = TextInput(
            label="Доступность",
            placeholder="Сколько времени вы готовы уделять работе?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        self.fields['team_experience'] = TextInput(
            label="Опыт работы в команде",
            placeholder="Расскажите о вашем опыте работы в команде",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        self.fields['position_experience'] = TextInput(
            label="Профессиональный опыт",
            placeholder="Расскажите о вашем опыте в данной сфере",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        for field in self.fields.values():
            self.add_item(field)

class PRManagerModal(BaseApplicationModal):
    def __init__(self):
        super().__init__(title="Заявка на должность Пиар-менеджера")
    
    async def on_submit(self, interaction: discord.Interaction):
        if forms_cog := interaction.client.get_cog("Forms"):
            await forms_cog.handle_modal_submit(interaction, self, "Пиар-менеджер")

class ModeratorModal(BaseApplicationModal):
    def __init__(self):
        super().__init__(title="Заявка на должность Хелпера/Модератора")
    
    async def on_submit(self, interaction: discord.Interaction):
        if forms_cog := interaction.client.get_cog("Forms"):
            await forms_cog.handle_modal_submit(interaction, self, "Хелпер/Модератор")

class ApplicationView(View):
    def __init__(self, application_data, user_id: int, position: str):
        super().__init__(timeout=None)
        self.application_data = application_data
        self.user_id = user_id
        self.position = position
        
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_application")
    async def accept(self, interaction: discord.Interaction, button: Button):
        try:
            user = interaction.guild.get_member(self.user_id)
            if not user:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Пользователь не найден на сервере",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Отправляем уведомление пользователю
            try:
                await user.send(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Заявка принята!",
                        description=f"Ваша заявка на должность {self.position} была принята!\nАдминистрация свяжется с вами в ближайшее время.",
                        color="GREEN"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"{Emojis.SUCCESS} Заявка принята: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Заявка обработана",
                    description=f"Заявка пользователя {user.mention} на должность {self.position} была принята",
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
            
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reject_application")
    async def reject(self, interaction: discord.Interaction, button: Button):
        try:
            user = interaction.guild.get_member(self.user_id)
            if not user:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Пользователь не найден на сервере",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Отправляем уведомление пользователю
            try:
                await user.send(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Заявка отклонена",
                        description=f"Ваша заявка на должность {self.position} была отклонена.",
                        color="RED"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = f"{Emojis.ERROR} Заявка отклонена: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Заявка обработана",
                    description=f"Заявка пользователя {user.mention} на должность {self.position} была отклонена",
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

class Forms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        bot.loop.create_task(self.setup_form_view())

    async def setup_form_view(self):
        """Настройка панели заявок"""
        try:
            # Получаем канал для заявок
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'forms' AND key = 'channel'"
            )
            
            if not result:
                return
                
            channel_id = result['value']    
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            # Создаем сообщение с панелью
            embed = Embed(
                title="📝 Подать заявку",
                description=(
                    "Нажмите на кнопку ниже, чтобы подать заявку на должность.\n\n"
                    f"{Emojis.DOT} Выберите интересующую вас должность\n"
                    f"{Emojis.DOT} Заполните анкету\n"
                    f"{Emojis.DOT} Ожидайте ответа от администрации"
                ),
                color="BLUE"
            )
            
            message = await channel.send(embed=embed, view=ApplicationButton())
            
            # Сохраняем ID сообщения
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value)
                VALUES ('forms', 'message', ?)
                """,
                str(message.id)
            )
            
            return message
            
        except Exception as e:
            print(f"❌ Ошибка при настройке панели заявок: {e}")
            return None

    @app_commands.command(name="form", description="Управление панелью заявок")
    @app_commands.describe(
        action="Действие (create/set)",
        message_id="ID сообщения с панелью для подачи заявок",
        applications_channel="ID канала куда будут отправляться заявки"
    )
    @commands.has_permissions(administrator=True)
    async def form(self, interaction: discord.Interaction, action: str, message_id: str = None, applications_channel: str = None):
        action = action.lower()
        if action not in ["create", "set"]:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'")
            return

        try:
            if action == "create":
                await self._handle_create_form(interaction, message_id, applications_channel)
            else:
                await self._handle_set_form(interaction, applications_channel)
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}")

    async def _handle_create_form(self, interaction, message_id, applications_channel):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await interaction.response.send_message("❌ Сообщение не найдено!")
            return

        try:
            applications_channel_id = int(applications_channel)
            if not (channel := self.bot.get_channel(applications_channel_id)):
                await interaction.response.send_message("❌ Канал для заявок не найден!")
                return
        except ValueError:
            await interaction.response.send_message("❌ Неверный формат ID канала!")
            return

        embed = Embed(
            title="📋 Набор в команду сервера",
            description=(
                "**Доступные должности:**\n\n"
                "**📢 Пиар-менеджер**\n"
                "• Продвижение и реклама сервера\n"
                "• Управление партнерствами\n"
                "• Развитие сервера\n\n"
                "**🛡️ Хелпер/Модератор**\n"
                "• Поддержание порядка в чатах\n"
                "• Помощь участникам\n"
                "• Модерация контента\n\n"
                "**Нажмите кнопку ниже, чтобы подать заявку!**"
            )
        )

        await message.edit(embed=embed, view=ApplicationButton())
        
        # Сохраняем настройки в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?), (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = excluded.value
            """,
            'forms', 'channel', str(applications_channel_id),
            'forms', 'message', str(message_id)
        )

        await interaction.response.send_message(
            f"✅ Панель подачи заявок успешно создана!\n"
            f"📝 ID сообщения: `{message_id}`\n"
            f"📨 Канал для заявок: {channel.mention}"
        )

    async def _handle_set_form(self, interaction, applications_channel):
        channel = await commands.TextChannelConverter().convert(interaction, applications_channel)
        
        # Сохраняем канал в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = ?
            """,
            'forms', 'channel', str(channel.id), str(channel.id)
        )
            
        embed = Embed(
            title="✅ Канал для заявок установлен",
            description=f"Канал {channel.mention} успешно установлен для получения заявок."
        )
        await interaction.response.send_message(embed=embed)

    async def handle_modal_submit(self, interaction: discord.Interaction, modal, position: str):
        """Обработка отправки формы"""
        try:
            # Получаем канал для заявок
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'forms' AND key = 'channel'"
            )
            
            if not result:
                await interaction.response.send_message("❌ Канал для заявок не настроен!")
                return
                
            channel_id = result['value']
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message("❌ Канал для заявок не найден!")
                return

            application_data = {field_name: field.value for field_name, field in modal.fields.items()}

            embed = Embed(
                title=f"📝 Новая заявка на должность {position}",
                description=(
                    f"{Emojis.DOT} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                    f"{Emojis.DOT} **Личная информация:**\n```\n{application_data['personal_info']}```\n"
                    f"{Emojis.DOT} **Мотивация:**\n```\n{application_data['motivation']}```\n"
                    f"{Emojis.DOT} **Доступность:**\n```\n{application_data['availability']}```\n"
                    f"{Emojis.DOT} **Опыт работы в команде:**\n```\n{application_data['team_experience']}```\n"
                    f"{Emojis.DOT} **Профессиональный опыт:**\n```\n{application_data['position_experience']}```"
                ),
                footer={"text": f"ID пользователя: {interaction.user.id}"}
            )

            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

            await channel.send(embed=embed, view=ApplicationView(application_data, interaction.user.id, position))

            success_embed = Embed(
                title="✅ Заявка отправлена",
                description="Ваша заявка успешно отправлена!\nОжидайте ответа от администрации.",
                color="GREEN"
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)

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
    await bot.add_cog(Forms(bot))