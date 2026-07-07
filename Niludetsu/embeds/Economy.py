from ..tools.Embed import Colors, Embed
from ..tools.Emojis import Emojis
from ..locale import DEFAULT_LOCALE
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


def _locale_text(module: str, key: str, **kwargs) -> str:
    """Отримує текст з DEFAULT_LOCALE."""
    text = DEFAULT_LOCALE.get(module, {}).get(key, key)
    if kwargs and text:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text


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
        embed = Embed.user(
            user=user,
            title_prefix=_locale_text("economy", "balance_title"),
            color=Colors.PRIMARY,
        )
        embed.add_field(
            name=f"> {_locale_text('economy', 'balance_wallet')}", value=f"**{wallet:,}** {Emojis.MONEY}", inline=True
        )
        embed.add_field(
            name=f"> {_locale_text('economy', 'balance_bank')}", value=f"**{bank:,}** {Emojis.MONEY}", inline=True
        )
        if family is not None:
            embed.add_field(
                name=f"> {_locale_text('economy', 'balance_family')}",
                value=f"**{family:,}** {Emojis.MONEY}",
                inline=True,
            )
        if rewards_info:
            embed.add_field(
                name=f"> {_locale_text('economy', 'balance_rewards')}", value=rewards_info, inline=False
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
        if user is None:
            return Embed.error(title=f"{_locale_text('economy', 'error_title')} — {_locale_text('economy', 'error_suffix')}", description=text)

        return Embed.user(
            user=user,
            title_prefix=_locale_text("economy", "error_title"),
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
        lines = []
        if bet is not None:
            lines.append(f"**{_locale_text('economy', 'game_stake')}:** {bet:,} {Emojis.MONEY}\n")

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
        "daily": _locale_text("economy", "event_daily"),
        "work": _locale_text("economy", "event_work"),
        "slut": _locale_text("economy", "event_slut"),
        "slut_penalty": _locale_text("economy", "event_slut_penalty"),
        "rob": _locale_text("economy", "event_rob"),
        "rob_penalty": _locale_text("economy", "event_rob_penalty"),
        "pay": _locale_text("economy", "event_pay"),
        "deposit": _locale_text("economy", "event_deposit"),
        "withdraw": _locale_text("economy", "event_withdraw"),
        "withdraw_family": _locale_text("economy", "event_withdraw_family"),
        "coinflip": _locale_text("economy", "event_coinflip"),
        "slots": _locale_text("economy", "event_slots"),
        "roulette": _locale_text("economy", "event_roulette"),
        "blackjack": _locale_text("economy", "event_blackjack"),
        "duel": _locale_text("economy", "event_duel"),
        "bump": _locale_text("economy", "event_bump"),
        "income": _locale_text("economy", "event_income"),
        "shop": _locale_text("economy", "event_shop"),
        "refund": _locale_text("economy", "event_refund"),
        "quest_reward": _locale_text("economy", "event_quest_reward"),
    }

    FILTER_MAP = {
        "all": None,
        "income": ["daily", "work", "slut", "bump", "income", "quest_reward"],
        "games": ["coinflip", "slots", "roulette", "blackjack"],
        "transfers": ["pay", "rob", "rob_penalty", "duel"],
        "bank": ["deposit", "withdraw", "withdraw_family"],
    }

    FILTER_LABELS = {
        "all": _locale_text("economy", "filter_all"),
        "income": _locale_text("economy", "filter_income"),
        "games": _locale_text("economy", "filter_games"),
        "transfers": _locale_text("economy", "filter_transfers"),
        "bank": _locale_text("economy", "filter_bank"),
    }

    @staticmethod
    def transaction_row(tx: dict, time_svc) -> str:
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
        filter_label: str = None,
        avatar_url: Optional[str] = None,
    ) -> "Embed":
        if filter_label is None:
            filter_label = _locale_text("economy", "filter_all")
        if not rows:
            embed = Embed(
                title=f"📋 {_locale_text('economy', 'transactions_title')} — {display_name}",
                description=f"*{_locale_text('economy', 'transactions_empty')}*",
                color=Colors.PRIMARY,
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            return embed

        lines = [EconomyEmbed.transaction_row(tx, time_svc) for tx in rows]
        max_page = max(0, (total - 1) // page_size)

        embed = Embed(
            title=f"📋 {_locale_text('economy', 'transactions_title')} — {display_name}",
            description="\n".join(lines),
            color=Colors.PRIMARY,
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.set_footer(
            text=_locale_text("economy", "transactions_page_footer", page=page + 1, max_page=max_page + 1, filter=filter_label, total=f"{total:,}")
        )
        return embed
