import aiohttp, discord, io
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from Niludetsu.image.core import ImageResources
from PIL import Image, ImageChops, ImageDraw, ImageFont
from typing import Any, Dict, Optional, Sequence, Tuple

class ProfileGenerator:

    CANVAS_SIZE: Tuple[int, int] = (1920, 1060)
    AVATAR_OVERLAY_SIZE: Tuple[int, int] = (500, 500)
    AVATAR_FOREGROUND_SIZE: Tuple[int, int] = (300, 300)
    AVATAR_OVERLAY_POS: Tuple[int, int] = (40, 40)
    AVATAR_FOREGROUND_POS: Tuple[int, int] = (140, 140)
    AVATAR_CORNER_RADIUS: int = 50
    LETTER_SPACING_RATIO: float = -0.05
    FONT_FILE: str = "FixelVariable.ttf"

    def __init__(self) -> None:
        self.resources = ImageResources()
        self._avatar_cache: Dict[str, Image.Image] = {}
        self.font_path = self.resources.fonts_dir / self.FONT_FILE
        if not self.font_path.exists():
            raise FileNotFoundError(
                f"Не найден шрифт {self.FONT_FILE} по пути {self.font_path}"
            )
        self._font_cache: Dict[Tuple[int, int], ImageFont.FreeTypeFont] = {}

    async def _load_avatar(self, url: str) -> Optional[Image.Image]:
        if not url:
            return None
        if url in self._avatar_cache:
            return self._avatar_cache[url].copy()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    data = await response.read()
        except Exception:
            return None
        try:
            avatar = Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            return None
        self._avatar_cache[url] = avatar
        return avatar.copy()

    @staticmethod
    def _apply_opacity(image: Image.Image, alpha: int) -> Image.Image:
        rgba = image.copy()
        if rgba.mode != "RGBA":
            rgba = rgba.convert("RGBA")
        r, g, b, original_alpha = rgba.split()
        new_alpha = original_alpha.point(lambda _: alpha)
        rgba.putalpha(new_alpha)
        return rgba

    def _create_vertical_gradient(
        self,
        size: Tuple[int, int],
        start_color: str,
        end_color: str,
        *,
        start_alpha: int = 0,
        end_alpha: int = 255,
    ) -> Image.Image:
        width, height = size

        start_rgb = tuple(int(start_color.strip("#")[i:i + 2], 16) for i in (0, 2, 4))
        end_rgb = tuple(int(end_color.strip("#")[i:i + 2], 16) for i in (0, 2, 4))

        y_positions = np.linspace(0, 1, height, dtype=np.float32)

        r_channel = (start_rgb[0] + (end_rgb[0] - start_rgb[0]) * y_positions).astype(np.uint8)
        g_channel = (start_rgb[1] + (end_rgb[1] - start_rgb[1]) * y_positions).astype(np.uint8)
        b_channel = (start_rgb[2] + (end_rgb[2] - start_rgb[2]) * y_positions).astype(np.uint8)
        a_channel = (start_alpha + (end_alpha - start_alpha) * y_positions).astype(np.uint8)

        gradient_array = np.zeros((height, width, 4), dtype=np.uint8)
        gradient_array[:, :, 0] = r_channel[:, np.newaxis]
        gradient_array[:, :, 1] = g_channel[:, np.newaxis]
        gradient_array[:, :, 2] = b_channel[:, np.newaxis]
        gradient_array[:, :, 3] = a_channel[:, np.newaxis]

        gradient = Image.fromarray(gradient_array, mode="RGBA")
        return gradient

    def _create_top_rounded_mask(self, size: Tuple[int, int], radius: int) -> Image.Image:
        width, height = size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((radius, 0, width - radius, height), fill=255)
        draw.rectangle((0, radius, width, height), fill=255)
        corner = Image.new("L", (radius * 2, radius * 2), 0)
        corner_draw = ImageDraw.Draw(corner)
        corner_draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
        mask.paste(corner, (0, 0))
        mask.paste(corner.rotate(90), (width - radius * 2, 0))
        return mask

    @staticmethod
    def _create_circle_mask(size: Tuple[int, int]) -> Image.Image:
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        return mask

    @staticmethod
    def _make_circle_image(image: Image.Image) -> Image.Image:
        size = image.size
        mask = ProfileGenerator._create_circle_mask(size)

        output = Image.new("RGBA", size, (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)

        return output

    def _get_font(self, weight: int, size: int) -> ImageFont.FreeTypeFont:
        key = (weight, size)
        if key in self._font_cache:
            return self._font_cache[key]
        instance_path = self.resources.instances_dir / f"fixel_{weight}_{size}.ttf"
        if not instance_path.exists():
            tt_font = TTFont(str(self.font_path))
            instance = instantiateVariableFont(tt_font, {"wght": weight})
            instance.save(str(instance_path))
        font_obj = ImageFont.truetype(str(instance_path), size=size)
        self._font_cache[key] = font_obj
        return font_obj

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        return text[:limit] if len(text) > limit else text

    @staticmethod
    def _format_currency(value: int) -> str:
        return f"{int(value):,}".replace(",", " ")

    @staticmethod
    def _format_voice_duration(seconds: int) -> str:
        if seconds <= 0:
            return "0ч 0м"
        total_minutes = seconds // 60
        total_hours = total_minutes // 60
        minutes = total_minutes % 60
        days = total_hours // 24
        hours = total_hours % 24
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        return f"{total_hours}ч {minutes}м"

    def _measure_text(
        self, 
        text: str, 
        font: ImageFont.FreeTypeFont, 
        spacing_ratio: float | None
    ) -> Tuple[float, float]:
        if not text:
            return 0.0, 0.0

        letter_spacing = (font.size * spacing_ratio) if spacing_ratio else 0.0
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
        spacing_ratio: float | None,
    ) -> None:
        if not text:
            return

        letter_spacing = (font.size * spacing_ratio) if spacing_ratio else 0.0
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
        text_width, text_height = self._measure_text(text, font, spacing)
        draw = ImageDraw.Draw(image)
        start_x = x + (width - text_width) / 2
        start_y = y + (height - text_height) / 2
        self._render_text(draw, text, font, color, start_x, start_y, spacing)

    def _draw_right_aligned_text(
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
        text_width, text_height = self._measure_text(text, font, spacing)
        draw = ImageDraw.Draw(image)
        start_x = x + width - text_width
        start_y = y + (height - text_height) / 2
        self._render_text(draw, text, font, color, start_x, start_y, spacing)

    def _draw_multiline_centered(
        self,
        image: Image.Image,
        lines: Sequence[str],
        *,
        box: Tuple[int, int, int, int],
        font: ImageFont.FreeTypeFont,
        color: str,
        spacing: float | None = None,
        line_gap: int = 12,
    ) -> None:
        widths_heights = [self._measure_text(line, font, spacing) for line in lines]
        total_height = sum(h for _, h in widths_heights) + line_gap * (len(lines) - 1 if lines else 0)
        x, y, width, height = box
        draw = ImageDraw.Draw(image)
        current_y = y + (height - total_height) / 2
        for (line, (line_width, line_height)) in zip(lines, widths_heights):
            start_x = x + (width - line_width) / 2
            self._render_text(draw, line, font, color, start_x, current_y, spacing)
            current_y += line_height + line_gap

    async def generate(
        self,
        user: discord.Member,
        profile: Dict[str, Any],
        economy: Dict[str, Any],
        analytics: Dict[str, Any],
        marriage: Optional[Dict[str, Any]] = None,
        partner: Optional[discord.Member] = None,
        achievements_count: int = 0,
    ) -> Optional[bytes]:
        import asyncio
        avatar = await self._load_avatar(str(user.display_avatar.replace(size=512).url))
        partner_avatar = await self._load_avatar(str(partner.display_avatar.replace(size=512).url)) if partner else None

        def build_sync() -> bytes:
            background_path = self.resources.image_path("profile.jpg")
            if not background_path.exists():
                background_path = self.resources.image_path("profile.png")
            if not background_path.exists():
                raise FileNotFoundError("Не найден шаблон profile.jpg или profile.png в data/images")

            background = Image.open(str(background_path)).convert("RGBA")

            bold64 = self._get_font(700, 64)
            medium32 = self._get_font(500, 32)

            if avatar:
                overlay = avatar.resize(self.AVATAR_OVERLAY_SIZE, Image.LANCZOS)
                overlay = self._apply_opacity(overlay, 128)
                mask = self._create_top_rounded_mask(self.AVATAR_OVERLAY_SIZE, self.AVATAR_CORNER_RADIUS)
                overlay_alpha = overlay.split()[3]
                overlay.putalpha(ImageChops.multiply(overlay_alpha, mask))
                gradient = self._create_vertical_gradient(
                    self.AVATAR_OVERLAY_SIZE,
                    "#000000",
                    "#212121",
                    start_alpha=0,
                    end_alpha=255,
                )
                blended_overlay = Image.alpha_composite(overlay, gradient)
                background.paste(blended_overlay, self.AVATAR_OVERLAY_POS, blended_overlay)

                circle_avatar = self._make_circle_image(
                    avatar.copy().resize(self.AVATAR_FOREGROUND_SIZE, Image.LANCZOS)
                )
                background.paste(circle_avatar, self.AVATAR_FOREGROUND_POS, circle_avatar)

            display_name = self._truncate(user.display_name, 14)
            username = self._truncate(f"@{user.name}", 26)
            self._draw_centered_text(
                background,
                display_name,
                box=(40, 458, 500, 88),
                font=bold64,
                color="#FFFFFF",
                spacing=self.LETTER_SPACING_RATIO,
            )
            self._draw_centered_text(
                background,
                username,
                box=(40, 546, 500, 44),
                font=medium32,
                color="#A4A4A4",
                spacing=self.LETTER_SPACING_RATIO,
            )

            balance_value = max(0, int(economy.get("balance", 0)))
            deposit_value = max(0, int(economy.get("deposit", 0)))
            self._draw_right_aligned_text(
                background,
                self._format_currency(balance_value),
                box=(208, 768, 300, 88),
                font=bold64,
                color="#FFFFFF",
                spacing=self.LETTER_SPACING_RATIO,
            )
            self._draw_right_aligned_text(
                background,
                self._format_currency(deposit_value),
                box=(208, 903, 300, 88),
                font=bold64,
                color="#FFFFFF",
                spacing=self.LETTER_SPACING_RATIO,
            )

            if partner:
                if partner_avatar:
                    partner_circle = self._make_circle_image(
                        partner_avatar.resize((280, 280), Image.LANCZOS)
                    )
                    background.paste(partner_circle, (715, 165), partner_circle)
                partner_display = self._truncate(partner.display_name, 15)
                partner_username = self._truncate(f"@{partner.name}", 28)
                self._draw_centered_text(
                    background,
                    partner_display,
                    box=(580, 440, 550, 88),
                    font=bold64,
                    color="#FFFFFF",
                    spacing=self.LETTER_SPACING_RATIO,
                )
                self._draw_centered_text(
                    background,
                    partner_username,
                    box=(580, 528, 550, 44),
                    font=medium32,
                    color="#A4A4A4",
                    spacing=self.LETTER_SPACING_RATIO,
                )
            else:
                self._draw_multiline_centered(
                    background,
                    ["Мы верим,", "что найдёте!"],
                    box=(580, 227, 550, 176),
                    font=bold64,
                    color="#FFFFFF",
                    spacing=self.LETTER_SPACING_RATIO,
                    line_gap=24,
                )

            messages_total = max(0, int(analytics.get("messages_total", 0)))
            voice_seconds = max(0, int(analytics.get("voice_seconds", 0)))
            reputation_value = int(profile.get("reputation", 0))
            self._draw_right_aligned_text(
                background,
                self._format_currency(messages_total),
                box=(1535, 198, 310, 88),
                font=bold64,
                color="#3D1FD4",
                spacing=self.LETTER_SPACING_RATIO,
            )
            self._draw_right_aligned_text(
                background,
                self._format_voice_duration(voice_seconds),
                box=(1535, 335, 310, 88),
                font=bold64,
                color="#3D1FD4",
                spacing=self.LETTER_SPACING_RATIO,
            )
            self._draw_right_aligned_text(
                background,
                self._format_currency(reputation_value),
                box=(1535, 472, 310, 88),
                font=bold64,
                color="#3D1FD4",
                spacing=self.LETTER_SPACING_RATIO,
            )

            buffer = io.BytesIO()
            background.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()
            
        return await asyncio.to_thread(build_sync)

async def setup(bot):
    return None

