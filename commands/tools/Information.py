import discord, platform, psutil, re, time
from discord import app_commands
from discord.ext import commands
from discord.utils import snowflake_time
from Niludetsu import Emojis, Colors, InfoCard


class InfoCommands(commands.Cog):
    """Ког для вывода различной информации"""

    def __init__(self, bot):
        self.bot = bot
        self._type_aliases = {
            "bot": "bot",
            "бот": "bot",
            "channel": "channel",
            "канал": "channel",
            "emoji": "emoji",
            "эмодзи": "emoji",
            "invite": "invite",
            "инвайт": "invite",
            "role": "role",
            "роль": "role",
            "server": "server",
            "сервер": "server",
            "guild": "server",
            "user": "user",
            "пользователь": "user",
            "юзер": "user",
        }
        self._invite_url_pattern = re.compile(
            r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.com/invite|discord\.gg)/[A-Za-z0-9-]+",
            re.IGNORECASE,
        )
        self._invite_code_pattern = re.compile(r"^[A-Za-z0-9-]{2,32}$")

    def _parse_prefix_arguments(self, ctx: commands.Context) -> tuple[str, str | None]:
        prefix = (getattr(ctx, "prefix", "") or "")
        invoked = (getattr(ctx, "invoked_with", "") or "")
        content = ctx.message.content if ctx.message else ""
        raw_args = content[len(prefix + invoked):].strip() if content else ""
        if not raw_args:
            return "bot", None

        parts = raw_args.split()
        first_part = parts[0]
        remaining = " ".join(parts[1:]) if len(parts) > 1 else None
        alias = self._type_aliases.get(first_part.lower())
        if alias:
            return alias, remaining

        detection = self._detect_target_type(ctx, first_part)
        if detection:
            return detection

        if remaining:
            combined_detection = self._detect_target_type(ctx, raw_args)
            if combined_detection:
                return combined_detection

        return "bot", None

    def _detect_target_type(self, ctx: commands.Context, token: str) -> tuple[str, str] | None:
        candidate = token.strip()
        if not candidate:
            return None

        if re.match(r"^<a?:[\w]+:\d+>$", candidate):
            return "emoji", candidate

        if self._invite_url_pattern.search(candidate):
            return "invite", candidate

        if candidate.startswith("<@&") and candidate.endswith(">"):
            return "role", candidate
        if candidate.startswith("<@") and candidate.endswith(">"):
            return "user", candidate
        if candidate.startswith("<#") and candidate.endswith(">"):
            return "channel", candidate

        stripped = candidate.strip("<@!#>&")
        if stripped.isdigit():
            identifier = int(stripped)
            guild = ctx.guild
            if guild:
                role = guild.get_role(identifier)
                if role:
                    return "role", candidate
                channel = guild.get_channel(identifier)
                if channel:
                    return "channel", candidate
                member = guild.get_member(identifier)
                if member:
                    return "user", candidate
            user = self.bot.get_user(identifier)
            if user:
                return "user", candidate

        if self._invite_code_pattern.fullmatch(candidate):
            return "invite", candidate

        return None

    async def _dispatch_info(self, ctx: commands.Context, info_type: str, target: str | None) -> None:
        if info_type == "bot":
            await self.show_botinfo(ctx)
            return

        if info_type == "channel":
            if target:
                try:
                    channel_id = int(target.strip("<>#"))
                    channel = ctx.guild.get_channel(channel_id) if ctx.guild else None
                    if channel:
                        await self.show_channelinfo(ctx, channel)
                        return
                except Exception:
                    pass
                await ctx.send(f"{Emojis.ERROR} Укажите корректный канал")
                return
            await self.show_channelinfo(ctx)
            return

        if info_type == "emoji":
            if target:
                await self.show_emojiinfo(ctx, target)
            else:
                await ctx.send(f"{Emojis.ERROR} Укажите эмодзи")
            return

        if info_type == "invite":
            if target:
                try:
                    invite_obj = await self.bot.fetch_invite(target)
                except Exception:
                    await ctx.send(f"{Emojis.ERROR} Инвайт не найден")
                    return
                await self.show_inviteinfo(ctx, invite_obj)
            else:
                await ctx.send(f"{Emojis.ERROR} Укажите ссылку или код инвайта")
            return

        if info_type == "role":
            if target and ctx.guild:
                try:
                    role_id = int(target.strip("<@&>"))
                    role = ctx.guild.get_role(role_id)
                    if role:
                        await self.show_roleinfo(ctx, role)
                        return
                except Exception:
                    pass
                await ctx.send(f"{Emojis.ERROR} Укажите корректную роль")
            else:
                await ctx.send(f"{Emojis.ERROR} Укажите роль")
            return

        if info_type == "server":
            await self.show_serverinfo(ctx)
            return

        if info_type == "user":
            user: discord.abc.User
            if target:
                normalized = target.strip()
                try:
                    user_id = int(normalized.strip("<@!>"))
                    user = await self.bot.fetch_user(user_id)
                except Exception:
                    guild_member = None
                    if ctx.guild:
                        guild_member = ctx.guild.get_member_named(normalized)
                        if not guild_member and normalized.lower().startswith("@"):
                            guild_member = ctx.guild.get_member_named(normalized[1:])
                    if guild_member:
                        user = guild_member
                    else:
                        await ctx.send(f"{Emojis.ERROR} Пользователь не найден")
                        return
            else:
                user = ctx.author
            await self.show_userinfo(ctx, user)
            return

    async def show_botinfo(self, ctx):
        """Показать информацию о боте"""
        bot = self.bot

        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        gpu_usage = None
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_usage = float(result.stdout.strip().split('\n')[0])
        except Exception:
            pass

        start_time = getattr(bot, 'start_time', time.time())
        uptime_seconds = int(time.time() - start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            uptime = f"{days}д {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        total_guilds = len(bot.guilds)
        total_users = sum(g.member_count for g in bot.guilds)
        total_cogs = len(bot.cogs)
        total_commands = len([cmd for cmd in bot.tree.walk_commands()])

        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)

        load_parts = [f"CPU ``{cpu_usage:.1f}%``"]
        if gpu_usage is not None:
            load_parts.append(f"GPU ``{gpu_usage:.1f}%``")
        load_str = " • ".join(load_parts)

        created_at = discord.utils.snowflake_time(bot.user.id)

        card = InfoCard(colour=0x000001)
        card.thumbnail_url = bot.user.avatar.url if bot.user.avatar else None
        card.header = (
            f"**Привет, я {bot.user.name}!**\n"
            f"- Меня создал **``@entaytion``** для сервера **[Æther!](https://discord.gg/HxwZ6ceKKj)**."
        )
        card.sections = [
            (
                f"> {Emojis.ANALYTICS} Аналитика:\n"
                f"**Статистика:** ``{total_guilds}`` {'сервер' if total_guilds == 1 else 'серверов'}, "
                f"``{total_users}`` {'пользователь' if total_users == 1 else 'пользователей'}, "
                f"``{total_cogs}`` {'ког' if total_cogs == 1 else 'когов'}, "
                f"``{total_commands}`` {'команда' if total_commands == 1 else 'команд'}.\n"
                f"**Технологии:** <:aeDiscordPython:1375863045007343770> Discord.py ``{discord.__version__}`` • "
                f"<:aePython:1375862844096249937> Python ``{platform.python_version()}``\n"
                f"**Производительность:** Пинг ``{round(bot.latency * 1000)}`` мс • Аптайм ``{uptime}``"
            ),
            (
                f"> {Emojis.HARDWARE} Система:\n"
                f"**ОС:** ``{platform.system()} {platform.release()}``\n"
                f"**Нагрузка:** {load_str}\n"
                f"**RAM:** ``{memory.percent:.1f}%`` (``{memory_used_gb:.1f}`` / ``{memory_total_gb:.1f}`` GB)\n"
                f"**Диск:** ``{disk.percent:.1f}%`` (``{disk_used_gb:.1f}`` / ``{disk_total_gb:.1f}`` GB)"
            ),
        ]
        card.footer = f"-# ID: {bot.user.id} • Создан: {created_at.strftime('%d.%m.%Y')}"

        await ctx.send(view=card.build())

    async def show_channelinfo(self, ctx, channel: discord.abc.GuildChannel = None):
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

        card = InfoCard(colour=0x000001)
        card.header = (
            f"**Информация о канале {channel.name}**\n"
            f"- **Канал:** {channel.mention} • `{channel.id}`"
        )

        sections = [
            (
                f"> {Emojis.INFORMATION} Основная информация:\n"
                f"**Тип:** `{channel_type_str}`\n"
                f"**Категория:** `{category}`\n"
                f"**Дата создания:** <t:{created_ts}:R>\n"
                f"**Позиция:** `{position}`"
            ),
        ]

        if isinstance(channel, discord.TextChannel):
            topic = channel.topic or "Нет"
            slowmode = channel.slowmode_delay
            nsfw = "Да" if channel.nsfw else "Нет"
            sections.append(
                f"> {Emojis.INFORMATION} Настройки текстового канала:\n"
                f"**Тема:** `{topic}`\n"
                f"**Медленный режим:** `{slowmode} сек.`\n"
                f"**NSFW:** `{nsfw}`"
            )
            first_msg = None
            last_msg = None
            try:
                async for msg in channel.history(limit=1, oldest_first=True):
                    first_msg = msg
                    break
            except Exception:
                pass
            try:
                if channel.last_message_id:
                    last_msg = await channel.fetch_message(channel.last_message_id)
            except Exception:
                pass
            parts = []
            if first_msg:
                parts.append(f"- Первое: [Перейти к первому сообщению]({first_msg.jump_url})")
            if last_msg:
                ts = int(last_msg.created_at.timestamp())
                parts.append(f"- Последнее: {last_msg.author.mention} • <t:{ts}:R>")
            if parts:
                sections.append(f"> {Emojis.CHAT} Сообщения:\n" + "\n".join(parts))

        elif isinstance(channel, discord.VoiceChannel):
            bitrate = channel.bitrate // 1000
            user_limit = channel.user_limit if channel.user_limit > 0 else "Без лимита"
            members = len(channel.members)
            sections.append(
                f"> {Emojis.INFORMATION} Настройки голосового канала:\n"
                f"**Битрейт:** `{bitrate} kbps`\n"
                f"**Лимит пользователей:** `{user_limit}`\n"
                f"**Подключено участников:** `{members}`"
            )

        elif hasattr(discord, "ForumChannel") and isinstance(channel, discord.ForumChannel):
            topic = getattr(channel, "topic", "Нет")
            default_layout = getattr(channel, "default_layout", "Нет")
            default_sort = getattr(channel, "default_sort_order", "Нет")
            sections.append(
                f"> {Emojis.INFORMATION} Настройки форума:\n"
                f"**Тема:** `{topic}`\n"
                f"**Стандартная разметка:** `{default_layout}`\n"
                f"**Сортировка:** `{default_sort}`"
            )

        card.sections = sections
        await ctx.send(view=card.build())

    async def show_emojiinfo(self, ctx, emoji: str):
        """Показать информацию о кастомном эмодзи Discord"""
        match = re.match(r"^<(?P<anim>a?):(?P<name>[\w]+):(?P<id>\d+)>$", emoji)
        if not match:
            try:
                await ctx.message.add_reaction("💢")
                import asyncio
                await asyncio.sleep(3)
                await ctx.message.delete()
            except:
                pass
            return

        anim_flag = bool(match.group('anim'))
        name = match.group('name')
        emoji_id = match.group('id')
        fmt = 'gif' if anim_flag else 'png'
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{fmt}?size=1024"
        created = snowflake_time(int(emoji_id))

        card = InfoCard(colour=0x000001)
        card.thumbnail_url = url
        card.header = (
            f"**Информация об эмодзи {name}**\n"
            f"- **Эмодзи:** {emoji} • ``{emoji_id}``"
        )
        card.sections = [
            (
                f"> {Emojis.INFORMATION} Основная информация:\n"
                f"**Имя:** ``{name}``\n"
                f"**Анимировано:** ``{'Да' if anim_flag else 'Нет'}``\n"
                f"**Формат:** ``{fmt.upper()}``\n"
                f"**Ссылка:** [Открыть эмодзи]({url})"
            ),
        ]
        card.footer = f"-# ID: {emoji_id} • Создан: {created.strftime('%d.%m.%Y')}"

        await ctx.send(view=card.build())

    async def show_inviteinfo(self, ctx, invite: discord.Invite):
        """Показать информацию о приглашении"""
        guild = invite.guild
        if not guild:
            await ctx.send("Не удалось получить информацию о сервере.")
            return

        member_count = invite.approximate_member_count or 0
        online_count = invite.approximate_presence_count or 0
        offline_count = member_count - online_count
        channel_count = len(getattr(guild, 'channels', []))
        emoji_count = len(getattr(guild, 'emojis', []))
        role_count = len(getattr(guild, 'roles', []))
        icon_url = guild.icon.url if guild.icon else None
        banner_url = guild.banner.url if guild.banner else None
        splash_url = guild.splash.url if guild.splash else None
        discovery_splash_url = guild.discovery_splash.url if getattr(guild, "discovery_splash", None) else None

        desc_lines = []
        if hasattr(guild, 'owner_id') and guild.owner_id:
            desc_lines.append(f"- **Владелец сервера:** <@{guild.owner_id}> • `{guild.owner_id}`")
        else:
            desc_lines.append(f"- **Владелец сервера:** **Discord**")
        img_parts = []
        if icon_url:
            img_parts.append(f"[Аватарка `👤`]({icon_url})")
        if banner_url:
            img_parts.append(f"[Баннер `🖼️`]({banner_url})")
        if splash_url:
            img_parts.append(f"[Приглашение `🏙️`]({splash_url})")
        if discovery_splash_url:
            img_parts.append(f"[Discovery Splash `🏜️`]({discovery_splash_url})")
        if img_parts:
            desc_lines.append(f"- **Изображения:** {' • '.join(img_parts)}")
        desc_lines.append(f"- **Описание:** {guild.description or 'Нет описания'}")

        vanity_code = getattr(guild, 'vanity_url_code', None)
        is_vanity = bool(vanity_code and invite.code == vanity_code)
        info_lines = []
        if is_vanity:
            info_lines.append("**Создал(а):** **Discord**")
        else:
            inviter = invite.inviter
            info_lines.append(f"**Создал(а):** {inviter.mention if inviter else 'Неизвестно'} • `{inviter.id if inviter else 'N/A'}`")
        try:
            channel_mention = f"<#{invite.channel.id}>"
        except Exception:
            channel_mention = "Неизвестно"
        info_lines.append(f"**Канал:** {channel_mention} • `{invite.channel.name}`")
        info_lines.append(f"**Участников:** {online_count} {Emojis.ONLINE} / {offline_count} {Emojis.OFFLINE} • `{member_count}` участников")
        expires = 'Бессрочная' if not invite.expires_at else f"До <t:{int(invite.expires_at.timestamp())}:f>"
        info_lines.append(f"**Срок действия:** {expires}")
        info_lines.append(f"**Ссылка:** `https://discord.gg/{invite.code}`")
        if not is_vanity:
            info_lines.append(f"- **Аналитика:** `{channel_count}` каналов, `{emoji_count}` эмодзи, `{role_count}` ролей.")

        card = InfoCard(colour=0x000001)
        card.thumbnail_url = icon_url
        card.header = f"**{guild.name}**\n" + "\n".join(desc_lines)
        card.sections = [
            f"> {Emojis.NAME} Информация о приглашении:\n" + "\n".join(info_lines),
        ]
        card.footer = f"-# ID: {guild.id} • Создан: {guild.created_at.strftime('%d.%m.%Y')}"

        await ctx.send(view=card.build())

    async def show_roleinfo(self, ctx, role: discord.Role):
        """Показать информацию о роли"""
        guild = ctx.guild
        created_at = int(role.created_at.timestamp())

        color = str(role.color) if role.color.value else "Нет"
        members_with_role = [member for member in guild.members if role in member.roles]
        members_total = len(members_with_role)
        permissions = [name.replace('_', ' ').capitalize() for name, value in role.permissions if value]

        embed = discord.Embed(
            title="Информация о роли:",
            description=f"- **Роль: {role.mention} • ``{role.name}`` • ``{role.id}``**\n",    
            color=role.color
        )

        embed.add_field(
            name="> <:aeInfoStatus:1375565493439692921> Характеристики:",
            value=(
                f"- **Цвет: ``{color}``**\n"
                f"- **Позиция: ``{role.position} из {len(guild.roles)}``**\n"
                f"- **Дата создания: <t:{created_at}:R>**\n"
            ),
            inline=True
        )

        embed.add_field(
            name="> <:aeInfoStatus:1375565493439692921> О роли:",
            value=(
                f"- **Отдельно? — ``{'Да' if role.hoist else 'Нет'}``**\n"
                f"- **Роль бота? — ``{'Да' if role.is_bot_managed() else 'Нет'}``**\n"
                f"- **Интеграция? — ``{'Да' if role.is_integration() else 'Нет'}``**\n"
                f"- **Премиум? — ``{'Да' if role.is_premium_subscriber() else 'Нет'}``**\n"
                f"- **Участников с ролью: ``{members_total}``**\n"
            ),
            inline=True
        )

        if permissions:
            embed.add_field(
                name="> <:aeInfoStatus:1375565493439692921> Разрешения:",
                value=", ".join(permissions),
                inline=False
            )

        if role.icon:
            embed.set_thumbnail(url=role.icon.url)

        view = RoleMembersView(role, members_with_role)
        await ctx.send(embed=embed, view=view)

    async def show_serverinfo(self, ctx):
        """Показать информацию о сервере"""
        guild = ctx.guild
        if not guild:
            await ctx.send("Команда работает только на сервере.")
            return

        icon_url = guild.icon.url if guild.icon else None
        banner_url = guild.banner.url if guild.banner else None
        splash_url = guild.splash.url if guild.splash else None
        discovery_splash_url = getattr(guild, 'discovery_splash', None)
        discovery_url = discovery_splash_url.url if discovery_splash_url else None

        img_parts = []
        if icon_url:
            img_parts.append(f"[Аватарка `👤`]({icon_url})")
        if banner_url:
            img_parts.append(f"[Баннер `🖼️`]({banner_url})")
        if splash_url:
            img_parts.append(f"[Приглашение `🏙️`]({splash_url})")
        if discovery_url:
            img_parts.append(f"[Discovery Splash `🏜️`]({discovery_url})")

        desc_lines = []
        try:
            owner = await guild.fetch_member(guild.owner_id)
            owner_mention = owner.mention
        except:
            owner_mention = f"ID: {guild.owner_id}"
        desc_lines.append(f"- **Владелец сервера:** {owner_mention} • `{guild.owner_id}`")
        if img_parts:
            desc_lines.append(f"- **Изображения:** {' • '.join(img_parts)}")
        desc_lines.append(f"- **Описание:** {guild.description or 'Отсутствует'}")

        admins = len([m for m in guild.members if m.guild_permissions.administrator])
        boosters = len([m for m in guild.members if m.premium_since])
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot and not m.guild_permissions.administrator and not m.premium_since])
        bots = total - humans

        channels_count = len(guild.channels)
        text_ch = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_ch = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        cat_ch = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        stage_ch = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        forum_ch = len([c for c in guild.channels if hasattr(discord, 'ForumChannel') and isinstance(c, discord.ForumChannel)])

        roles = guild.roles[1:]

        rules = guild.rules_channel.mention if guild.rules_channel else 'Отсутствует'
        system = guild.system_channel.mention if guild.system_channel else 'Отсутствует'
        updates = guild.public_updates_channel.mention if guild.public_updates_channel else 'Отсутствует'
        alerts = guild.safety_alerts_channel.mention if hasattr(guild, 'safety_alerts_channel') and guild.safety_alerts_channel else 'Отсутствует'

        card = InfoCard(colour=Colors.INFO)
        card.thumbnail_url = icon_url
        card.header = f"**{guild.name}**\n" + "\n".join(desc_lines)
        card.sections = [
            (
                f"> <:aeInfoPerms:1375568887449518342> `{total}` участников:\n"
                f"- Админов: **`{admins}`**\n"
                f"- Бустеров: **`{boosters}`**\n"
                f"- Ботов: **`{bots}`**\n"
                f"- Людей: **`{humans}`**"
            ),
            (
                f"> 📋 `{channels_count}` каналов:\n"
                f"- Категорий: **`{cat_ch}`**\n"
                f"- Текстовых: **`{text_ch}`**\n"
                f"- Голосовых: **`{voice_ch}`**\n"
                f"- Сцен: **`{stage_ch}`**\n"
                f"- Форумов: **`{forum_ch}`**"
            ),
            (
                f"> {Emojis.ICON_CONFIG} Прочее:\n"
                f"- Эмодзи: **`{len(guild.emojis)}`**\n"
                f"- Стикеры: **`{len(guild.stickers)}`**\n"
                f"- Роли: **`{len(roles)}`**"
            ),
            (
                f"> {Emojis.ICON_CONFIG} Системные каналы:\n"
                f"- Правила: {rules}\n"
                f"- Системные сообщения: {system}\n"
                f"- Обновления: {updates}\n"
                f"- Безопасность: {alerts}"
            ),
        ]
        card.footer = f"-# ID: {guild.id} • Создан: {guild.created_at.strftime('%d.%m.%Y')}"

        await ctx.send(view=card.build())

    async def show_userinfo(self, ctx, user: discord.User = None):
        """Показать информацию о пользователе"""
        if user is None:
            user = ctx.author

        guild = ctx.guild
        member = guild.get_member(user.id) if guild else None
        on_guild = bool(member)

        if on_guild and member.joined_at:
            joined_members = sorted(
                [m for m in guild.members if m.joined_at],
                key=lambda m: m.joined_at
            )
            pos = next((i for i, m in enumerate(joined_members, start=1) if m.id == member.id), None)
            total = len(joined_members)
            pos_str = f" (#{pos}/{total})" if pos else ""
        else:
            pos_str = ""

        banner_url = await get_user_banner(self.bot, user.id, guild.id if on_guild else None)

        status_map = {
            discord.Status.online: Emojis.ONLINE,
            discord.Status.idle: Emojis.IDLE,
            discord.Status.dnd: Emojis.DND,
            discord.Status.offline: Emojis.OFFLINE
        }
        status_names = {
            discord.Status.online: "Онлайн",
            discord.Status.idle: "Неактивен",
            discord.Status.dnd: "Не беспокоить",
            discord.Status.offline: "Оффлайн"
        }
        stat = member.status if on_guild else discord.Status.offline
        status_display = f"{status_map.get(stat, '')} {status_names.get(stat, stat.name.capitalize())}"

        flags = user.public_flags
        badge_mapping = {
            'staff': Emojis.DISCORD_STAFF,
            'partner': Emojis.PARTNER_DISCORD,
            'bug_hunter': Emojis.BUG_HUNTER_1,
            'bug_hunter_level_2': Emojis.BUG_HUNTER_2,
            'hypesquad_events': Emojis.HYPESQUAD_EVENTS,
            'hypesquad_bravery': Emojis.HYPESQUAD_BRAVERY,
            'hypesquad_brilliance': Emojis.HYPESQUAD_BRILLIANCE,
            'hypesquad_balance': Emojis.HYPESQUAD_BALANCE,
            'early_supporter': Emojis.EARLY_SUPPORTER,
            'verified_bot_developer': Emojis.VERIFIED_BOT_DEVELOPER
        }
        badges = [emoji for attr, emoji in badge_mapping.items() if getattr(flags, attr, False)]
        if user.bot:
            badges.append(Emojis.BOT_DISCORD)
        badges_str = ' '.join(badges)

        desc_lines = []
        user_line = f"- **Пользователь:** {user.mention}"
        if badges_str:
            user_line += f" • {badges_str}"
        desc_lines.append(user_line)
        desc_lines.append(f"- **На сервере:** {'Да' if on_guild else 'Нет'}{pos_str}")

        img_parts = []
        if user.avatar:
            img_parts.append(f"[Аватарка `👤`]({user.avatar.url})")
        if banner_url:
            img_parts.append(f"[Баннер `🖼️`]({banner_url})")
        if img_parts:
            desc_lines.append(f"- **Изображения:** {' • '.join(img_parts)}")
        desc_lines.append(f"- **Статус:** {status_display}")

        colour = member.color.value if on_guild and member.color.value else 0x5865F2
        card = InfoCard(colour=colour)
        card.thumbnail_url = user.avatar.url if user.avatar else None
        card.header = f"**{user.name}**\n" + "\n".join(desc_lines)

        sections = []

        if on_guild and member.joined_at:
            joined_ts = int(member.joined_at.timestamp())
            sorted_roles = sorted(
                (r for r in member.roles if r.name != "@everyone"),
                key=lambda r: r.position,
                reverse=True
            )
            roles_text = " ".join(r.mention for r in sorted_roles) if sorted_roles else "Нет ролей"
            sections.append(
                f"> {Emojis.ICON_CONFIG} Серверная информация:\n"
                f"**Вступил(а):** <t:{joined_ts}:R>\n"
                f"**Роли:** {roles_text}"
            )

            activities = []
            for act in member.activities:
                if act.type == discord.ActivityType.playing:
                    activities.append(f"🎮 Играет в **{act.name}**")
                elif act.type == discord.ActivityType.streaming:
                    activities.append(f"📺 Стримит **{act.name}**")
                elif act.type == discord.ActivityType.listening and hasattr(act, 'title'):
                    activities.append(f"🎵 Слушает **{act.title}**")
                elif act.type == discord.ActivityType.watching:
                    activities.append(f"👀 Смотрит **{act.name}**")
                else:
                    activities.append(f"- {act.name}")
            if activities:
                sections.append(
                    f"> {Emojis.ICON_STATISTICS} Активности:\n" + "\n".join(activities)
                )

        card.sections = sections
        card.footer = f"-# ID: {user.id} • Создан: {user.created_at.strftime('%d.%m.%Y')}"

        await ctx.send(view=card.build())

    @commands.command(name="info", aliases=["инфо", "information"])
    async def info_prefix(self, ctx: commands.Context):
        info_type, target = self._parse_prefix_arguments(ctx)
        await self._dispatch_info(ctx, info_type, target)

    @app_commands.command(name="about", description="🤖 Показать информацию о боте")
    async def about_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.show_botinfo(ctx)

    @app_commands.command(name="channelinfo", description="📝 Показать информацию о канале")
    async def channelinfo_slash(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel | None = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.show_channelinfo(ctx, channel)

    @app_commands.command(name="roleinfo", description="🎭 Показать информацию о роли")
    async def roleinfo_slash(self, interaction: discord.Interaction, role: discord.Role):
        ctx = await commands.Context.from_interaction(interaction)
        await self.show_roleinfo(ctx, role)

    @app_commands.command(name="userinfo", description="👤 Показать информацию о пользователе")
    async def userinfo_slash(self, interaction: discord.Interaction, user: discord.User | None = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.show_userinfo(ctx, user)

    @commands.command(name="server", aliases=["serverinfo", "сервер"], description="🏰 Показать информацию о сервере")
    async def server_prefix(self, ctx: commands.Context):
        await self.show_serverinfo(ctx)

    @app_commands.command(name="server", description="🏰 Показать информацию о сервере")
    async def server_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.show_serverinfo(ctx)

class RoleMembersView(discord.ui.View):
    """View для кнопки просмотра участников с ролью"""

    def __init__(self, role: discord.Role, members_with_role: list):
        super().__init__(timeout=300)
        self.role = role
        self.members_with_role = members_with_role

    @discord.ui.button(label="Глянуть участников с ролью", style=discord.ButtonStyle.primary, emoji="👥")
    async def show_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Показать список участников с ролью"""
        if not self.members_with_role:
            await interaction.response.send_message(
                f"❌ Нет участников с ролью {self.role.mention}", 
                ephemeral=True
            )
            return

        members_per_page = 20
        total_pages = (len(self.members_with_role) + members_per_page - 1) // members_per_page

        page = 1
        start_idx = (page - 1) * members_per_page
        end_idx = min(start_idx + members_per_page, len(self.members_with_role))

        members_list = []
        for i, member in enumerate(self.members_with_role[start_idx:end_idx], start_idx + 1):
            members_list.append(f"{i}. {member.mention}")

        embed = discord.Embed(
            title=f"Участники с ролью {self.role.name}",
            description="\n".join(members_list),
            color=self.role.color
        )
        embed.set_footer(text=f"Страница {page}/{total_pages} • Всего участников: {len(self.members_with_role)}")

        if total_pages > 1:
            view = MembersPaginationView(
                self.role,
                self.members_with_role,
                page,
                members_per_page=members_per_page
            )
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
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
        members_per_page: int = 20
    ):
        super().__init__(timeout=300)
        self.role = role
        self.members_with_role = members_with_role
        self.current_page = current_page
        self.members_per_page = max(1, members_per_page)
        self.total_pages = (len(members_with_role) + self.members_per_page - 1) // self.members_per_page
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
        for i, member in enumerate(self.members_with_role[start_idx:end_idx], start_idx + 1):
            members_list.append(f"{i}. {member.mention}")

        embed = discord.Embed(
            title=f"Участники с ролью {self.role.name}",
            description="\n".join(members_list),
            color=self.role.color
        )
        embed.set_footer(text=f"Страница {self.current_page}/{self.total_pages} • Всего участников: {len(self.members_with_role)}")
        return embed

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Предыдущая страница"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_buttons()
            embed = self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Вперед", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        method = "GET"
        route = discord.http.Route(method, path)
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

