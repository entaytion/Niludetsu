from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext import commands
    from Niludetsu.config_manager import ConfigManager

_bot: commands.Bot | None = None


def set_bot(bot: commands.Bot) -> None:
    global _bot
    _bot = bot


def get_bot() -> commands.Bot | None:
    return _bot


def get_config_manager() -> "ConfigManager | None":
    if _bot is None:
        return None
    return getattr(_bot, "config_manager", None)
