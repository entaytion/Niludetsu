import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, Embed, Emojis
from Niludetsu.moderation.system.slowmode import SlowmodeSystem

from typing import Optional

class SlowmodeCog(commands.Cog):
    """Команды управления медленным режимом."""

    def __init__(self, bot):
        self.bot = bot
        self.slowmode = SlowmodeSystem(bot)

    @commands.hybrid_command(
        name="slowmode",
        description="Установить медленный режим в канале"
    )
    @app_commands.describe(
        duration="⏰ Длительность (например: 10s, 1m, 1h, 0/off)",
        channel="#️⃣ Канал (по умолчанию — текущий)",
        reason="💬 Причина"
    )
    @moderationcommand(required_level=2, cooldown=60)
    async def slowmode(
        self,
        ctx: commands.Context,
        duration: str,
        channel: Optional[discord.TextChannel] = None,
        *,
        reason: str = "Не указана"
    ):
        """
        Установить медленный режим в канале.
        Максимальная длительность: 6 часов (ограничение Discord).

        Примеры:
        • !slowmode 10s Флуд
        • !slowmode 1m #general Спам
        • !slowmode 0 Отключить
        • !slowmode off Отключить
        • !slowmode 30s --all Массовый флуд
        • /slowmode duration:10s channel:#general reason:Флуд
        """

        is_interaction = getattr(ctx, 'interaction', None) is not None
        apply_to_all = False

        if not is_interaction:
            # Префиксная команда — проверяем флаг --all
            if reason and "--all" in reason:
                apply_to_all = True
                reason = reason.replace("--all", "").strip()
                if not reason:
                    reason = "Не указана"

        # Если канал не указан, используем текущий (только для одного канала)
        if channel is None and not apply_to_all:
            channel = ctx.channel

        # ПРИМЕНЯЕМ КО ВСЕМ КАНАЛАМ (--all)

        if apply_to_all:
            success_channels, failed_channels = await self.slowmode.set_slowmode_all(
                guild=ctx.guild,
                moderator=ctx.author,
                duration=duration,
                reason=reason
            )

            # Создаём итоговый embed
            if success_channels:
                description = (
                    f"{Emojis.SUCCESS} Медленный режим установлен на **{duration}** "
                    f"в **{len(success_channels)}** каналах"
                )
                if failed_channels:
                    description += (
                        f"\n❌ Не удалось установить в **{len(failed_channels)}** каналах "
                        "(нет прав или ошибка)"
                    )
                result_embed = Embed.success(description=description)
            else:
                result_embed = Embed.error(
                    description="Не удалось установить медленный режим ни в одном канале"
                )

            await send(ctx, embed=result_embed, ephemeral=True)

        else:
            embed = await self.slowmode.set_slowmode(
                guild=ctx.guild,
                moderator=ctx.author,
                channel=channel,
                duration=duration,
                reason=reason
            )
            await send(ctx, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlowmodeCog(bot))

