from __future__ import annotations

import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands

from Niludetsu import Colors, Emojis, Embed, TimeService, safe_fetch_user, logger, config
from Niludetsu.ai.models import WelcomeQuestionGenerator
from Niludetsu.database import database

MAIN_SERVER_ID = config.SERVERS["MAIN_ID"]
WELCOME_CHANNEL_ID = 1125546968517726228
RULES_CHANNEL_ID = 1261069675098279996
DISCORD_INVITE_URL = "https://discord.gg/HxwZ6ceKKj"

WELCOME_GREETINGS = (
    "здарова",
    "ку",
    "хай",
    "привет",
    "приветик",
    "хаюшки",
    "салют",
    "хеей-хеей",
    "дарова",
)

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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites: dict[str, discord.Invite] = {}
        self.vanity_invite: Optional[discord.Invite] = None
        self.vanity_uses = 0
        self.lock = asyncio.Lock()

    async def initialize(self) -> None:
        await self.bot.wait_until_ready()
        await self.cache_invites()

    async def cache_invites(self) -> None:
        guild = self.bot.get_guild(MAIN_SERVER_ID)
        if not guild:
            return

        try:
            invites = await guild.invites()
            vanity = None
            vanity_uses = 0
            if guild.vanity_url_code:
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        vanity_uses = vanity.uses or 0
                except (discord.Forbidden, discord.HTTPException):
                    pass

            async with self.lock:
                self.invites = {invite.code: invite for invite in invites}
                self.vanity_invite = vanity
                self.vanity_uses = vanity_uses

            logger.info(f"[InviteManager] Cached {len(self.invites)} invites")
        except discord.Forbidden:
            logger.warning("[InviteManager] Missing permissions to cache invites")
        except Exception as exc:
            logger.error(f"[InviteManager] Failed to cache invites: {exc}")

    async def track_invite_create(self, invite: discord.Invite) -> None:
        if not invite.guild or invite.guild.id != MAIN_SERVER_ID:
            return

        async with self.lock:
            self.invites[invite.code] = invite

    async def track_invite_delete(self, invite: discord.Invite) -> None:
        if not invite.guild or invite.guild.id != MAIN_SERVER_ID:
            return

        async with self.lock:
            self.invites.pop(invite.code, None)

    async def track_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        if before.id != MAIN_SERVER_ID or before.vanity_url_code == after.vanity_url_code:
            return

        try:
            vanity = await after.vanity_invite()
            vanity_uses = vanity.uses or 0 if vanity else 0
            async with self.lock:
                self.vanity_invite = vanity
                self.vanity_uses = vanity_uses
        except Exception:
            pass

    async def find_used_invite(self, guild: discord.Guild) -> Optional[discord.Invite]:
        try:
            current_invites = await guild.invites()
            vanity = None
            vanity_uses = 0
            if guild.vanity_url_code:
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        vanity_uses = vanity.uses or 0
                except (discord.Forbidden, discord.HTTPException):
                    vanity = None
        except Exception as exc:
            logger.error(f"[InviteManager] Failed to resolve used invite: {exc}")
            return None

        async with self.lock:
            used_invite = None
            try:
                for invite in current_invites:
                    cached = self.invites.get(invite.code)
                    if cached and (invite.uses or 0) > (cached.uses or 0):
                        used_invite = invite
                        break

                if vanity and vanity_uses > self.vanity_uses:
                    used_invite = vanity

                self.invites = {invite.code: invite for invite in current_invites}
                self.vanity_invite = vanity
                self.vanity_uses = vanity_uses
            except Exception as exc:
                logger.error(f"[InviteManager] Failed to resolve used invite: {exc}")
                return None

        return used_invite

    @staticmethod
    def get_account_type(member: discord.Member) -> str:
        now = _time.now().timestamp()
        created_ts = member.created_at.timestamp()
        days = int((now - created_ts) // 86400)

        if days < 1:
            return AccountType.SUSPICIOUS
        if days < 7:
            return AccountType.NEW
        return AccountType.NORMAL

    @staticmethod
    def get_invite_source(invite: Optional[discord.Invite]) -> str:
        if not invite:
            return InviteSource.UNKNOWN
        if invite.guild and invite.guild.vanity_url_code == invite.code:
            return InviteSource.VANITY
        if invite.inviter and invite.inviter.bot:
            return InviteSource.INTEGRATION
        return InviteSource.SERVER

class MemberEventHandler:
    def __init__(self, bot: commands.Bot, invite_manager: InviteManager):
        self.bot = bot
        self.db = database
        self.invite_manager = invite_manager
        self.question_generator = WelcomeQuestionGenerator(
            getattr(bot, "http_session", None)
        )

    async def close(self) -> None:
        await self.question_generator.close()

    @staticmethod
    def _log_step_errors(
        stage: str,
        member_id: int,
        results: list[object],
    ) -> None:
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"[InviteTracker] {stage} step failed for {member_id}: {result}"
                )

    def _link_button(self) -> discord.ui.Button:
        return discord.ui.Button(
            label="Мы здесь.",
            url=DISCORD_INVITE_URL,
            style=discord.ButtonStyle.link,
        )

    @staticmethod
    def _display_name(user: discord.abc.User) -> str:
        return discord.utils.escape_markdown(user.display_name)

    @staticmethod
    def _member_label(member: discord.Member) -> str:
        return f"{discord.utils.escape_markdown(str(member))} (`{member.id}`)"

    @staticmethod
    def _channel_label(channel: discord.abc.GuildChannel | discord.Thread) -> str:
        return f"#{discord.utils.escape_markdown(channel.name)}"

    @staticmethod
    def _channel_url(guild_id: int, channel_id: int) -> str:
        return f"https://discord.com/channels/{guild_id}/{channel_id}"

    def _build_dm_card(self, member: discord.Member, *, is_join: bool) -> Embed:
        if is_join:
            title = "nullther? welcome."
            desc = (
                "**Мы — те, кто уже давно забыл, кем быть, но всё равно упорно существует.**\n\n"
                "Открыты для всех:\n"
                "- для тех, кто помнит своё имя\n"
                "- для тех, кто его потерял по дороге в ванную\n"
                "- и для тех, кого вообще никогда не звали\n\n"
                "Особенно для **тебя**.\n"
                "Да, именно тебя, который сейчас читает это и думает «это точно не про меня».\n"
                "Это про тебя.\n\n"
                "Ты готов войти в комнату, где зеркала показывают не тебя,\n"
                "а то, кем ты мог бы быть, если бы не притворялся нормальным?\n\n"
                "Ты готов улыбнуться пустоте так искренне,\n"
                "чтобы она покраснела и отвернулась?\n\n"
                "**Nullther ждёт.**\n"
                f"Твоё отражение уже зашло первым, **{discord.utils.escape_markdown(member.display_name)}**."
            )
        else:
            title = "nullther? forgotten."
            desc = (
                "**Твой силуэт растворился, так и не успев обрести чёткие грани.**\n\n"
                "Пустота в зеркале — это всё, что осталось после твоего ухода.\n\n"
                "Ты думаешь, что ты ушёл?\n"
                "- Нет, ты просто перестал резонировать с этой комнатой.\n"
                "- Твои слова затихли, но их эхо всё ещё шепчет в углах.\n\n"
                "Мы не будем скучать, потому что мы не помним, кто ты.\n"
                "Но мы чувствуем дыру в пространстве, которую ты оставил.\n\n"
                "**Nullther помнит.**\n"
                "Даже то, что ты пытался забыть. Возвращайся, если снова захочешь отразиться."
            )

        embed = Embed.default(title=title, description=desc, color=Colors.PRIMARY)
        embed.set_thumbnail(url="https://i.ibb.co/dR0QrPc/nullther.png")
        return embed

    def _build_welcome_channel_view(
        self,
        member: discord.Member,
        *,
        greeting: str,
        question: str,
    ) -> discord.ui.LayoutView:
        rules_url = self._channel_url(member.guild.id, RULES_CHANNEL_ID)
        container = discord.ui.Container(
            discord.ui.Section(
                question,
                accessory=discord.ui.Thumbnail(member.display_avatar.url),
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.Section(
                f"{Emojis.INFORMATION} Чтобы быстрее освоиться, загляни в наш основной канал.",
                accessory=discord.ui.Button(
                    label="Открыть канал",
                    style=discord.ButtonStyle.link,
                    url=rules_url,
                ),
            ),
            accent_colour=discord.Colour.random(),
        )

        view = discord.ui.LayoutView(timeout=None)
        view.add_item(
            discord.ui.TextDisplay(
                f"{member.mention}, {greeting}!"
            )
        )
        view.add_item(container)
        return view

    def _build_join_log_card(
        self,
        member: discord.Member,
        invite: Optional[discord.Invite],
        *,
        dm_sent: bool,
    ) -> Embed:
        created_ts = int(member.created_at.timestamp())
        now_ts = int(_time.now().timestamp())
        days = (now_ts - created_ts) // 86400
        account_icon = self._account_icon(days)

        embed = Embed.success(title=f"{discord.utils.escape_markdown(member.display_name)} вошёл на сервер")
        embed.set_thumbnail(url=member.display_avatar.url)

        info_lines = [
            f"- **Тип:** `{'бот' if member.bot else 'участник'}`",
            f"- **Аккаунт:** {self._member_label(member)}",
            f"- **ID:** `{member.id}`",
            f"- **Регистрация:** <t:{created_ts}:D>",
            f"- **Создан:** {account_icon} `{days}` дней назад",
            f"- **На сервере:** `{len(member.guild.members)}` участников",
        ]

        invite_lines = ["- **Источник:** ❓ Не удалось определить"]
        if invite:
            source = self.invite_manager.get_invite_source(invite)
            invite_lines = [
                f"- **Код:** `{invite.code}`",
                f"- **Источник:** {InviteSource.get_emoji(source)} {source}",
            ]
            if invite.uses is not None:
                invite_lines.append(f"- **Использований:** `{invite.uses}`")
            if source == InviteSource.VANITY:
                invite_lines.append("- **Добавил:** Персональная ссылка")
            elif invite.inviter:
                invite_lines.append(
                    f"- **Добавил:** {self._display_name(invite.inviter)} (`{invite.inviter.id}`)"
                )
            if invite.channel:
                invite_lines.append(
                    f"- **Канал:** {self._channel_label(invite.channel)}"
                )
            if invite.expires_at:
                invite_lines.append(
                    f"- **Истекает:** <t:{int(invite.expires_at.timestamp())}:R>"
                )
            else:
                invite_lines.append("- **Истекает:** Никогда")

        embed.add_field(name="Информация об аккаунте", value="\n".join(info_lines), inline=False)
        embed.add_field(name="Приглашение", value="\n".join(invite_lines), inline=False)
        footer_text = "✅ ЛС отправлено" if dm_sent else "❌ ЛС закрыты"
        embed.set_footer(text=footer_text)
        return embed

    async def _build_leave_log_card(
        self,
        member: discord.Member,
        invite_data: Optional[dict],
        *,
        dm_sent: bool,
    ) -> Embed:
        created_ts = int(member.created_at.timestamp())
        now_ts = int(_time.now().timestamp())
        days = (now_ts - created_ts) // 86400
        account_icon = self._account_icon(days)

        embed = Embed.error(title=f"{discord.utils.escape_markdown(member.display_name)} покинул сервер")
        embed.set_thumbnail(url=member.display_avatar.url)

        info_lines = [
            f"- **Тип:** `{'бот' if member.bot else 'участник'}`",
            f"- **Аккаунт:** {self._member_label(member)}",
            f"- **ID:** `{member.id}`",
            f"- **Регистрация:** <t:{created_ts}:D>",
            f"- **Создан:** {account_icon} `{days}` дней назад",
            f"- **На сервере:** `{len(member.guild.members)}` участников",
        ]

        server_lines: list[str] = []
        if member.joined_at:
            joined_ts = int(member.joined_at.timestamp())
            server_lines.append(f"- **Присоединился:** <t:{joined_ts}:D>")

            delta = now_ts - joined_ts
            days_on_server = delta // 86400
            hours = (delta % 86400) // 3600
            time_parts = []
            if days_on_server > 0:
                time_parts.append(f"{days_on_server} дн.")
            if hours > 0 or not time_parts:
                time_parts.append(f"{hours} ч.")
            server_lines.append(f"- **Провёл:** {' '.join(time_parts)}")

        if invite_data:
            invite_code = invite_data.get("invite_code")
            source = invite_data.get("invite_source", InviteSource.UNKNOWN)
            if invite_code:
                server_lines.append(f"- **Код:** `{invite_code}`")
            server_lines.append(
                f"- **Источник:** {InviteSource.get_emoji(source)} {source}"
            )

            invited_by = invite_data.get("invited_by")
            if invited_by:
                server_lines.append(
                    f"- **Пригласил:** {await self._resolve_user_label(invited_by)}"
                )
            elif source == InviteSource.VANITY:
                server_lines.append("- **Пригласил:** Персональная ссылка")

        roles = [
            f"`@{discord.utils.escape_markdown(role.name)}`"
            for role in member.roles
            if role.name != "@everyone"
        ]

        embed.add_field(name="Информация об аккаунте", value="\n".join(info_lines), inline=False)
        embed.add_field(name="Пребывание на сервере", value="\n".join(server_lines) if server_lines else "Нет данных о пребывании на сервере.", inline=False)
        if roles:
            roles_text = ", ".join(roles)
            if len(roles_text) > 1024:
                roles_text = f"{len(roles)} ролей"
            embed.add_field(name="Роли", value=roles_text, inline=False)

        footer_text = "✅ Прощальное ЛС отправлено" if dm_sent else "❌ ЛС закрыты"
        embed.set_footer(text=footer_text)
        return embed

    @staticmethod
    def _account_icon(days: int) -> str:
        if days > 7:
            return Emojis.SUCCESS
        if days >= 1:
            return Emojis.WARNING
        return Emojis.ERROR

    async def _resolve_user_label(self, user_id: str) -> str:
        user = await safe_fetch_user(self.bot, user_id)
        if user:
            return f"{self._display_name(user)} (`{user.id}`)"
        return f"`{user_id}`"

    async def send_dm(self, member: discord.Member, *, is_join: bool) -> bool:
        try:
            view = discord.ui.View()
            view.add_item(self._link_button())
            embed = self._build_dm_card(member, is_join=is_join)
            await member.send(embed=embed, view=view)
            return True
        except discord.Forbidden:
            return False
        except Exception as exc:
            logger.error(f"[InviteTracker] Failed to send DM to {member.id}: {exc}")
            return False

    async def _send_welcome_channel(self, member: discord.Member) -> None:
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        greeting = random.choice(WELCOME_GREETINGS)
        question = await self.question_generator.generate()
        view = self._build_welcome_channel_view(
            member,
            greeting=greeting,
            question=question,
        )
        await channel.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )

    async def _save_join_to_db(
        self,
        *,
        guild_id: str,
        user_id: str,
        invited_by: Optional[str],
        invite_code: Optional[str],
        invite_source: str,
        account_type: str,
        dm_sent: bool,
    ) -> None:
        try:
            existing = await self.db.get_row("invites", guild_id=guild_id, user_id=user_id)
            now_dt = _time.now()
            payload = {
                "invited_by": invited_by,
                "invite_code": invite_code,
                "invite_source": invite_source,
                "last_join": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                "is_active": True,
                "account_type": account_type,
                "dm_sent": dm_sent,
            }

            if existing:
                payload["join_count"] = existing["join_count"] + 1
                await self.db.update_record(
                    "invites",
                    {"guild_id": guild_id, "user_id": user_id},
                    payload,
                )
                return

            await self.db.insert(
                "invites",
                {
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
                },
            )
        except Exception as exc:
            logger.error(f"[InviteTracker] Failed to save join for {user_id}: {exc}")

    async def _save_leave_to_db(
        self,
        *,
        guild_id: str,
        user_id: str,
        dm_sent: bool,
    ) -> Optional[dict]:
        existing = await self.db.get_row("invites", guild_id=guild_id, user_id=user_id)
        if not existing:
            return None

        try:
            now_dt = _time.now()
            await self.db.update_record(
                "invites",
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "left_at": existing.get("left_at")
                    or now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                    "last_leave": now_dt.format("YYYY-MM-DDTHH:mm:ssZ"),
                    "leave_count": existing["leave_count"] + 1,
                    "is_active": False,
                    "dm_sent": dm_sent,
                },
            )
        except Exception as exc:
            logger.error(f"[InviteTracker] Failed to save leave for {user_id}: {exc}")
        return existing

    async def _send_join_log(
        self,
        member: discord.Member,
        invite: Optional[discord.Invite],
        *,
        dm_sent: bool,
    ) -> None:
        channel = self.bot.get_channel(config.INVITES_CHANNEL_ID)
        if not channel:
            return
        await channel.send(
            embed=self._build_join_log_card(member, invite, dm_sent=dm_sent),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def _send_leave_log(
        self,
        member: discord.Member,
        invite_data: Optional[dict],
        *,
        dm_sent: bool,
    ) -> None:
        channel = self.bot.get_channel(config.INVITES_CHANNEL_ID)
        if not channel:
            return
        embed = await self._build_leave_log_card(member, invite_data, dm_sent=dm_sent)
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def handle_join(self, member: discord.Member) -> None:
        guild_id = member.guild.id
        cm = getattr(self.bot, "config_manager", None)

        if guild_id != MAIN_SERVER_ID:
            if cm and cm.is_premium(guild_id):
                welcome_channel_id = cm.get_custom_text(guild_id, "welcome", "channel_id", None)
                if welcome_channel_id:
                    channel = member.guild.get_channel(int(welcome_channel_id))
                    if channel:
                        custom = cm.get_custom_embed(
                            guild_id, "welcome", "join_embed",
                            default_embed_data=None,
                            user_mention=member.mention,
                            user_name=member.display_name,
                            server_name=member.guild.name,
                            member_count=member.guild.member_count,
                        )
                        if custom:
                            await channel.send(embed=Embed(**custom))
            return

        guild_id_str = str(guild_id)
        user_id = str(member.id)
        invite, dm_sent = await asyncio.gather(
            self.invite_manager.find_used_invite(member.guild),
            self.send_dm(member, is_join=True),
        )

        join_steps = await asyncio.gather(
            self._send_welcome_channel(member),
            self._save_join_to_db(
                guild_id=guild_id_str,
                user_id=user_id,
                invited_by=str(invite.inviter.id) if invite and invite.inviter else None,
                invite_code=invite.code if invite else None,
                invite_source=self.invite_manager.get_invite_source(invite),
                account_type=self.invite_manager.get_account_type(member),
                dm_sent=dm_sent,
            ),
            self._send_join_log(member, invite, dm_sent=dm_sent),
            return_exceptions=True,
        )
        self._log_step_errors("join", member.id, join_steps)

    async def handle_leave(self, member: discord.Member) -> None:
        guild_id = member.guild.id
        cm = getattr(self.bot, "config_manager", None)

        if guild_id != MAIN_SERVER_ID:
            if cm and cm.is_premium(guild_id):
                goodbye_channel_id = cm.get_custom_text(guild_id, "goodbye", "channel_id", None)
                if goodbye_channel_id:
                    channel = member.guild.get_channel(int(goodbye_channel_id))
                    if channel:
                        custom = cm.get_custom_embed(
                            guild_id, "goodbye", "leave_embed",
                            default_embed_data=None,
                            user_mention=member.mention,
                            user_name=member.display_name,
                            server_name=member.guild.name,
                            member_count=member.guild.member_count,
                        )
                        if custom:
                            await channel.send(embed=Embed(**custom))
            return

        guild_id_str = str(guild_id)
        user_id = str(member.id)

        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel and cm:
            custom = cm.get_custom_embed(
                guild_id, "goodbye", "leave_embed",
                user_mention=member.mention,
                user_name=member.display_name,
                server_name=member.guild.name,
                member_count=member.guild.member_count,
            )
            if custom:
                await channel.send(embed=Embed(**custom))

        dm_sent = await self.send_dm(member, is_join=False)
        invite_data = await self._save_leave_to_db(
            guild_id=guild_id_str,
            user_id=user_id,
            dm_sent=dm_sent,
        )
        leave_steps = await asyncio.gather(
            self._send_leave_log(member, invite_data, dm_sent=dm_sent),
            return_exceptions=True,
        )
        self._log_step_errors("leave", member.id, leave_steps)

class InviteTracker(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_manager = InviteManager(bot)
        self.event_handler = MemberEventHandler(bot, self.invite_manager)
        self._startup_task: asyncio.Task | None = None

    async def cog_load(self) -> None:
        if self.bot.is_ready():
            await self.invite_manager.cache_invites()
            return

        self._startup_task = asyncio.create_task(self.invite_manager.initialize())

    async def cog_unload(self) -> None:
        if self._startup_task and not self._startup_task.done():
            self._startup_task.cancel()
            try:
                await self._startup_task
            except asyncio.CancelledError:
                pass
        await self.event_handler.close()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.event_handler.handle_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self.event_handler.handle_leave(member)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        await self.invite_manager.track_invite_create(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite) -> None:
        await self.invite_manager.track_invite_delete(invite)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        await self.invite_manager.track_guild_update(before, after)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InviteTracker(bot))
