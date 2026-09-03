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
from Niludetsu.locale import _

class UtilitiesSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="whois", aliases=["domain"], description="Получить информацию о домене или IP-адресе")
    async def whois(self, ctx: commands.Context, *, target: str = None):
        await whois_api.whois_lookup(ctx, target)

    @commands.command(name="weather", description="Узнать погоду в указанном городе")
    async def weather(
        self,
        ctx: commands.Context,
        *,
        city: str = None
    ):
        if city is None:
            raise commands.MissingRequiredArgument(ctx.command.params['city'])

        await weather_api.get_weather_info(ctx, city)

    @commands.command(name="color", description="Конвертировать цвет между форматами")
    async def color(
        self,
        ctx: commands.Context,
        *,
        color: str = None
    ):
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
        await qrcode_api.generate_qrcode(ctx, content, color)

    @commands.command(name="qrdecode", description="Декодировать QR-код из изображения")
    async def qrdecode(
        self,
        ctx: commands.Context
    ):
        t = _(ctx=ctx)
        if not ctx.message.attachments:
            await ctx.reply(embed=Embed.error(description=t("qrdecode_no_image")))
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
        t = _(ctx=ctx)
        if not address:
            embed = Embed.error(
                description=t("mcserver_usage")
            )
            await ctx.reply(embed=embed)
            return

        is_bedrock = edition.lower() in ["bedrock", "be", "pocket", "mcpe"]

        await minecraft_server_api.get_server_info(ctx, address, port, is_bedrock)

    @commands.command(name="calc", aliases=["calculate", "math"], description="Вычислить математическое выражение")
    async def calc(self, ctx: commands.Context, *, expression: str = None):
        await math_calculator_api.calculate(ctx, expression)

    @commands.command(name="rand", aliases=["random", "рандом"], description="Генерация случайного числа")
    async def rand(
        self,
        ctx: commands.Context,
        max_value: int = None,
        min_value: Optional[int] = None
    ):
        if max_value is None:
            raise commands.MissingRequiredArgument(ctx.command.params['max_value'])
        await random_api.generate_random_number(ctx, max_value, min_value)

    @commands.command(name="ping", description="Проверка задержки бота")
    async def ping(self, ctx: commands.Context):
        t = _(ctx=ctx)
        latency = round(self.bot.latency * 1000)

        embed = Embed.default(
            title=t("ping_title"),
            description=t("ping_desc", latency=latency),
            color=Colors.SUCCESS if latency < 200 else Colors.WARNING if latency < 400 else Colors.ERROR
        )

        await ctx.reply(embed=embed)

    @commands.command(name="t", description="Транслитерация текста между кириллицей и латиницей")
    async def translit(self, ctx: commands.Context, *, text: str = None):
        await transliteration_api.translit_text(ctx, text)

    @commands.command(name="k", description="Исправление текста, набранного в неправильной раскладке")
    async def keyboard(self, ctx: commands.Context, *, text: str = None):
        await transliteration_api.fix_keyboard_layout(ctx, text)

    @commands.command(name="translate", description="Перевести текст на русский язык")
    async def translate(
        self,
        ctx: commands.Context,
        *,
        text: str = None
    ):
        await translate_api.translate_text(ctx, text)

    @commands.command(name="hash", aliases=["хеш"], description="Получить хеш текста (MD5, SHA256)")
    async def hash_command(self, ctx: commands.Context, *, text: str = None):
        t = _(ctx=ctx)
        if not text:
            await ctx.reply(embed=Embed.error(
                description=t("hash_usage")
            ))
            return

        parts = text.rsplit(' ', 1)
        algorithm = None

        if len(parts) == 2 and parts[1].lower() in ['md5', 'sha1', 'sha256', 'sha512']:
            text = parts[0]
            algorithm = parts[1].lower()

        await hash_api.generate_hash(ctx, text, algorithm)

    @commands.command(name="ascii", aliases=["аски"], description="Создать ASCII арт из текста")
    async def ascii_command(self, ctx: commands.Context, *, args: str = None):
        t = _(ctx=ctx)
        if not args:
            await ctx.reply(embed=Embed.error(
                description=t("ascii_usage")
            ))
            return

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
        await screenshot_api.screenshot_command(ctx, url)

    @commands.command(name="testguilds", aliases=[], description="Проверяю видимость гильдий (почистить лишнее)")
    @commands.is_owner()
    async def testguilds(self, ctx: commands.Context):
        allowed_guilds = config.SERVERS.get("ALLOWED_ID", [])

        if not allowed_guilds:
            await ctx.reply(embed=Embed.error(description="Список ALLOWED_ID пуст!"))
            return

        embed = Embed(
            title="🔍 Проверка гильдий",
            description=f"Проверяю **{len(allowed_guilds)}** гильдий из `ALLOWED_ID`"
        )

        visible = []
        invisible = []

        for guild_id in allowed_guilds:
            guild = self.bot.get_guild(guild_id)
            if guild:
                member_count = guild.member_count if guild.member_count else "?"
                visible.append(f"{Emoji.SUCCESS} **{guild.name}** ({member_count} участников)\n└ ID: `{guild_id}`")
            else:
                invisible.append(f"❌ Гильдия не найдена\n└ ID: `{guild_id}`")

        if visible:
            visible_text = "\n\n".join(visible)
            embed.add_field(
                name=f"📍 Видимые ({len(visible)})",
                value=visible_text if len(visible_text) <= 1024 else visible_text[:1021] + "...",
                inline=False
            )

        if invisible:
            invisible_text = "\n\n".join(invisible)
            embed.add_field(
                name=f"👻 Не видит ({len(invisible)})",
                value=invisible_text if len(invisible_text) <= 1024 else invisible_text[:1021] + "...",
                inline=False
            )

        embed.set_footer(text=f"Всего гильдий: {len(allowed_guilds)} | Видимых: {len(visible)} | Невидимых: {len(invisible)}")

        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesSystem(bot))

