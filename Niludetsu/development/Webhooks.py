import asyncio
import discord
from ..tools.Embed import Colors, Embed
from ..tools.Time import TimeService

from typing import Iterable, Optional

_WEBHOOK_NAME = "Æther!"
_time = TimeService()

class Webhooks:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self._webhook_cache: dict[int, discord.Webhook] = {}
        self._avatar_bytes: bytes | None = None
        self._locks: dict[int, asyncio.Lock] = {}
        self.webhook_avatar_url = "https://entaytion.vercel.app/ae/aeCatalog.png"

    async def _get_avatar_bytes(self) -> Optional[bytes]:
        if self._avatar_bytes is None:
            user = getattr(self.bot, "user", None)
            if not user:
                return None
            try:
                self._avatar_bytes = await user.display_avatar.read()
            except discord.HTTPException:
                self._avatar_bytes = None
        return self._avatar_bytes

    async def get_or_create_webhook(
        self,
        channel: discord.TextChannel,
        *,
        name: str = _WEBHOOK_NAME,
    ) -> Optional[discord.Webhook]:
        cached = self._webhook_cache.get(channel.id)
        if cached:
            return cached

        # Lock per channel щоб не створювати дублі при паралельних евентах
        if channel.id not in self._locks:
            self._locks[channel.id] = asyncio.Lock()

        async with self._locks[channel.id]:
            # Перевіряємо кеш ще раз під локом
            cached = self._webhook_cache.get(channel.id)
            if cached:
                return cached

            webhooks = await channel.webhooks()
            for webhook in webhooks:
                if webhook.name == name:
                    self._webhook_cache[channel.id] = webhook
                    return webhook

            avatar_bytes = await self._get_avatar_bytes()
            try:
                webhook = await channel.create_webhook(name=name, avatar=avatar_bytes)
            except (discord.Forbidden, discord.HTTPException):
                return None

            self._webhook_cache[channel.id] = webhook
            return webhook

    async def _send_webhook(
        self,
        webhook: discord.Webhook,
        *,
        channel: discord.TextChannel,
        payload: dict,
        name: str,
    ) -> None:
        """
        Единоразовая попытка отправить сообщение.
        Если вебхук пропал, выбрасывает discord.NotFound.
        """
        await webhook.send(
            username=name,
            avatar_url=self.webhook_avatar_url,
            **payload,
        )

    async def send_log(
        self,
        channel: discord.TextChannel,
        title: str,
        description: Optional[str] = None,
        *,
        color: int = Colors.PRIMARY,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        fields: Optional[Iterable[dict]] = None,
        guild: Optional[discord.Guild] = None,
        changes: Optional[str] = None,
        webhook_name: str = _WEBHOOK_NAME,
        **kwargs,
    ) -> None:
        webhook = await self.get_or_create_webhook(channel, name=webhook_name)
        if webhook is None:
            return

        embed = Embed(
            title=title,
            description=description or "",
            color=color,
            image=image_url,
            thumbnail=thumbnail_url,
            timestamp=False,
        )

        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", "—"),
                    value=field.get("value", "—"),
                    inline=field.get("inline", False),
                )

        if changes:
            embed.add_field(name="> Изменения", value=changes, inline=False)

        footer_parts = []
        if guild:
            footer_parts.append(f"ID сервера: {guild.id}")
        footer_parts.append(_time.format_datetime(embed.timestamp))
        embed.set_footer(text=" | ".join(footer_parts))

        kwargs.pop("attachments", None)

        if kwargs.get("file") is None:
            kwargs.pop("file", None)

        files = kwargs.get("files")
        if files is not None:
            cleaned = [f for f in files if f is not None]
            if cleaned:
                kwargs["files"] = cleaned
            else:
                kwargs.pop("files", None)

        payload = {"embed": embed, **kwargs}

        try:
            await self._send_webhook(
                webhook,
                channel=channel,
                payload=payload,
                name=webhook_name,
            )
        except discord.NotFound:
            # Вебхук исчез → очищаем кеш и создаём заново
            self._webhook_cache.pop(channel.id, None)
            fresh = await self.get_or_create_webhook(channel, name=webhook_name)
            if fresh is None:
                return
            try:
                await self._send_webhook(
                    fresh,
                    channel=channel,
                    payload=payload,
                    name=webhook_name,
                )
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return
        except (discord.Forbidden, discord.HTTPException):
            return

