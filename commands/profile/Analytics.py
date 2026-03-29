import discord
from discord.ext import commands

from Niludetsu import Embed, Emojis, TimeService, config
from Niludetsu.achievements.manager import AchievementsManager
from Niludetsu.analytics.manager import AnalyticsManager
from Niludetsu.analytics.tracker import AnalyticsTracker

_time = TimeService()


class Analytics(commands.Cog):
    """Команды и слушатели аналитики."""

    MESSAGE_ACHIEVEMENTS = (
        "first_message",
        "ten_messages",
        "fifty_messages",
        "hundred_messages",
        "thousand_messages",
        "ten_thousand_messages",
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        main_guild_id = getattr(config, "SERVERS", {}).get("MAIN_ID")

        self.manager = AnalyticsManager()
        self.tracker = AnalyticsTracker(bot, main_guild_id=main_guild_id)

        from Niludetsu.levels.tracker import LevelTracker

        self.level_tracker = LevelTracker(main_guild_id=main_guild_id)
        self.achievements_manager = AchievementsManager()

    def cog_unload(self) -> None:
        """Очистка ресурсов при выгрузке кога"""
        self.tracker.cog_unload()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Отслеживает сообщения для аналитики и начисления опыта"""
        if not message.guild or message.author.bot:
            return

        # Игнорируем команды
        prefixes = await self.bot.command_prefix(self.bot, message)
        if any(message.content.startswith(prefix) for prefix in prefixes):
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        automod_listener = self.bot.get_cog("AutoModListener")

        has_violation = False
        if automod_listener:
            has_violation = await automod_listener.check_message_violations(message)

        await self.tracker.track_message(guild_id, user_id, channel_id)

        if not has_violation:
            # Начисляем опыт (уровни)
            await self.level_tracker.track_message_xp(
                guild_id, user_id, message.channel
            )

            # Проверяем достижения за сообщения
            await self._check_message_achievements(guild_id, user_id, message.channel)

    async def _check_message_achievements(
        self, guild_id: str, user_id: str, channel: discord.abc.Messageable
    ):
        """Проверяет и выдаёт достижения за количество сообщений (только чистых, без нарушений)"""
        stats = await self.manager.get_user_stats(guild_id, user_id)
        unlocked = await self.achievements_manager.evaluate_requirements(
            guild_id,
            user_id,
            channel=channel,
            stats=stats,
            achievement_ids=self.MESSAGE_ACHIEVEMENTS,
        )

        if unlocked:
            clean_messages = stats["messages"]["total"] - stats["messages"]["deleted"]
            print(
                f"🎯 [Achievements] user={user_id}, clean_messages={clean_messages}, unlocked={','.join(unlocked)}"
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Отслеживает удалённые сообщения"""
        if not message.guild or message.author.bot:
            return

        await self.tracker.track_message_delete(
            str(message.guild.id),
            str(message.author.id),
            str(message.channel.id),
        )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Отслеживает активность в голосовых каналах"""
        if member.bot or not member.guild:
            return

        guild_id = str(member.guild.id)
        user_id = str(member.id)

        if before.channel and after.channel and before.channel.id != after.channel.id:
            # Выходим из старого
            await self._handle_voice_leave(member, before.channel, guild_id, user_id)
            # Входим в новый
            await self.tracker.track_voice_join(member, after.channel)
            return

        if after.channel and not before.channel:
            await self.tracker.track_voice_join(member, after.channel)
            return

        if before.channel and not after.channel:
            await self._handle_voice_leave(member, before.channel, guild_id, user_id)
            return

    async def _handle_voice_leave(
        self,
        member: discord.Member,
        channel: discord.VoiceChannel,
        guild_id: str,
        user_id: str,
    ):
        """Обрабатывает выход из голосового канала с начислением опыта"""
        # Считаем время в канале
        stats = await self.manager.get_user_stats(guild_id, user_id)
        last_join = stats.get("voice", {}).get("last_join")

        if last_join:
            now = _time.now()
            joined_at = _time.ensure_datetime(last_join)
            minutes = int((now - joined_at).total_seconds() // 60)

            # Начисляем опыт за голос
            if minutes > 0:
                await self.level_tracker.track_voice_xp(
                    guild_id, user_id, minutes, channel
                )

        # Обновляем аналитику
        await self.tracker.track_voice_leave(member)

    @commands.hybrid_command(
        name="analytics", description="📊 Показать статистику пользователя"
    )
    @discord.app_commands.describe(user="👤 Кого показать статистику")
    async def analytics(
        self, ctx: commands.Context, user: discord.User | None = None
    ) -> None:
        """Показывает статистику активности пользователя"""
        target = user or ctx.author
        guild = ctx.guild

        if not guild:
            await ctx.reply(
                f"{Emojis.ERROR} Команда доступна только на сервере.",
                mention_author=False,
            )
            return

        # Получаем статистику
        stats = await self.manager.get_user_stats(str(guild.id), str(target.id))

        if not stats["messages"]["total"] and not stats["voice"]["total_seconds"]:
            await ctx.reply(
                embed=Embed.error(description="Пока данных по этому пользователю нет."),
                mention_author=False,
            )
            return

        # Получаем топ пользователей
        top = await self.manager.get_top_users(str(guild.id))
        messages_rank = self._find_rank(top["messages"], str(target.id))
        voice_rank = self._find_rank(top["voice"], str(target.id))
        voice_total = stats["voice"]["total_seconds"]

        # Получаем информацию о пользователе
        member = guild.get_member(target.id)
        display_name = member.display_name if member else target.name
        avatar_url = member.display_avatar.url if member else target.display_avatar.url

        # Создаём embed
        embed = Embed(
            title=f"{Emojis.ANALYTICS} Аналитика — {display_name}",
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(
            name="> 🏆 Позиции в рейтинге",
            value=(f"**Текст:** {messages_rank}\n**Голос:** {voice_rank}"),
            inline=True,
        )

        embed.add_field(
            name="> 📊 Общая статистика",
            value=(
                f"**Сообщений:** `{stats['messages']['total']:,}`\n"
                f"**Удалено:** `{stats['messages']['deleted']:,}`\n"
                f"**Голосовая активность:** {_time.format_duration(voice_total)}"
            ),
            inline=True,
        )

        embed.add_field(
            name="> 💬 Любимые текстовые каналы",
            value=self._format_text_channels(guild, stats["messages"]["channels"]),
            inline=False,
        )

        embed.add_field(
            name="> 🎙️ Любимые голосовые каналы",
            value=self._format_voice_channels(guild, stats["voice"]["channels"]),
            inline=True,
        )

        embed.set_footer(text="Серверная аналитика • данные обновляются автоматически")

        await ctx.reply(embed=embed, mention_author=False)

    @staticmethod
    def _find_rank(entries, user_id: str) -> str:
        """Находит место пользователя в рейтинге"""
        for index, (candidate_id, _) in enumerate(entries, start=1):
            if candidate_id == user_id:
                if index == 1:
                    return "🥇 **1-е место**"
                if index == 2:
                    return "🥈 **2-е место**"
                if index == 3:
                    return "🥉 **3-е место**"
                return f"`#{index}`"
        return "—"

    @staticmethod
    def _format_text_channels(guild: discord.Guild, channels: dict[str, int]) -> str:
        """Форматирует топ текстовых каналов"""
        items = sorted(channels.items(), key=lambda item: item[1], reverse=True)[:5]
        lines = []
        medals = ("🥇", "🥈", "🥉")

        for index, (channel_id, count) in enumerate(items, start=1):
            if channel_id.startswith("temp_"):
                continue

            channel = guild.get_channel(int(channel_id))
            if channel:
                prefix = medals[index - 1] if index <= 3 else f"`#{index}`"
                lines.append(f"{prefix} {channel.mention} — **{count:,}**")

        return "\n".join(lines) if lines else "> Пока нет данных"

    @staticmethod
    def _format_voice_channels(guild: discord.Guild, channels: dict[str, int]) -> str:
        """Форматирует топ голосовых каналов"""
        items = sorted(channels.items(), key=lambda item: item[1], reverse=True)[:5]
        lines = []
        temp_total = 0
        medals = ("🥇", "🥈", "🥉")

        for index, (channel_id, seconds) in enumerate(items, start=1):
            if channel_id.startswith("temp_"):
                temp_total += seconds
                continue

            channel = guild.get_channel(int(channel_id))
            if channel:
                prefix = medals[index - 1] if index <= 3 else f"`#{index}`"
                lines.append(
                    f"{prefix} {channel.mention} — {_time.format_duration(seconds)}"
                )

        if temp_total:
            lines.append(f"🪄 Временные каналы — {_time.format_duration(temp_total)}")

        return "\n".join(lines) if lines else "> Пока нет данных"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Analytics(bot))
