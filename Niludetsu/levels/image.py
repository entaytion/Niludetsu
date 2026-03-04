import aiohttp, discord, io
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from Niludetsu.image.core import ImageResources
from Niludetsu.levels.manager import LevelManager
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont
from typing import Dict, Tuple

class LevelCardRenderer:
    """Формирует PNG-карточку уровня на основе шаблона и данных профиля."""

    PROGRESS_COLOR = "#E6B632"
    PROGRESS_BG = "#433C2D"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#A4A4A4"
    TEXT_ACCENT = "#E6B632"
    EXP_TEXT_COLOR = "#654790"

    def __init__(self, background_path: str | None = None) -> None:
        self.resources = ImageResources()

        if background_path:
            self.background_path = Path(background_path)
        else:
            primary = self.resources.image_path("level.jpg")
            fallback = self.resources.image_path("level.png")
            self.background_path = primary if primary.exists() else fallback

        if not self.background_path.exists():
            raise FileNotFoundError(
                f"Не найден шаблон карточки уровня: {self.background_path}\n"
                "Положите level.jpg или level.png в Niludetsu/data/images или передайте путь вручную."
            )

        self.font_path = self.resources.fonts_dir / "FixelVariable.ttf"
        if not self.font_path.exists():
            raise FileNotFoundError(
                f"Не найден шрифт FixelVariable.ttf в {self.font_path}"
            )

        self._font_cache: Dict[Tuple[int, int], ImageFont.FreeTypeFont] = {}

        self.levels = LevelManager()

    async def _load_image_async(self, url: str) -> Image.Image | None:
        """Асинхронная загрузка изображения по URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    data = await response.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            return None

    @staticmethod
    def _make_circle_image(image: Image.Image) -> Image.Image:
        """Преобразует изображение в круглое."""
        size = image.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)

        output = Image.new("RGBA", size, (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)

        return output

    def _draw_rounded_rectangle(
        self,
        image: Image.Image,
        position: Tuple[int, int],
        size: Tuple[int, int],
        color: str,
        radius: int,
    ) -> None:
        """Рисует скругленный прямоугольник."""
        x, y = position
        width, height = size

        # Создаем временное изображение для прямоугольника
        rect_img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(rect_img)
        draw.rounded_rectangle(
            [(0, 0), (width, height)],
            radius=radius,
            fill=color
        )

        # Накладываем на основное изображение
        image.paste(rect_img, (x, y), rect_img)

    async def render(
        self,
        member: discord.Member,
        profile: Dict[str, int],
    ) -> bytes:
        """Строит карточку и возвращает PNG в виде байтов."""
        # Загружаем фоновое изображение
        background = Image.open(str(self.background_path)).convert("RGBA")

        level = int(profile.get("level", 1))
        exp = max(0, int(profile.get("experience", 0)))
        needed = max(1, self.levels.next_level_xp(level))
        progress_ratio = min(1.0, exp / needed) if needed else 0.0

        # Загрузка и обработка аватара
        avatar_url = member.display_avatar.replace(size=512).url
        avatar = await self._load_image_async(avatar_url)

        if avatar:
            # Большой полупрозрачный аватар на фоне
            large_avatar = avatar.resize((500, 500), Image.LANCZOS)
            translucent = self._apply_opacity(large_avatar, 128)

            gradient_overlay = self._create_vertical_gradient(
                (500, 500),
                "#000000",
                "#212121",
                start_alpha=0,
                end_alpha=255,
            )
            blended = Image.alpha_composite(translucent, gradient_overlay)
            mask = self._create_top_rounded_mask((500, 500), 50)
            blended_alpha = blended.split()[3]
            blended.putalpha(ImageChops.multiply(blended_alpha, mask))
            background.paste(blended, (26, 68), blended)

            # Круглый аватар поверх
            circle_avatar = self._make_circle_image(avatar.copy().resize((300, 300), Image.LANCZOS))
            background.paste(circle_avatar, (126, 168), circle_avatar)

        display_name = self._truncate(member.display_name, 14)
        username = self._truncate(f"@{member.name}", 26)
        level_next = level + 1

        # Отрисовка текста
        self._draw_centered_text(
            background,
            display_name,
            box=(26, 488, 500, 78),
            font=self._get_font(700, 64),
            color=self.TEXT_PRIMARY,
            spacing=-0.05,
        )

        self._draw_centered_text(
            background,
            username,
            box=(26, 556, 500, 36),
            font=self._get_font(500, 32),
            color=self.TEXT_SECONDARY,
            spacing=-0.05,
        )

        self._draw_centered_text(
            background,
            str(level),
            box=(566, 214, 550, 256),
            font=self._get_font(700, 256),
            color=self.TEXT_ACCENT,
        )

        self._draw_centered_text(
            background,
            str(level),
            box=(591, 473, 67, 55),
            font=self._get_font(500, 40),
            color=self.TEXT_ACCENT,
        )

        self._draw_centered_text(
            background,
            str(level_next),
            box=(1027, 473, 67, 55),
            font=self._get_font(500, 40),
            color=self.TEXT_ACCENT,
        )

        self._draw_centered_text(
            background,
            f"{exp:,}".replace(",", " "),
            box=(1156, 166, 724, 353),
            font=self._get_font(700, 256),
            color=self.EXP_TEXT_COLOR,
        )

        # Прогресс-бар
        bar_x, bar_y = 591, 535
        bar_w, bar_h = 500, 40
        radius = 60

        # Фон прогресс-бара
        self._draw_rounded_rectangle(
            background,
            (bar_x, bar_y),
            (bar_w, bar_h),
            self.PROGRESS_BG,
            radius
        )

        # Заполнение прогресс-бара
        fill_w = int(bar_w * progress_ratio)
        if fill_w > 0:
            # Создаем полный прогресс-бар
            fill_layer = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(fill_layer)
            draw.rounded_rectangle(
                [(0, 0), (bar_w, bar_h)],
                radius=radius,
                fill=self.PROGRESS_COLOR
            )
            # Обрезаем до нужной ширины
            cropped = fill_layer.crop((0, 0, fill_w, bar_h))
            background.paste(cropped, (bar_x, bar_y), cropped)

        # Сохранение в буфер
        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def _create_top_rounded_mask(self, size: Tuple[int, int], radius: int) -> Image.Image:
        width, height = size
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((radius, 0, width - radius, height), fill=255)
        draw.rectangle((0, radius, width, height), fill=255)
        corner = Image.new("L", (radius * 2, radius * 2), 0)
        corner_draw = ImageDraw.Draw(corner)
        corner_draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
        mask.paste(corner, (0, 0))
        mask.paste(corner.rotate(90), (width - radius * 2, 0))
        return mask

    def _create_vertical_gradient(
        self,
        size: Tuple[int, int],
        start: str,
        end: str,
        *,
        start_alpha: int = 255,
        end_alpha: int = 255,
    ) -> Image.Image:
        """Создает вертикальный градиент с плавными переходами без артефактов."""
        width, height = size

        # Парсим цвета
        start_rgb = tuple(int(start.strip("#")[i:i + 2], 16) for i in (0, 2, 4))
        end_rgb = tuple(int(end.strip("#")[i:i + 2], 16) for i in (0, 2, 4))

        # Создаем массив с float значениями для плавного градиента
        y_positions = np.linspace(0, 1, height, dtype=np.float32)

        # Интерполируем каждый канал отдельно (R, G, B, A)
        r_channel = (start_rgb[0] + (end_rgb[0] - start_rgb[0]) * y_positions).astype(np.uint8)
        g_channel = (start_rgb[1] + (end_rgb[1] - start_rgb[1]) * y_positions).astype(np.uint8)
        b_channel = (start_rgb[2] + (end_rgb[2] - start_rgb[2]) * y_positions).astype(np.uint8)
        a_channel = (start_alpha + (end_alpha - start_alpha) * y_positions).astype(np.uint8)

        # Создаем массив градиента (height, width, 4)
        gradient_array = np.zeros((height, width, 4), dtype=np.uint8)
        gradient_array[:, :, 0] = r_channel[:, np.newaxis]  # R
        gradient_array[:, :, 1] = g_channel[:, np.newaxis]  # G
        gradient_array[:, :, 2] = b_channel[:, np.newaxis]  # B
        gradient_array[:, :, 3] = a_channel[:, np.newaxis]  # A

        # Конвертируем numpy array в PIL Image
        gradient = Image.fromarray(gradient_array, mode="RGBA")
        return gradient

    def _apply_opacity(self, image: Image.Image, alpha: int) -> Image.Image:
        rgba = image.copy()
        if rgba.mode != "RGBA":
            rgba = rgba.convert("RGBA")
        r, g, b, a = rgba.split()
        blended_alpha = a.point(lambda _: alpha)
        rgba.putalpha(blended_alpha)
        return rgba

    def _truncate(self, text: str, limit: int) -> str:
        return text[:limit]

    def _measure_text(
        self, 
        text: str, 
        font: ImageFont.FreeTypeFont, 
        spacing: float | None
    ) -> Tuple[float, float]:
        """Измеряет размеры текста с учетом letter-spacing."""
        if not text:
            return 0.0, 0.0

        letter_spacing = (font.size * spacing) if spacing else 0.0
        width = 0.0
        height = 0.0

        for index, char in enumerate(text):
            bbox = font.getbbox(char)
            glyph_width = bbox[2] - bbox[0]
            glyph_height = bbox[3] - bbox[1]

            width += glyph_width
            if index < len(text) - 1:
                width += letter_spacing
            if glyph_height > height:
                height = glyph_height

        return width, height

    def _render_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: str,
        start_x: float,
        start_y: float,
        spacing: float | None,
    ) -> None:
        """Рендерит текст с кастомным letter-spacing."""
        if not text:
            return

        letter_spacing = (font.size * spacing) if spacing else 0.0
        cursor_x = start_x

        for index, char in enumerate(text):
            draw.text((cursor_x, start_y), char, font=font, fill=color)
            bbox = font.getbbox(char)
            glyph_width = bbox[2] - bbox[0]
            cursor_x += glyph_width
            if index < len(text) - 1:
                cursor_x += letter_spacing

    def _draw_centered_text(
        self,
        image: Image.Image,
        text: str,
        *,
        box: Tuple[int, int, int, int],
        font: ImageFont.FreeTypeFont,
        color: str,
        spacing: float | None = None,
    ) -> None:
        x, y, width, height = box
        if not text:
            return

        text_width, text_height = self._measure_text(text, font, spacing)
        draw = ImageDraw.Draw(image)
        start_x = x + (width - text_width) / 2
        start_y = y + (height - text_height) / 2
        self._render_text(draw, text, font, color, start_x, start_y, spacing)

    def _get_font(self, weight: int, size: int) -> ImageFont.FreeTypeFont:
        key = (weight, size)
        if key in self._font_cache:
            return self._font_cache[key]
        instance_path = self.resources.instances_dir / f"fixel_{weight}_{size}.ttf"
        if not instance_path.exists():
            font = TTFont(str(self.font_path))
            instance = instantiateVariableFont(font, {"wght": weight})
            instance.save(str(instance_path))
        font_obj = ImageFont.truetype(str(instance_path), size=size)
        self._font_cache[key] = font_obj
        return font_obj

