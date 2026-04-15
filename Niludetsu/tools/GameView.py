"""Базовый View для игровых когов."""

from __future__ import annotations

import discord

from Niludetsu.tools.Discord import safe_edit


class GameView(discord.ui.View):
    """Базовый View с общей логикой отключения кнопок."""

    message: discord.Message | None

    async def disable_all(self) -> None:
        """Отключить все кнопки и обновить сообщение."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await safe_edit(self.message, view=self)
