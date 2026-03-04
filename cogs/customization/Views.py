import discord
from discord.ui import View, Select
from typing import Optional, Dict, Any
from Niludetsu import Emojis, Embed
from Niludetsu.config import GENDER_ROLES, COLOR_ROLES, OPTIONAL_ROLES, SERVERS
from Niludetsu.database.supabase_database import SupabaseDatabase

class ProfileView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProfileButton(
            label="Цвет роли",
            emoji=Emojis.ICON_PALETTE,
            custom_id="profile_color"
        ))
        self.add_item(ProfileButton(
            label="Гендерная роль",
            emoji=Emojis.ICON_GENDER,
            custom_id="profile_gender"
        ))
        self.add_item(ProfileButton(
            label="Опциональные роли",
            emoji=Emojis.ICON_NEWS,
            custom_id="profile_optional_roles"
        ))
        self.add_item(ProfileButton(
            label="Роль бустера",
            emoji=Emojis.ICON_BOOSTER,
            custom_id="profile_booster_role"
        ))

class ProfileButton(discord.ui.Button):
    def __init__(self, label, emoji, custom_id):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            emoji=emoji,
            custom_id=custom_id
        )

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == "profile_color":
            if COLOR_ROLES:
                await interaction.response.send_message(
                    content="Выберите цвет роли:",
                    view=ColorSelectView(COLOR_ROLES),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="Цветные роли не настроены. Обратитесь к администрации.",
                    ephemeral=True
                )

        elif self.custom_id == "profile_gender":
            if GENDER_ROLES:
                await interaction.response.send_message(
                    content="Выберите пол:",
                    view=GenderSelectView(GENDER_ROLES),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="Гендерные роли не настроены. Обратитесь к администрации.",
                    ephemeral=True
                )

        elif self.custom_id == "profile_optional_roles":
            await interaction.response.send_message(
                embed=Embed.default(
                    title="Опциональные роли",
                    description="Выберите роли, которые хотите ОТКЛЮЧИТЬ. Отмеченные роли будут сняты; снятие отменится, если убрать отметку. По умолчанию роли выдаются всем."
                ),
                view=OptionalRolesMultiSelect(interaction.user),
                ephemeral=True
            )

        elif self.custom_id == "profile_booster_role":
            await show_booster_panel(interaction)

# MultiSelect для опциональных ролей
class OptionalRolesMultiSelect(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.add_item(OptionalRolesSelect(user))

class OptionalRolesSelect(discord.ui.Select):
    def __init__(self, user):
        options = [
            discord.SelectOption(
                label=role["name"],
                value=str(role["id"]),
                description=role.get("description", ""),
                emoji=role.get("emoji")
            )
            for role in OPTIONAL_ROLES
        ]
        super().__init__(
            placeholder="Выберите роли...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id="optional_roles_select"
        )
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        added = []
        removed = []

        for option in self.options:
            role = interaction.guild.get_role(int(option.value))
            if not role:
                continue

            if option.value in self.values:
                # Выбранные роли — отключить (снять)
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role, reason="Пользователь отключил роль через меню профиля")
                    removed.append(role.mention)
            else:
                # Неотмеченные роли — включить (выдать)
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Пользователь включил роль через меню профиля")
                    added.append(role.mention)

        msg = ""
        if removed:
            msg += f"Отключены роли: {', '.join(removed)}\n"
        if added:
            msg += f"Включены роли: {', '.join(added)}"
        if not msg:
            msg = "Изменений нет."

        await interaction.response.send_message(msg, ephemeral=True)

