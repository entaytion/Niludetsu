import aiohttp, asyncio, discord, os, random
from discord.ext import commands
from dotenv import load_dotenv
from Niludetsu.config import SERVERS
from Niludetsu.database.supabase_database import database
from Niludetsu import Embed, Colors, TimeService, Emojis
from typing import Optional, Dict

load_dotenv()

MAIN_SERVER_ID = SERVERS["MAIN_ID"]
INVITES_CHANNEL_ID = 1130114236673171476  # Канал для логов инвайтов
WELCOME_CHANNEL_ID = 1125546968517726228  # Канал приветствия
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

_time = TimeService()

class AccountType:
    NORMAL = "NORMAL"
    NEW = "NEW"
    SUSPICIOUS = "SUSPICIOUS"

class InviteSource:
    UNKNOWN = "UNKNOWN"
    DISCORD = "DISCORD"
    SERVER = "SERVER"
    VANITY = "VANITY"
    INTEGRATION = "INTEGRATION"

    EMOJI_MAP = {
        "SERVER": "🏠",
        "VANITY": "🔗",
        "INTEGRATION": "🤖",
        "DISCORD": "🔷",
        "UNKNOWN": "❓",
    }

    @staticmethod
    def get_emoji(source: str) -> str:
        return InviteSource.EMOJI_MAP.get(source.upper(), "❓")

