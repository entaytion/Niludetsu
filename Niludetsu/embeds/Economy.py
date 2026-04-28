from ..tools.Embed import Colors, Embed
from ..tools.Emojis import Emojis
"""Унифицированные эмбеды для экономических команд.

Формат:
    Title:       "Действие — username"
    Description: "@user, текст..."
    Thumbnail:   аватар пользователя
    Color:       Colors.PRIMARY
    Footer:      нет
    Fields:      нет (кроме balance)
"""

from typing import Optional

import discord

class EconomyEmbed:
    """Фабрика embed'ов для экономики."""

    @staticmethod
    def result(
        *,
        action: str,
        user: discord.Member | discord.User,
        text: str,
        color: int = Colors.PRIMARY,
    ) -> Embed:
        """Стандартный embed результата."""
        return Embed.user_action(
            action=action,
            user=user,
            color=color,
            text=text,
        )

    @staticmethod
    def balance(
        *,
        user: discord.Member | discord.User,
        wallet: int,
        bank: int,
        family: Optional[int] = None,
        rewards_info: Optional[str] = None,
    ) -> Embed:
        """Embed баланса пользователя."""
        embed = Embed.user(
            user=user,
            title_prefix="Кошелёк пользователя",
            color=Colors.PRIMARY,
        )
        embed.add_field(
            name="> Кошелёк", value=f"**{wallet:,}** {Emojis.MONEY}", inline=True
        )
        embed.add_field(
            name="> Банк", value=f"**{bank:,}** {Emojis.MONEY}", inline=True
        )
        if family is not None:
            embed.add_field(
                name="> Семейный счёт",
                value=f"**{family:,}** {Emojis.MONEY}",
                inline=True,
            )
        if rewards_info:
            embed.add_field(
                name="> Доступные награды", value=rewards_info, inline=False
            )
        return embed

    @staticmethod
    def game(
        *,
        action: str,
        user: discord.Member | discord.User,
        text: str,
        color: int = Colors.PRIMARY,
    ) -> Embed:
        """Embed для результата мини-игры (coinflip, slots, etc).

        Аналогичен result(), но для единообразия выделен отдельно.
        """
        return EconomyEmbed.result(
            action=action,
            user=user,
            text=text,
            color=color,
        )

    @staticmethod
    def error(
        text: str,
        user: Optional[discord.Member | discord.User] = None,
    ) -> Embed:
        """Ошибка экономической команды в формате: title='Ошибка — ...', description='@user, ...'."""
        if user is None:
            return Embed.error(title="Ошибка — экономика", description=text)

        return Embed.user(
            user=user,
            title_prefix="Ошибка",
            color=Colors.ERROR,
            text=text,
            mention=True,
        )

    @staticmethod
    def game_lobby(
        *,
        action: str,
        user: discord.Member | discord.User,
        description: Optional[str] = None,
        bet: Optional[int] = None,
        color: int = Colors.PRIMARY,
    ) -> Embed:
        """Embed для начала мини-игры (выбор ставки, ожидание)."""
        lines = []
        if bet is not None:
            lines.append(f"**Ставка:** {bet:,} {Emojis.MONEY}\n")

        if description:
            lines.append(description)

        return Embed.user(
            user=user,
            title_prefix=action,
            color=color,
            description="\n".join(lines).strip(),
        )

    # ——— Транзакції ———

    EVENT_LABELS = {
        "daily": "Ежедневка",
        "work": "Подработка",
        "slut": "Заработок",
        "slut_penalty": "Штраф",
        "rob": "Ограбление",
        "rob_penalty": "Штраф",
        "pay": "Перевод",
        "deposit": "Депозит",
        "withdraw": "Снятие",
        "withdraw_family": "Семейный счёт",
        "coinflip": "Монетка",
        "slots": "Слоты",
        "roulette": "Рулетка",
        "blackjack": "Блекджек",
        "duel": "Дуэль",
        "bump": "Бамп",
        "income": "Доход с роли",
        "shop": "Покупка",
        "refund": "Возврат",
        "quest_reward": "Квест",
    }

    FILTER_MAP = {
        "all": None,
        "income": ["daily", "work", "slut", "bump", "income", "quest_reward"],
        "games": ["coinflip", "slots", "roulette", "blackjack"],
        "transfers": ["pay", "rob", "rob_penalty", "duel"],
        "bank": ["deposit", "withdraw", "withdraw_family"],
    }

    FILTER_LABELS = {
        "all": "Все",
        "income": "Доход",
        "games": "Игры",
        "transfers": "Переводы",
        "bank": "Банк",
    }

    @staticmethod
    def transaction_row(tx: dict, time_svc) -> str:
        """Форматирует одну строку транзакции."""
        from Niludetsu.tools.Emojis import Emojis as _Emojis

        amount = tx["amount"]
        event = tx["event"]
        label = EconomyEmbed.EVENT_LABELS.get(event, event)

        icon = _Emojis.PLUS if amount >= 0 else _Emojis.MINUS

        created = time_svc.ensure_datetime(tx.get("created_at"))
        if created:
            unix_ts = int(created.timestamp())
            date_str = f"<t:{unix_ts}:f>"
        else:
            date_str = ""

        related = tx.get("related_user_id")
        related_str = ""
        if related:
            related_str = f" → <@{related}>" if amount < 0 else f" ← <@{related}>"

        return f"{icon} **{label}**{related_str} ・ **{abs(amount):,}** {_Emojis.MONEY} ・ {date_str}"

    @staticmethod
    def transactions_page(
        *,
        display_name: str,
        rows: list,
        time_svc,
        page: int = 0,
        total: int = 0,
        page_size: int = 10,
        filter_label: str = "Все",
        avatar_url: Optional[str] = None,
    ) -> "Embed":
        """Embed-страница транзакций."""
        if not rows:
            embed = Embed(
                title=f"📋 Транзакции — {display_name}",
                description="*История пуста.*",
                color=Colors.PRIMARY,
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            return embed

        lines = [EconomyEmbed.transaction_row(tx, time_svc) for tx in rows]
        max_page = max(0, (total - 1) // page_size)

        embed = Embed(
            title=f"📋 Транзакции — {display_name}",
            description="\n".join(lines),
            color=Colors.PRIMARY,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.set_footer(
            text=f"Страница {page + 1}/{max_page + 1} • Фильтр: {filter_label} • Всего: {total:,}"
        )
        return embed
