import discord
from discord import app_commands
from discord.app_commands import MissingPermissions
from discord.ext import commands
from Niludetsu import Embed, Colors, config, Time
from Niludetsu.database import database

_time = Time()

_ADMIN_PANEL_IMAGE_URL = "https://c.tenor.com/sls2zgBMCf4AAAAd/tenor.gif"
_ADMIN_PANEL_DESCRIPTION = (
    "Добро пожаловать в панель управления участниками!\n"
    "Выберите пользователя для просмотра и редактирования."
)
_FIELD_NAMES = {
    'balance': '💰 Основной баланс',
    'deposit': '🏦 Банк',
    'spousal_balance': '💑 Семейный баланс',
    'level': '⭐ Уровень',
    'experience': '✨ Опыт (XP)'
}


def _build_admin_panel_embed():
    embed = Embed(
        title="Админ-панель",
        description=_ADMIN_PANEL_DESCRIPTION,
        color=Colors.PRIMARY
    )
    embed.set_image(url=_ADMIN_PANEL_IMAGE_URL)
    return embed


def _parse_user_ref(value):
    value = value.strip()
    if value.isdigit():
        return int(value)
    if value.startswith('<@') and value.endswith('>'):
        cleaned_value = value.replace('<@!', '').replace('<@', '').replace('>', '')
        if cleaned_value.isdigit():
            return int(cleaned_value)
    return None


def _collect_changed_value(raw_value, old_row, old_key, new_key, changes):
    if not raw_value:
        return None

    new_value = int(raw_value)
    old_value = (old_row.get(old_key) or 0) if old_row else 0
    if new_value == old_value:
        return None

    changes[new_key] = (old_value, new_value)
    return new_value


