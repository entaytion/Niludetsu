"""Унифицированные эмбеды для экономических команд.

Формат:
    Title:       "Действие — username"
    Description: "@user, текст..."
                 "**Ваш текущий баланс:** X <money>"
    Thumbnail:   аватар пользователя
    Color:       Colors.PRIMARY
    Footer:      нет
    Fields:      нет (кроме balance)
"""

import discord
from Niludetsu.tools.Embed import Embed, Colors
from Niludetsu.tools.Emojis import Emojis
from typing import Optional


class EconomyEmbed:
    """Фабрика embed'ов для экономики."""

    @staticmethod
    def result(
        *,
        action: str,
        user: discord.Member | discord.User,
        text: str,
        balance: Optional[int] = None,
        color: int = Colors.PRIMARY,
    ) -> Embed:
        """Стандартный embed результата."""
        if text.startswith("```") or text.startswith("\n"):
            lines = [f"{user.mention}\n{text.strip()}"]
        else:
            lines = [f"{user.mention}, {text}"]
            
        if balance is not None:
            lines.append(f"\n**Ваш текущий баланс:** {balance:,} {Emojis.MONEY}")

        embed = Embed(
            title=f"{action} — {user.display_name}",
            description="\n".join(lines).strip(),
            color=color,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        return embed

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
        embed = Embed(
            title=f"Кошелёк пользователя — {user.display_name}",
            color=Colors.PRIMARY,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="> Кошелёк", value=f"**{wallet:,}** {Emojis.MONEY}", inline=True)
        embed.add_field(name="> Банк", value=f"**{bank:,}** {Emojis.MONEY}", inline=True)
        if family is not None:
            embed.add_field(name="> Семейный счёт", value=f"**{family:,}** {Emojis.MONEY}", inline=True)
        if rewards_info:
            embed.add_field(name="> Доступные награды", value=rewards_info, inline=False)
        return embed

    @staticmethod
    def game(
        *,
        action: str,
        user: discord.Member | discord.User,
        text: str,
        balance: Optional[int] = None,
        color: int = Colors.PRIMARY,
    ) -> Embed:
        """Embed для результата мини-игры (coinflip, slots, etc).

        Аналогичен result(), но для единообразия выделен отдельно.
        """
        return EconomyEmbed.result(
            action=action,
            user=user,
            text=text,
            balance=balance,
            color=color,
        )

    @staticmethod
    def error(text: str) -> Embed:
        """Ошибка экономической команды (без title-username)."""
        return Embed.error(description=text)

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
            
        embed = Embed(
            title=f"{action} — {user.display_name}",
            description="\n".join(lines).strip(),
            color=color,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        return embed

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