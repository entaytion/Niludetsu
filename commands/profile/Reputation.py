import discord
from datetime import timedelta
from discord.ext import commands
from Niludetsu import Embed, Time
from Niludetsu.database.supabase_database import database
from Niludetsu.levels.manager import LevelManager

THUMBS_UP = {"👍", "👍🏻", "👍🏼", "👍🏽", "👍🏾", "👍🏿"}
THUMBS_DOWN = {"👎", "👎🏻", "👎🏼", "👎🏽", "👎🏾", "👎🏿"}
COOLDOWN = timedelta(hours=12)
_time = Time()

class Reputation(commands.Cog):
    """Позволяет менять репутацию через ответ с 👍 или 👎."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = database
        self.levels = LevelManager()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.reference or not message.guild:
            return

        content = message.content.strip()
        if content not in THUMBS_UP and content not in THUMBS_DOWN:
            return

        # Вытаскиваем исходное сообщение, чтобы знать, кого “плюсуем/минусуем”
        target_message = message.reference.resolved
        if not isinstance(target_message, discord.Message):
            try:
                target_message = await message.channel.fetch_message(message.reference.message_id)
            except Exception:
                return

        target_user = target_message.author
        actor = message.author
        guild = message.guild

        if target_user.bot or target_user.id == actor.id:
            await message.reply(
                Embed.error(
                    title="Ой!",
                    description="Нельзя менять репутацию ботам или самому себе.",
                ),
                mention_author=False,
            )
            return

        guild_id = str(guild.id)
        target_id = str(target_user.id)

        # Проверяем, когда в последний раз этого пользователя трогали
        recent_change = await self.db.get_rows(
            "user_reputation_log",
            guild_id=guild_id,
            target_id=target_id,
            limit=1,
            order="created_at",
            ascending=False,
        )
        if recent_change:
            last_change = recent_change[0]
            last_timestamp = _time.ensure_datetime(last_change["created_at"])

            if last_timestamp:
                cooldown_end = last_timestamp.add(seconds=int(COOLDOWN.total_seconds()))
                now = _time.now()
                if now < cooldown_end:
                    _, pretty = _time.format_remaining_time(cooldown_end)
                    await message.reply(
                        Embed.warn(
                            title="Подожди чуть-чуть",
                            description=(
                                f"Репутацию {target_user.mention} уже меняли недавно.\n"
                                f"Попробуй снова через {pretty}."
                            ),
                        ),
                        mention_author=False,
                    )
                    return

        delta = 1 if content in THUMBS_UP else -1
        profile = await self.levels.adjust_reputation(guild_id, target_id, delta)

        await self.db.create_record(
            "user_reputation_log",
            values={
                "guild_id": guild_id,
                "target_id": target_id,
                "actor_id": str(actor.id),
                "delta": delta,
            },
        )

        # Аккуратные реакции — чтобы ребята видели, что всё сработало
        try:
            await message.add_reaction("✅")
        except discord.HTTPException:
            pass

        try:
            await target_message.add_reaction("⭐" if delta > 0 else "💢")
        except discord.HTTPException:
            pass

        await message.reply(
            Embed.success(
                title="Репутация обновлена",
                description=(
                    f"{target_user.mention} теперь имеет репутацию **{profile['reputation']}** "
                    f"({'+1' if delta > 0 else '-1'} от {actor.mention})."
                ),
            ),
            mention_author=False,
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reputation(bot))

