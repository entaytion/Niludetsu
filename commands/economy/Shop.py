import json
import math
import re
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

from Niludetsu import Colors, Embed, Emojis, EconomyManager
from Niludetsu.database import database

ITEMS_PER_PAGE = 5
PERSONAL_ROLE_PRICE = 10_000
HEX_RE = re.compile(r"^[0-9a-fA-F]{6}$")

def normalize_hex(value: str) -> str:
    value = value.strip().lstrip("#")
    if not HEX_RE.match(value):
        raise ValueError("HEX-цвет должен состоять из 6 символов 0-9/A-F.")
    return f"#{value.lower()}"

class RoleShopRepository:
    def __init__(self, db):
        self.db = db

    async def list_roles(self, guild_id: str) -> List[Dict[str, Any]]:
        rows = await self.db.list_shop_roles(guild_id)
        return sorted(rows, key=lambda row: int(row.get("price") or 0))

    async def delete_role(self, role_row_id: int) -> None:
        await self.db.delete_shop_roles([role_row_id])

    async def upsert_role(
        self,
        *,
        guild_id: str,
        role_id: str,
        owner_id: str,
        name: str,
        color: str,
        description: str,
        price: int,
    ) -> Dict[str, Any]:
        payload = {
            "guild_id": guild_id,
            "role_id": role_id,
            "owner_id": owner_id,
            "name": name,
            "color": color,
            "description": description,
            "price": price,
            "rights": json.dumps({}),
        }
        row = await self.db.add_shop_role(payload)
        if not row:
            raise RuntimeError("Не удалось сохранить роль в таблице roles.")
        return row

    async def record_inventory_entry(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        price: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        existing = await self.db.get_inventory_role(guild_id, user_id, role_id)
        payload = {
            "price_paid": price,
            "meta": meta or {},
        }
        if existing:
            await self.db.update_record("user_inventory", where={"id": existing["id"]}, values=payload)
            return
        await self.db.insert(
            "user_inventory",
            {
                "guild_id": guild_id,
                "user_id": user_id,
                "item_type": "role",
                "item_key": role_id,
                "price_paid": price,
                "meta": meta or {},
            },
        )

    async def user_owns_role(self, guild_id: str, user_id: str, role_id: str) -> bool:
        return bool(await self.db.get_inventory_role(guild_id, user_id, role_id))

    async def fetch_owner_map(self, guild_id: str) -> Dict[str, List[str]]:
        rows = await self.db.get_rows("user_inventory", guild_id=guild_id, item_type="role")
        owners: Dict[str, List[str]] = {}
        for row in rows:
            meta = row.get("meta") or {}
            if meta.get("source") == "personal_role":
                continue
            owners.setdefault(row["item_key"], []).append(row["user_id"])
        return owners

    async def fetch_personal_role_by_owner(self, guild_id: str, owner_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_row("roles", guild_id=guild_id, owner_id=owner_id)

    async def purge_inventory_for_missing_role(self, guild_id: str, role_id: str) -> None:
        await self.db.purge_inventory_roles(guild_id, [role_id])

class PurchaseConfirmView(discord.ui.View):
    def __init__(
        self,
        *,
        repo: RoleShopRepository,
        economy: EconomyManager,
        role_data: Dict[str, Any],
        buyer: discord.Member,
        seller: discord.Member,
        guild: discord.Guild,
    ):
        super().__init__(timeout=40)
        self.repo = repo
        self.economy = economy
        self.role_data = role_data
        self.buyer = buyer
        self.seller = seller
        self.guild = guild

    @discord.ui.button(label="Купить", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.buyer.id:
            await interaction.response.send_message(embed=Embed.error("Эта покупка не для тебя."), ephemeral=True)
            return

        guild_id = str(self.guild.id)
        buyer_id = str(self.buyer.id)
        seller_id = str(self.seller.id)
        role_id = self.role_data["role_id"]
        price = int(self.role_data["price"])

        if await self.repo.user_owns_role(guild_id, buyer_id, role_id):
            await interaction.response.edit_message(embed=Embed.error("У тебя уже есть эта роль."), view=None)
            return

        result = await self.economy.transfer_money(buyer_id, seller_id, guild_id, price, event="shop_purchase")
        if not result:
            await interaction.response.edit_message(embed=Embed.error(result.message), view=None)
            return

        role = self.guild.get_role(int(role_id))
        if not role:
            await self.repo.delete_role(self.role_data["id"])
            await self.repo.purge_inventory_for_missing_role(guild_id, role_id)
            await interaction.response.edit_message(embed=Embed.error("Роль исчезла. Сделка отменена."), view=None)
            return

        await self.repo.record_inventory_entry(
            guild_id=guild_id,
            user_id=buyer_id,
            role_id=role_id,
            price=price,
            meta={"name": self.role_data.get("name"), "source": "shop"},
        )
        await self.buyer.add_roles(role, reason="Покупка роли в магазине")

        account = result.data or await self.economy.get_account(buyer_id, guild_id)
        embed = Embed.success(
            description=(
                f"Ты купил {role.mention} за **{price:,}** {Emojis.MONEY}.\n"
                f"Твой баланс: **{account['balance']:,}** {Emojis.MONEY}"
            )
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Отменить", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.buyer.id:
            await interaction.response.send_message(embed=Embed.error("Эта кнопка не для тебя."), ephemeral=True)
            return
        await interaction.response.edit_message(embed=Embed.error("Покупка отменена."), view=None)

class RolePurchaseButton(discord.ui.Button):
    def __init__(
        self,
        *,
        role_data: Dict[str, Any],
        seller_present: bool,
        guild: discord.Guild,
        repo: RoleShopRepository,
        economy: EconomyManager,
    ):
        role = guild.get_role(int(role_data["role_id"]))
        label = role.name if role else f"Роль {role_data['id']}"
        super().__init__(
            label=label,
            style=discord.ButtonStyle.green if seller_present else discord.ButtonStyle.red,
            custom_id=f"shop_role_{role_data['id']}",
            disabled=not seller_present,
        )
        self.role_data = role_data
        self.guild = guild
        self.repo = repo
        self.economy = economy

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message(embed=Embed.error("Магазин доступен только внутри сервера."), ephemeral=True)
            return
        if str(interaction.user.id) == str(self.role_data["owner_id"]):
            await interaction.response.send_message(embed=Embed.error("Зачем покупать свою же роль? Она уже твоя."), ephemeral=True)
            return

        seller = interaction.guild.get_member(int(self.role_data["owner_id"]))
        if not seller:
            await interaction.response.send_message(embed=Embed.error("Продавца нет на сервере. Сделка невозможна."), ephemeral=True)
            return

        role = interaction.guild.get_role(int(self.role_data["role_id"]))
        if not role:
            await self.repo.delete_role(self.role_data["id"])
            await self.repo.purge_inventory_for_missing_role(str(interaction.guild.id), self.role_data["role_id"])
            await interaction.response.send_message(embed=Embed.error("Роль удалена. Магазин скоро обновится."), ephemeral=True)
            return

        if await self.repo.user_owns_role(str(interaction.guild.id), str(interaction.user.id), self.role_data["role_id"]):
            await interaction.response.send_message(embed=Embed.error("У тебя уже есть эта роль."), ephemeral=True)
            return

        price = int(self.role_data["price"])
        embed = Embed.info(
            title="Подтверждение покупки",
            description=(
                f"{role.mention}\n"
                f"- Стоимость: **{price:,}** {Emojis.MONEY}\n"
                f"- Продавец: {seller.mention}\n"
                f"- Описание: {self.role_data.get('description') or 'не указано'}"
            ),
        )
        view = PurchaseConfirmView(
            repo=self.repo,
            economy=self.economy,
            role_data=self.role_data,
            buyer=interaction.user,
            seller=seller,
            guild=interaction.guild,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CreatePersonalRoleButton(discord.ui.Button):
    def __init__(self, *, repo: RoleShopRepository, economy: EconomyManager, guild: discord.Guild):
        super().__init__(label="Создать личную роль", style=discord.ButtonStyle.primary, emoji="➕")
        self.repo = repo
        self.economy = economy
        self.guild = guild

    async def callback(self, interaction: discord.Interaction) -> None:
        guild_id = str(self.guild.id)
        user_id = str(interaction.user.id)
        existing = await self.repo.fetch_personal_role_by_owner(guild_id, user_id)
        if existing:
            await interaction.response.send_message(
                embed=Embed.error("Личная роль уже создана и выставлена в магазине."),
                ephemeral=True,
            )
            return

        account = await self.economy.get_account(user_id, guild_id)
        balance = int(account.get("balance") or 0)
        if balance < PERSONAL_ROLE_PRICE:
            await interaction.response.send_message(
                embed=Embed.error(
                    f"Нужно **{PERSONAL_ROLE_PRICE:,}** {Emojis.MONEY}, а у тебя только **{balance:,}** {Emojis.MONEY}."
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            CreatePersonalRoleModal(repo=self.repo, economy=self.economy, guild=self.guild)
        )

class CreatePersonalRoleModal(discord.ui.Modal, title="Создание личной роли"):
    def __init__(self, *, repo: RoleShopRepository, economy: EconomyManager, guild: discord.Guild):
        super().__init__()
        self.repo = repo
        self.economy = economy
        self.guild = guild

        self.name_input = discord.ui.TextInput(label="Название", placeholder="Например: Лучший Саппорт", min_length=2, max_length=100)
        self.color_input = discord.ui.TextInput(label="Цвет (HEX)", placeholder="#ff9000 или ff9000", default="#ff9000", min_length=6, max_length=7)
        self.description_input = discord.ui.TextInput(
            label="Описание (необязательно)",
            placeholder="Короткое описание роли",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )
        self.price_input = discord.ui.TextInput(label="Цена продажи", placeholder="Сколько брать с покупателей (целое число)", default="5000")

        self.add_item(self.name_input)
        self.add_item(self.color_input)
        self.add_item(self.description_input)
        self.add_item(self.price_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        guild = self.guild
        guild_id = str(guild.id)
        user_id = str(interaction.user.id)

        try:
            color_value = normalize_hex(self.color_input.value)
        except ValueError as exc:
            await interaction.response.send_message(embed=Embed.error(str(exc)), ephemeral=True)
            return

        price_str = self.price_input.value.strip()
        if not price_str.isdigit():
            await interaction.response.send_message(
                embed=Embed.error("Цена продажи должна быть положительным целым числом."),
                ephemeral=True,
            )
            return

        resale_price = int(price_str)
        if resale_price < 1:
            await interaction.response.send_message(embed=Embed.error("Минимальная цена продажи — 1."), ephemeral=True)
            return

        result = await self.economy.remove_money(user_id, guild_id, PERSONAL_ROLE_PRICE)
        if not result:
            await interaction.response.send_message(embed=Embed.error(result.message), ephemeral=True)
            return

        await interaction.response.send_message(embed=Embed.info("Создаю роль, подожди пару секунд..."), ephemeral=True)

        new_role: Optional[discord.Role] = None
        try:
            new_role = await guild.create_role(
                name=self.name_input.value,
                color=discord.Color.from_str(color_value),
                reason=f"Личная роль пользователя {interaction.user}",
            )
            bot_top_role = guild.me.top_role if guild.me else None
            if bot_top_role:
                await guild.edit_role_positions(positions={new_role: bot_top_role.position - 1})

            await self.repo.upsert_role(
                guild_id=guild_id,
                role_id=str(new_role.id),
                owner_id=user_id,
                name=new_role.name,
                color=color_value,
                description=self.description_input.value or "",
                price=resale_price,
            )
            await self.repo.record_inventory_entry(
                guild_id=guild_id,
                user_id=user_id,
                role_id=str(new_role.id),
                price=PERSONAL_ROLE_PRICE,
                meta={"source": "personal_role"},
            )
            await interaction.user.add_roles(new_role, reason="Создание личной роли")

            await interaction.edit_original_response(
                embed=Embed.success(
                    description=(
                        f"Личная роль {new_role.mention} создана!\n"
                        f"- Цвет: `{color_value}`\n"
                        f"- Цена продажи: **{resale_price:,}** {Emojis.MONEY}\n"
                        f"- Стоимость создания: **{PERSONAL_ROLE_PRICE:,}** {Emojis.MONEY} списана."
                    )
                )
            )
        except Exception as exc:
            await self.economy.add_money(user_id, guild_id, PERSONAL_ROLE_PRICE, share_spousal=False)
            if new_role:
                try:
                    await new_role.delete(reason="Откат после ошибки создания личной роли")
                except Exception:
                    pass
            await interaction.edit_original_response(embed=Embed.error(f"Не удалось создать роль: {exc}"))

class ShopView(discord.ui.View):
    def __init__(
        self,
        *,
        roles: List[Dict[str, Any]],
        owners_map: Dict[str, List[str]],
        repo: RoleShopRepository,
        economy: EconomyManager,
        guild: discord.Guild,
        page: int = 0,
    ):
        super().__init__(timeout=180)
        self.roles = roles
        self.owners_map = owners_map
        self.repo = repo
        self.economy = economy
        self.guild = guild
        self.page = page
        self.max_pages = max(1, math.ceil(len(roles) / ITEMS_PER_PAGE))
        self._build_role_buttons()
        self._build_navigation()
        self.add_item(CreatePersonalRoleButton(repo=self.repo, economy=self.economy, guild=self.guild))

    def _build_role_buttons(self) -> None:
        start = self.page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(self.roles))
        for role_data in self.roles[start:end]:
            seller_present = bool(self.guild.get_member(int(role_data["owner_id"])))
            self.add_item(
                RolePurchaseButton(
                    role_data=role_data,
                    seller_present=seller_present,
                    guild=self.guild,
                    repo=self.repo,
                    economy=self.economy,
                )
            )

    def _build_navigation(self) -> None:
        if self.max_pages <= 1:
            return
        if self.page > 0:
            prev_button = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary)
            prev_button.callback = self._page_callback(self.page - 1)
            self.add_item(prev_button)
        if self.page < self.max_pages - 1:
            next_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary)
            next_button.callback = self._page_callback(self.page + 1)
            self.add_item(next_button)

    def _page_callback(self, new_page: int):
        async def callback(interaction: discord.Interaction):
            fresh_owners = await self.repo.fetch_owner_map(str(self.guild.id))
            new_view = ShopView(
                roles=self.roles,
                owners_map=fresh_owners,
                repo=self.repo,
                economy=self.economy,
                guild=self.guild,
                page=new_page,
            )
            await interaction.response.edit_message(embed=new_view.build_embed(), view=new_view)

        return callback

    def build_embed(self) -> Embed:
        embed = Embed(
            title=f"{Emojis.ICON_SHOP} Магазин ролей — страница {self.page + 1}/{self.max_pages}",
            description=(
                f"> Создай личную роль за **{PERSONAL_ROLE_PRICE:,}** {Emojis.MONEY} или купи выставленную.\n"
                f"- Всего ролей в продаже: {len(self.roles)}\n"
            ),
            color=Colors.INFO,
        )
        start = self.page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(self.roles))

        blocks: List[str] = []
        for role_data in self.roles[start:end]:
            role = self.guild.get_role(int(role_data["role_id"]))
            if not role:
                continue
            owners = self.owners_map.get(role_data["role_id"], [])
            seller = self.guild.get_member(int(role_data["owner_id"]))
            lines = [
                f"{role.mention}",
                f"└ Цена: **{int(role_data['price']):,}** {Emojis.MONEY}",
                f"└ Продавец: {seller.mention if seller else 'нет на сервере'}",
                f"└ Купили: {len(owners)}",
            ]
            if role_data.get("description"):
                desc = role_data["description"]
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                lines.append(f"└ Описание: {desc}")
            blocks.append("\n".join(lines))

        embed.description += "\n" + "\n".join(blocks) if blocks else "На этой странице пока пусто — листай дальше."
        return embed

class EmptyShopView(discord.ui.View):
    def __init__(self, *, repo: RoleShopRepository, economy: EconomyManager, guild: discord.Guild):
        super().__init__(timeout=120)
        self.add_item(CreatePersonalRoleButton(repo=repo, economy=economy, guild=guild))

class RoleShop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.repo = RoleShopRepository(self.db)
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="shop", description="Открыть магазин ролей")
    async def open_shop(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            await ctx.reply(embed=Embed.error("Магазин работает только на сервере."), ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        roles = await self.repo.list_roles(guild_id)
        owners_map = await self.repo.fetch_owner_map(guild_id)

        valid_roles: List[Dict[str, Any]] = []
        for role_data in roles:
            role = ctx.guild.get_role(int(role_data["role_id"]))
            seller = ctx.guild.get_member(int(role_data["owner_id"]))
            if role and seller:
                valid_roles.append(role_data)
                continue
            await self.repo.delete_role(role_data["id"])
            await self.repo.purge_inventory_for_missing_role(guild_id, role_data["role_id"])

        if not valid_roles:
            embed = Embed.info(
                title=f"{Emojis.ICON_SHOP} Магазин ролей",
                description=(
                    "Пока здесь пусто.\n"
                    f"Создай личную роль за **{PERSONAL_ROLE_PRICE:,}** {Emojis.MONEY} — кнопка ниже."
                ),
            )
            await ctx.reply(
                embed=embed,
                view=EmptyShopView(repo=self.repo, economy=self.economy, guild=ctx.guild),
                mention_author=False,
            )
            return

        view = ShopView(
            roles=valid_roles,
            owners_map=owners_map,
            repo=self.repo,
            economy=self.economy,
            guild=ctx.guild,
        )
        await ctx.reply(embed=view.build_embed(), view=view, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleShop(bot))
