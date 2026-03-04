import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.config import NOTIFICATION_CHANNEL_ID
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu.moderation.exceptions import ModerationError
from Niludetsu.tools.Embed import Embed
from typing import Optional

class ClearCog(commands.Cog):
    """Команда очистки сообщений в канале."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        aliases=["очистить", "purge"],
        description="🛡️ Очистить сообщения в канале"
    )
    @app_commands.describe(
        amount="🔢 Количество сообщений для удаления (1-100)",
        target="👤 Пользователь, чьи сообщения нужно удалить (опционально)"
    )
    @moderationcommand(required_level=2, cooldown=60)
    async def clear(
        self,
        ctx: commands.Context,
        amount: str,
        target: Optional[discord.Member] = None
    ):
        """
        Очистить сообщения в канале.

        Примеры:
        • !clear 10 - удалить 10 последних сообщений
        • !clear 50 @user - удалить 50 сообщений конкретного пользователя
        • !clear 20 (в ответе на сообщение) - удалить 20 сообщений этого пользователя
        • /clear amount:10 target:@user

        Параметры:
        • amount - Количество сообщений (1-100)
        • target - Пользователь (опционально)
        """
        is_interaction = ctx.interaction is not None

        if not target and not is_interaction:
            # Проверяем, есть ли reply на сообщение
            if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
                target = ctx.message.reference.resolved.author

        if not amount.isdigit():
            raise ModerationError(
                "Укажите корректное количество сообщений (например, `10`, `50`, `100`)!"
            )

        num = int(amount)

        if num < 1:
            raise ModerationError("Количество сообщений должно быть положительным числом!")

        if num > 100:
            raise ModerationError(
                "Количество сообщений не должно превышать **100**!\n"
                "(Ограничение Discord API)"
            )

        bot_permissions = ctx.channel.permissions_for(ctx.guild.me)

        if not bot_permissions.manage_messages:
            raise ModerationError(
                f"У меня нет прав на **управление сообщениями** в канале {ctx.channel.mention}!"
            )

        if not bot_permissions.read_message_history:
            raise ModerationError(
                f"У меня нет прав на **чтение истории сообщений** в канале {ctx.channel.mention}!"
            )

        if is_interaction:
            # Для slash команды - defer с ephemeral
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            # Для префиксной команды - удаляем команду
            try:
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        messages_to_delete = []

        # Если указан target, просматриваем больше сообщений (до 500)
        history_limit = num if not target else min(500, num * 10)

        try:
            async for msg in ctx.channel.history(limit=history_limit):
                # Если указан target, фильтруем по автору
                if target and msg.author != target:
                    continue

                messages_to_delete.append(msg)

                # Останавливаемся, когда набрали нужное количество
                if len(messages_to_delete) >= num:
                    break

        except discord.Forbidden:
            raise ModerationError("У меня нет прав на чтение истории сообщений!")
        except discord.HTTPException as e:
            raise ModerationError(f"Ошибка при получении сообщений: {str(e)}")

        if not messages_to_delete:
            raise ModerationError(
                f"Не найдено сообщений для удаления"
                f"{f' от пользователя {target.mention}' if target else ''}!"
            )

        try:
            # Используем bulk delete для массового удаления (быстрее)
            await ctx.channel.delete_messages(messages_to_delete)
            deleted_count = len(messages_to_delete)

        except discord.Forbidden:
            raise ModerationError("У меня нет прав на удаление сообщений!")
        except discord.HTTPException as e:
            # Если bulk delete не сработал, пробуем удалить по одному
            deleted_count = 0
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                    deleted_count += 1
                except:
                    pass

        description = f"{Emoji.SUCCESS} Успешно удалено **{deleted_count}** сообщений"
        if target:
            description += f" пользователя {target.mention}"
        description += "!"

        result_embed = Embed.success(description=description)

        # Устанавливаем аватар цели или модератора
        thumb_url = (target or ctx.author).display_avatar.url
        result_embed.set_thumbnail(url=thumb_url)

        if is_interaction:
            await ctx.interaction.followup.send(embed=result_embed, ephemeral=True)
        else:
            # Для префиксной команды отправляем в канал и удаляем через 5 секунд
            result_msg = await ctx.send(embed=result_embed)
            await result_msg.delete(delay=5.0)

        await self._log_clear_action(
            guild=ctx.guild,
            moderator=ctx.author,
            channel=ctx.channel,
            deleted_count=deleted_count,
            target=target
        )

    async def _log_clear_action(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        channel: discord.TextChannel,
        deleted_count: int,
        target: Optional[discord.Member] = None
    ) -> None:
        """
        Логирует очистку сообщений в канал модерации.

        Parameters
        ----------
        guild : discord.Guild
            Сервер
        moderator : discord.Member
            Модератор
        channel : discord.TextChannel
            Канал, где были удалены сообщения
        deleted_count : int
            Количество удалённых сообщений
        target : Optional[discord.Member]
            Пользователь, чьи сообщения удалены (если указан)
        """
        embed = Embed(
            title="🗑️ Очистка сообщений",
            description=(
                f"**Канал:** {channel.mention}\n"
                f"**Модератор:** {moderator.mention} ({moderator.id})\n"
                f"**Удалено сообщений:** {deleted_count}"
            ),
            color=0xffa500
        )

        if target:
            embed.description += f"**Цель:** {target.mention} ({target.id})"

        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )

        # Ищем канал для логов
        log_channel = None

        if NOTIFICATION_CHANNEL_ID:
            log_channel = guild.get_channel(int(NOTIFICATION_CHANNEL_ID))

        if not log_channel:
            log_channel = discord.utils.get(
                guild.text_channels,
                name__in=["mod-logs", "модерация", "logs"]
            )

        if log_channel:
            try:
                await log_channel.send(embed=log_channel)
            except (discord.Forbidden, discord.HTTPException):
                pass

async def setup(bot):
    """Загрузка расширения."""
    await bot.add_cog(ClearCog(bot))

