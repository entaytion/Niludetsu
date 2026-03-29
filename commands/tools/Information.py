import platform
import re
import time

import discord
import psutil
from discord.ext import commands
from discord.utils import snowflake_time

from Niludetsu import Colors, Emojis

OWNER_ONLY_INFO_ID = 636570363605680139


class InfoCommands(commands.Cog):
    """Ког для вывода различной информации"""

    def __init__(self, bot):
        self.bot = bot
        self._invite_url_pattern = re.compile(
            r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.com/invite|discord\.gg)/[A-Za-z0-9-]+",
            re.IGNORECASE,
        )
        self._invite_code_pattern = re.compile(r"^[A-Za-z0-9-]{2,32}$")

    def _is_owner_info_allowed(self, ctx: commands.Context) -> bool:
        return ctx.author.id == OWNER_ONLY_INFO_ID

    async def _resolve_target(self, ctx: commands.Context, target: str):
        # 1. Проверяем инвайт
        if self._invite_url_pattern.search(target) or self._invite_code_pattern.fullmatch(target):
            try:
                invite = await self.bot.fetch_invite(target)
                return "invite", invite
            except:
                pass

        # 2. Ищем по ID
        target_id = None
        id_match = re.search(r"(\d{17,20})", target)
        if id_match:
            target_id = int(id_match.group(1))

        if target_id:
            # Юзер?
            try:
                user = await self.bot.fetch_user(target_id)
                return "user", user
            except:
                pass
            
            # Если на сервере, ищем роли/каналы
            if ctx.guild:
                role = ctx.guild.get_role(target_id)
                if role: return "role", role
                chan = ctx.guild.get_channel(target_id)
                if chan: return "channel", chan

        # 3. Эмодзи?
        if re.match(r"^<a?:\w+:\d+>$", target):
            return "emoji", target

        # 4. Ищем по именам (только на сервере)
        if ctx.guild:
            member = ctx.guild.get_member_named(target)
            if member: return "user", member
            
            role = discord.utils.get(ctx.guild.roles, name=target)
            if role: return "role", role
            
            chan = discord.utils.get(ctx.guild.channels, name=target)
            if chan: return "channel", chan

        return None, None

    async def _dispatch_info(self, ctx: commands.Context, target: str | None) -> None:
        if not self._is_owner_info_allowed(ctx):
            return

        if not target:
            await ctx.send(f"{Emojis.ERROR} Введи цель для поиска (ID, инвайт, имя или ник).")
            return

        t_type, obj = await self._resolve_target(ctx, target)

        if t_type == "invite":
            await self.show_combined_info(ctx, obj)
        elif t_type == "user":
            await self.show_userinfo(ctx, obj)
        elif t_type == "role":
            await self.show_roleinfo(ctx, obj)
        elif t_type == "channel":
            await self.show_channelinfo(ctx, obj)
        elif t_type == "emoji":
            await self.show_emojiinfo(ctx, target)
        else:
            await ctx.send(f"{Emojis.ERROR} Нихуя не нашел по этому запросу. Попробуй ID или прямую ссылку.")

    async def show_channelinfo(self, ctx, channel=None):
        """Показать информацию о канале"""
        if channel is None:
            channel = ctx.channel

        created_ts = int(channel.created_at.timestamp())
        category = channel.category.name if channel.category else "Нет"
        position = channel.position

        if isinstance(channel, discord.TextChannel):
            channel_type_str = "Текстовый канал" if not channel.is_news() else "Новостной канал"
        elif isinstance(channel, discord.VoiceChannel):
            channel_type_str = "Голосовой канал"
        elif isinstance(channel, discord.CategoryChannel):
            channel_type_str = "Категория"
        elif isinstance(channel, discord.StageChannel):
            channel_type_str = "Сцена"
        elif hasattr(discord, "ForumChannel") and isinstance(channel, discord.ForumChannel):
            channel_type_str = "Форум"
        else:
            channel_type_str = "Неизвестный тип"

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} Инфо о канале {channel.name}",
            description=f"**Канал:** {channel.mention} • `{channel.id}`",
            color=0x000001,
        )

        fields = [
            (
                f"> {Emojis.INFORMATION} Основное",
                f"**Тип:** `{channel_type_str}`\n"
                f"**Категория:** `{category}`\n"
                f"**Создан:** <t:{created_ts}:R>\n"
                f"**Позиция:** `{position}`",
            ),
        ]

        if isinstance(channel, discord.TextChannel):
            topic = channel.topic or "Нет"
            slowmode = channel.slowmode_delay
            nsfw = "Да" if channel.nsfw else "Нет"
            fields.append(
                (
                    f"> {Emojis.INFORMATION} Настройки текста",
                    f"**Тема:** `{topic}`\n"
                    f"**Слоумод:** `{slowmode} сек.`\n"
                    f"**NSFW:** `{nsfw}`",
                )
            )
            first_msg, last_msg = None, None
            try:
                async for msg in channel.history(limit=1, oldest_first=True):
                    first_msg = msg
                    break
            except: pass
            try:
                if channel.last_message_id:
                    last_msg = await channel.fetch_message(channel.last_message_id)
            except: pass
            parts = []
            if first_msg: parts.append(f"- Первое: [Тык сюда]({first_msg.jump_url})")
            if last_msg:
                ts = int(last_msg.created_at.timestamp())
                parts.append(f"- Последнее: {last_msg.author.mention} • <t:{ts}:R>")
            if parts: fields.append((f"> {Emojis.CHAT} Сообщения", "\n".join(parts)))

        elif isinstance(channel, discord.VoiceChannel):
            bitrate = channel.bitrate // 1000
            user_limit = channel.user_limit if channel.user_limit > 0 else "Без лимита"
            fields.append(
                (
                    f"> {Emojis.INFORMATION} Настройки голоса",
                    f"**Битрейт:** `{bitrate} kbps`\n"
                    f"**Лимит юзеров:** `{user_limit}`\n"
                    f"**В канале:** `{len(channel.members)}`",
                )
            )

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    async def show_emojiinfo(self, ctx, emoji: str):
        """Инфо о кастомном эмодзи"""
        match = re.match(r"^<(?P<anim>a?):(?P<name>[\w]+):(?P<id>\d+)>$", emoji)
        if not match: return

        anim_flag = bool(match.group("anim"))
        name, emoji_id = match.group("name"), match.group("id")
        fmt = "gif" if anim_flag else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{fmt}?size=1024"
        created = snowflake_time(int(emoji_id))

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} Эмодзи {name}",
            description=f"**Эмодзи:** {emoji} • ``{emoji_id}``",
            color=0x000001,
        )
        embed.set_thumbnail(url=url)
        embed.add_field(
            name=f"> {Emojis.INFORMATION} Детали",
            value=f"**Имя:** ``{name}``\n**Анимированное:** ``{'Да' if anim_flag else 'Нет'}``\n**Ссылка:** [Открыть]({url})",
            inline=False,
        )
        embed.set_footer(text=f"ID: {emoji_id} • Создано: {created.strftime('%d.%m.%Y')}")
        await ctx.send(embed=embed)

    async def show_roleinfo(self, ctx, role: discord.Role):
        """Инфо о роли"""
        guild = ctx.guild
        created_at = int(role.created_at.timestamp())
        color = str(role.color) if role.color.value else "Нет"
        members_with_role = [member for member in guild.members if role in member.roles]
        permissions = [n.replace("_", " ").capitalize() for n, v in role.permissions if v]

        embed = discord.Embed(
            title="Информация о роли:",
            description=f"- **Роль: {role.mention} • ``{role.name}`` • ``{role.id}``**\n",
            color=role.color,
        )
        embed.add_field(
            name="> <:aeInfoStatus:1375565493439692921> Характеристики:",
            value=f"- **Цвет: ``{color}``**\n- **Позиция: ``{role.position} из {len(guild.roles)}``**\n- **Создана: <t:{created_at}:R>**\n",
            inline=True,
        )
        embed.add_field(
            name="> <:aeInfoStatus:1375565493439692921> О роли:",
            value=f"- **Отдельно? — ``{'Да' if role.hoist else 'Нет'}``**\n- **Бот? — ``{'Да' if role.is_bot_managed() else 'Нет'}``**\n- **Участников: ``{len(members_with_role)}``**\n",
            inline=True,
        )
        if permissions:
            embed.add_field(name="> <:aeInfoStatus:1375565493439692921> Права:", value=", ".join(permissions[:20]) + ("..." if len(permissions) > 20 else ""), inline=False)

        if role.icon: embed.set_thumbnail(url=role.icon.url)
        await ctx.send(embed=embed, view=RoleMembersView(role, members_with_role))

    async def show_combined_info(self, ctx, invite):
        """Сервер + Инвайт в одном флаконе"""
        embed = self.build_serverinfo_from_invite_embed(invite)
        if embed: await ctx.send(embed=embed)
        else: await ctx.send(f"{Emojis.ERROR} Не смог вытянуть инфу о сервере.")

    def build_serverinfo_from_invite_embed(self, invite) -> discord.Embed | None:
        guild = invite.guild
        if guild is None: return None

        icon_url = guild.icon.url if guild.icon else None
        banner_url = guild.banner.url if guild.banner else None
        
        desc_lines = [f"- **Владелец:** <@{getattr(guild, 'owner_id', '???')}> • `{getattr(guild, 'owner_id', '???')}`"]
        img_parts = []
        if icon_url: img_parts.append(f"[Ава `👤`]({icon_url})")
        if banner_url: img_parts.append(f"[Баннер `🖼️`]({banner_url})")
        if img_parts: desc_lines.append(f"- **Изображения:** {' • '.join(img_parts)}")
        desc_lines.append(f"- **Описание:** {getattr(guild, 'description', None) or 'Нет'}")

        member_count = invite.approximate_member_count or 0
        online_count = invite.approximate_presence_count or 0

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} Информация о сервере",
            description=f"**{getattr(guild, 'name', 'ХЗ сервер')}**\n" + "\n".join(desc_lines),
            color=Colors.INFO,
        )
        if icon_url: embed.set_thumbnail(url=icon_url)

        embed.add_field(
            name=f"> <:aeInfoPerms:1375568887449518342> `{member_count}` участников",
            value=f"- Онлайн: **`{online_count}`**\n- Оффлайн: **`{max(member_count - online_count, 0)}`**\n- Всего: **`{member_count}`**",
            inline=False,
        )
        embed.add_field(
            name=f"> {Emojis.NAME} Инвайт",
            value=f"- Канал: <#{invite.channel.id if invite.channel else '???'}>\n- Код: `{invite.code}`\n- Ссылка: `https://discord.gg/{invite.code}`",
            inline=False,
        )
        created = getattr(guild, 'created_at', None)
        footer_text = f"ID: {getattr(guild, 'id', '???')} • Создан: {created.strftime('%d.%m.%Y') if created else 'ХЗ'}"
        embed.set_footer(text=footer_text)
        return embed


    async def build_userinfo_embed(self, ctx, user=None) -> discord.Embed:
        """Собрать embed с информацией о пользователе"""
        if user is None:
            user = ctx.author

        guild = ctx.guild
        member = guild.get_member(user.id) if guild else None
        on_guild = bool(member)

        if on_guild and member.joined_at:
            joined_members = sorted(
                [m for m in guild.members if m.joined_at], key=lambda m: m.joined_at
            )
            pos = next(
                (i for i, m in enumerate(joined_members, start=1) if m.id == member.id),
                None,
            )
            total = len(joined_members)
            pos_str = f" (#{pos}/{total})" if pos else ""
        else:
            pos_str = ""

        user_id = getattr(user, "id", 0)
        banner_url = await get_user_banner(
            self.bot, user_id, guild.id if on_guild else None
        )

        status_map = {
            discord.Status.online: Emojis.ONLINE,
            discord.Status.idle: Emojis.IDLE,
            discord.Status.dnd: Emojis.DND,
            discord.Status.offline: Emojis.OFFLINE,
        }
        status_names = {
            discord.Status.online: "Онлайн",
            discord.Status.idle: "Неактивен",
            discord.Status.dnd: "Не беспокоить",
            discord.Status.offline: "Оффлайн",
        }
        stat = member.status if on_guild else discord.Status.offline
        status_display = f"{status_map.get(stat, '')} {status_names.get(stat, stat.name.capitalize())}"

        flags = getattr(user, "public_flags", None)
        badge_mapping = {
            "staff": Emojis.DISCORD_STAFF,
            "partner": Emojis.PARTNER_DISCORD,
            "bug_hunter": Emojis.BUG_HUNTER_1,
            "bug_hunter_level_2": Emojis.BUG_HUNTER_2,
            "hypesquad_events": Emojis.HYPESQUAD_EVENTS,
            "hypesquad_bravery": Emojis.HYPESQUAD_BRAVERY,
            "hypesquad_brilliance": Emojis.HYPESQUAD_BRILLIANCE,
            "hypesquad_balance": Emojis.HYPESQUAD_BALANCE,
            "early_supporter": Emojis.EARLY_SUPPORTER,
            "verified_bot_developer": Emojis.VERIFIED_BOT_DEVELOPER,
        }
        badges = [
            emoji
            for attr, emoji in badge_mapping.items()
            if flags and getattr(flags, attr, False)
        ]
        if getattr(user, "bot", False):
            badges.append(Emojis.BOT_DISCORD)
        badges_str = " ".join(badges) if badges else "Нет"

        img_parts = []
        user_avatar = getattr(user, "avatar", None)
        if user_avatar:
            img_parts.append(f"[Аватарка `👤`]({user_avatar.url})")
        if banner_url:
            img_parts.append(f"[Баннер `🖼️`]({banner_url})")
        images_text = " • ".join(img_parts) if img_parts else "Нет"

        colour = member.color.value if on_guild and member.color.value else 0x5865F2
        user_mention = getattr(user, "mention", "Неизвестный пользователь")
        display_avatar = getattr(user, "display_avatar", None)

        embed = discord.Embed(
            title=f"{Emojis.UNKNOWN} Информация о пользователе",
            description=(
                f"**Пользователь:** {user_mention}\n"
                f"**Статус:** {status_display}\n"
                f"**На сервере:** {'Да' if on_guild else 'Нет'}{pos_str}\n"
                f"**Значки:** {badges_str}\n"
                f"**Изображения:** {images_text}"
            ),
            color=colour,
        )
        thumbnail_url = (
            user_avatar.url
            if user_avatar
            else (display_avatar.url if display_avatar else None)
        )
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        user_name = getattr(user, "name", "Неизвестно")
        user_created_at = getattr(user, "created_at", None)
        user_created_text = (
            f"<t:{int(user_created_at.timestamp())}:F>"
            if user_created_at
            else "Неизвестно"
        )

        embed.add_field(
            name="> Основная информация",
            value=(
                f"**Имя:** `{user_name}`\n"
                f"**ID:** `{user_id}`\n"
                f"**Создан:** {user_created_text}"
            ),
            inline=False,
        )

        if on_guild and member.joined_at:
            joined_ts = int(member.joined_at.timestamp())
            sorted_roles = sorted(
                (r for r in member.roles if r.name != "@everyone"),
                key=lambda r: r.position,
                reverse=True,
            )
            roles_text = (
                " • ".join(f"`{r.name}`" for r in sorted_roles)
                if sorted_roles
                else "Нет ролей"
            )
            embed.add_field(
                name=f"> {Emojis.ICON_CONFIG} Серверная информация",
                value=(f"**Вступил(а):** <t:{joined_ts}:R>\n**Роли:** {roles_text}"),
                inline=False,
            )

            activities = []
            for act in member.activities:
                if act.type == discord.ActivityType.playing:
                    activities.append(f"🎮 Играет в **{act.name}**")
                elif act.type == discord.ActivityType.streaming:
                    activities.append(f"📺 Стримит **{act.name}**")
                elif act.type == discord.ActivityType.listening and hasattr(
                    act, "title"
                ):
                    activities.append(f"🎵 Слушает **{act.title}**")
                elif act.type == discord.ActivityType.watching:
                    activities.append(f"👀 Смотрит **{act.name}**")
                else:
                    activities.append(f"- {act.name}")

            if activities:
                embed.add_field(
                    name=f"> {Emojis.ICON_STATISTICS} Активности",
                    value="\n".join(activities),
                    inline=False,
                )

        user_created_footer = (
            user_created_at.strftime("%d.%m.%Y") if user_created_at else "Неизвестно"
        )
        embed.set_footer(text=f"ID: {user_id} • Создан: {user_created_footer}")
        return embed

    async def show_userinfo(self, ctx, user=None):
        """Показать информацию о пользователе"""
        await ctx.send(embed=await self.build_userinfo_embed(ctx, user))

    @commands.hybrid_command(name="user", aliases=["userinfo", "uinfo"])
    async def user_hybrid(self, ctx: commands.Context, *, target: discord.User = None):
        """Показать информацию о пользователе (доступно всем)"""
        await self.show_userinfo(ctx, target or ctx.author)

    @commands.command(name="info", aliases=["инфо", "information"])
    async def info_prefix(self, ctx: commands.Context, *, target: str = None):
        """Главная команда для получения инфы о чем угодно (только для владельца)"""
        await self._dispatch_info(ctx, target)



