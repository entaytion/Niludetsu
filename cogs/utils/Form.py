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
                emoji="📢"
            ),
            discord.SelectOption(
                label="Хелпер/Модератор",
                description="Поддержание порядка и помощь участникам", 
                emoji="🛡️"
            )
        ]
        super().__init__(
            placeholder="Выберите должность...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        position = self.values[0]
        
        if position == "Пиар-менеджер":
            modal = PRManagerModal()
        else:
            modal = ModeratorModal()
            
        await interaction.response.send_modal(modal)

class ApplicationButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PositionSelect())

class BaseApplicationModal(Modal):
    def __init__(self, title: str):
        super().__init__(title=title)
        
        self.personal_info = TextInput(
            label="Личная информация",
            placeholder="Ваше имя, возраст, часовой пояс",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.motivation = TextInput(
            label="Мотивация",
            placeholder="Почему вы хотите присоединиться к команде?",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.availability = TextInput(
            label="Доступность",
            placeholder="Сколько времени вы готовы уделять работе?",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.team_experience = TextInput(
            label="Опыт работы в команде",
            placeholder="Расскажите о вашем опыте работы в команде",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.position_experience = TextInput(
            label="Профессиональный опыт",
            placeholder="Опыт работы на подобной должности",
            style=discord.TextStyle.paragraph,
            required=True
        )

        self.add_item(self.personal_info)
        self.add_item(self.motivation)
        self.add_item(self.availability)
        self.add_item(self.team_experience)
        self.add_item(self.position_experience)

class PRManagerModal(BaseApplicationModal):
    def __init__(self):
        super().__init__(title="Заявка на должность Пиар-менеджера")
    
    async def on_submit(self, interaction: discord.Interaction):
        forms_cog = interaction.client.get_cog("Forms")
        if forms_cog:
            await forms_cog.handle_modal_submit(interaction, self, "Пиар-менеджер")

class ModeratorModal(BaseApplicationModal):
    def __init__(self):
        super().__init__(title="Заявка на должность Хелпера/Модератора")
    
    async def on_submit(self, interaction: discord.Interaction):
        forms_cog = interaction.client.get_cog("Forms")
        if forms_cog:
            await forms_cog.handle_modal_submit(interaction, self, "Хелпер/Модератор")

class ApplicationView(View):
    def __init__(self, application_data: dict, user_id: int, position: str):
        super().__init__(timeout=None)
        self.application_data = application_data
        self.user_id = user_id
        self.position = position
        
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: Button):
        user = interaction.client.get_user(self.user_id)
        if user:
            try:
                await user.send(f"✅ Ваша заявка на должность {self.position} была **принята**!")
            except:
                pass
                
        embed = interaction.message.embeds[0]
        embed.color = 0x00FF00
        embed.title = f"✅ Заявка принята | {self.position}"
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Заявка пользователя {user.mention} была принята", ephemeral=True)
        
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: Button):
        user = interaction.client.get_user(self.user_id)
        if user:
            try:
                await user.send(f"❌ Ваша заявка на должность {self.position} была **отклонена**.")
            except:
                pass
                
        embed = interaction.message.embeds[0]
        embed.color = 0xFF0000
        embed.title = f"❌ Заявка отклонена | {self.position}"
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"❌ Заявка пользователя {user.mention} была отклонена", ephemeral=True)

class Forms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config/config.json', 'r') as f:
            self.config = json.load(f)

    @app_commands.command(name="form", description="Создать панель для подачи заявок")
    @app_commands.describe(
        message_id="ID сообщения с панелью для подачи заявок",
        applications_channel="ID канала куда будут отправляться заявки",
        action="Действие (create/set)"
    )
    @commands.has_permissions(administrator=True)
    async def form(self, interaction: discord.Interaction, action: str, message_id: str = None, applications_channel: str = None):
        """Создать панель для подачи заявок или установить канал для заявок"""
        if action.lower() == "create":
            try:
                # Получаем сообщение
                try:
                    message = await interaction.channel.fetch_message(int(message_id))
                except (discord.NotFound, ValueError):
                    await interaction.response.send_message("❌ Сообщение не найдено!", ephemeral=True)
                    return

                # Проверяем канал для заявок
                try:
                    applications_channel_id = int(applications_channel)
                    channel = self.bot.get_channel(applications_channel_id)
                    if not channel:
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

                view = ApplicationButton()
                
                # Обновляем сообщение
                await message.edit(embed=embed, view=view)
                
                # Сохраняем ID в конфиг
                self.config['FORM_MESSAGE_ID'] = message_id
                self.config['APPLICATIONS_CHANNEL_ID'] = str(applications_channel_id)
                
                with open('config/config.json', 'w') as f:
                    json.dump(self.config, f, indent=4)

                await interaction.response.send_message(
                    f"✅ Панель подачи заявок успешно создана!\n"
                    f"📝 ID сообщения: `{message_id}`\n"
                    f"📨 Канал для заявок: {channel.mention}", 
                    ephemeral=True
                )

            except Exception as e:
                await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)
                
        elif action.lower() == "set":
            try:
                channel = await commands.TextChannelConverter().convert(interaction, applications_channel)
                self.config['APPLICATIONS_CHANNEL_ID'] = str(channel.id)
                
                with open('config/config.json', 'w') as f:
                    json.dump(self.config, f, indent=4)
                    
                embed = create_embed(
                    title="✅ Канал для заявок установлен",
                    description=f"Канал {channel.mention} успешно установлен для получения заявок."
                )
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'", ephemeral=True)

    async def handle_modal_submit(self, interaction: discord.Interaction, modal, position: str):
        if 'APPLICATIONS_CHANNEL_ID' not in self.config:
            await interaction.response.send_message(
                "❌ Канал для заявок не настроен в конфиге!", 
                ephemeral=True
            )
            return

        channel_id = int(self.config['APPLICATIONS_CHANNEL_ID'])
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message(
                "❌ Канал для заявок не найден!", 
                ephemeral=True
            )
            return

        application_data = {
            "personal_info": modal.children[0].value,
            "motivation": modal.children[1].value,
            "availability": modal.children[2].value,
            "team_experience": modal.children[3].value,
            "position_experience": modal.children[4].value
        }

        embed = create_embed(
            title=f"📝 Новая заявка на должность {position}",
            description=f"{EMOJIS['DOT']} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                       f"{EMOJIS['DOT']} **Личная информация:**\n```\n{application_data['personal_info']}```\n"
                       f"{EMOJIS['DOT']} **Мотивация:**\n```\n{application_data['motivation']}```\n"
                       f"{EMOJIS['DOT']} **Доступность:**\n```\n{application_data['availability']}```\n"
                       f"{EMOJIS['DOT']} **Опыт работы в команде:**\n```\n{application_data['team_experience']}```\n"
                       f"{EMOJIS['DOT']} **Профессиональный опыт:**\n```\n{application_data['position_experience']}```",
            footer={"text": f"ID пользователя: {interaction.user.id}"}
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        view = ApplicationView(application_data, interaction.user.id, position)
        await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            "✅ Ваша заявка успешно отправлена! Ожидайте ответа от администрации.", 
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Forms(bot))