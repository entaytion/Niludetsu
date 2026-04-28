import random
from discord import app_commands
from discord.ext import commands
import aiohttp
import discord
from Niludetsu import MarriageManager, Embed
from Niludetsu.api.Gifs import GifsAPI

from typing import Optional

class ReactionSystem(commands.Cog):
    """Система реакций и ролевых команд"""

    def __init__(self, bot):
        self.bot = bot
        self.gifs_api = GifsAPI(getattr(bot, "http_session", None))
        self.marriage = MarriageManager()
        self.purrbot_api = "https://purrbot.site/api/img"

        # NSFW команды
        self.nsfw_reactions = ["sex", "anal", "blowjob", "cum", "fuck", "pussylick", "solo"]

        # Безопасные фоллбеки для NSFW команд в не-NSFW каналах
        self.sfw_fallback_gifs = {
            "sex": [
                "https://media1.tenor.com/m/9G1zsVIiV6UAAAAC/anime-bed.gif",
                "https://media1.tenor.com/m/Os8BXJbIFvYAAAAC/call-of-the-night-sex.gif",
            ],
        }

        # Конфигурация реакций
        self.reactions = {
            "bite": {
                "description": "Укусить пользователя",
                "messages": [
                    "{author} нежно кусает {target}! 💕",
                    "{author} игриво кусает {target}! 🦷",
                    "{author} делает ням-ням {target}! 😋"
                ]
            },
            "cry": {
                "description": "Расплакаться",
                "messages": [
                    "{author} плачет... 😢",
                    "{author} расстроился и плачет... 😭",
                    "У {author} текут слёзки... 💧"
                ]
            },
            "hug": {
                "description": "Обнять пользователя",
                "messages": [
                    "{author} крепко обнимает {target}! 🤗",
                    "{author} дарит тёплые объятия {target}! 💝",
                    "{author} заключает в объятия {target}! 🫂"
                ]
            },
            "kiss": {
                "description": "Поцеловать пользователя",
                "messages": [
                    "{author} нежно целует {target}! 💋",
                    "{author} дарит поцелуй {target}! 😘",
                    "{author} страстно целует {target}! 💕"
                ]
            },
            "pat": {
                "description": "Погладить пользователя",
                "messages": [
                    "{author} нежно гладит {target}! 🤗",
                    "{author} ласково гладит {target} по голове! ✨",
                    "{author} заботливо гладит {target}! 💝"
                ]
            },
            "slap": {
                "description": "Ударить пользователя",
                "messages": [
                    "{author} даёт пощёчину {target}! 👋",
                    "{author} шлёпает {target}! 😠",
                    "{author} бьёт {target}! 💢"
                ]
            },
            "dance": {
                "description": "Танцевать",
                "messages": [
                    "{author} танцует! 💃",
                    "{author} зажигает на танцполе! 🕺",
                    "{author} показывает свои лучшие движения! ✨"
                ]
            },
            "sorry": {
                "description": "Извиниться",
                "messages": [
                    "{author} извиняется перед {target}! 🙏",
                    "{author} просит прощения у {target}! 😔",
                    "{author} раскаивается перед {target}! 💭"
                ]
            },
            "tickle": {
                "description": "Пощекотать пользователя",
                "messages": [
                    "{author} щекочет {target}! 😆",
                    "{author} начинает щекотать {target}! 😹",
                    "{author} атакует щекоткой {target}! ✨"
                ]
            },
            "sneeze": {
                "description": "Чихнуть",
                "messages": [
                    "{author} чихает! 🤧",
                    "{author} громко чихает! 💨",
                    "{author} говорит: Апчхи! 🤧"
                ]
            },
            "mad": {
                "description": "Разозлиться",
                "messages": [
                    "{author} в ярости! 💢",
                    "{author} очень зол! 😡"
                ]
            },
            "love": {
                "description": "Признаться в любви",
                "messages": [
                    "{author} признаётся в любви {target}! ❤️",
                    "{author} говорит {target}: Я тебя люблю! 💕",
                    "{author} дарит свою любовь {target}! 💖"
                ]
            },
            "nervous": {
                "description": "Нервничать",
                "messages": [
                    "{author} нервничает... 😰",
                    "{author} очень волнуется... 😨",
                    "{author} в панике! 😱"
                ]
            },
            "sex": {
                "description": "Заняться любовью с пользователем",
                "messages": [
                    "{author} и {target} занимаются любовью! ❤️‍🔥",
                    "{author} и {target} слились в экстазе! 🥵",
                    "{author} и {target} наслаждаются друг другом! 🔞"
                ],
                "married_messages": [
                    "💕 {author} страстно занимается любовью со своим партнером {target}",
                    "💝 {author} и {target} отдаются друг другу в порыве страсти",
                    "💖 {author} и {target} разделяют интимный момент как настоящие супруги"
                ]
            },
            "anal": {
                "description": "Заняться анальным сексом",
                "messages": [
                    "{author} глубоко и страстно входит в {target} сзади... 🥵",
                    "{author} и {target} исследуют новые глубины удовольствия... 🔥",
                    "{author} доминирует над {target}, доставляя незабываемые ощущения... 😈"
                ]
            },
            "blowjob": {
                "description": "Сделать минет",
                "messages": [
                    "{author} опускается на колени перед {target}... 👄",
                    "{target} наслаждается умелыми действиями {author}... 🤤",
                    "{author} дарит {target} незабываемое удовольствие... 💦"
                ]
            },
            "cum": {
                "description": "Кончить на пользователя",
                "messages": [
                    "{author} изливается на {target}... 💦",
                    "{target} покрыт(а) горячей спермой {author}... 🥵",
                    "{author} кончает, забрызгивая {target}... 🥛"
                ]
            },
            "fuck": {
                "description": "Выебать пользователя",
                "messages": [
                    "{author} жёстко имеет {target}! 🔞",
                    "{author} грубо вдалбливает в {target}! 😈",
                    "{author} и {target} грязно трахаются! 🥵"
                ],
                "married_messages": [
                    "🔥 {author} страстно трахает своего партнера {target}",
                    "💥 {author} и {target} дико занимаются сексом как супруги",
                    "😈 {author} жестко имеет свою половинку {target}"
                ]
            },
            "pussylick": {
                "description": "Сделать куннилингус",
                "messages": [
                    "{author} нежно ласкает языком {target}... 👅",
                    "{target} стонет от удовольствия, пока {author} продолжает... 🤤",
                    "{author} доставляет {target} райское наслаждение... ✨"
                ]
            },
            "solo": {
                "description": "Мастурбировать",
                "messages": [
                    "{author} уединяется для личных утех... 😏",
                    "{author} ласкает себя, погружаясь в фантазии... 💭",
                    "{author} находит способ расслабиться в одиночестве... 💦"
                ]
            }
        }

    async def cog_load(self):
        self.gifs_api.bind_session(getattr(self.bot, "http_session", None))

    async def _get_purrbot_gif(self, type_name: str, is_nsfw: bool = False) -> Optional[str]:
        """Получает гифку из PurrBot API"""
        category = "nsfw" if is_nsfw else "sfw"
        session = getattr(self.bot, "http_session", None)
        if session is None or session.closed:
            return None

        try:
            async with session.get(
                f"{self.purrbot_api}/{category}/{type_name}/gif",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("link")
        except Exception:
            pass
        return None

    async def _check_marriage_restriction(
        self,
        ctx: commands.Context,
        target: discord.Member,
        action_name: str
    ) -> Optional[discord.Embed]:
        """
        Проверяет ограничения по браку для интимных команд

        Args:
            ctx: Контекст команды
            target: Целевой пользователь
            action_name: Название действия (sex/fuck)

        Returns:
            Embed с ошибкой или None если всё ок
        """
        guild_id = str(ctx.guild.id)
        author_id = str(ctx.author.id)
        target_id = str(target.id)

        # Получаем браки обоих пользователей
        author_marriage = await self.marriage.fetch_marriage(guild_id, author_id)
        target_marriage = await self.marriage.fetch_marriage(guild_id, target_id)

        # Проверяем, женаты ли они друг на друге
        if author_marriage and target_marriage:
            # Проверяем, один ли это брак
            is_married_together = (
                author_marriage["id"] == target_marriage["id"] and
                {author_marriage["partner_a_id"], author_marriage["partner_b_id"]} == {author_id, target_id}
            )

            if is_married_together:
                # Они женаты друг на друге — разрешаем
                return None

        # Проверяем, женат ли автор на ком-то другом
        if author_marriage:
            partner_id = await self.marriage.db.get_marriage_partner(author_marriage, author_id)
            partner = ctx.guild.get_member(int(partner_id))
            partner_mention = partner.mention if partner else "вашим партнером"

            action_text = "заниматься любовью" if action_name == "sex" else "трахаться"

            return Embed.error(
                description=f"Вы состоите в браке! Вы можете {action_text} только с {partner_mention}."
            )

        # Проверяем, женат ли target на ком-то другом
        if target_marriage:
            partner_id = await self.marriage.db.get_marriage_partner(target_marriage, target_id)
            partner = ctx.guild.get_member(int(partner_id))
            partner_mention = partner.mention if partner else "своим партнером"

            action_text = "заниматься любовью" if action_name == "sex" else "трахаться"

            return Embed.error(
                description=f"{target.mention} состоит в браке с {partner_mention}! Вы не можете {action_text} с чужим супругом."
            )

        # Оба не женаты — разрешаем
        return None

    async def _is_married_couple(self, guild_id: str, user_a_id: str, user_b_id: str) -> bool:
        """Проверяет, являются ли два пользователя женатой парой"""
        marriage_a = await self.marriage.fetch_marriage(guild_id, user_a_id)
        marriage_b = await self.marriage.fetch_marriage(guild_id, user_b_id)

        if not marriage_a or not marriage_b:
            return False

        # Проверяем, один ли это брак
        return (
            marriage_a["id"] == marriage_b["id"] and
            {marriage_a["partner_a_id"], marriage_a["partner_b_id"]} == {user_a_id, user_b_id}
        )

    async def _handle_reaction(
        self,
        ctx: commands.Context,
        reaction_type: str,
        target: Optional[discord.Member] = None
    ):
        """Обработчик реакций с поддержкой ответов на сообщения"""
        is_nsfw_channel = ctx.channel.is_nsfw()
        reaction_info = self.reactions[reaction_type]

        if target is None and ctx.message.reference:
            try:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                target = referenced_msg.author
            except Exception:
                pass

        if target and (target.id == ctx.author.id or target.bot):
            error_text = "собой" if target.id == ctx.author.id else "ботом"
            return await ctx.reply(
                embed=Embed.error(description=f"Вы не можете взаимодействовать с {error_text}!"),
                ephemeral=True
            )

        if reaction_type in ["sex", "fuck"] and target:
            # Проверяем ограничения по браку
            error_embed = await self._check_marriage_restriction(ctx, target, reaction_type)
            if error_embed:
                return await ctx.reply(embed=error_embed, ephemeral=True)

            # Проверяем, женаты ли они друг на друге
            is_married = await self._is_married_couple(
                str(ctx.guild.id),
                str(ctx.author.id),
                str(target.id)
            )

            # Используем специальные сообщения для супругов
            if is_married and "married_messages" in reaction_info:
                messages = reaction_info["married_messages"]
            else:
                messages = reaction_info["messages"]
        else:
            messages = reaction_info["messages"]

        if target:
            message = random.choice(messages).format(
                author=ctx.author.mention,
                target=target.mention
            )
        else:
            # Команды без цели (cry, dance, sneeze, mad, nervous, solo)
            if reaction_type in ["cry", "dance", "sneeze", "mad", "nervous", "solo"]:
                message = random.choice(messages).format(author=ctx.author.mention)
            else:
                return await ctx.reply(
                    embed=Embed.error(description="Укажите пользователя или ответьте на сообщение!"),
                    ephemeral=True
                )

        gif_url = None

        if reaction_type in self.nsfw_reactions:
            if is_nsfw_channel:
                # NSFW канал — используем NSFW гифки
                gif_type = "fuck" if reaction_type == "sex" else reaction_type
                gif_url = await self._get_purrbot_gif(gif_type, is_nsfw=True)
            else:
                # Не-NSFW канал — используем безопасные фоллбеки
                fallbacks = self.sfw_fallback_gifs.get(reaction_type)
                if fallbacks:
                    gif_url = random.choice(fallbacks)
        else:
            # SFW команды — используем обычные гифки
            try:
                gif_url = await self.gifs_api.get_random_gif(reaction_type)
            except Exception:
                # Фоллбек на PurrBot
                if reaction_type in ["kiss", "hug", "pat", "slap", "tickle"]:
                    gif_url = await self._get_purrbot_gif(reaction_type)

        embed = Embed(description=message)
        if gif_url:
            embed.set_image(url=gif_url)

        await ctx.reply(embed=embed)

    @commands.command(name="bite", aliases=["укусить", "кусь"])
    async def bite(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "bite", user)

    @commands.command(name="cry", aliases=["плакать", "реветь"])
    async def cry(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "cry")

    @commands.command(name="hug", aliases=["обнять", "обнимашки"])
    async def hug(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "hug", user)

    @commands.command(name="kiss", aliases=["поцеловать", "чмок"])
    async def kiss(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "kiss", user)

    @commands.command(name="pat", aliases=["погладить"])
    async def pat(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "pat", user)

    @commands.command(name="slap", aliases=["ударить", "шлепнуть"])
    async def slap(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "slap", user)

    @commands.command(name="dance", aliases=["танцевать"])
    async def dance(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "dance")

    @commands.command(name="sorry", aliases=["извиниться"])
    async def sorry(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "sorry", user)

    @commands.command(name="tickle", aliases=["щекотать", "щекотка"])
    async def tickle(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "tickle", user)

    @commands.command(name="sneeze", aliases=["чихнуть", "апчхи"])
    async def sneeze(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "sneeze")

    @commands.command(name="mad", aliases=["злиться"])
    async def mad(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "mad")

    @commands.command(name="love", aliases=["любовь"])
    async def love(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "love", user)

    @commands.command(name="nervous", aliases=["нервничать"])
    async def nervous(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "nervous")

    @commands.command(name="sex", aliases=["секс"])
    async def sex(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "sex", user)

    @commands.command(name="anal", aliases=["анал"])
    async def anal(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "anal", user)

    @commands.command(name="blowjob", aliases=["минет"])
    async def blowjob(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "blowjob", user)

    @commands.command(name="cum", aliases=["кончить"])
    async def cum(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "cum", user)

    @commands.command(name="fuck", aliases=["выебать", "трахнуть"])
    async def fuck(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "fuck", user)

    @commands.command(name="pussylick", aliases=["куни"])
    async def pussylick(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        await self._handle_reaction(ctx, "pussylick", user)

    @commands.command(name="solo", aliases=["мастурбация"])
    async def solo(self, ctx: commands.Context):
        await self._handle_reaction(ctx, "solo")

    @commands.hybrid_command(name="rp", description="Выполнить ролевую реакцию")
    @app_commands.describe(action="🎭 Выберите действие", user="👤 Пользователь (если нужен)")
    @app_commands.choices(action=[
        app_commands.Choice(name="🦷 Укусить", value="bite"),
        app_commands.Choice(name="😢 Расплакаться", value="cry"),
        app_commands.Choice(name="🤗 Обнять", value="hug"),
        app_commands.Choice(name="💋 Поцеловать", value="kiss"),
        app_commands.Choice(name="✨ Погладить", value="pat"),
        app_commands.Choice(name="🖐️ Ударить", value="slap"),
        app_commands.Choice(name="💃 Танцевать", value="dance"),
        app_commands.Choice(name="🙏 Извиниться", value="sorry"),
        app_commands.Choice(name="😜 Пощекотать", value="tickle"),
        app_commands.Choice(name="🤧 Чихнуть", value="sneeze"),
        app_commands.Choice(name="😡 Разозлиться", value="mad"),
        app_commands.Choice(name="❤️ Признаться в любви", value="love"),
        app_commands.Choice(name="😰 Нервничать", value="nervous"),
        app_commands.Choice(name="🔞 Заняться любовью", value="sex"),
        app_commands.Choice(name="🔞 Анальный секс", value="anal"),
        app_commands.Choice(name="🔞 Минет", value="blowjob"),
        app_commands.Choice(name="🔞 Кончить", value="cum"),
        app_commands.Choice(name="🔞 Трахнуть", value="fuck"),
        app_commands.Choice(name="🔞 Куннилингус", value="pussylick"),
        app_commands.Choice(name="🔞 Мастурбация", value="solo"),
    ])
    async def rp(self, ctx: commands.Context, action: str, user: Optional[discord.Member] = None):
        """Выполняет ролевую реакцию"""
        # Проверяем, нужен ли пользователь для этого действия
        requires_user = action in [
            "bite", "hug", "kiss", "pat", "slap", "sorry", "tickle", "love",
            "sex", "anal", "blowjob", "cum", "fuck", "pussylick"
        ]

        if requires_user and not user:
            return await ctx.reply(
                embed=Embed.error(description="Укажите пользователя для этого действия!"),
                ephemeral=True
            )

        await self._handle_reaction(ctx, action, user)

async def setup(bot):
    await bot.add_cog(ReactionSystem(bot))

