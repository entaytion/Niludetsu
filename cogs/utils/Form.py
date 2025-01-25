import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button, Select
import json
import datetime
from utils import create_embed, EMOJIS

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
        
        self.fields = {
            "personal_info": TextInput(
                label="Личная информация",
                placeholder="Ваше имя, возраст, часовой пояс",
                style=discord.TextStyle.paragraph,
                required=True
            ),
            "motivation": TextInput(
                label="Мотивация",
                placeholder="Почему вы хотите присоединиться к команде?",
                style=discord.TextStyle.paragraph,
                required=True
            ),
            "availability": TextInput(
                label="Доступность",
                placeholder="Сколько времени вы готовы уделять работе?",
                style=discord.TextStyle.paragraph,
                required=True
            ),
            "team_experience": TextInput(
                label="Опыт работы в команде",
                placeholder="Расскажите о вашем опыте работы в команде",
                style=discord.TextStyle.paragraph,
                required=True
            ),
            "position_experience": TextInput(
                label="Профессиональный опыт",
                placeholder="Опыт работы на подобной должности",
                style=discord.TextStyle.paragraph,
                required=True
            )
        }

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
    def __init__(self, application_data: dict, user_id: int, position: str):
        super().__init__(timeout=None)
        self.application_data = application_data
        self.user_id = user_id
        self.position = position

    async def _update_application_status(self, interaction: discord.Interaction, status: str, color: int, reason: str = None):
        user = interaction.client.get_user(self.user_id)
        status_emoji = "✅" if status == "принята" else "❌"
        
        if user:
            try:
                embed = create_embed(
                    title=f"{status_emoji} Статус вашей заявки",
                    description=(
                        f"Ваша заявка на должность {self.position} была **{status}**!"
                    ),
                    color=color
                )
                
                if reason:
                    embed.add_field(name="Причина", value=reason, inline=False)
                    
                await user.send(embed=embed)
            except discord.Forbidden:
                pass

        embed = interaction.message.embeds[0]
        embed.color = color
        embed.title = f"{status_emoji} Заявка {status} | {self.position}"
        
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)
        
        response_message = f"{status_emoji} Заявка пользователя {user.mention} была {status}"
        if reason:
            response_message += f"\n**Причина:** {reason}"
        
        await interaction.response.send_message(response_message, ephemeral=True)

    async def _handle_accept(self, interaction: discord.Interaction, reason: str = None):
        await self._update_application_status(interaction, "принята", 0x00FF00, reason)

    async def _handle_reject(self, interaction: discord.Interaction, reason: str = None):
        await self._update_application_status(interaction, "отклонена", 0xFF0000, reason)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина принятия", self._handle_accept)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина отказа", self._handle_reject)
        await interaction.response.send_modal(modal)

class Forms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config/config.json', 'r') as f:
            self.config = json.load(f)
        bot.loop.create_task(self.setup_form_view())

    async def setup_form_view(self):
        await self.bot.wait_until_ready()
        if 'FORM_CHANNEL_ID' in self.config and 'FORM_MESSAGE_ID' in self.config:
            try:
                channel = self.bot.get_channel(int(self.config['FORM_CHANNEL_ID']))
                if channel:
                    try:
                        message = await channel.fetch_message(int(self.config['FORM_MESSAGE_ID']))
                        embed = create_embed(
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
                        print(f"✅ Панель заявок загружена: {channel.name} ({channel.id})")
                    except discord.NotFound:
                        print("❌ Сообщение с панелью заявок не найдено!")
                else:
                    print("❌ Канал для заявок не найден!")
            except Exception as e:
                print(f"❌ Ошибка при загрузке панели заявок: {e}")

    @app_commands.command(name="form", description="Создать панель для подачи заявок")
    @app_commands.describe(
        message_id="ID сообщения с панелью для подачи заявок",
        applications_channel="ID канала куда будут отправляться заявки",
        action="Действие (create/set)"
    )
    @commands.has_permissions(administrator=True)
    async def form(self, interaction: discord.Interaction, action: str, message_id: str = None, applications_channel: str = None):
        action = action.lower()
        if action not in ["create", "set"]:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'", ephemeral=True)
            return

        try:
            if action == "create":
                await self._handle_create_form(interaction, message_id, applications_channel)
            else:
                await self._handle_set_form(interaction, applications_channel)
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

    async def _handle_create_form(self, interaction, message_id, applications_channel):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await interaction.response.send_message("❌ Сообщение не найдено!", ephemeral=True)
            return

        try:
            applications_channel_id = int(applications_channel)
            if not (channel := self.bot.get_channel(applications_channel_id)):
                await interaction.response.send_message("❌ Канал для заявок не найден!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Неверный формат ID канала!", ephemeral=True)
            return

        embed = create_embed(
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
        
        self.config.update({
            'FORM_MESSAGE_ID': message_id,
            'FORM_CHANNEL_ID': str(applications_channel_id)
        })
        
        with open('config/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

        await interaction.response.send_message(
            f"✅ Панель подачи заявок успешно создана!\n"
            f"📝 ID сообщения: `{message_id}`\n"
            f"📨 Канал для заявок: {channel.mention}",
            ephemeral=True
        )

    async def _handle_set_form(self, interaction, applications_channel):
        channel = await commands.TextChannelConverter().convert(interaction, applications_channel)
        self.config['FORM_CHANNEL_ID'] = str(channel.id)
        
        with open('config/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
            
        embed = create_embed(
            title="✅ Канал для заявок установлен",
            description=f"Канал {channel.mention} успешно установлен для получения заявок."
        )
        await interaction.response.send_message(embed=embed)

    async def handle_modal_submit(self, interaction: discord.Interaction, modal, position: str):
        if 'FORM_CHANNEL_ID' not in self.config:
            await interaction.response.send_message("❌ Канал для заявок не настроен в конфиге!", ephemeral=True)
            return

        if not (channel := self.bot.get_channel(int(self.config['FORM_CHANNEL_ID']))):
            await interaction.response.send_message("❌ Канал для заявок не найден!", ephemeral=True)
            return

        application_data = {field_name: field.value for field_name, field in modal.fields.items()}

        embed = create_embed(
            title=f"📝 Новая заявка на должность {position}",
            description=(
                f"{EMOJIS['DOT']} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                f"{EMOJIS['DOT']} **Личная информация:**\n```\n{application_data['personal_info']}```\n"
                f"{EMOJIS['DOT']} **Мотивация:**\n```\n{application_data['motivation']}```\n"
                f"{EMOJIS['DOT']} **Доступность:**\n```\n{application_data['availability']}```\n"
                f"{EMOJIS['DOT']} **Опыт работы в команде:**\n```\n{application_data['team_experience']}```\n"
                f"{EMOJIS['DOT']} **Профессиональный опыт:**\n```\n{application_data['position_experience']}```"
            ),
            footer={"text": f"ID пользователя: {interaction.user.id}"}
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        await channel.send(embed=embed, view=ApplicationView(application_data, interaction.user.id, position))
        
        success_embed = create_embed(
            title="✅ Заявка отправлена",
            description=(
                "Ваша заявка успешно отправлена!\n"
                "Ожидайте ответа от администрации."
            ),
            color=0x00FF00
        )
        
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Forms(bot))