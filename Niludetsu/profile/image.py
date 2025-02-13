import os, aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from easy_pil import Editor, Font
from typing import Tuple
from .models import ProfileData

class ProfileImage:
    def __init__(self):
        self.font_path_regular = os.path.join('data', 'fonts', 'TTNormsPro-Regular.ttf')
        self.font_path_bold = os.path.join('data', 'fonts', 'TTNormsPro-Bold.ttf')
        self.font_path_emoji = os.path.join('data', 'fonts', 'NotoColorEmoji.ttf')
        
        # Проверяем наличие шрифтов
        if not os.path.exists(self.font_path_emoji):
            self.font_path_emoji = None
            print("Шрифт эмодзи не найден, будут использованы текстовые символы")

    def get_emoji_font(self) -> ImageFont.FreeTypeFont:
        """Получить шрифт для эмодзи с проверкой"""
        if self.font_path_emoji:
            try:
                return ImageFont.truetype(self.font_path_emoji, size=109)  # Фиксированный размер для NotoColorEmoji
            except Exception as e:
                print(f"Ошибка загрузки шрифта эмодзи: {e}")
                self.font_path_emoji = None
        return None

    def get_text_width(self, text: str, font: Font) -> int:
        """Получить ширину текста"""
        return font.getsize(text)[0]

    async def load_image_async(self, url: str) -> Image:
        """Загрузить изображение по URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch image: {response.status}")
                data = await response.read()
                return Image.open(BytesIO(data))

    def rounded_rectangle(self, draw: ImageDraw, x1: int, y1: int, x2: int, y2: int, 
                         radius: int, fill=None, outline=None) -> None:
        """Нарисовать прямоугольник с закругленными углами"""
        diameter = radius * 2
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        if diameter <= (x2 - x1) and diameter <= (y2 - y1): 
            draw.ellipse((x1, y1, x1 + diameter, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y1, x2, y1 + diameter), fill=fill, outline=outline)
            draw.ellipse((x1, y2 - diameter, x1 + diameter, y2), fill=fill, outline=outline)
            draw.ellipse((x2 - diameter, y2 - diameter, x2, y2), fill=fill, outline=outline)
            draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill, outline=outline)
            draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill, outline=outline)
        else:
            draw.rectangle((x1, y1, x2, y2), fill=fill, outline=outline)

    def create_card(self, draw: ImageDraw, x: int, y: int, width: int, height: int, 
                   color: tuple = (23, 24, 26, 255)) -> None:
        """Создать карточку с тенью"""
        self.rounded_rectangle(draw, x, y, x+width, y+height, 15, fill=color)

    def draw_emoji(self, background: Editor, x: int, y: int, emoji: str, font: ImageFont.FreeTypeFont, scale: float = 0.15) -> None:
        """Нарисовать эмодзи с масштабированием"""
        # Создаем временное изображение большего размера для эмодзи
        temp = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp)
        
        # Рисуем эмодзи в центре временного изображения
        temp_draw.text((0, 0), emoji, font=font, embedded_color=True)
        bbox = temp.getbbox()
        if bbox:
            cropped = temp.crop(bbox)
            # Используем фиксированный размер для всех эмодзи
            fixed_size = 20  # фиксированный размер в пикселях
            resized = cropped.resize((fixed_size, fixed_size), Image.Resampling.LANCZOS)
            # Накладываем на фон
            background.paste(resized, (x, y))

    def draw_custom_icon(self, background: Editor, x: int, y: int, icon_path: str, size: int = 22) -> None:
        """Нарисовать кастомную иконку"""
        try:
            icon = Image.open(icon_path).convert('RGBA')
            icon = icon.resize((size, size), Image.Resampling.LANCZOS)
            background.paste(icon, (x, y))
        except Exception as e:
            print(f"Ошибка загрузки иконки: {e}")

    async def create_profile_image(self, profile_data: ProfileData, 
                                 user_name: str, avatar_url: str) -> BytesIO:
        """Создать изображение профиля"""
        # Создаем фон
        background = Editor(Image.new('RGBA', (1000, 450), color=(18, 18, 18, 255)))

        # Создаем карточки
        # Левая карточка (профиль)
        self.create_card(ImageDraw.Draw(background.image), 20, 20, 450, 260)
        # Правая карточка (баланс и статистика)
        self.create_card(ImageDraw.Draw(background.image), 490, 20, 490, 260)
        # Нижняя карточка (биография)
        self.create_card(ImageDraw.Draw(background.image), 20, 300, 960, 130)

        # Загружаем и добавляем аватар
        profile_image = await self.load_image_async(avatar_url)
        profile_image = Editor(profile_image).resize((120, 120)).circle_image()
        
        # Создаем обводку для аватара
        circle_border = Image.new('RGBA', (130, 130), (0, 0, 0, 0))
        draw = ImageDraw.Draw(circle_border)
        draw.ellipse((0, 0, 129, 129), outline=(88, 101, 242, 255), width=3)
        circle_border = Editor(circle_border)
        
        # Накладываем аватар и обводку
        background.paste(profile_image, (45, 45))
        background.paste(circle_border, (40, 40))

        # Загружаем шрифты
        font_regular = Font(self.font_path_regular, size=20)
        font_small = Font(self.font_path_regular, size=18)
        font_bold = Font(self.font_path_bold, size=32)
        font_emoji = self.get_emoji_font()

        # Функция для отрисовки текста с эмодзи
        def draw_with_emoji(x: int, y: int, emoji: str, text: str, text_font: Font, text_color: str):
            if font_emoji:
                # Рисуем эмодзи с масштабированием
                self.draw_emoji(background, x, y-1, emoji, font_emoji)  # Немного подняли эмодзи
                background.text((x + 25, y), text, font=text_font, color=text_color)  # Добавили отступ
            else:
                # Если шрифт эмодзи недоступен, используем обычный текст
                background.text((x, y), text, font=text_font, color=text_color)

        # Левая карточка
        # Имя пользователя
        background.text((40, 180), user_name, font=font_bold, color="white")
        
        # Рассчитываем XP и уровень
        next_level_xp = profile_data.calculate_next_level_xp()
        xp_percentage = min(profile_data.xp / next_level_xp * 100, 100)
        
        # Уровень и XP
        draw_with_emoji(40, 220, "⭐", f"Уровень {profile_data.level}", font_regular, "#5865F2")
        background.text((200, 220), f"{profile_data.xp}/{next_level_xp} XP", font_small, color="#72767d")
        
        # Прогресс-бар уровня
        bar_width = 350
        bar_height = 8
        bar_x = 40
        bar_y = 250
        
        # Фон прогресс-бара
        self.rounded_rectangle(
            ImageDraw.Draw(background.image),
            bar_x, bar_y,
            bar_x + bar_width, bar_y + bar_height,
            4, fill=(47, 49, 54, 255)
        )
        
        # Заполненная часть прогресс-бара
        filled_width = int(bar_width * (xp_percentage / 100))
        if filled_width > 0:
            self.rounded_rectangle(
                ImageDraw.Draw(background.image),
                bar_x, bar_y,
                bar_x + filled_width, bar_y + bar_height,
                4, fill=(88, 101, 242, 255)
            )

        # Правая карточка
        # Разделяем правую карточку на две колонки
        # Баланс (левая колонка)
        background.text((510, 40), "БАЛАНС", font=font_bold, color="#5865F2")
        
        # Форматируем текст с гривнами
        total_text = f"Всего: {profile_data.total_balance:,} ₴"
        bank_text = f"Банк: {profile_data.deposit:,} ₴"
        cash_text = f"Наличка: {profile_data.balance:,} ₴"
        
        # Рисуем текст и эмодзи
        draw_with_emoji(510, 90, "💎", total_text, font_regular, "#72767d")
        draw_with_emoji(510, 120, "🏦", bank_text, font_regular, "#72767d")
        draw_with_emoji(510, 150, "💵", cash_text, font_regular, "#72767d")

        # Статистика (правая колонка)
        background.text((700, 40), "СТАТИСТИКА", font=font_bold, color="#5865F2")
        
        draw_with_emoji(700, 90, "🎤", f"Время в ГС: {profile_data.format_voice_time()}", font_regular, "#72767d")
        draw_with_emoji(700, 120, "💬", f"Сообщений: {profile_data.messages_count:,}", font_regular, "#72767d")

        # Биография (в нижней карточке)
        background.text((40, 320), "ИНФОРМАЦИЯ", font=font_bold, color="#5865F2")
        
        bio_text = []
        if profile_data.name:
            bio_text.append(("👤", f"Имя: {profile_data.name}"))
        if profile_data.birthday:  # Добавляем дату рождения
            bio_text.append(("🎂", f"День рождения: {profile_data.birthday}"))
            if profile_data.age is not None:  # Добавляем возраст, только если он вычислен
                bio_text.append(("📅", f"Возраст: {profile_data.age} лет"))
        if profile_data.country:
            bio_text.append(("🌍", f"Страна: {profile_data.country}"))
        
        if bio_text:
            x_pos = 40
            y_pos = 360
            for i, (emoji, info) in enumerate(bio_text):
                draw_with_emoji(x_pos, y_pos, emoji, info, font_regular, "#72767d")
                if i < len(bio_text) - 1:
                    text_width = self.get_text_width(info, font_regular)
                    background.text((x_pos + 35 + text_width + 5, y_pos), "|", font=font_regular, color="#72767d")
                    x_pos += text_width + 55
        else:
            # Если нет информации, показываем сообщение
            draw_with_emoji(40, 360, "⚠️", "Информация не заполнена", font_regular, "#72767d")
            draw_with_emoji(40, 385, "💡", "Используйте /profile set для заполнения", font_regular, "#72767d")
        
        if profile_data.bio:
            bio = profile_data.bio[:100] + "..." if len(profile_data.bio) > 100 else profile_data.bio
            draw_with_emoji(40, 410 if not bio_text else 390, "📝", f"О себе: {bio}", font_regular, "#72767d")

        return background.image_bytes 