class InviteManager:
    """Управление инвайтами и их отслеживание"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database

        # Кеш инвайтов
        self.invites: Dict[str, discord.Invite] = {}
        self.vanity_invite: Optional[discord.Invite] = None
        self.vanity_uses: int = 0

        self.lock = asyncio.Lock()

        # Инициализируем кеш
        bot.loop.create_task(self._initialize())

    async def _initialize(self):
        """Инициализация кеша инвайтов"""
        await self.bot.wait_until_ready()
        await self.cache_invites()

    async def cache_invites(self):
        """Кеширует все инвайты сервера"""
        guild = self.bot.get_guild(MAIN_SERVER_ID)
        if not guild:
            return

        async with self.lock:
            try:
                # Кешируем обычные инвайты
                invites = await guild.invites()
                self.invites = {invite.code: invite for invite in invites}

                # Кешируем vanity invite
                if guild.vanity_url_code:
                    try:
                        vanity = await guild.vanity_invite()
                        if vanity:
                            self.vanity_invite = vanity
                            self.vanity_uses = vanity.uses
                    except (discord.Forbidden, discord.HTTPException):
                        pass

                print(f"[InviteManager] Кеш инвайтов обновлён: {len(self.invites)} инвайтов")

            except discord.Forbidden:
                print(f"[InviteManager] Нет прав для получения инвайтов")
            except Exception as e:
                print(f"[InviteManager] Ошибка кеширования инвайтов: {e}")

    async def track_invite_create(self, invite: discord.Invite):
        """Отслеживает создание инвайта"""
        if not invite.guild or invite.guild.id != MAIN_SERVER_ID:
            return

        async with self.lock:
            self.invites[invite.code] = invite

    async def track_invite_delete(self, invite: discord.Invite):
        """Отслеживает удаление инвайта"""
        if not invite.guild or invite.guild.id != MAIN_SERVER_ID:
            return

        async with self.lock:
            self.invites.pop(invite.code, None)

    async def track_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Отслеживает изменение vanity URL"""
        if before.id != MAIN_SERVER_ID:
            return

        if before.vanity_url_code != after.vanity_url_code:
            try:
                vanity = await after.vanity_invite()
                if vanity:
                    async with self.lock:
                        self.vanity_invite = vanity
                        self.vanity_uses = vanity.uses
            except Exception:
                pass

    async def find_used_invite(self, guild: discord.Guild) -> Optional[discord.Invite]:
        """Находит использованный инвайт"""
        async with self.lock:
            try:
                # Получаем текущие инвайты
                current_invites = await guild.invites()

                # Сравниваем с кешем
                for invite in current_invites:
                    cached = self.invites.get(invite.code)
                    if cached and invite.uses > cached.uses:
                        # Обновляем кеш
                        self.invites[invite.code] = invite
                        return invite

                # Проверяем vanity invite
                if guild.vanity_url_code:
                    vanity = await guild.vanity_invite()
                    if vanity and vanity.uses > self.vanity_uses:
                        self.vanity_invite = vanity
                        self.vanity_uses = vanity.uses
                        return vanity

                # Обновляем кеш для следующего раза
                self.invites = {inv.code: inv for inv in current_invites}

            except Exception as e:
                print(f"[InviteManager] Ошибка поиска инвайта: {e}")

        return None

    def get_account_type(self, member: discord.Member) -> str:
        """Определяет тип аккаунта"""
        now = _time.now().timestamp()
        created_ts = member.created_at.timestamp()
        days = int((now - created_ts) // 86400)

        if days < 1:
            return AccountType.SUSPICIOUS
        elif days < 7:
            return AccountType.NEW
        else:
            return AccountType.NORMAL

    def get_invite_source(self, invite: Optional[discord.Invite]) -> str:
        """Определяет источник инвайта"""
        if not invite:
            return InviteSource.UNKNOWN

        if invite.guild and invite.guild.vanity_url_code == invite.code:
            return InviteSource.VANITY

        if invite.inviter and invite.inviter.bot:
            return InviteSource.INTEGRATION

        return InviteSource.SERVER

class QuestionGenerator:
    """Генерирует приветственные вопросы через AI"""

    FALLBACK_QUESTIONS = [
        "какую привычку ты считаешь своей самой полезной?",
        "если бы у тебя было лишних 2 часа в день, на что бы ты их тратил?",
        "как выглядел бы твой идеальный выходной?",
        "какой навык ты хотел бы выучить в этом месяце?",
        "что приносит тебе ощущение спокойствия?",
        "в каком вымышленном мире ты хотел бы пожить день?",
        "какое маленькое достижение сегодня тобой гордится?",
    ]

    @staticmethod
    async def generate() -> str:
        """Генерирует вопрос через Mistral AI"""
        if not MISTRAL_API_KEY:
            return random.choice(QuestionGenerator.FALLBACK_QUESTIONS)

        prompt = (
            "Сгенерируй один оригинальный и интересный вопрос для нового участника Discord сервера. "
            "Вопрос должен быть коротким, неформальным, и заставляющим задуматься. "
            "Избегай банальных тем. Обязательно закончи вопрос знаком вопроса (?). "
            "Не используй кавычки. Не надо писать вводные фразы — просто вопрос."
        )

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 60,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        question = result["choices"][0]["message"]["content"].strip()

                        # Убираем кавычки
                        if question.startswith('"') and question.endswith('"'):
                            question = question[1:-1]

                        # Добавляем знак вопроса если нет
                        if not question.endswith("?"):
                            question += "?"

                        return question

        except Exception as e:
            print(f"[QuestionGenerator] Ошибка генерации: {e}")

        return random.choice(QuestionGenerator.FALLBACK_QUESTIONS)

class MemberEventHandler:
    """Обработка событий входа и выхода участников"""

    def __init__(self, bot: commands.Bot, invite_manager: InviteManager):
        self.bot = bot
        self.invite_manager = invite_manager
        self.db = database

    async def send_dm(self, member: discord.Member, is_join: bool = True) -> bool:
        """Унифицированная функция отправки ЛС"""
        if is_join:
            embed = Embed(
                title="Добро пожаловать в ``Æther!🖤``",
                description=(
                    "> Мы **``очень рады``** видеть тебя здесь! ``🖤`` "
                    "Надеемся, **``тебе понравится``**, и ты останешься с нами. ``🤗``"
                ),
                color=0xF24862
            )

            embed.add_field(
                name="<:aeRules:1356241893977096343> Чтобы быстро освоиться:",
                value=(
                    "- Ознакомься с ботом: **`/help`** или **`!help`**\n"
                    "- Напиши **первое сообщение** и получи валюту 🪙\n"
                    "- Роль с пингами выдаётся **автоматически**."
                ),
                inline=False
            )

            embed.set_thumbnail(url="https://entaytion.vercel.app/ae/welcome.gif")

            class WelcomeButtons(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(
                        label="Наша империя!",
                        url="https://discord.gg/HxwZ6ceKKj",
                        style=discord.ButtonStyle.link
                    ))
                    self.add_item(discord.ui.Button(
                        label="Наш телеграм!",
                        url="https://t.me/ae_there",
                        style=discord.ButtonStyle.link
                    ))

            view = WelcomeButtons()

        else:
            embed = Embed(
                title="Надеемся увидеть тебя снова! 💔",
                description=(
                    "> Ты покинул(а) сервер **``Æther!``** 😢\n"
                    "Нам **``очень жаль``**, что ты уходишь. Если что-то не так — "
                    "всегда можешь вернуться! ``🤗``"
                ),
                color=0xF24862
            )

            embed.add_field(
                name="<:aeRules:1356241893977096343> Если хочешь вернуться:",
                value=(
                    "- Мы всегда рады новым и старым участникам! 💙\n"
                    "- Твой прогресс и баланс **сохранены** 🪙\n"
                    "- Присоединяйся снова по ссылке ниже ⬇️"
                ),
                inline=False
            )

            embed.set_thumbnail(url="https://entaytion.vercel.app/ae/goodbye.gif")

            class GoodbyeButtons(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(
                        label="Вернуться на сервер",
                        url="https://discord.gg/HxwZ6ceKKj",
                        style=discord.ButtonStyle.link,
                        emoji="🏠"
                    ))

            view = GoodbyeButtons()

        embed.set_author(
            name=member.name,
            icon_url=member.display_avatar.url
        )

        try:
            await member.send(embed=embed, view=view)
            return True
        except discord.Forbidden:
            return False

    async def handle_join(self, member: discord.Member):
        """Обрабатывает вход участника"""
        if member.guild.id != MAIN_SERVER_ID:
            return

        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)

        invite = await self.invite_manager.find_used_invite(guild)

        invited_by = str(invite.inviter.id) if invite and invite.inviter else None
        invite_code = invite.code if invite else None
        invite_source = self.invite_manager.get_invite_source(invite)
        account_type = self.invite_manager.get_account_type(member)

        dm_sent = await self.send_dm(member, is_join=True)

        await self._send_welcome_channel(member)

        await self._save_join_to_db(
            guild_id=guild_id,
            user_id=user_id,
            invited_by=invited_by,
            invite_code=invite_code,
            invite_source=invite_source,
            account_type=account_type,
            dm_sent=dm_sent
        )

        await self._log_join(member, invite, dm_sent)

    async def _send_welcome_channel(self, member: discord.Member):
        """Отправляет приветствие в канал"""
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        greeting = random.choice([
            "здарова", "ку", "хай", "привет", "приветик",
            "хаюшки", "салют", "хеей-хеей", "дарова"
        ])

        question = await QuestionGenerator.generate()

        embed = Embed(
            description=(
                f"**{member.name}**, `{question}`\n"
                "- Ознакомься с правилами в <#1261069675098279996>"
            ),
            color=discord.Color.random()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(
            f"{member.mention}, {greeting}! <a:aeGreetingHi:1352232699774898218>",
            embed=embed
        )

    async def _save_join_to_db(
        self,
        guild_id: str,
        user_id: str,
        invited_by: Optional[str],
        invite_code: Optional[str],
        invite_source: str,
        account_type: str,
        dm_sent: bool
    ):
        """Сохраняет вход в БД"""
        try:
            # Проверяем существующую запись
            existing = await self.db.get_row("invites", guild_id=guild_id, user_id=user_id)

            now_dt = _time.now()

            if existing:
                # Обновляем существующую запись
                await self.db.update_record(
                    "invites",
                    {"guild_id": guild_id, "user_id": user_id},
                    {
                        "invited_by": invited_by,
                        "invite_code": invite_code,
                        "invite_source": invite_source,
                        "last_join": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                        "join_count": existing["join_count"] + 1,
                        "is_active": True,
                        "account_type": account_type,
                        "dm_sent": dm_sent,
                    }
                )
                print(f"[InviteTracker] Обновлён вход: {user_id} (join_count: {existing['join_count'] + 1})")

            else:
                # Создаём новую запись
                await self.db.insert("invites", {
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "invited_by": invited_by,
                    "invite_code": invite_code,
                    "invite_source": invite_source,
                    "joined_at": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                    "last_join": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                    "join_count": 1,
                    "leave_count": 0,
                    "is_active": True,
                    "account_type": account_type,
                    "dm_sent": dm_sent,
                })
                print(f"[InviteTracker] Создана запись входа: {user_id}")

        except Exception as e:
            print(f"[InviteTracker] Ошибка сохранения входа: {e}")

    async def _log_join(self, member: discord.Member, invite: Optional[discord.Invite], dm_sent: bool):
        """Логирует вход в канал"""
        channel = self.bot.get_channel(INVITES_CHANNEL_ID)
        if not channel:
            return

        # Создаём embed с информацией о входе
        created_ts = int(member.created_at.timestamp())
        now_ts = int(_time.now().timestamp())
        days = (now_ts - created_ts) // 86400

        # Иконка типа аккаунта
        if days > 7:
            account_icon = Emojis.SUCCESS
        elif days >= 1:
            account_icon = Emojis.WARNING
        else:
            account_icon = Emojis.ERROR

        embed = Embed(
            title=f"{Emojis.SUCCESS} ``{member.name}``",
            color=Colors.SUCCESS,
            timestamp=_time.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Информация об участнике
        info = [
            f"- ``❓`` **Тип:** ``{'бот' if member.bot else 'участник'}``",
            f"- ``👥`` **Аккаунт:** {member.mention}",
            f"- ``🆔`` **ID:** `{member.id}`",
            f"- ``📅`` **Регистрация:** <t:{created_ts}:D>",
            f"- {account_icon} **Создан:** ``{days}`` дней назад",
            f"- ``🚪`` **На сервере:** ``{len(member.guild.members)}`` участников",
        ]
        embed.add_field(name="Информация:", value="\n".join(info), inline=True)

        # Информация об инвайте
        if invite:
            source = self.invite_manager.get_invite_source(invite)
            emoji = InviteSource.get_emoji(source)

            invite_info = [
                f"- ``🔗`` **Код:** `{invite.code}`",
                f"- ``🌐`` **Источник:** {emoji} {source}",
            ]

            if invite.uses is not None:
                invite_info.append(f"- ``🔢`` **Использований:** `{invite.uses}`")

            if source == InviteSource.VANITY:
                invite_info.append("- ``➕`` **Добавил:** Персональная ссылка")
            elif invite.inviter:
                invite_info.append(f"- ``➕`` **Добавил:** {invite.inviter.mention}")

            if invite.channel:
                invite_info.append(f"- ``💬`` **Канал:** {invite.channel.mention}")

            if invite.expires_at:
                expires_ts = int(invite.expires_at.timestamp())
                invite_info.append(f"- ``⌛`` **Истекает:** <t:{expires_ts}:R>")
            else:
                invite_info.append("- ``⌛`` **Истекает:** Никогда")

            embed.add_field(name="Приглашение:", value="\n".join(invite_info), inline=True)
        else:
            embed.add_field(
                name="Приглашение:",
                value="❓ Не удалось определить источник",
                inline=True
            )

        # Footer с информацией о ЛС
        footer_text = "✅ ЛС отправлено" if dm_sent else "❌ ЛС закрыты"
        embed.set_footer(text=footer_text)

        await channel.send(embed=embed)

    async def handle_leave(self, member: discord.Member):
        """Обрабатывает выход участника"""
        if member.guild.id != MAIN_SERVER_ID:
            return

        guild_id = str(member.guild.id)
        user_id = str(member.id)

        # Отправляем прощальное сообщение
        dm_sent = await self.send_dm(member, is_join=False)

        try:
            existing = await self.db.get_row("invites", guild_id=guild_id, user_id=user_id)

            if existing:
                now_dt = _time.now()

                await self.db.update_record(
                    "invites",
                    {"guild_id": guild_id, "user_id": user_id},
                    {
                        "left_at": existing.get("left_at") or now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                        "last_leave": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                        "leave_count": existing["leave_count"] + 1,
                        "is_active": False,
                        "dm_sent": dm_sent,
                    }
                )
                print(f"[InviteTracker] Обновлён выход: {user_id} (leave_count: {existing['leave_count'] + 1}, DM: {dm_sent})")

        except Exception as e:
            print(f"[InviteTracker] Ошибка сохранения выхода: {e}")

        await self._log_leave(member, existing, dm_sent)

    async def _log_leave(self, member: discord.Member, invite_data: Optional[Dict], dm_sent: bool = False):
        """Логирует выход в канал"""
        channel = self.bot.get_channel(INVITES_CHANNEL_ID)
        if not channel:
            return

        created_ts = int(member.created_at.timestamp())
        now_ts = int(_time.now().timestamp())
        days = (now_ts - created_ts) // 86400

        # Иконка типа аккаунта
        if days > 7:
            account_icon = Emojis.SUCCESS
        elif days >= 1:
            account_icon = Emojis.WARNING
        else:
            account_icon = Emojis.ERROR

        embed = Embed(
            title=f"{Emojis.ERROR} ``{member.name}``",
            color=Colors.ERROR,
            timestamp=_time.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Информация об участнике
        info = [
            f"- ``❓`` **Тип:** ``{'бот' if member.bot else 'участник'}``",
            f"- ``👥`` **Аккаунт:** {member.mention}",
            f"- ``🆔`` **ID:** `{member.id}`",
            f"- ``📅`` **Регистрация:** <t:{created_ts}:D>",
            f"- {account_icon} **Создан:** ``{days}`` дней назад",
            f"- ``🚪`` **На сервере:** ``{len(member.guild.members)}`` участников",
        ]
        embed.add_field(name="Информация:", value="\n".join(info), inline=True)

        # Информация о времени на сервере
        server_info = []

        if member.joined_at:
            joined_ts = int(member.joined_at.timestamp())
            server_info.append(f"- ``😶‍🌫️`` **Присоединился:** <t:{joined_ts}:D>")

            delta = now_ts - joined_ts
            days_on_server = delta // 86400
            hours = (delta % 86400) // 3600

            time_parts = []
            if days_on_server > 0:
                time_parts.append(f"{days_on_server} дн.")
            if hours > 0 or not time_parts:
                time_parts.append(f"{hours} ч.")

            server_info.append(f"- ``🕰️`` **Провёл:** {' '.join(time_parts)}")

        # Информация об инвайте
        if invite_data:
            invite_code = invite_data.get("invite_code")
            source = invite_data.get("invite_source", InviteSource.UNKNOWN)
            emoji = InviteSource.get_emoji(source)

            if invite_code:
                server_info.append(f"- ``🔗`` **Код:** `{invite_code}`")
            server_info.append(f"- ``🌐`` **Источник:** {emoji} {source}")

            invited_by = invite_data.get("invited_by")
            if invited_by:
                inviter = self.bot.get_user(int(invited_by))
                mention = inviter.mention if inviter else f"<@{invited_by}>"
                server_info.append(f"- ``➕`` **Пригласил:** {mention}")
            elif source == InviteSource.VANITY:
                server_info.append("- ``➕`` **Пригласил:** Персональная ссылка")

        embed.add_field(
            name="На сервере:",
            value="\n".join(server_info) if server_info else "Нет данных",
            inline=True
        )

        # Роли
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            roles_text = ", ".join(roles)
            if len(roles_text) > 1024:
                roles_text = f"{len(roles)} ролей"
            embed.add_field(name="Роли:", value=roles_text, inline=False)

        # Footer с информацией о ЛС
        footer_text = "✅ Прощальное ЛС отправлено" if dm_sent else "❌ ЛС закрыты"
        embed.set_footer(text=footer_text)

        await channel.send(embed=embed)

class InviteTracker(commands.Cog):
    """Отслеживание инвайтов и приветствие участников"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_manager = InviteManager(bot)
        self.event_handler = MemberEventHandler(bot, self.invite_manager)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Обработка входа участника"""
        await self.event_handler.handle_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Обработка выхода участника"""
        await self.event_handler.handle_leave(member)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Отслеживание создания инвайта"""
        await self.invite_manager.track_invite_create(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Отслеживание удаления инвайта"""
        await self.invite_manager.track_invite_delete(invite)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Отслеживание изменения vanity URL"""
        await self.invite_manager.track_guild_update(before, after)

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteTracker(bot))