class RoleMembersView(discord.ui.View):
    """View для кнопки просмотра участников с ролью"""

    def __init__(self, role: discord.Role, members_with_role: list):
        super().__init__(timeout=300)
        self.role = role
        self.members_with_role = members_with_role

    @discord.ui.button(
        label="Глянуть участников с ролью",
        style=discord.ButtonStyle.primary,
        emoji="👥",
    )
    async def show_members(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Показать список участников с ролью"""
        if not self.members_with_role:
            await interaction.response.send_message(
                f"❌ Нет участников с ролью {self.role.mention}", ephemeral=True
            )
            return

        members_per_page = 20
        total_pages = (
            len(self.members_with_role) + members_per_page - 1
        ) // members_per_page

        page = 1
        start_idx = (page - 1) * members_per_page
        end_idx = min(start_idx + members_per_page, len(self.members_with_role))

        members_list = []
        for i, member in enumerate(
            self.members_with_role[start_idx:end_idx], start_idx + 1
        ):
            members_list.append(f"{i}. {member.mention}")

        embed = discord.Embed(
            title=f"Участники с ролью {self.role.name}",
            description="\n".join(members_list),
            color=self.role.color,
        )
        embed.set_footer(
            text=f"Страница {page}/{total_pages} • Всего участников: {len(self.members_with_role)}"
        )

        if total_pages > 1:
            view = MembersPaginationView(
                self.role,
                self.members_with_role,
                page,
                members_per_page=members_per_page,
            )
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


class MembersPaginationView(discord.ui.View):
    """View для навигации по страницам участников"""

    def __init__(
        self,
        role: discord.Role,
        members_with_role: list,
        current_page: int = 1,
        *,
        members_per_page: int = 20,
    ):
        super().__init__(timeout=300)
        self.role = role
        self.members_with_role = members_with_role
        self.current_page = current_page
        self.members_per_page = max(1, members_per_page)
        self.total_pages = (
            len(members_with_role) + self.members_per_page - 1
        ) // self.members_per_page
        self.update_buttons()

    def update_buttons(self):
        """Обновить состояние кнопок навигации"""
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= self.total_pages

    def get_page_embed(self):
        """Получить embed для текущей страницы"""
        start_idx = (self.current_page - 1) * self.members_per_page
        end_idx = min(start_idx + self.members_per_page, len(self.members_with_role))

        members_list = []
        for i, member in enumerate(
            self.members_with_role[start_idx:end_idx], start_idx + 1
        ):
            members_list.append(f"{i}. {member.mention}")

        embed = discord.Embed(
            title=f"Участники с ролью {self.role.name}",
            description="\n".join(members_list),
            color=self.role.color,
        )
        embed.set_footer(
            text=f"Страница {self.current_page}/{self.total_pages} • Всего участников: {len(self.members_with_role)}"
        )
        return embed

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Предыдущая страница"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_buttons()
            embed = self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Вперед", style=discord.ButtonStyle.secondary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Следующая страница"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_buttons()
            embed = self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)


async def get_user_banner(bot, user_id, guild_id=None):
    """Получает баннер пользователя через API Discord"""
    try:
        if guild_id:
            path = f"/guilds/{guild_id}/members/{user_id}"
        else:
            path = f"/users/{user_id}"

        route_cls = getattr(getattr(bot, "http", None), "Route", None)
        if route_cls is None:
            return None

        route = route_cls("GET", path)
        data = await bot.http.request(route)
        if guild_id:
            banner_hash = data.get("user", {}).get("banner")
        else:
            banner_hash = data.get("banner")
        if banner_hash is None:
            return None
        fmt = "gif" if str(banner_hash).startswith("a_") else "png"
        return f"https://cdn.discordapp.com/banners/{user_id}/{banner_hash}.{fmt}?size=4096"
    except Exception as e:
        print(f"Ошибка при получении баннера: {e}")
        return None


async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