class ColorSelectView(View):
    def __init__(self, color_roles: list):
        super().__init__(timeout=60)
        self.color_roles = color_roles

        # Создаем селект-меню с ролями
        select = discord.ui.Select(
            custom_id="color_select",
            placeholder="Выберите цвет роли",
            min_values=0,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Убрать цветную роль",
                    value="remove",
                    description="Вернуть стандартный цвет",
                    emoji="🗑️"
                )
            ] + [
                discord.SelectOption(
                    label=role["name"],
                    value=str(role["id"]),
                    emoji=role.get("emoji"),
                    default=False
                )
                for role in color_roles if role.get("emoji") and role.get("id")
            ]
        )
        select.callback = self.color_callback
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Устанавливаем текущую роль как выбранную по умолчанию
        select = self.children[0]
        current_role = None

        for option in select.options[1:]:  # Пропускаем опцию удаления
            role_id = int(option.value)
            has_role = any(role.id == role_id for role in interaction.user.roles)
            if has_role:
                current_role = option
                option.default = True
            else:
                option.default = False

        if current_role:
            select.placeholder = f"Текущий цвет: {current_role.label}"
        else:
            select.placeholder = "Стандартный цвет"

        return True

    async def color_callback(self, interaction: discord.Interaction):
        values = interaction.data.get("values", [])

        # Удаляем старые цветные роли
        removed_roles = []
        for member_role in interaction.user.roles:
            for color_role in self.color_roles:
                if member_role.id == color_role["id"]:
                    await interaction.user.remove_roles(member_role)
                    removed_roles.append(member_role.name)

        # Если был выбран новый цвет и это не опция удаления
        if values and values[0] != "remove":
            role_id = int(values[0])
            new_role = interaction.guild.get_role(role_id)
            if new_role:
                await interaction.user.add_roles(new_role)
                await interaction.response.send_message(
                    f"Вы успешно выбрали цвет {new_role.name}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена",
                    ephemeral=True
                )
        else:
            # Если выбрано удаление
            message = "Цветная роль была удалена"
            if removed_roles:
                message += f" ({', '.join(removed_roles)})"
            await interaction.response.send_message(
                message,
                ephemeral=True
            )

class GenderSelectView(View):
    def __init__(self, gender_roles: list):
        super().__init__(timeout=60)
        self.gender_roles = gender_roles

        # Создаем селект-меню с ролями
        select = discord.ui.Select(
            custom_id="gender_select",
            placeholder="Выберите пол",
            min_values=0,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Убрать гендерную роль",
                    value="remove",
                    description="Скрыть отображение пола",
                    emoji="🗑️"
                )
            ] + [
                discord.SelectOption(
                    label=role["name"],
                    value=str(role["id"]),
                    emoji=role.get("emoji"),
                    default=False
                )
                for role in gender_roles if role.get("emoji") and role.get("id")
            ]
        )
        select.callback = self.gender_callback
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Устанавливаем текущую роль как выбранную по умолчанию
        select = self.children[0]
        current_role = None

        for option in select.options[1:]:  # Пропускаем опцию удаления
            role_id = int(option.value)
            has_role = any(role.id == role_id for role in interaction.user.roles)
            if has_role:
                current_role = option
                option.default = True
            else:
                option.default = False

        if current_role:
            select.placeholder = f"Текущий пол: {current_role.label}"
        else:
            select.placeholder = "Пол не выбран"

        return True

    async def gender_callback(self, interaction: discord.Interaction):
        values = interaction.data.get("values", [])

        # Удаляем старые гендерные роли
        removed_roles = []
        for member_role in interaction.user.roles:
            for gender_role in self.gender_roles:
                if member_role.id == gender_role["id"]:
                    await interaction.user.remove_roles(member_role)
                    removed_roles.append(member_role.name)

        # Если был выбран новый пол и это не опция удаления
        if values and values[0] != "remove":
            role_id = int(values[0])
            new_role = interaction.guild.get_role(role_id)
            if new_role:
                await interaction.user.add_roles(new_role)
                await interaction.response.send_message(
                    f"Вы успешно выбрали роль {new_role.name}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена",
                    ephemeral=True
                )
        else:
            # Если выбрано удаление
            message = "Гендерная роль была удалена"
            if removed_roles:
                message += f" ({', '.join(removed_roles)})"
            await interaction.response.send_message(
                message,
                ephemeral=True
            )

async def show_booster_panel(interaction: discord.Interaction) -> None:
    """Показывает панель управления бустерской ролью"""
    
    db: SupabaseDatabase = interaction.client.db
    main_server_id = SERVERS["MAIN_ID"]
    
    # Проверяем, бустит ли пользователь сервер
    member = interaction.user
    guild = interaction.guild
    
    if not guild or guild.id != main_server_id:
        await interaction.response.send_message(
            embed=Embed.error(description="Эта функция доступна только на основном сервере"),
            ephemeral=True
        )
        return
    
    # Проверяем, является ли пользователь создателем сервера или бустером
    is_owner = member.id == guild.owner_id
    is_booster = member.premium_since is not None
    
    if not is_owner and not is_booster:
        await interaction.response.send_message(
            embed=Embed.error(
                description="Вы должны быть создателем сервера или бустером, чтобы использовать эту функцию"
            ),
            ephemeral=True
        )
        return
    
    # Получаем информацию о текущей бустерской роли
    booster_item = await get_booster_role_item(db, str(member.id), str(guild.id))
    
    # Создаём embed
    embed = Embed.default(
        title=f"{Emojis.ICON_BOOSTER} Роль бустера",
        description="Приятно осознавать, что **вы поддерживаете сервер**. Теперь у вас есть возможность **создать свою бустерскую роль!** ``🎉``",
        image="https://entaytion.vercel.app/ae/aeBooster.jpg"
    )
    
    # Создаём view с кнопками
    view = BoosterRoleView(db, member, guild, booster_item)
    
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True
    )


