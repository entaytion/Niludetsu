from discord.ext import commands
from Niludetsu import Embed, config, Colors
from Niludetsu.api.ASCII import ascii_api
from Niludetsu.api.Color import color_api
from Niludetsu.api.Hash import hash_api
from Niludetsu.api.Math import math_calculator_api
from Niludetsu.api.MCServer import minecraft_server_api
from Niludetsu.api.QRCode import qrcode_api
from Niludetsu.api.Random import random_api
from Niludetsu.api.Screenshot import screenshot_api
from Niludetsu.api.Translate import translate_api
from Niludetsu.api.Translit import transliteration_api
from Niludetsu.api.Weather import weather_api
from Niludetsu.api.Whois import whois_api
from typing import Optional

class UtilitiesSystem(commands.Cog):
    """Ког с различными утилитами"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="whois", aliases=["domain"], description="Получить информацию о домене или IP-адресе")
    async def whois(self, ctx: commands.Context, *, target: str = None):
        """
        Получить WhoIs информацию о домене или IP-адресе

        Поддерживает:
        - Домены: google.com, discord.gg
        - IP-адреса: 8.8.8.8, 2001:4860:4860::8888
        - URL: https://github.com, http://example.com
        - Автоматическое извлечение домена из URL
        """
        await whois_api.whois_lookup(ctx, target)

    @commands.command(name="weather", description="Узнать погоду в указанном городе")
    async def weather(
        self,
        ctx: commands.Context,
        *,  # Позволяет передавать города с пробелами без кавычек
        city: str = None
    ):
        """Узнать погоду в указанном городе"""
        if city is None:
            raise commands.MissingRequiredArgument(ctx.command.params['city'])

        # Используем метод класса вместо функции
        await weather_api.get_weather_info(ctx, city)

    @commands.command(name="color", description="Конвертировать цвет между форматами")
    async def color(
        self,
        ctx: commands.Context,
        *,  # Позволяет передавать цвета с пробелами
        color: str = None
    ):
        """Конвертировать цвет между форматами"""
        if color is None:
            raise commands.MissingRequiredArgument(ctx.command.params['color'])

        await color_api.get_color_info(ctx, color)

    @commands.command(name="qrcode", description="Создать QR-код из текста или ссылки")
    async def qrcode(
        self,
        ctx: commands.Context,
        color: str = "#000000",
        *,
        content: str = None
    ):
        """Создать QR-код из текста или ссылки"""
        await qrcode_api.generate_qrcode(ctx, content, color)

    @commands.command(name="qrdecode", description="Декодировать QR-код из изображения")
    async def qrdecode(
        self,
        ctx: commands.Context
    ):
        """Декодировать QR-код из изображения"""
        if not ctx.message.attachments:
            await ctx.reply(embed=Embed.error(description="Прикрепите изображение с QR-кодом."))
            return

        image = ctx.message.attachments[0]
        await qrcode_api.decode_qrcode(ctx, image)

    @commands.command(name="mcserver", aliases=["minecraft", "mcinfo"], description="Получить информацию о Minecraft сервере")
    async def mcserver(
        self,
        ctx: commands.Context,
        address: str = None,
        port: int = None,
        edition: str = "java"
    ):
        """
        Получить информацию о Minecraft сервере

        Parameters:
        - address: IP адрес или домен сервера
        - port: Порт сервера (необязательно)
        - edition: Издание (java/bedrock)
        """
        if not address:
            embed = Embed.error(
                title="Недостаточно параметров",
                description="Укажите адрес сервера!\n**Использование:**\n"
                        "`!mcserver <адрес> [порт] [издание]`\n"
                        "**Примеры:**\n"
                        "`!mcserver hypixel.net`\n"
                        "`!mcserver 192.168.1.1 25565 java`\n"
                        "`!mcserver play.server.com 19132 bedrock`\n"
            )
            await ctx.reply(embed=embed)
            return

        # Определяем тип сервера
        is_bedrock = edition.lower() in ["bedrock", "be", "pocket", "mcpe"]

        await minecraft_server_api.get_server_info(ctx, address, port, is_bedrock)

    @commands.command(name="calc", aliases=["calculate", "math"], description="Вычислить математическое выражение")
    async def calc(self, ctx: commands.Context, *, expression: str = None):
        """
        Вычислить математическое выражение

        Поддерживает:
        - Базовые операции: +, -, *, /, ^(степень)
        - Функции: sin, cos, tan, sqrt, log, abs и др.
        - Константы: pi, e, tau
        - Неявное умножение: 2(3+4), 2pi, sin(x)cos(x)
        """
        await math_calculator_api.calculate(ctx, expression)

    @commands.command(name="rand", aliases=["random", "рандом"], description="Генерация случайного числа")
    async def rand(
        self,
        ctx: commands.Context,
        max_value: int = None,
        min_value: Optional[int] = None
    ):
        """Генерация случайного числа в указанном диапазоне"""
        if max_value is None:
            raise commands.MissingRequiredArgument(ctx.command.params['max_value'])
        await random_api.generate_random_number(ctx, max_value, min_value)

    @commands.command(name="ping", description="Проверка задержки бота")
    async def ping(self, ctx: commands.Context):
        """Проверка задержки бота"""
        latency = round(self.bot.latency * 1000)

        embed = Embed.default(
            title="🏓 Понг!",
            description=f"- Задержка бота: **`{latency}мс`**",
            color=Colors.SUCCESS if latency < 200 else Colors.WARNING if latency < 400 else Colors.ERROR
        )

        await ctx.reply(embed=embed)

    @commands.command(name="t", description="Транслитерация текста между кириллицей и латиницей")
    async def translit(self, ctx: commands.Context, *, text: str = None):
        """Транслитерация текста между кириллицей и латиницей"""
        await transliteration_api.translit_text(ctx, text)

    @commands.command(name="k", description="Исправление текста, набранного в неправильной раскладке")
    async def keyboard(self, ctx: commands.Context, *, text: str = None):
        """Исправление текста, набранного в неправильной раскладке"""
        await transliteration_api.fix_keyboard_layout(ctx, text)

    @commands.command(name="translate", description="Перевести текст на русский язык")
    async def translate(
        self,
        ctx: commands.Context,
        *,
        text: str = None
    ):
        """Перевести текст на русский язык"""
        await translate_api.translate_text(ctx, text)

    @commands.command(name="hash", aliases=["хеш"], description="Получить хеш текста (MD5, SHA256)")
    async def hash_command(self, ctx: commands.Context, *, text: str = None):
        """
        Получить хеш текста (MD5, SHA256)

        Использование:
        !hash текст
        !hash текст md5
        !hash текст sha256
        """
        if not text:
            await ctx.reply(embed=Embed.error(
                description="Укажите текст для хеширования!\n\n**Использование:**\n`!hash текст`\n`!hash текст md5`"
            ))
            return

        # Парсим алгоритм из текста
        parts = text.rsplit(' ', 1)
        algorithm = None

        if len(parts) == 2 and parts[1].lower() in ['md5', 'sha1', 'sha256', 'sha512']:
            text = parts[0]
            algorithm = parts[1].lower()

        await hash_api.generate_hash(ctx, text, algorithm)

    @commands.command(name="ascii", aliases=["аски"], description="Создать ASCII арт из текста")
    async def ascii_command(self, ctx: commands.Context, *, args: str = None):
        """
        Создать ASCII арт из текста

        Использование:
        !ascii текст
        !ascii текст standard
        !ascii текст slant

        Доступные шрифты: standard, banner, big, block, bubble, digital,
        graffiti, lean, mini, script, shadow, slant, small, speed, starwars
        """
        if not args:
            await ctx.reply(embed=Embed.error(
                description="Укажите текст для создания ASCII арта!\n\n**Использование:**\n`!ascii текст`\n`!ascii текст slant`"
            ))
            return

        # Парсим шрифт из аргументов
        parts = args.rsplit(' ', 1)
        font = None
        text = args

        available_fonts = ['standard', 'banner', 'big', 'block', 'bubble', 'digital',
                          'graffiti', 'lean', 'mini', 'script', 'shadow', 'slant',
                          'small', 'speed', 'starwars']

        if len(parts) == 2 and parts[1].lower() in available_fonts:
            text = parts[0]
            font = parts[1].lower()

        await ascii_api.generate_ascii_art(ctx, text, font)

    @commands.command(name="screenshot", aliases=["скрин", "ss"], description="Создать скриншот веб-страницы")
    async def screenshot_command(self, ctx: commands.Context, *, url: str = None):
        """
        Создать скриншот веб-страницы

        Использование:
        !screenshot <url>

        Примеры:
        !screenshot google.com
        !screenshot https://github.com
        !screenshot discord.gg
        """
        await screenshot_api.screenshot_command(ctx, url)

    @commands.command(name="testguilds", aliases=[], description="Проверяю видимость гильдий (почистить лишнее)")
    @commands.is_owner()
    async def testguilds(self, ctx: commands.Context):
        """
        Проверить какие гильдии из ALLOWED_ID бот видит

        Команда доступна только владельцу бота
        """
        allowed_guilds = config.SERVERS.get("ALLOWED_ID", [])

        if not allowed_guilds:
            await ctx.reply(embed=Embed.error(description="Список ALLOWED_ID пуст!"))
            return

        # Создаем embed
        embed = Embed(
            title="🔍 Проверка гильдий",
            description=f"Проверяю **{len(allowed_guilds)}** гильдий из `ALLOWED_ID`"
        )

        visible = []
        invisible = []

        # Проверяем каждую гильдию
        for guild_id in allowed_guilds:
            guild = self.bot.get_guild(guild_id)
            if guild:
                # Бот видит гильдию
                member_count = guild.member_count if guild.member_count else "?"
                visible.append(f"{Emoji.SUCCESS} **{guild.name}** ({member_count} участников)\n└ ID: `{guild_id}`")
            else:
                # Бот не видит гильдию
                invisible.append(f"❌ Гильдия не найдена\n└ ID: `{guild_id}`")

        # Добавляем видимые гильдии
        if visible:
            visible_text = "\n\n".join(visible)
            embed.add_field(
                name=f"📍 Видимые ({len(visible)})",
                value=visible_text if len(visible_text) <= 1024 else visible_text[:1021] + "...",
                inline=False
            )

        # Добавляем невидимые гильдии
        if invisible:
            invisible_text = "\n\n".join(invisible)
            embed.add_field(
                name=f"👻 Не видит ({len(invisible)})",
                value=invisible_text if len(invisible_text) <= 1024 else invisible_text[:1021] + "...",
                inline=False
            )

        # Статистика
        embed.set_footer(text=f"Всего гильдий: {len(allowed_guilds)} | Видимых: {len(visible)} | Невидимых: {len(invisible)}")

        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesSystem(bot))

