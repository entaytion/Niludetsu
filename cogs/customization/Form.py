import discord, re
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button, Select
from Niludetsu import Embed, Emojis
from Niludetsu.config import SERVERS, NOTIFICATION_CHANNEL_ID, SERVER_TEAM_ID, JUNIOR_MODERATOR_ID, MODER_TEAM_ID, PARTNER_MANAGER_ID, PM_TEAM_ID, EVENT_MANAGER_ID, EVENT_TEAM_ID

# Маппинг должностей на роли
POSITION_ROLES = {
    "helper": {
        "name": "Младший модератор",
        "emoji": Emojis.ICON_ROLE_MOD,
        "roles": [SERVER_TEAM_ID, JUNIOR_MODERATOR_ID, MODER_TEAM_ID]
    },
    "partner-manager": {
        "name": "Партнёр-менеджер",
        "emoji": Emojis.ICON_ROLE_PM,
        "roles": [SERVER_TEAM_ID, PARTNER_MANAGER_ID, PM_TEAM_ID]
    },
    "event-manager": {
        "name": "Ивент-менеджер",
        "emoji": Emojis.ICON_ROLE_EVENT,
        "roles": [SERVER_TEAM_ID, EVENT_MANAGER_ID, EVENT_TEAM_ID]
    }
}

class PositionSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Младший модератор",
                description="Поддержание порядка и помощь участникам",
                emoji=Emojis.ICON_ROLE_MOD, 
                value="helper"
            ),
            discord.SelectOption(
                label="Партнёр-менеджер",
                description="Продвижение и реклама сервера", 
                emoji=Emojis.ICON_ROLE_PM,
                value="partner-manager"
            ),
            discord.SelectOption(
                label="Ивент-менеджер",
                description="Организация и проведение мероприятий",
                emoji=Emojis.ICON_ROLE_EVENT,
                value="event-manager"
            ),
        ]
        super().__init__(
            placeholder="Выберите должность...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="position_select"
        )

    async def callback(self, interaction: discord.Interaction):
        form_cog = interaction.client.get_cog("Form")
        if form_cog:
            await form_cog.handle_position_select(interaction, self.values[0])

class FormButton(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Подать заявку", 
        style=discord.ButtonStyle.secondary, 
        emoji=Emojis.ICON_FORM, 
        custom_id="form_submit"
    )
    async def submit(self, interaction: discord.Interaction, button: Button):
        view = View(timeout=None)
        view.add_item(PositionSelect())
        await interaction.response.send_message("Выберите должность:", view=view, ephemeral=True)

