import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send
from Niludetsu.moderation.system.lock import LockSystem as NiludetsuLockSystem
from Niludetsu.tools.Embed import Embed

class LockSystem(commands.Cog):
    """Команды управления блокировкой каналов."""

    def __init__(self, bot):
        self.bot = bot
        self.lock_system = NiludetsuLockSystem(bot)
        # Хранилище ID сообщений-уведомлений: {guild_id: [(channel_id, message_id), ...]}
        self.locked_messages = {}

    @commands.hybrid_command(
        name="lock",
        description="🛡️ Закрыть канал(ы) для отправки сообщений"
    )
    @app_commands.describe(
        channel="#️⃣ Канал для блокировки (по умолчанию — текущий)",
        reason="💬 Причина блокировки"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def lock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        *,
        reason: str = None
    ):
        """
        Закрыть канал(ы) для отправки сообщений.

        Примеры:
        • !lock Рейд
        • !lock #general Технические работы
        • !lock --all Экстренная ситуация
        • /lock channel:#general reason:Рейд
        """

        is_interaction = getattr(ctx, 'interaction', None) is not None
        lock_all = False

        if is_interaction:
            # Slash команда
            if reason is None:
                reason = "Не указана"
            if channel is None:
                channel = ctx.channel
        else:
            # Префиксная команда
            # Парсим аргументы из текста команды
            content = ctx.message.content.partition(' ')[2].strip()

            # Проверяем флаг --all
            if '--all' in content:
                lock_all = True
                content = content.replace('--all', '').strip()

            # Если канал не указан, используем текущий
            if channel is None and not lock_all:
                channel = ctx.channel

            # Остаток текста — причина
            if reason is None:
                reason = content if content else "Не указана"

        lock_ids = await self.lock_system.lock_channel(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=channel,
            reason=reason,
            for_all=lock_all
        )

        # Сохраняем ID сообщений-уведомлений
        if lock_ids:
            self.locked_messages.setdefault(ctx.guild.id, []).extend(lock_ids)

        # Отправляем подтверждение
        channels_count = len(lock_ids)
        if lock_all:
            description = f"{Emoji.SUCCESS} Заблокировано **{channels_count}** каналов"
        else:
            description = f"{Emoji.SUCCESS} Канал {channel.mention} заблокирован"

        embed = Embed.success(description=description)
        await send(ctx, embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="unlock",
        description="🛡️ Открыть канал(ы) для отправки сообщений"
    )
    @app_commands.describe(
        channel="#️⃣ Канал для разблокировки (по умолчанию — текущий)",
        reason="💬 Причина разблокировки"
    )
    @moderationcommand(required_level=3, cooldown=1800)
    async def unlock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None,
        *,
        reason: str = None
    ):
        """
        Открыть канал(ы) для отправки сообщений.

        Примеры:
        • !unlock Рейд окончен
        • !unlock #general Технические работы завершены
        • !unlock --all Ситуация решена
        • /unlock channel:#general reason:Рейд окончен
        """

        is_interaction = getattr(ctx, 'interaction', None) is not None
        unlock_all = False

        if is_interaction:
            # Slash команда
            if reason is None:
                reason = "Не указана"
            if channel is None:
                channel = ctx.channel
        else:
            # Префиксная команда
            content = ctx.message.content.partition(' ')[2].strip()

            # Проверяем флаг --all
            if '--all' in content:
                unlock_all = True
                content = content.replace('--all', '').strip()

            # Если канал не указан, используем текущий
            if channel is None and not unlock_all:
                channel = ctx.channel

            # Остаток текста — причина
            if reason is None:
                reason = content if content else "Не указана"

        # Получаем ID сообщений-уведомлений для удаления
        lock_ids = self.locked_messages.get(ctx.guild.id, [])

        await self.lock_system.unlock_channel(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=channel,
            reason=reason,
            for_all=unlock_all,
            lock_message_ids=lock_ids
        )

        # Очищаем хранилище сообщений
        self.locked_messages[ctx.guild.id] = []

        # Отправляем подтверждение
        if unlock_all:
            description = "✅ Все каналы разблокированы"
        else:
            description = f"{Emoji.SUCCESS} Канал {channel.mention} разблокирован"

        embed = Embed.success(description=description)
        await send(ctx, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LockSystem(bot))

