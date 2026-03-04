import discord, random
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis
from Niludetsu.database.supabase_database import database
from Niludetsu.inventory.manager import InventoryManager

INVENTORY_TIMEOUT = 180

class InventoryView(discord.ui.View):
    def __init__(self, *, user_id: str, guild_id: str, manager: InventoryManager, db):
        super().__init__(timeout=INVENTORY_TIMEOUT)
        self.user_id = user_id
        self.guild_id = guild_id
        self.manager = manager
        self.db = database

        self.add_item(PersonalRoleButton())
        self.add_item(OtherItemsButton())
        self.add_item(OpenEventboxButton())

    async def fetch_personal_role(self) -> discord.Embed:
        role = await self.manager.get_personal_role(self.user_id, self.guild_id)
        embed = Embed(
            title="🎭 Моя личная роль",
            color=Colors.PRIMARY,
            description="У тебя пока нет персональной роли.\nЗагляни в магазин, чтобы оформить её!",
        )
        if role:
            embed.description = role.get("description") or "Описание отсутствует, но выглядит солидно!"
            embed.add_field(name="Название", value=role.get("name", "Безымянная"), inline=True)
            embed.add_field(
                name="Стоимость",
                value=f"**``{role.get('price', 0):,}``** {Emojis.MONEY}",
                inline=True,
            )
        return embed

    async def fetch_other_items(self) -> discord.Embed:
        items = await self.manager.get_items(self.user_id, self.guild_id)
        non_role = [item for item in items if item["item_type"] != "role"]

        # Подсчитываем ивентбоксы
        eventboxes = [item for item in non_role if item["item_type"] == "eventbox"]

        embed = Embed(
            title="🎒 Другие вещи",
            color=Colors.PRIMARY,
        )
        if not non_role:
            embed.description = "Полки пустуют. Самое время пополнить коллекцию!"
            return embed

        # Показываем ивентбоксы отдельно
        if eventboxes:
            embed.add_field(
                name="🎁 Тайные боксы",
                value=f"У вас **{len(eventboxes)}** тайных боксов.\nНажмите кнопку ниже, чтобы открыть один!",
                inline=False
            )

        # Показываем остальные предметы
        other_items = [item for item in non_role if item["item_type"] != "eventbox"]
        for item in other_items[:10]:
            meta = item.get("meta") or {}
            desc = meta.get("description") or "Описание отсутствует."
            embed.add_field(
                name=f"{meta.get('title', item['item_key']).capitalize()}",
                value=(
                    f"{desc}\n"
                    f"• Тип: `{item['item_type']}`\n"
                    f"• Цена покупки: **``{item.get('price_paid', 0):,}``** {Emojis.MONEY}\n"
                    f"• Получено: {item.get('acquired_at', 'неизвестно')}"
                ),
                inline=False,
            )
        if len(other_items) > 10:
            embed.set_footer(text=f"И ещё {len(other_items) - 10} предмет(-ов) вне предпросмотра.")
        return embed

class PersonalRoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Моя личная роль",
            style=discord.ButtonStyle.primary,
            emoji="🎭"
        )

    async def callback(self, interaction: discord.Interaction):
        view: InventoryView = self.view  # type: ignore
        if interaction.user.id != int(view.user_id):
            await interaction.response.send_message("Это не твой инвентарь 🙃", ephemeral=True)
            return
        embed = await view.fetch_personal_role()
        await interaction.response.edit_message(embed=embed, view=view)

class OtherItemsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Другие вещи",
            style=discord.ButtonStyle.secondary,
            emoji="🎒"
        )

    async def callback(self, interaction: discord.Interaction):
        view: InventoryView = self.view  # type: ignore
        if interaction.user.id != int(view.user_id):
            await interaction.response.send_message("Это не твой инвентарь 🙃", ephemeral=True)
            return
        embed = await view.fetch_other_items()
        await interaction.response.edit_message(embed=embed, view=view)

class OpenEventboxButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Открыть тайный бокс",
            style=discord.ButtonStyle.success,
            emoji="🎁"
        )

    async def callback(self, interaction: discord.Interaction):
        view: InventoryView = self.view  # type: ignore
        if interaction.user.id != int(view.user_id):
            await interaction.response.send_message("Это не твой инвентарь 🙃", ephemeral=True)
            return

        # Получаем все ивентбоксы пользователя
        items = await view.manager.get_items(view.user_id, view.guild_id)
        eventboxes = [item for item in items if item["item_type"] == "eventbox"]

        if not eventboxes:
            await interaction.response.send_message(f"{Emojis.ERROR} У вас нет тайных боксов!", ephemeral=True)
            return

        # Берём первый ивентбокс
        eventbox = eventboxes[0]

        # Создаём мини-игру 3x3
        game_view = EventboxGameView(
            user_id=view.user_id,
            guild_id=view.guild_id,
            eventbox_key=eventbox["item_key"],
            db=view.db
        )

        embed = Embed(
            title="🎁 Тайный бокс",
            color=Colors.PRIMARY,
            description="Выберите **3 ячейки** из сетки 3x3, чтобы открыть бокс и получить награду!\n\n"
                       "💰 Награда: **100-1000** монет"
        )

        await interaction.response.send_message(embed=embed, view=game_view, ephemeral=True)

