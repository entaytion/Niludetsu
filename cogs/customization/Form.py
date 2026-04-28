import discord, re
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button, Select
from Niludetsu import Embed, Emojis, config

FORM_VIEWS_FLAG = "_form_views_registered"

# Маппинг должностей на роли
POSITION_ROLES = {
    "helper": {
        "name": "Младший модератор",
        "emoji": Emojis.ICON_ROLE_MOD,
        "roles": [config.SERVER_TEAM_ID, config.JUNIOR_MODERATOR_ID, config.MODER_TEAM_ID]
    },
    "partner-manager": {
        "name": "Партнёр-менеджер",
        "emoji": Emojis.ICON_ROLE_PM,
        "roles": [config.SERVER_TEAM_ID, config.PARTNER_MANAGER_ID, config.PM_TEAM_ID]
    },
    "event-manager": {
        "name": "Ивент-менеджер",
        "emoji": Emojis.ICON_ROLE_EVENT,
        "roles": [config.SERVER_TEAM_ID, config.EVENT_MANAGER_ID, config.EVENT_TEAM_ID]
    }
}

class PositionSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Младший модератор",
                description="Следить за порядком и не дать комнате развалиться",
                emoji=Emojis.ICON_ROLE_MOD, 
                value="helper"
            ),
            discord.SelectOption(
                label="Партнёр-менеджер",
                description="Таскать сервер наружу и договариваться с людьми", 
                emoji=Emojis.ICON_ROLE_PM,
                value="partner-manager"
            ),
            discord.SelectOption(
                label="Ивент-менеджер",
                description="Собирать движ и не дать ему умереть по дороге",
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
        await interaction.response.send_message(
            "Выбери, куда именно хочешь влезть.",
            view=view,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

class FormModal(Modal):
    def __init__(self, position: str):
        position_data = POSITION_ROLES.get(position, {})
        super().__init__(title=f"Анкета: {position_data.get('name', 'Unknown')}")
        self.position = position

        self.name_input = TextInput(
            label="Имя",
            placeholder="Как тебя называть в этой комнате?",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )

        self.age_input = TextInput(
            label="Возраст",
            placeholder="Сколько тебе лет?",
            style=discord.TextStyle.short,
            required=True,
            max_length=3
        )

        self.experience_input = TextInput(
            label="Опыт",
            placeholder="Что ты уже умеешь и где с этим сталкивался?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.about_input = TextInput(
            label="О себе",
            placeholder="Коротко расскажи, кто ты и почему мы должны пустить тебя глубже.",
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

    async def cog_load(self) -> None:
        if getattr(self.bot, FORM_VIEWS_FLAG, False):
            return

        self.bot.add_view(FormButton(self.bot))
        self.bot.add_view(FormActionsView(self.bot))
        setattr(self.bot, FORM_VIEWS_FLAG, True)

    def is_admin(self, member: discord.Member) -> bool:
        """Проверяет, является ли пользователь администратором."""
        return member.guild_permissions.administrator

    async def handle_position_select(self, interaction: discord.Interaction, position: str):
        """Обрабатывает выбор должности"""
        modal = FormModal(position)
        await interaction.response.send_modal(modal)

    async def send_form(self, interaction, position, name, age, experience, about):
        """Отправляет заявку в канал уведомлений"""
        notification_channel = self.bot.get_channel(config.NOTIFICATION_CHANNEL_ID)
        if not notification_channel:
            print(f"Канал уведомлений {config.NOTIFICATION_CHANNEL_ID} не найден!")
            return

        position_data = POSITION_ROLES.get(position, {})
        pos_name = position_data.get("name", "Неизвестная должность")
        pos_emoji = position_data.get("emoji", "")

        embed = Embed.default(
            title=f"{pos_emoji} Новая анкета: {pos_name}",
            description=(
                f"Кандидат: **{discord.utils.escape_markdown(str(interaction.user))}**\n"
                f"ID: `{interaction.user.id}`"
            ),
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
        embed.set_footer(text="nullthe.re смотрит молча, но всё записывает.")
        await notification_channel.send(
            embed=embed,
            view=FormActionsView(self.bot),
            allowed_mentions=discord.AllowedMentions.none(),
        )

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
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # Отправляем сообщение об успешной отправке
        await interaction.response.send_message(
            embed=Embed.success(
                title="Анкета отправлена",
                description="Комната услышала тебя. Заявка ушла на рассмотрение."
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

        # Отправляем анкету в канал уведомлений
        await self.send_form(interaction, position, name, age, experience, about)

    async def handle_form_review(self, interaction: discord.Interaction, action: str):
        """Обрабатывает рассмотрение заявки"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Проверяем, что команда выполняется на основном сервере
            if interaction.guild_id != config.SERVERS["MAIN_ID"]:
                raise ValueError("Команда доступна только на основном сервере.")

            embed = interaction.message.embeds[0]
            description = embed.description or ""
            title = embed.title

            # Извлекаем ID пользователя
            user_id_match = (
                re.search(r'\((\d+)\)', description)
                or re.search(r'ID:\s*`?(\d+)`?', description)
            )
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
                    title="Заявка принята",
                    description=(
                        f"Твоя заявка на должность **{pos_name}** одобрена.\n"
                        "Похоже, дверь действительно открылась."
                    ),
                ))
            else:  # reject
                await user.send(embed=Embed.error(
                    title="Заявка отклонена",
                    description=(
                        f"Заявка на должность **{pos_name}** отклонена.\n"
                        "Не конец света. Просто эта дверь сегодня не твоя."
                    ),
                ))

            # Обновляем embed с результатом
            message = interaction.message
            new_embed = message.embeds[0].copy()
            new_embed.add_field(
                name="> Результат",
                value=(
                    f"- **{'Принята' if action == 'accept' else 'Отклонена'}**\n"
                    f"- Решение: **{discord.utils.escape_markdown(str(interaction.user))}** (`{interaction.user.id}`)"
                ),
                inline=False
            )

            await message.edit(embed=new_embed, view=None)

        except (ValueError, discord.HTTPException) as e:
            await interaction.followup.send(
                embed=Embed.error(description=f"Ошибка при обработке анкеты: {e}"),
                allowed_mentions=discord.AllowedMentions.none(),
            )

async def setup(bot):
    """Инициализация кога"""
    await bot.add_cog(Form(bot))

