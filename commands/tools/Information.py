import platform
import re
import time

import discord
import psutil
from discord.ext import commands
from discord.utils import snowflake_time

from Niludetsu import Colors, Emojis, safe_fetch_user
from Niludetsu.locale import _, DEFAULT_LOCALE

OWNER_ONLY_INFO_ID = 636570363605680139
I = DEFAULT_LOCALE.get("info", {})


class InfoCommands(commands.Cog):
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
        if self._invite_url_pattern.search(target) or self._invite_code_pattern.fullmatch(target):
            try:
                invite = await self.bot.fetch_invite(target)
                return "invite", invite
            except:
                pass

        target_id = None
        id_match = re.search(r"(\d{17,20})", target)
        if id_match:
            target_id = int(id_match.group(1))

        if target_id:
            user = await safe_fetch_user(self.bot, target_id)
            if user:
                return "user", user
            
            if ctx.guild:
                role = ctx.guild.get_role(target_id)
                if role: return "role", role
                chan = ctx.guild.get_channel(target_id)
                if chan: return "channel", chan

        if re.match(r"^<a?:\w+:\d+>$", target):
            return "emoji", target

        if ctx.guild:
            member = ctx.guild.get_member_named(target)
            if member: return "user", member
            
            role = discord.utils.get(ctx.guild.roles, name=target)
            if role: return "role", role
            
            chan = discord.utils.get(ctx.guild.channels, name=target)
            if chan: return "channel", chan

        return None, None

    async def _dispatch_info(self, ctx: commands.Context, target: str | None) -> None:
        t = _(ctx=ctx)
        if not self._is_owner_info_allowed(ctx):
            return

        if not target:
            await ctx.send(f"{Emojis.ERROR} {t('info', 'info_cmd_no_target')}")
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
            await ctx.send(f"{Emojis.ERROR} {t('info', 'info_cmd_not_found')}")

    async def show_channelinfo(self, ctx, channel=None):
        t = _(ctx=ctx)
        if channel is None:
            channel = ctx.channel

        created_ts = int(channel.created_at.timestamp())
        category = channel.category.name if channel.category else t("info", "channel_none")
        position = channel.position

        if isinstance(channel, discord.TextChannel):
            channel_type_str = t("info", "channel_type_news" if channel.is_news() else "channel_type_text")
        elif isinstance(channel, discord.VoiceChannel):
            channel_type_str = t("info", "channel_type_voice")
        elif isinstance(channel, discord.CategoryChannel):
            channel_type_str = t("info", "channel_type_category")
        elif isinstance(channel, discord.StageChannel):
            channel_type_str = t("info", "channel_type_stage")
        elif hasattr(discord, "ForumChannel") and isinstance(channel, discord.ForumChannel):
            channel_type_str = t("info", "channel_type_forum")
        else:
            channel_type_str = t("info", "channel_type_unknown")

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} {t('info', 'channel_info_title', name=channel.name)}",
            description=t("info", "channel_info_desc", mention=channel.mention, id=channel.id),
            color=0x000001,
        )

        fields = [
            (
                f"> {Emojis.INFORMATION} {t('info', 'channel_info_main')}",
                f"{t('info', 'channel_info_type', type=channel_type_str)}\n"
                f"{t('info', 'channel_info_category', category=category)}\n"
                f"{t('info', 'channel_info_created', timestamp=created_ts)}\n"
                f"{t('info', 'channel_info_position', position=position)}",
            ),
        ]

        if isinstance(channel, discord.TextChannel):
            topic = channel.topic or t("info", "channel_none")
            slowmode = t("info", "channel_slowmode", delay=channel.slowmode_delay)
            nsfw = t("info", "channel_yes" if channel.nsfw else "channel_no")
            fields.append(
                (
                    f"> {Emojis.INFORMATION} {t('info', 'channel_info_text_settings')}",
                    f"{t('info', 'channel_info_topic', topic=topic)}\n"
                    f"{t('info', 'channel_info_slowmode', slowmode=slowmode)}\n"
                    f"{t('info', 'channel_info_nsfw', nsfw=nsfw)}",
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
            if first_msg: parts.append(t("info", "channel_info_first_msg", url=first_msg.jump_url))
            if last_msg:
                ts = int(last_msg.created_at.timestamp())
                parts.append(t("info", "channel_info_last_msg", author=last_msg.author.mention, timestamp=ts))
            if parts: fields.append((f"> {Emojis.CHAT} {t('info', 'channel_info_messages')}", "\n".join(parts)))

        elif isinstance(channel, discord.VoiceChannel):
            bitrate = channel.bitrate // 1000
            user_limit = t("info", "channel_info_no_limit") if channel.user_limit <= 0 else f"`{channel.user_limit}`"
            fields.append(
                (
                    f"> {Emojis.INFORMATION} {t('info', 'channel_info_voice_settings')}",
                    f"{t('info', 'channel_info_bitrate', bitrate=bitrate)}\n"
                    f"{t('info', 'channel_info_user_limit', limit=user_limit)}\n"
                    f"{t('info', 'channel_info_in_channel', count=len(channel.members))}",
                )
            )

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    async def show_emojiinfo(self, ctx, emoji: str):
        t = _(ctx=ctx)
        match = re.match(r"^<(?P<anim>a?):(?P<name>[\w]+):(?P<id>\d+)>$", emoji)
        if not match: return

        anim_flag = bool(match.group("anim"))
        name, emoji_id = match.group("name"), match.group("id")
        fmt = "gif" if anim_flag else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{fmt}?size=1024"
        created = snowflake_time(int(emoji_id))

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} {t('info', 'emoji_info_title', name=name)}",
            description=t("info", "emoji_info_desc", emoji=emoji, id=emoji_id),
            color=0x000001,
        )
        embed.set_thumbnail(url=url)
        embed.add_field(
            name=f"> {Emojis.INFORMATION} {t('info', 'emoji_info_details')}",
            value=f"{t('info', 'emoji_info_name', name=name)}\n{t('info', 'emoji_info_animated', animated=t('info', 'emoji_yes' if anim_flag else 'emoji_no'))}\n{t('info', 'emoji_info_link', url=url)}",
            inline=False,
        )
        embed.set_footer(text=t("info", "emoji_footer", id=emoji_id, date=created.strftime('%d.%m.%Y')))
        await ctx.send(embed=embed)

    async def show_roleinfo(self, ctx, role: discord.Role):
        t = _(ctx=ctx)
        guild = ctx.guild
        created_at = int(role.created_at.timestamp())
        color = str(role.color) if role.color.value else t("info", "role_info_no_color")
        members_with_role = [member for member in guild.members if role in member.roles]
        permissions = [n.replace("_", " ").capitalize() for n, v in role.permissions if v]

        embed = discord.Embed(
            title=t("info", "role_info_title"),
            description=t("info", "role_info_desc", mention=role.mention, name=role.name, id=role.id),
            color=role.color,
        )
        embed.add_field(
            name=f"> <:aeInfoStatus:1375565493439692921> {t('info', 'role_info_chars')}",
            value=f"{t('info', 'role_info_color', color=color)}\n{t('info', 'role_info_position', pos=role.position, total=len(guild.roles))}\n{t('info', 'role_info_created', timestamp=created_at)}\n",
            inline=True,
        )
        embed.add_field(
            name=f"> <:aeInfoStatus:1375565493439692921> {t('info', 'role_info_about')}",
            value=f"{t('info', 'role_info_hoist', value=t('info', 'role_hoist_yes' if role.hoist else 'role_no_hoist'))}\n{t('info', 'role_info_bot', value=t('info', 'role_bot_yes' if role.is_bot_managed() else 'role_bot_no'))}\n{t('info', 'role_info_members', count=len(members_with_role))}\n",
            inline=True,
        )
        if permissions:
            embed.add_field(name=f"> <:aeInfoStatus:1375565493439692921> {t('info', 'role_info_rights')}", value=", ".join(permissions[:20]) + (t("info", "role_info_rights_more") if len(permissions) > 20 else ""), inline=False)

        if role.icon: embed.set_thumbnail(url=role.icon.url)
        await ctx.send(embed=embed, view=RoleMembersView(role, members_with_role))

    async def show_combined_info(self, ctx, invite):
        t = _(ctx=ctx)
        embed = self.build_serverinfo_from_invite_embed(invite, t)
        if embed: await ctx.send(embed=embed)
        else: await ctx.send(f"{Emojis.ERROR} {t('info', 'info_cmd_server_error')}")

    def build_serverinfo_from_invite_embed(self, invite, t=None) -> discord.Embed | None:
        if t is None: t = lambda *a, **kw: DEFAULT_LOCALE.get(a[0], {}).get(a[1], "")
        guild = invite.guild
        if guild is None: return None

        icon_url = guild.icon.url if guild.icon else None
        banner_url = guild.banner.url if guild.banner else None
        
        owner_id = getattr(guild, 'owner_id', '???')
        desc_lines = [t("info", "server_info_owner", owner_id=owner_id)]
        img_parts = []
        if icon_url: img_parts.append(t("info", "server_info_avatar_link", url=icon_url))
        if banner_url: img_parts.append(t("info", "server_info_banner_link", url=banner_url))
        if img_parts: desc_lines.append(t("info", "server_info_images", images=" • ".join(img_parts)))
        desc_lines.append(t("info", "server_info_desc_label", desc=getattr(guild, 'description', None) or t("info", "server_info_no_desc")))

        member_count = invite.approximate_member_count or 0
        online_count = invite.approximate_presence_count or 0

        guild_name = getattr(guild, 'name', t("info", "server_info_unknown"))
        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} {t('info', 'server_info_title')}",
            description=f"**{guild_name}**\n" + "\n".join(desc_lines),
            color=Colors.INFO,
        )
        if icon_url: embed.set_thumbnail(url=icon_url)

        embed.add_field(
            name=f"> <:aeInfoPerms:1375568887449518342> {t('info', 'server_info_members', count=member_count)}",
            value=f"{t('info', 'server_info_online', online=online_count)}\n{t('info', 'server_info_offline', offline=max(member_count - online_count, 0))}\n{t('info', 'server_info_total', total=member_count)}",
            inline=False,
        )
        embed.add_field(
            name=f"> {Emojis.NAME} {t('info', 'server_info_invite')}",
            value=f"{t('info', 'server_info_invite_channel', channel_id=invite.channel.id if invite.channel else '???')}\n{t('info', 'server_info_invite_code', code=invite.code)}\n{t('info', 'server_info_invite_link', url=f'https://discord.gg/{invite.code}')}",
            inline=False,
        )
        created = getattr(guild, 'created_at', None)
        footer_text = t("info", "server_info_footer", id=getattr(guild, 'id', '???'), date=created.strftime('%d.%m.%Y') if created else t("info", "server_info_unknown"))
        embed.set_footer(text=footer_text)
        return embed


    async def build_userinfo_embed(self, ctx, user=None) -> discord.Embed:
        t = _(ctx=ctx)
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
            pos_str = t("info", "user_info_pos", pos=pos, total=total) if pos else ""
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
            discord.Status.online: t("info", "status_online"),
            discord.Status.idle: t("info", "status_idle"),
            discord.Status.dnd: t("info", "status_dnd"),
            discord.Status.offline: t("info", "status_offline"),
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
        badges_str = " ".join(badges) if badges else t("info", "user_info_no_badges")

        img_parts = []
        user_avatar = getattr(user, "avatar", None)
        if user_avatar:
            img_parts.append(t("info", "user_info_avatar_link", url=user_avatar.url))
        if banner_url:
            img_parts.append(t("info", "user_info_banner_link", url=banner_url))
        images_text = " • ".join(img_parts) if img_parts else t("info", "user_info_no_images")

        colour = member.color.value if on_guild and member.color.value else 0x5865F2
        user_mention = getattr(user, "mention", t("info", "user_info_unknown_mention"))
        display_avatar = getattr(user, "display_avatar", None)

        embed = discord.Embed(
            title=f"{Emojis.UNKNOWN} {t('info', 'user_info_title')}",
            description=(
                f"{t('info', 'user_info_desc_user', mention=user_mention)}\n"
                f"{t('info', 'user_info_desc_status', status=status_display)}\n"
                f"{t('info', 'user_info_desc_guild', on_guild=t('info', 'user_info_yes' if on_guild else 'user_info_no'), pos=pos_str)}\n"
                f"{t('info', 'user_info_desc_badges', badges=badges_str)}\n"
                f"{t('info', 'user_info_desc_images', images=images_text)}"
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

        user_name = getattr(user, "name", t("info", "user_info_unknown"))
        user_created_at = getattr(user, "created_at", None)
        user_created_text = (
            f"<t:{int(user_created_at.timestamp())}:F>"
            if user_created_at
            else t("info", "user_info_unknown")
        )

        embed.add_field(
            name=f"> {t('info', 'user_info_thumbnail')}",
            value=(
                f"{t('info', 'user_info_name', name=user_name)}\n"
                f"{t('info', 'user_info_id', id=user_id)}\n"
                f"{t('info', 'user_info_created', date=user_created_text)}"
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
                else t("info", "user_info_no_roles")
            )
            embed.add_field(
                name=f"> {Emojis.ICON_CONFIG} {t('info', 'user_info_guild_info')}",
                value=(f"{t('info', 'user_info_joined', timestamp=joined_ts)}\n{t('info', 'user_info_roles', roles=roles_text)}"),
                inline=False,
            )

            activities = []
            for act in member.activities:
                if act.type == discord.ActivityType.playing:
                    activities.append(t("info", "user_info_playing", name=act.name))
                elif act.type == discord.ActivityType.streaming:
                    activities.append(t("info", "user_info_streaming", name=act.name))
                elif act.type == discord.ActivityType.listening and hasattr(act, "title"):
                    activities.append(t("info", "user_info_listening", name=act.title))
                elif act.type == discord.ActivityType.watching:
                    activities.append(t("info", "user_info_watching", name=act.name))
                else:
                    activities.append(t("info", "user_info_activity_other", name=act.name))

            if activities:
                embed.add_field(
                    name=f"> {Emojis.ICON_STATISTICS} {t('info', 'user_info_activities')}",
                    value="\n".join(activities),
                    inline=False,
                )

        user_created_footer = (
            user_created_at.strftime("%d.%m.%Y") if user_created_at else t("info", "user_info_unknown")
        )
        embed.set_footer(text=t("info", "user_info_footer", id=user_id, date=user_created_footer))
        return embed

    async def show_userinfo(self, ctx, user=None):
        await ctx.send(embed=await self.build_userinfo_embed(ctx, user))

    @commands.hybrid_command(name="user", aliases=["userinfo", "uinfo"], description="Показать информацию о пользователе")
    async def user_hybrid(self, ctx: commands.Context, *, target: discord.User = None):
        await self.show_userinfo(ctx, target or ctx.author)

    @commands.hybrid_command(name="server", aliases=["serverinfo", "sinfo"], description="Показать информацию о текущем сервере")
    async def server_hybrid(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            await ctx.reply("Команда доступна только на сервере!", ephemeral=True)
            return

        owner = guild.owner or await safe_fetch_user(self.bot, guild.owner_id)
        owner_text = f"{owner.mention} (`{owner.id}`)" if owner else f"`{guild.owner_id}`"

        total_members = guild.member_count or len(guild.members)
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        created_ts = int(guild.created_at.timestamp())
        boost_tier = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0

        embed = discord.Embed(
            title=f"{Emojis.INFORMATION} Информация о сервере",
            description=f"**{guild.name}**\nID: `{guild.id}`\nСоздан: <t:{created_ts}:D> (<t:{created_ts}:R>)",
            color=Colors.INFO,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(
            name="> Владелец",
            value=owner_text,
            inline=True,
        )
        embed.add_field(
            name="> Бусты",
            value=f"Уровень {boost_tier} ({boost_count} бустов)",
            inline=True,
        )
        embed.add_field(
            name="> Участники",
            value=f"Всего: **{total_members}** (Людей: {humans}, Ботов: {bots})",
            inline=False,
        )
        embed.add_field(
            name="> Каналы",
            value=f"Текстовых: **{text_channels}** | Голосовых: **{voice_channels}** | Категорий: **{categories}**",
            inline=False,
        )
        embed.add_field(
            name="> Дополнительно",
            value=f"Ролей: **{len(guild.roles)}** | Эмодзи: **{len(guild.emojis)}** | Стикеров: **{len(guild.stickers)}**",
            inline=False,
        )
        embed.set_footer(text=f"Запросил {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(name="info", aliases=["инфо", "information"], description="Главная команда для получения инфы о чем угодно")
    async def info_prefix(self, ctx: commands.Context, *, target: str = None):
        await self._dispatch_info(ctx, target)


class RoleMembersView(discord.ui.View):
    def __init__(self, role: discord.Role, members_with_role: list):
        super().__init__(timeout=300)
        self.role = role
        self.members_with_role = members_with_role

    @discord.ui.button(
        label=I.get("role_members_view_label", "Глянуть участников с ролью"),
        style=discord.ButtonStyle.primary,
        emoji="👥",
    )
    async def show_members(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not self.members_with_role:
            msg = I.get("role_members_no_members", "❌ Нет участников с ролью {role_mention}").format(role_mention=self.role.mention)
            await interaction.response.send_message(msg, ephemeral=True)
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
            title=I.get("role_members_embed_title", "Участники с ролью {name}").format(name=self.role.name),
            description="\n".join(members_list),
            color=self.role.color,
        )
        embed.set_footer(
            text=I.get("role_members_footer", "Страница {page}/{total} • Всего участников: {count}").format(page=page, total=total_pages, count=len(self.members_with_role))
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
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= self.total_pages

    def get_page_embed(self):
        start_idx = (self.current_page - 1) * self.members_per_page
        end_idx = min(start_idx + self.members_per_page, len(self.members_with_role))

        members_list = []
        for i, member in enumerate(
            self.members_with_role[start_idx:end_idx], start_idx + 1
        ):
            members_list.append(f"{i}. {member.mention}")

        embed = discord.Embed(
            title=I.get("role_members_embed_title", "Участники с ролью {name}").format(name=self.role.name),
            description="\n".join(members_list),
            color=self.role.color,
        )
        embed.set_footer(
            text=I.get("role_members_footer", "Страница {page}/{total} • Всего участников: {count}").format(page=self.current_page, total=self.total_pages, count=len(self.members_with_role))
        )
        return embed

    @discord.ui.button(label=I.get("role_members_pagination_back", "◀️ Назад"), style=discord.ButtonStyle.secondary)
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_buttons()
            embed = self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label=I.get("role_members_pagination_next", "▶️ Вперед"), style=discord.ButtonStyle.secondary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_buttons()
            embed = self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)


async def get_user_banner(bot, user_id, guild_id=None):
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
        print(f"Banner error: {e}")
        return None


async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
