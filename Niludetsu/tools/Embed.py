import discord
from dataclasses import dataclass
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Time import TimeService
from typing import Optional, Sequence

@dataclass(frozen=True)
class Colors:
    PRIMARY: int = 0x000001
    ERROR: int = 0xF20C3C
    WARNING: int = 0xF2F20C
    SUCCESS: int = 0x0CF232
    INFO: int = 0x820CF2
_time = TimeService()

def _normalize_timestamp(value: Optional[object]) -> Optional[discord.utils.snowflake_time]:
    if value is True:
        return _time.now()
    if value in (None, False):
        return None
    return _time.ensure_datetime(value)

class Embed(discord.Embed):
    def __init__(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[Sequence[dict]] = None,
        footer: Optional[dict] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        author: Optional[dict] = None,
        url: Optional[str] = None,
        timestamp: Optional[object] = None,
        emoji: Optional[str] = None,
        inline_fields: bool = False,
        **kwargs,
    ) -> None:
        thumbnail = thumbnail or kwargs.pop("thumbnail_url", None)
        image = image or kwargs.pop("image_url", None)
        
        color = Colors.PRIMARY if color is None else color
        if emoji:
            title = f"{emoji} {title}" if title else emoji

        super().__init__(
            title=title,
            description=description,
            color=color,
            url=url,
            timestamp=_normalize_timestamp(timestamp),
            **kwargs,
        )

        if fields:
            for field in fields:
                self.add_field(**field)

        if inline_fields:
            for field in self.fields:
                field.inline = True

        if footer:
            self.set_footer(**footer)
        if thumbnail:
            self.set_thumbnail(url=thumbnail)
        if image:
            self.set_image(url=image)
        if author:
            self.set_author(**author)

    @classmethod
    def _base(cls, *, emoji: Optional[str], color: Optional[int], **kwargs) -> "Embed":
        override_color = kwargs.pop("color", None)
        resolved_color = override_color if override_color is not None else color
        return cls(emoji=emoji, color=resolved_color, **kwargs)

    @classmethod
    def default(cls, **kwargs) -> "Embed":
        color = kwargs.pop("color", Colors.PRIMARY)
        return cls._base(emoji=None, color=color, **kwargs)

    @classmethod
    def success(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Успешно!", emoji=Emojis.SUCCESS, color=Colors.SUCCESS, **kwargs)

    @classmethod
    def error(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Ошибка!", emoji=Emojis.ERROR, color=Colors.ERROR, **kwargs)

    @classmethod
    def warning(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Предупреждение!", emoji=Emojis.WARNING, color=Colors.WARNING, **kwargs)

    @classmethod
    def info(cls, title: Optional[str] = None, **kwargs) -> "Embed":
        return cls._base(title=title or "Информация!", emoji=Emojis.UNKNOWN, color=Colors.INFO, **kwargs)