class FormModal(Modal):
    def __init__(self, position: str):
        position_data = POSITION_ROLES.get(position, {})
        super().__init__(title=f"Заявка на должность {position_data.get('name', 'Unknown')}")
        self.position = position

        self.name_input = TextInput(
            label="Имя",
            placeholder="Ваше имя...",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )

        self.age_input = TextInput(
            label="Возраст",
            placeholder="Ваш возраст...",
            style=discord.TextStyle.short,
            required=True,
            max_length=3
        )

        self.experience_input = TextInput(
            label="Опыт",
            placeholder="Ваш опыт работы...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.about_input = TextInput(
            label="О себе",
            placeholder="Расскажите о себе...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(self.name_input)
        self.add_item(self.age_input)
        self.add_item(self.experience_input)
        self.add_item(self.about_input)

    async def on_submit(self, interaction: discord.Interaction):
        form_cog = interaction.client.get_cog("Form")
        if form_cog:
            await form_cog.handle_form_submit(
                interaction, 
                self.position,
                self.name_input.value,
                self.age_input.value,
                self.experience_input.value,
                self.about_input.value
            )

class FormActionsView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        form_cog = self.bot.get_cog("Form")
        if not form_cog:
            return False

        is_admin = form_cog.is_admin(interaction.user)
        if not is_admin:
            await interaction.response.send_message(
                embed=Embed.error(description="У вас нет прав для выполнения этого действия!"),
                ephemeral=True
            )
        return is_admin

    @discord.ui.button(
        label="Принять", 
        style=discord.ButtonStyle.secondary, 
        emoji=Emojis.SUCCESS, 
        custom_id="form_accept"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        form_cog = self.bot.get_cog("Form")
        if form_cog:
            await form_cog.handle_form_review(interaction, "accept")

    @discord.ui.button(
        label="Отклонить", 
        style=discord.ButtonStyle.secondary, 
        emoji=Emojis.ERROR, 
        custom_id="form_reject"
    )
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        form_cog = self.bot.get_cog("Form")
        if form_cog:
            await form_cog.handle_form_review(interaction, "reject")

class Form(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(FormButton(bot))
        self.bot.add_view(FormActionsView(bot))

    def is_admin(self, member: discord.Member) -> bool:
        """Проверяет, является ли пользователь администратором."""
        return member.guild_permissions.administrator

    async def handle_position_select(self, interaction: discord.Interaction, position: str):
        """Обрабатывает выбор должности"""
        modal = FormModal(position)
        await interaction.response.send_modal(modal)

    async def send_form(self, interaction, position, name, age, experience, about):
        """Отправляет заявку в канал уведомлений"""
        notification_channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not notification_channel:
            print(f"Канал уведомлений {NOTIFICATION_CHANNEL_ID} не найден!")
            return

        position_data = POSITION_ROLES.get(position, {})
        pos_name = position_data.get("name", "Неизвестная должность")
        pos_emoji = position_data.get("emoji", "")

        embed = Embed.default(
            title=f"{pos_emoji} Новая анкета на должность {pos_name}",
            description=f"Заявка от пользователя {interaction.user.mention} ({interaction.user.id})"
        )
        embed.add_field(
            name=f"> {Emojis.NAME} Имя",
            value=f"``{name}``",
            inline=True
        )
        embed.add_field(
            name=f"> {Emojis.AGE} Возраст",
            value=f"``{age}``",
            inline=True
        )
        embed.add_field(
            name=f"> {Emojis.EXP} Опыт",
            value=f"``{experience}``",
            inline=False
        )
        embed.add_field(
            name=f"> {Emojis.CHAT} О себе",
            value=f"``{about}``",
            inline=False
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await notification_channel.send(embed=embed, view=FormActionsView(self.bot))

    async def handle_form_submit(
        self, 
        interaction: discord.Interaction, 
        position: str,
        name: str,
        age: str,
        experience: str,
        about: str
    ):
        """Обрабатывает отправку анкеты"""
        # Проверяем валидность должности
        if position not in POSITION_ROLES:
            return await interaction.response.send_message(
                embed=Embed.error(description="Неизвестная должность!"),
                ephemeral=True
            )

        # Отправляем сообщение об успешной отправке
        await interaction.response.send_message(
            embed=Embed.success(
                title=f"Успешно",
                description="Ваша анкета успешно отправлена на рассмотрение!"
            ),
            ephemeral=True
        )

        # Отправляем анкету в канал уведомлений
        await self.send_form(interaction, position, name, age, experience, about)

    async def handle_form_review(self, interaction: discord.Interaction, action: str):
        """Обрабатывает рассмотрение заявки"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Проверяем, что команда выполняется на основном сервере
            if interaction.guild_id != SERVERS["MAIN_ID"]:
                raise ValueError("Команда доступна только на основном сервере.")

            embed = interaction.message.embeds[0]
            description = embed.description
            title = embed.title

            # Извлекаем ID пользователя
            user_id_match = re.search(r'\((\d+)\)', description)
            if not user_id_match:
                raise ValueError("Не удалось извлечь ID пользователя из анкеты.")
            user_id = int(user_id_match.group(1))

            # Определяем должность из заголовка
            position = None
            for pos_key, pos_data in POSITION_ROLES.items():
                if pos_data["name"] in title:
                    position = pos_key
                    break

            if not position:
                raise ValueError("Не удалось определить должность из анкеты.")

            # Получаем пользователя
            user = interaction.guild.get_member(user_id)
            if not user:
                raise ValueError("Пользователь не найден на сервере.")

            position_data = POSITION_ROLES[position]
            pos_name = position_data["name"]
            role_ids = position_data["roles"]

            if action == "accept":
                # Получаем объекты ролей
                roles_to_add = []
                for role_id in role_ids:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        roles_to_add.append(role)
                    else:
                        print(f"Роль с ID {role_id} не найдена!")

                if not roles_to_add:
                    raise ValueError("Не удалось найти ни одной роли для выдачи.")

                # Выдаем роли
                await user.add_roles(
                    *roles_to_add, 
                    reason=f"Принятие заявки модератором {interaction.user}"
                )

                # Отправляем сообщение пользователю
                await user.send(embed=Embed.success(
                    title=f"Заявка принята",
                    description=f"Поздравляем! Ваша заявка на должность **{pos_name}** была одобрена."
                ))
            else:  # reject
                await user.send(embed=Embed.error(
                    title=f"Заявка отклонена",
                    description=f"К сожалению, ваша заявка на должность **{pos_name}** была отклонена."
                ))

            # Обновляем embed с результатом
            message = interaction.message
            new_embed = message.embeds[0].copy()
            new_embed.add_field(
                name="> Результат",
                value=f"- **{'Принята' if action == 'accept' else 'Отклонена'}** администратором {interaction.user.mention}",
                inline=False
            )

            await message.edit(embed=new_embed, view=None)

        except (ValueError, discord.HTTPException) as e:
            await interaction.followup.send(
                embed=Embed.error(description=f"Ошибка при обработке анкеты: {e}")
            )

async def setup(bot):
    """Инициализация кога"""
    await bot.add_cog(Form(bot))

