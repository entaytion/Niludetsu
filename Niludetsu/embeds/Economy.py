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