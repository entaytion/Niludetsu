from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from pathlib import Path
from PIL import ImageFont
from typing import Dict

class ImageResources:
    """Универсальный менеджер ресурсов: шрифты, шаблоны, директории."""

    WEIGHT_MAP: Dict[str, int] = {
        "light": 300,
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
    }

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[2]
        self.fonts_dir = self.base_dir / "data" / "fonts"
        self.images_dir = self.base_dir / "data" / "images"
        self.instances_dir = self.fonts_dir / "instances"
        self.variable_font_path = self.fonts_dir / "Bounded-Variable.ttf"

        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)

        if not self.variable_font_path.exists():
            raise FileNotFoundError(
                f"Вариативный шрифт не найден: {self.variable_font_path}\n"
                "Положите Bounded-Variable.ttf в data/fonts."
            )

        self._font_cache: Dict[str, ImageFont.FreeTypeFont] = {}

    def get_font(self, weight: str, size: int) -> ImageFont.FreeTypeFont:
        """Возвращает инстанс вариативного шрифта с нужным весом и размером."""
        weight_value = self.WEIGHT_MAP.get(weight.lower(), self.WEIGHT_MAP["regular"])
        cache_key = f"{weight_value}_{size}"

        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        instance_path = self.instances_dir / f"bounded_{weight_value}_{size}.ttf"
        if not instance_path.exists():
            font = TTFont(self.variable_font_path)
            instance = instantiateVariableFont(font, {"wght": weight_value})
            instance.save(instance_path)

        font = ImageFont.truetype(str(instance_path), size=size)
        self._font_cache[cache_key] = font
        return font

    def image_path(self, *parts: str) -> Path:
        """Возвращает путь к изображению в data/images."""
        return self.images_dir.joinpath(*parts)