async def get_booster_role_item(db: SupabaseDatabase, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
    """Получает запись о бустерской роли из инвентаря"""
    try:
        items = await db.fetch_inventory_items(user_id, guild_id)
        for item in items:
            if item.get("item_type") == "booster_role":
                return item
    except Exception as e:
        print(f"[BoosterRole] Ошибка получения бустерской роли: {e}")
    return None


async def create_booster_role(db: SupabaseDatabase, member: discord.Member, guild: discord.Guild) -> Optional[discord.Role]:
    """Создаёт новую бустерскую роль"""
    try:
        # Проверяем, есть ли уже бустерская роль
        existing_item = await get_booster_role_item(db, str(member.id), str(guild.id))
        if existing_item:
            return None
        
        # Создаём роль с золотым цветом
        role = await guild.create_role(
            name=f"⭐ {member.name}",
            color=discord.Color.gold(),
            reason=f"Бустерская роль для {member.name}"
        )
        
        # Выдаём роль пользователю
        await member.add_roles(role, reason="Выдача бустерской роли")
        
        # Сохраняем в инвентарь
        await db.ensure_inventory_item(
            user_id=str(member.id),
            guild_id=str(guild.id),
            item_key=f"booster_role_{role.id}",
            item_type="booster_role",
            meta={
                "role_id": str(role.id),
                "role_name": role.name,
                "role_color": str(role.color),
                "created_by": str(member.id),
            }
        )
        
        return role
    except Exception as e:
        print(f"[BoosterRole] Ошибка создания бустерской роли: {e}")
        return None


async def update_booster_role(
    db: SupabaseDatabase,
    member: discord.Member,
    guild: discord.Guild,
    booster_item: Dict[str, Any],
    name: Optional[str] = None,
    color: Optional[discord.Color] = None
) -> bool:
    """Обновляет бустерскую роль"""
    try:
        role_id = int(booster_item.get("meta", {}).get("role_id"))
        role = guild.get_role(role_id)
        
        if not role:
            return False
        
        # Обновляем название
        if name:
            await role.edit(name=name, reason=f"Обновление бустерской роли {member.name}")
        
        # Обновляем цвет
        if color:
            await role.edit(color=color, reason=f"Обновление бустерской роли {member.name}")
        
        # Обновляем метаданные в инвентаре
        meta = booster_item.get("meta", {})
        if name:
            meta["role_name"] = name
        if color:
            meta["role_color"] = str(color)
        
        db.client.table("user_inventory").update({
            "meta": meta
        }).eq("id", booster_item["id"]).execute()
        
        return True
    except Exception as e:
        print(f"[BoosterRole] Ошибка обновления бустерской роли: {e}")
        return False


async def delete_booster_role(db: SupabaseDatabase, member: discord.Member, guild: discord.Guild, booster_item: Dict[str, Any]) -> bool:
    """Удаляет бустерскую роль"""
    try:
        role_id = int(booster_item.get("meta", {}).get("role_id"))
        role = guild.get_role(role_id)
        
        if role:
            await role.delete(reason=f"Удаление бустерской роли {member.name}")
        
        # Удаляем из инвентаря
        await db.delete_inventory_item(
            user_id=str(member.id),
            guild_id=str(guild.id),
            item_key=booster_item["item_key"]
        )
        
        return True
    except Exception as e:
        print(f"[BoosterRole] Ошибка удаления бустерской роли: {e}")
        return False


class BoosterRoleView(discord.ui.View):
    """View с кнопками управления бустерской ролью"""
    
    def __init__(self, db: SupabaseDatabase, member: discord.Member, guild: discord.Guild, booster_item: Optional[Dict[str, Any]]):
        super().__init__(timeout=300)
        self.db = db
        self.member = member
        self.guild = guild
        self.booster_item = booster_item
    
    @discord.ui.button(label="Создать роль", emoji=Emojis.SUCCESS, style=discord.ButtonStyle.success)
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                embed=Embed.error(description="Это не твоя панель"),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Проверяем наличие роли перед созданием
        booster_item = await get_booster_role_item(self.db, str(self.member.id), str(self.guild.id))
        if booster_item:
            await interaction.followup.send(
                embed=Embed.error(description="У вас уже есть бустерская роль. Удалите её перед созданием новой."),
                ephemeral=True
            )
            return
        
        role = await create_booster_role(self.db, self.member, self.guild)
        
        if role:
            await interaction.followup.send(
                embed=Embed.success(
                    description=f"Бустерская роль **{role.name}** успешно создана!"
                ),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=Embed.error(description="Ошибка при создании роли. Проверьте логи."),
                ephemeral=True
            )
    
    @discord.ui.button(label="Изменить роль", emoji=Emojis.WARNING, style=discord.ButtonStyle.secondary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                embed=Embed.error(description="Это не твоя панель"),
                ephemeral=True
            )
            return
        
        # Обновляем booster_item перед редактированием (на случай если роль была создана)
        booster_item = await get_booster_role_item(self.db, str(self.member.id), str(self.guild.id))
        
        if not booster_item:
            await interaction.response.send_message(
                embed=Embed.error(description="У вас нет бустерской роли."),
                ephemeral=True
            )
            return
        
        # Проверяем, существует ли роль на сервере
        role_id = int(booster_item.get("meta", {}).get("role_id"))
        role = self.guild.get_role(role_id)
        
        if not role:
            await interaction.response.send_message(
                embed=Embed.error(description="Красава, додумался блядь редактировать роль, которой нету."),
                ephemeral=True
            )
            return
        
        # Показываем модальное окно для редактирования
        modal = EditBoosterRoleModal(self.db, self.member, self.guild, booster_item)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Удалить роль", emoji=Emojis.ERROR, style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                embed=Embed.error(description="Это не твоя панель"),
                ephemeral=True
            )
            return
        
        # Обновляем booster_item перед удалением (на случай если роль была создана)
        booster_item = await get_booster_role_item(self.db, str(self.member.id), str(self.guild.id))
        
        if not booster_item:
            await interaction.response.send_message(
                embed=Embed.error(description="У вас нет бустерской роли."),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        success = await delete_booster_role(self.db, self.member, self.guild, booster_item)
        
        if success:
            await interaction.followup.send(
                embed=Embed.success(description="Бустерская роль успешно удалена!"),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=Embed.error(description="Ошибка при удалении роли"),
                ephemeral=True
            )


class EditBoosterRoleModal(discord.ui.Modal):
    """Модальное окно для редактирования бустерской роли"""
    
    def __init__(self, db: SupabaseDatabase, member: discord.Member, guild: discord.Guild, booster_item: Dict[str, Any]):
        super().__init__(title="Редактирование бустерской роли", timeout=300)
        self.db = db
        self.member = member
        self.guild = guild
        self.booster_item = booster_item
        
        # Получаем текущее название
        current_name = booster_item.get("meta", {}).get("role_name", "")
        
        # Добавляем поле для названия
        self.name_input = discord.ui.TextInput(
            label="Название роли",
            placeholder="Введите новое название",
            default=current_name,
            max_length=100,
            required=True
        )
        self.add_item(self.name_input)
        
        # Добавляем поле для цвета (HEX)
        self.color_input = discord.ui.TextInput(
            label="Цвет роли (HEX, например: FFD700)",
            placeholder="FFD700",
            default=booster_item.get("meta", {}).get("role_color", "FFD700").lstrip("#"),
            max_length=6,
            required=False
        )
        self.add_item(self.color_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Парсим цвет
            color = None
            if self.color_input.value:
                try:
                    color = discord.Color(int(self.color_input.value, 16))
                except ValueError:
                    await interaction.followup.send(
                        embed=Embed.error(description="Неверный формат цвета. Используйте HEX (например: FFD700)"),
                        ephemeral=True
                    )
                    return
            
            # Обновляем роль
            success = await update_booster_role(
                self.db,
                self.member,
                self.guild,
                self.booster_item,
                name=self.name_input.value if self.name_input.value else None,
                color=color
            )
            
            if success:
                await interaction.followup.send(
                    embed=Embed.success(description="Бустерская роль успешно обновлена!"),
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    embed=Embed.error(description="Ошибка при обновлении роли"),
                    ephemeral=True
                )
        except Exception as e:
            print(f"[BoosterRole] Ошибка в модальном окне: {e}")
            await interaction.followup.send(
                embed=Embed.error(description="Произошла ошибка"),
                ephemeral=True
            )

async def setup(bot):
    bot.add_view(ProfileView())