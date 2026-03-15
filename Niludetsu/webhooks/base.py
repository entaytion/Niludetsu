"""
Базовий клас для всіх логерів.
Шарений Webhooks інстанс, утиліти для audit log та temp файлів.
"""

import os
import tempfile
import discord
from Niludetsu.development.Webhooks import Webhooks


class BaseLogger:
    def __init__(self, bot: discord.Client, webhooks: Webhooks):
        self.bot = bot
        self.webhooks = webhooks

    async def _safe_audit_log(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: int,
        limit: int = 3,
    ) -> discord.User | None:
        """Безпечне отримання юзера з audit log."""
        try:
            async for entry in guild.audit_logs(limit=limit, action=action):
                if entry.target and entry.target.id == target_id:
                    return entry.user
        except Exception:
            pass
        return None

    @staticmethod
    def _temp_file(content: str, prefix: str, suffix: str = ".txt") -> tuple[discord.File, str]:
        """Створити тимчасовий файл, повертає (discord.File, шлях для cleanup)."""
        f = tempfile.NamedTemporaryFile(
            mode='w', prefix=prefix, suffix=suffix,
            delete=False, encoding='utf-8'
        )
        f.write(content)
        f.close()
        return discord.File(f.name, filename=os.path.basename(f.name)), f.name

    @staticmethod
    def _cleanup(path: str | None):
        """Безпечне видалення тимчасового файлу."""
        if path:
            try:
                os.remove(path)
            except Exception:
                pass
