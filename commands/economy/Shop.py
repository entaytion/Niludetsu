import discord, json, math, re
from discord.ext import commands
from Niludetsu import Emojis, Colors, Embed
from Niludetsu.database.supabase_database import SupabaseDatabase, database
from Niludetsu.economy.manager import EconomyManager
from typing import Any, Dict, List, Optional

ITEMS_PER_PAGE = 5
PERSONAL_ROLE_PRICE = 10_000
HEX_RE = re.compile(r"^[0-9a-fA-F]{6}$")

def _extract_data(response: Optional[Any]) -> Optional[Any]:
    return getattr(response, "data", None) if response is not None else None

def normalize_hex(value: str) -> str:
    value = value.strip().lstrip("#")
    if not HEX_RE.match(value):
        raise ValueError("HEX-цвет должен состоять из 6 символов 0-9/A-F.")
    return f"#{value.lower()}"

class RoleShopRepository:
    def __init__(self, db: SupabaseDatabase):
        self.db = db

    async def list_roles(self, guild_id: str) -> List[Dict[str, Any]]:
        response = (
            self.db.client.table("roles")
            .select("*")
            .eq("guild_id", guild_id)
            .order("price", desc=False)
            .execute()
        )
        return _extract_data(response) or []

    async def delete_role(self, role_row_id: int) -> None:
        (
            self.db.client.table("roles")
            .delete()
            .eq("id", role_row_id)
            .execute()
        )

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
        response = (
            self.db.client.table("roles")
            .insert(payload)
            .execute()
        )
        data = _extract_data(response)
        if not data:
            raise RuntimeError("Не удалось сохранить роль в таблице roles.")
        return data[0]

    async def record_inventory_entry(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
        price: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        base_query = (
            self.db.client.table("user_inventory")
            .select("id")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .eq("item_type", "role")
            .eq("item_key", role_id)
            .maybe_single()
        )
        existing = _extract_data(base_query.execute())

        payload = {
            "guild_id": guild_id,
            "user_id": user_id,
            "item_type": "role",
            "item_key": role_id,
            "price_paid": price,
            "meta": meta or {},
        }

        if existing:
            (
                self.db.client.table("user_inventory")
                .update(
                    {
                        "price_paid": price,
                        "meta": payload["meta"],
                    }
                )
                .eq("id", existing["id"])
                .execute()
            )
        else:
            (
                self.db.client.table("user_inventory")
                .insert(payload)
                .execute()
            )

    async def remove_inventory_entry(
        self,
        *,
        guild_id: str,
        user_id: str,
        role_id: str,
    ) -> None:
        (
            self.db.client.table("user_inventory")
            .delete()
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .eq("item_type", "role")
            .eq("item_key", role_id)
            .execute()
        )

    async def user_owns_role(
        self, guild_id: str, user_id: str, role_id: str
    ) -> bool:
        response = (
            self.db.client.table("user_inventory")
            .select("id")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .eq("item_type", "role")
            .eq("item_key", role_id)
            .maybe_single()
            .execute()
        )
        data = _extract_data(response)
        return bool(data)

    async def fetch_owner_map(self, guild_id: str) -> Dict[str, List[str]]:
        response = (
            self.db.client.table("user_inventory")
            .select("user_id,item_key,meta")
            .eq("guild_id", guild_id)
            .eq("item_type", "role")
            .execute()
        )
        owners: Dict[str, List[str]] = {}
        for row in _extract_data(response) or []:
            meta = row.get("meta") or {}
            if meta.get("source") == "personal_role":
                continue
            owners.setdefault(row["item_key"], []).append(row["user_id"])
        return owners

    async def fetch_personal_role_by_owner(
        self, guild_id: str, owner_id: str
    ) -> Optional[Dict[str, Any]]:
        response = (
            self.db.client.table("roles")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("owner_id", owner_id)
            .maybe_single()
            .execute()
        )
        return _extract_data(response)

    async def purge_inventory_for_missing_role(
        self, guild_id: str, role_id: str
    ) -> None:
        (
            self.db.client.table("user_inventory")
            .delete()
            .eq("guild_id", guild_id)
            .eq("item_type", "role")
            .eq("item_key", role_id)
            .execute()
        )

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
            await interaction.response.send_message(
                embed=Embed.error("Эта покупка не для тебя."),
                ephemeral=True,
            )
            return

        guild_id = str(self.guild.id)
        buyer_id = str(self.buyer.id)
        seller_id = str(self.seller.id)
        role_id = self.role_data["role_id"]
        price = int(self.role_data["price"])

        already_owned = await self.repo.user_owns_role(guild_id, buyer_id, role_id)
        if already_owned:
            await interaction.response.edit_message(
                embed=Embed.error("У тебя уже есть эта роль."),
                view=None,
            )
            return

        success, message = await self.economy.transfer_money(
            buyer_id, seller_id, guild_id, price
        )
        if not success:
            await interaction.response.edit_message(
                embed=Embed.error(message),
                view=None,
            )
            return

        role = self.guild.get_role(int(role_id))
        if not role:
            await interaction.response.edit_message(
                embed=Embed.error("Роль исчезла. Сделка отменена."),
                view=None,
            )
            await self.repo.delete_role(self.role_data["id"])
            await self.repo.purge_inventory_for_missing_role(guild_id, role_id)
            return

        await self.repo.record_inventory_entry(
            guild_id=guild_id,
            user_id=buyer_id,
            role_id=role_id,
            price=price,
            meta={"name": self.role_data.get("name"), "source": "shop"},
        )

        await self.buyer.add_roles(role, reason="Покупка роли в магазине")
        buyer_wallet = await self.economy.get_wallet(buyer_id, guild_id)

        embed = Embed.success(
            description=(
                f"Ты купил {role.mention} за {self.economy.format_money(price)}.\n"
                f"Твой баланс: {self.economy.format_money(buyer_wallet)}"
            )
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Отменить", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.buyer.id:
            await interaction.response.send_message(
                embed=Embed.error("Эта кнопка не для тебя."),
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(
            embed=Embed.error("Покупка отменена."),
            view=None,
        )

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
            await interaction.response.send_message(
                embed=Embed.error("Магазин доступен только внутри сервера."),
                ephemeral=True,
            )
            return

        if str(interaction.user.id) == str(self.role_data["owner_id"]):
            await interaction.response.send_message(
                embed=Embed.error("Зачем покупать свою же роль? Она уже твоя."),
                ephemeral=True,
            )
            return

        seller = interaction.guild.get_member(int(self.role_data["owner_id"]))
        if not seller:
            await interaction.response.send_message(
                embed=Embed.error("Продавца нет на сервере. Сделка невозможна."),
                ephemeral=True,
            )
            return

        role = interaction.guild.get_role(int(self.role_data["role_id"]))
        if not role:
            await interaction.response.send_message(
                embed=Embed.error("Роль удалена. Магазин скоро обновится."),
                ephemeral=True,
            )
            await self.repo.delete_role(self.role_data["id"])
            await self.repo.purge_inventory_for_missing_role(
                str(interaction.guild.id), self.role_data["role_id"]
            )
            return

        user_has_role = await self.repo.user_owns_role(
            str(interaction.guild.id),
            str(interaction.user.id),
            self.role_data["role_id"],
        )
        if user_has_role:
            await interaction.response.send_message(
                embed=Embed.error("У тебя уже есть эта роль."),
                ephemeral=True,
            )
            return

        price = int(self.role_data["price"])
        embed = Embed.info(
            title="Подтверждение покупки",
            description=(
                f"{role.mention}\n"
                f"- Стоимость: {self.economy.format_money(price)}\n"
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
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

class CreatePersonalRoleButton(discord.ui.Button):
    def __init__(
        self,
        *,
        repo: RoleShopRepository,
        economy: EconomyManager,
        guild: discord.Guild,
    ):
        super().__init__(
            label="Создать личную роль",
            style=discord.ButtonStyle.primary,
            emoji="➕",
        )
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

        balance = await self.economy.get_wallet(user_id, guild_id)
        if balance < PERSONAL_ROLE_PRICE:
            await interaction.response.send_message(
                embed=Embed.error(
                    f"Нужно {self.economy.format_money(PERSONAL_ROLE_PRICE)}, а у тебя только {self.economy.format_money(balance)}."
                ),
                ephemeral=True,
            )
            return

        modal = CreatePersonalRoleModal(
            repo=self.repo,
            economy=self.economy,
            guild=self.guild,
        )
        await interaction.response.send_modal(modal)

class CreatePersonalRoleModal(discord.ui.Modal, title="Создание личной роли"):
    def __init__(
        self,
        *,
        repo: RoleShopRepository,
        economy: EconomyManager,
        guild: discord.Guild,
    ):
        super().__init__()
        self.repo = repo
        self.economy = economy
        self.guild = guild

        self.name_input = discord.ui.TextInput(
            label="Название",
            placeholder="Например: Лучший Саппорт",
            min_length=2,
            max_length=100,
        )
        self.color_input = discord.ui.TextInput(
            label="Цвет (HEX)",
            placeholder="#ff9000 или ff9000",
            default="#ff9000",
            min_length=6,
            max_length=7,
        )
        self.description_input = discord.ui.TextInput(
            label="Описание (необязательно)",
            placeholder="Короткое описание роли",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )
        self.price_input = discord.ui.TextInput(
            label="Цена продажи",
            placeholder="Сколько брать с покупателей (целое число)",
            default="5000",
        )

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
            await interaction.response.send_message(
                embed=Embed.error(str(exc)),
                ephemeral=True,
            )
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
            await interaction.response.send_message(
                embed=Embed.error("Минимальная цена продажи — 1."),
                ephemeral=True,
            )
            return

        success, message = await self.economy.remove_money(
            user_id, guild_id, PERSONAL_ROLE_PRICE
        )
        if not success:
            await interaction.response.send_message(
                embed=Embed.error(message),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=Embed.info("Создаю роль, подожди пару секунд..."),
            ephemeral=True,
        )

        new_role: Optional[discord.Role] = None
        try:
            new_role = await guild.create_role(
                name=self.name_input.value,
                color=discord.Color.from_str(color_value),
                reason=f"Личная роль пользователя {interaction.user}",
            )

            bot_top_role = guild.me.top_role if guild.me else None
            if bot_top_role:
                await guild.edit_role_positions(
                    positions={new_role: bot_top_role.position - 1}
                )

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
                        f"- Цена продажи: {self.economy.format_money(resale_price)}\n"
                        f"- Стоимость создания: {self.economy.format_money(PERSONAL_ROLE_PRICE)} списана."
                    )
                )
            )

        except Exception as exc:
            await self.economy.add_money(
                user_id, guild_id, PERSONAL_ROLE_PRICE, share_spousal=False
            )
            if new_role:
                try:
                    await new_role.delete(reason="Откат после ошибки создания личной роли")
                except Exception:
                    pass
            await interaction.edit_original_response(
                embed=Embed.error(f"Не удалось создать роль: {exc}")
            )

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
        self.add_item(
            CreatePersonalRoleButton(repo=self.repo, economy=self.economy, guild=self.guild)
        )

    def _build_role_buttons(self) -> None:
        start = self.page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(self.roles))
        for role_data in self.roles[start:end]:
            seller_present = bool(
                self.guild.get_member(int(role_data["owner_id"]))
            )
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
            prev_button = discord.ui.Button(
                label="◀️",
                style=discord.ButtonStyle.secondary,
            )
            prev_button.callback = self._page_callback(self.page - 1)
            self.add_item(prev_button)

        if self.page < self.max_pages - 1:
            next_button = discord.ui.Button(
                label="▶️",
                style=discord.ButtonStyle.secondary,
            )
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
            embed = new_view.build_embed()
            await interaction.response.edit_message(embed=embed, view=new_view)

        return callback

    def build_embed(self) -> Embed:
        embed = Embed(
            title=f"{Emojis.ICON_SHOP} Магазин ролей — страница {self.page + 1}/{self.max_pages}",
            description=(
                f"> Создай личную роль за {self.economy.format_money(PERSONAL_ROLE_PRICE)} или купи выставленную.\n"
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
                f"└ Цена: {self.economy.format_money(int(role_data['price']))}",
                f"└ Продавец: {seller.mention if seller else 'нет на сервере'}",
                f"└ Купили: {len(owners)}",
            ]
            if role_data.get("description"):
                desc = role_data["description"]
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                lines.append(f"└ Описание: {desc}")
            blocks.append("\n".join(lines))

        if blocks:
            embed.description += "\n" + "\n".join(blocks)
        else:
            embed.description += "На этой странице пока пусто — листай дальше."

        return embed

class EmptyShopView(discord.ui.View):
    def __init__(
        self,
        *,
        repo: RoleShopRepository,
        economy: EconomyManager,
        guild: discord.Guild,
    ):
        super().__init__(timeout=120)
        self.add_item(
            CreatePersonalRoleButton(repo=repo, economy=economy, guild=guild)
        )

class RoleShop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.repo = RoleShopRepository(self.db)
        self.economy = EconomyManager(self.db)

    @commands.hybrid_command(name="shop", description="🛒 Открыть магазин ролей")
    async def open_shop(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            await ctx.reply(
                embed=Embed.error("Магазин работает только на сервере."),
                ephemeral=True,
            )
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
            await self.repo.purge_inventory_for_missing_role(
                guild_id, role_data["role_id"]
            )

        if not valid_roles:
            embed = Embed.info(
                title=f"{Emojis.ICON_SHOP} Магазин ролей",
                description=(
                    "Пока здесь пусто.\n"
                    f"Создай личную роль за {self.economy.format_money(PERSONAL_ROLE_PRICE)} — кнопка ниже."
                ),
            )
            view = EmptyShopView(repo=self.repo, economy=self.economy, guild=ctx.guild)
            await ctx.reply(embed=embed, view=view, mention_author=False)
            return

        view = ShopView(
            roles=valid_roles,
            owners_map=owners_map,
            repo=self.repo,
            economy=self.economy,
            guild=ctx.guild,
        )
        embed = view.build_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleShop(bot))