def _build_user_panel_embed(user, profile, economy):
    embed = Embed(
        title=f"Пользователь: {user.display_name}",
        color=Colors.PRIMARY
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    if profile:
        embed.add_field(name="> Уровень:", value=f"```{profile.get('level', 1)}```", inline=True)
        embed.add_field(name="> XP:", value=f"```{profile.get('experience', 0)}```", inline=False)

    if economy:
        balance = economy.get('balance') or 0
        deposit = economy.get('deposit') or 0
        spousal = economy.get('spousal_balance') or 0

        embed.add_field(name="> Основной:", value=f"```{balance}```", inline=True)
        embed.add_field(name="> Банк:", value=f"```{deposit}```", inline=True)
        if spousal > 0:
            embed.add_field(name="> Семейный:", value=f"```{spousal}```", inline=True)

    return embed


def _collect_economy_updates(modal, old_economy, changes):
    updates = {}

    balance = _collect_changed_value(modal.money.value, old_economy, 'balance', 'balance', changes)
    if balance is not None:
        updates['balance'] = balance

    deposit = _collect_changed_value(modal.deposit.value, old_economy, 'deposit', 'deposit', changes)
    if deposit is not None:
        updates['deposit'] = deposit

    spousal_balance = _collect_changed_value(
        modal.love_deposit.value,
        old_economy,
        'spousal_balance',
        'spousal_balance',
        changes
    )
    if spousal_balance is not None:
        updates['spousal_balance'] = spousal_balance

    return updates


def _collect_profile_updates(modal, profile, changes):
    if not (modal.level.value or modal.xp.value):
        return None

    old_level = (profile.get('level') or 1) if profile else 1
    old_xp = (profile.get('experience') or 0) if profile else 0

    experience = int(modal.xp.value) if modal.xp.value else old_xp
    level = int(modal.level.value) if modal.level.value else old_level

    if modal.xp.value:
        while experience >= 5 * (level ** 2) + 50 * level + 100:
            experience -= 5 * (level ** 2) + 50 * level + 100
            level += 1

    if level != old_level:
        changes['level'] = (old_level, level)
    if experience != old_xp:
        changes['experience'] = (old_xp, experience)

    return {
        'experience': experience,
        'level': level,
        'updated_at': _time.now()
    }

class AdminPanelView(discord.ui.View):
    def __init__(self, bot, members, author):
        super().__init__(timeout=120)
        self.bot = bot
        self.members = members
        self.author = author
        self.add_item(UserSelectMenu())
        self.add_item(UserInputButton())

class UserSelectMenu(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Выберите пользователя", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.guild.get_member(int(self.values[0].id))
        if not user:
            await interaction.response.send_message("Пользователь не найден.", ephemeral=True)
            return
        await PanelCog.show_user_panel(interaction, user.id)

class UserInputButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ввести пользователя вручную", style=discord.ButtonStyle.secondary, custom_id="manual_user_input")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UserInputModal())

class UserInputModal(discord.ui.Modal, title="Ввод пользователя"):
    user_input = discord.ui.TextInput(label="ID или упоминание пользователя", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = _parse_user_ref(self.user_input.value)
        if not user_id:
            await interaction.response.send_message("Пользователь не найден. Введите корректный ID или упоминание.", ephemeral=True)
            return
        user = interaction.guild.get_member(user_id)
        if not user:
            await interaction.response.send_message("Пользователь не найден на сервере.", ephemeral=True)
            return
        await PanelCog.show_user_panel(interaction, user_id)

class UserPanelView(discord.ui.View):
    def __init__(self, bot, user, author, user_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.author = author
        self.user_id = user_id
        self.add_item(EditButton(user_id))
        self.add_item(BackButton())

class EditButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label="Редактировать данные", style=discord.ButtonStyle.primary, custom_id="edit_data")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await PanelCog.show_edit_modal(interaction, self.user_id)

class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Назад", style=discord.ButtonStyle.secondary, custom_id="back")

    async def callback(self, interaction: discord.Interaction):
        await PanelCog.show_main_panel(interaction)

class EditUserModal(discord.ui.Modal, title="Редактировать пользователя"):
    money = discord.ui.TextInput(label="Основной баланс", style=discord.TextStyle.short, required=False)
    deposit = discord.ui.TextInput(label="Банк (депозит)", style=discord.TextStyle.short, required=False)
    love_deposit = discord.ui.TextInput(label="Семейный баланс", style=discord.TextStyle.short, required=False)
    level = discord.ui.TextInput(label="Уровень", style=discord.TextStyle.short, required=False)
    xp = discord.ui.TextInput(label="XP", style=discord.TextStyle.short, required=False)

    def __init__(self, economy_data, profile_data, user_id):
        super().__init__()
        self.economy_data = economy_data
        self.profile_data = profile_data
        self.user_id = user_id

        # Данные из user_economy
        self.money.default = str((economy_data.get('balance') or 0) if economy_data else 0)
        self.deposit.default = str((economy_data.get('deposit') or 0) if economy_data else 0)
        self.love_deposit.default = str((economy_data.get('spousal_balance') or 0) if economy_data else 0)

        # Данные из user_profile (level и experience)
        self.level.default = str(profile_data.get('level', 1) if profile_data else 1)
        self.xp.default = str(profile_data.get('experience', 0) if profile_data else 0)

    async def on_submit(self, interaction: discord.Interaction):
        await PanelCog.save_user_edit(interaction, self, self.user_id)

class PanelCog(commands.Cog, name="Панель администратора"):
    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.level_system = getattr(bot, "level_system", None)

    @app_commands.command(name="apanel", description="То что тебе про это рано знать...")
    @app_commands.checks.has_permissions(administrator=True)
    async def apanel(self, interaction: discord.Interaction):
        members = [m for m in interaction.guild.members if not m.bot]
        await interaction.response.send_message(
            embed=_build_admin_panel_embed(),
            view=AdminPanelView(self.bot, members, interaction.user),
            ephemeral=True
        )

    @apanel.error
    async def apanel_error(self, interaction: discord.Interaction, error):
        if isinstance(error, MissingPermissions):
            embed = Embed.error(description="Не")
            embed.set_image(url="https://c.tenor.com/Om3_U2YnLZIAAAAd/tenor.gif")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error

    @staticmethod
    async def show_main_panel(interaction):
        members = [m for m in interaction.guild.members if not m.bot]
        await interaction.response.edit_message(
            embed=_build_admin_panel_embed(),
            view=AdminPanelView(interaction.client, members, interaction.user)
        )

    @staticmethod
    async def show_user_panel(interaction, user_id):
        user = interaction.guild.get_member(user_id)
        guild_id = str(interaction.guild.id)
        user_id_str = str(user_id)

        bundle = await database.get_user(user_id_str, guild_id)
        economy = bundle.get("economy") or {}
        profile = bundle.get("profile") or {}

        await interaction.response.edit_message(
            embed=_build_user_panel_embed(user, profile, economy),
            view=UserPanelView(interaction.client, user, interaction.user, user_id)
        )

    @staticmethod
    async def show_edit_modal(interaction, user_id):
        guild_id = str(interaction.guild.id)
        user_id_str = str(user_id)

        bundle = await database.get_user(user_id_str, guild_id)
        economy = bundle.get("economy") or {}
        profile = bundle.get("profile") or {}

        await interaction.response.send_modal(EditUserModal(economy, profile, user_id))

    @staticmethod
    async def save_user_edit(interaction, modal, user_id):
        guild_id = str(interaction.guild.id)
        user_id_str = str(user_id)

        try:
            edit_context = await PanelCog._prepare_user_edit_context(
                guild_id,
                user_id_str
            )

            await PanelCog._save_economy_updates(guild_id, user_id_str, modal, edit_context)
            await PanelCog._save_profile_updates(guild_id, user_id_str, modal, edit_context)

            if edit_context["changes"]:
                await PanelCog.log_change(
                    interaction.client,
                    interaction.user,
                    user_id,
                    edit_context["changes"],
                    guild_id
                )

            await interaction.response.send_message("✅ Данные пользователя успешно обновлены!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при сохранении: {e}", ephemeral=True)

    @staticmethod
    async def _prepare_user_edit_context(guild_id, user_id_str):
        return {
            "changes": {},
            "old_economy": await database.get_row("user_economy", user_id=user_id_str, guild_id=guild_id),
            "old_profile": await database.get_row("user_profile", user_id=user_id_str, guild_id=guild_id)
        }

    @staticmethod
    async def _save_economy_updates(guild_id, user_id_str, modal, edit_context):
        changes = edit_context["changes"]
        economy_updates = _collect_economy_updates(modal, edit_context["old_economy"], changes)
        if not economy_updates:
            return

        await database.update_record(
            "user_economy",
            where={"user_id": user_id_str, "guild_id": guild_id},
            values=economy_updates,
            ensure_if_missing=True,
            ensure_params={"user_id": user_id_str, "guild_id": guild_id}
        )

        if 'spousal_balance' in economy_updates:
            await PanelCog._sync_spousal_balance(guild_id, user_id_str, economy_updates['spousal_balance'])

    @staticmethod
    async def _sync_spousal_balance(guild_id, user_id_str, spousal_balance):
        marriage = await database.get_active_marriage(guild_id, user_id_str)
        if not marriage:
            return

        partner_id = await database.get_marriage_partner(marriage, user_id_str)
        await database.update_record(
            "user_economy",
            where={"user_id": partner_id, "guild_id": guild_id},
            values={"spousal_balance": spousal_balance},
            ensure_if_missing=True,
            ensure_params={"user_id": partner_id, "guild_id": guild_id}
        )

    @staticmethod
    async def _save_profile_updates(guild_id, user_id_str, modal, edit_context):
        profile_updates = _collect_profile_updates(modal, edit_context["old_profile"], edit_context["changes"])
        if not profile_updates:
            return

        await database.update_record(
            "user_profile",
            where={"user_id": user_id_str, "guild_id": guild_id},
            values=profile_updates,
            ensure_if_missing=True,
            ensure_params={"user_id": user_id_str, "guild_id": guild_id}
        )

    @staticmethod
    async def log_change(bot, moderator, user_id, changes, guild_id):
        """Логирование изменений в админ-панели с отображением старых → новых значений"""
        if not hasattr(config, 'NOTIFICATION_CHANNEL_ID'):
            return

        notification = bot.get_channel(config.NOTIFICATION_CHANNEL_ID)
        if not notification:
            return

        if not changes:
            return

        user_mention = f"<@{user_id}>"
        embed = Embed.info(
            title="Изменение данных пользователя через /apanel",
            description=f"**Модератор:** {moderator.mention}\n**Пользователь:** {user_mention}",
        )

        # Добавляем поля с изменениями
        for field, (old_val, new_val) in changes.items():
            field_name = _FIELD_NAMES.get(field, field.capitalize())
            embed.add_field(
                name=field_name,
                value=f"```{old_val:,} → {new_val:,}```",
                inline=True
            )

        await notification.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PanelCog(bot))