class EventboxGameView(discord.ui.View):
    def __init__(self, user_id: str, guild_id: str, eventbox_key: str, db):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_id = guild_id
        self.eventbox_key = eventbox_key
        self.db = database
        self.selected_count = 0
        self.prize_amount = random.randint(100, 1000)

        # Создаём 3x3 сетку кнопок
        for row in range(3):
            for col in range(3):
                button = EventboxCellButton(row=row, col=col)
                self.add_item(button)

    async def finish_game(self, interaction: discord.Interaction):
        """Завершить игру и выдать награду"""
        # Удаляем ивентбокс из инвентаря
        result = await self.db.delete_inventory_item(
            user_id=self.user_id,
            guild_id=self.guild_id,
            item_key=self.eventbox_key
        )

        # Получаем текущий баланс
        economy = await self.db.get_row("user_economy", user_id=self.user_id, guild_id=self.guild_id)
        current_balance = economy.get("balance", 0) if economy else 0

        # Начисляем монеты (добавляем к текущему балансу)
        new_balance = current_balance + self.prize_amount
        await self.db.update_economy(
            user_id=self.user_id,
            guild_id=self.guild_id,
            values={"balance": new_balance},
            json_fields=["cooldowns"]
        )

        # Создаём финальный эмбед
        win_embed = Embed(
            title="🎉 Поздравляем!",
            color=Colors.SUCCESS,
            description=f"Вы открыли тайный бокс и получили **``{self.prize_amount:,}``** {Emojis.MONEY}!\n\n"
                       f"Ваш баланс: **``{new_balance:,}``** {Emojis.MONEY}"
        )

        # Отключаем все кнопки
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=win_embed, view=self)
        self.stop()

class EventboxCellButton(discord.ui.Button):
    def __init__(self, row: int, col: int):
        super().__init__(
            label="❓",
            style=discord.ButtonStyle.secondary,
            row=row
        )
        self.cell_row = row
        self.cell_col = col

    async def callback(self, interaction: discord.Interaction):
        view: EventboxGameView = self.view  # type: ignore

        if interaction.user.id != int(view.user_id):
            await interaction.response.send_message("Это не ваша игра!", ephemeral=True)
            return

        # Отмечаем ячейку как выбранную
        self.label = "✨"
        self.style = discord.ButtonStyle.success
        self.disabled = True

        view.selected_count += 1

        if view.selected_count >= 3:
            # Игра завершена - выдаём награду
            await view.finish_game(interaction)
        else:
            # Обновляем сообщение
            remaining = 3 - view.selected_count
            embed = Embed(
                title="🎁 Тайный бокс",
                color=Colors.PRIMARY,
                description=f"Выберите ещё **{remaining}** {'ячейку' if remaining == 1 else 'ячейки'}!\n\n"
                           f"💰 Награда: **100-1000** монет"
            )
            await interaction.response.edit_message(embed=embed, view=view)

class Inventory(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.manager = InventoryManager(self.db)

    @commands.hybrid_command(name="inventory", description="🎒 Открыть инвентарь")
    @app_commands.describe(user="👤 Чей инвентарь посмотреть (по умолчанию — ваш)")
    async def inventory(self, ctx: commands.Context, user: discord.Member | None = None) -> None:
        target = user or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)

        await self.db.ensure_user(user_id, guild_id)
        items = await self.manager.get_items(user_id, guild_id)

        base_embed = Embed(
            title=f"🎒 Инвентарь {target.display_name}",
            color=Colors.SUCCESS,
            description=f"Всего предметов: **{len(items)}**.\n"
                        "Используй кнопки ниже, чтобы переключаться между разделами.",
        )
        base_embed.set_thumbnail(url=target.display_avatar.url)

        view = InventoryView(user_id=user_id, guild_id=guild_id, manager=self.manager, db=self.db)
        if ctx.guild and ctx.guild.me:
            base_embed.set_footer(text="Сессия кнопок истечёт через 3 минуты бездействия.")

        message = await ctx.reply(embed=base_embed, view=view, mention_author=False)
        for child in view.children:
            if isinstance(child, discord.ui.Button):
                child.view_message = message  # опционально для будущего обновления

async def setup(bot: commands.Bot):
    await bot.add_cog(Inventory(bot))

