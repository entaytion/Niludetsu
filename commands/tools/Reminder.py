import discord
from discord.ext import commands, tasks
from Niludetsu import safe_fetch_user
from Niludetsu.database.supabase_database import database
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Optional

_time = TimeService()

class Reminder(commands.GroupCog, group_name="reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database

        self.sleep_until: Optional[object] = None
        self.next_due_at: Optional[object] = None
        self.check_reminders.start()

    def cog_unload(self) -> None:
        self.check_reminders.cancel()

    async def get_due_reminders(self):
        now_iso = _time.now().to_iso8601_string()
        return await self.db.where(
            "user_reminders",
            filters=[
                {"op": "eq", "column": "completed", "value": False},
                {"op": "lte", "column": "remind_at", "value": now_iso},
            ],
        )

    async def get_user_reminders(self, user_id: int):
        return await self.db.where(
            "user_reminders",
            filters=[
                {"op": "eq", "column": "user_id", "value": str(user_id)},
                {"op": "eq", "column": "completed", "value": False},
            ],
        )

    async def get_next_pending_due_time(self):
        rows = await self.db.where(
            "user_reminders",
            filters=[{"op": "eq", "column": "completed", "value": False}],
            order=[{"column": "remind_at", "ascending": True}],
            limit=1,
            columns=["remind_at"],
        )
        if rows:
            return _time.ensure_datetime(rows[0]["remind_at"])
        return None

    async def add_reminder(
        self,
        user_id: int,
        guild_id: Optional[int],
        channel_id: Optional[int],
        message: str,
        remind_at,
    ):
        await self.db.ensure_user(
            user_id=str(user_id),
            guild_id=str(guild_id or "0"),
        )

        remind_dt = _time.ensure_datetime(remind_at)
        if remind_dt is None:
            return None

        payload = {
            "user_id": str(user_id),
            "guild_id": str(guild_id or "0"),
            "channel_id": str(channel_id or ""),
            "message": message,
            "remind_at": remind_dt.to_iso8601_string(),
            "completed": False,
        }
        created = await self.db.insert("user_reminders", payload)

        if created:
            if not self.next_due_at or remind_dt < self.next_due_at:
                self.next_due_at = remind_dt
            self.sleep_until = None

        return created["id"] if created else None

    async def complete_reminder(self, reminder_id: int) -> None:
        await self.db.update("user_reminders", {"id": reminder_id}, {"completed": True})

    async def delete_reminder(self, reminder_id: int, user_id: int):
        deleted = await self.db.delete(
            "user_reminders",
            id=reminder_id,
            user_id=str(user_id),
            completed=False,
        )
        if deleted:
            self.next_due_at = None
            self.sleep_until = None
        return deleted

    @tasks.loop(seconds=5)
    async def check_reminders(self):
        now = _time.now()

        if self.sleep_until and now < self.sleep_until:
            return
        self.sleep_until = None

        reminders = await self.get_due_reminders()
        if not reminders:
            if self.next_due_at and self.next_due_at > now:
                next_due = self.next_due_at
            else:
                next_due = await self.get_next_pending_due_time()
                self.next_due_at = next_due

            if next_due:
                seconds_left = max(0, int((next_due - now).total_seconds()))
                wait = min(max(seconds_left - 1, 5), 60)
                self.sleep_until = now.add(seconds=wait)
            else:
                self.sleep_until = now.add(seconds=60)
            return

        self.next_due_at = None

        for reminder in reminders:
            remind_at = _time.ensure_datetime(reminder["remind_at"])
            if not remind_at or remind_at > now:
                if remind_at and (not self.next_due_at or remind_at < self.next_due_at):
                    self.next_due_at = remind_at
                continue

            user_id = int(reminder["user_id"])
            user = await safe_fetch_user(self.bot, user_id)
            if not user:
                await self.complete_reminder(reminder["id"])
                continue

            channel = None
            if reminder.get("channel_id"):
                channel = self.bot.get_channel(int(reminder["channel_id"]))
                if (
                    not channel
                    and reminder.get("guild_id")
                    and int(reminder["guild_id"]) > 0
                ):
                    guild = self.bot.get_guild(int(reminder["guild_id"]))
                    if guild:
                        try:
                            channel = await guild.fetch_channel(
                                int(reminder["channel_id"])
                            )
                        except discord.HTTPException:
                            channel = None

            embed = Embed(title="⏰ Напоминание", description=reminder["message"])
            try:
                if channel:
                    await channel.send(f"{user.mention}", embed=embed)
                else:
                    await user.send(embed=embed)
            except Exception as exc:
                print(f"[НАПОМИНАНИЯ] Ошибка при отправке: {exc}")

            await self.complete_reminder(reminder["id"])

        self.sleep_until = None

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
        self.next_due_at = await self.get_next_pending_due_time()
        if not self.next_due_at:
            self.sleep_until = _time.now().add(seconds=60)

    @discord.app_commands.command(
        name="create",
        description="⌛ Создать новое напоминание",
    )
    @discord.app_commands.describe(
        time="⏰ Время напоминания. Например: 30с, 15 минут, 2ч, 1 день и т.д.",
        message="📝 Текст напоминания",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        time: str,
        message: str,
    ):
        duration_seconds, duration_str, error = _time.validate_duration(time, max_days=7)
        if error:
            await interaction.response.send_message(
                embed=Embed.error(description=error),
                ephemeral=True,
            )
            return

        active = await self.get_user_reminders(interaction.user.id)
        if len(active) >= 5:
            await interaction.response.send_message(
                embed=Embed.error(description="У вас уже 5 активных напоминаний."),
                ephemeral=True,
            )
            return

        remind_at = _time.add_duration(seconds=duration_seconds)
        reminder_id = await self.add_reminder(
            interaction.user.id,
            interaction.guild_id,
            interaction.channel_id,
            message,
            remind_at,
        )

        if reminder_id:
            await interaction.response.send_message(
                embed=Embed(
                    title="⏰ Напоминание создано",
                    description=f"Напомню через **{duration_str}**:\n{message}",
                )
            )
        else:
            await interaction.response.send_message(
                embed=Embed.error(description="Не удалось создать напоминание."),
                ephemeral=True,
            )

    @discord.app_commands.command(name="list", description="📋 Показать ваши напоминания")
    async def list(self, interaction: discord.Interaction):
        reminders = await self.get_user_reminders(interaction.user.id)
        if not reminders:
            await interaction.response.send_message(
                embed=Embed(
                    title="📋 Ваши напоминания",
                    description="У вас нет активных напоминаний.",
                ),
                ephemeral=True,
            )
            return

        now = _time.now()
        embed = Embed(
            title="📋 Ваши напоминания",
            description=f"Всего активных: {len(reminders)}",
        )

        for reminder in reminders:
            remind_at = _time.ensure_datetime(reminder["remind_at"]) or now
            seconds_left, readable = self.format_time_diff(now, remind_at)
            message_text = reminder["message"]
            if len(message_text) > 80:
                message_text = message_text[:77] + "..."
            embed.add_field(
                name=f"ID: {reminder['id']} (через {readable})",
                value=message_text,
                inline=False,
            )

        embed.set_footer(text="Удаление: /reminder delete [ID]")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.app_commands.command(name="delete", description="❌ Удалить напоминание")
    @discord.app_commands.describe(reminder_id="🆔 ID напоминания (смотрите /reminder list)")
    async def delete(self, interaction: discord.Interaction, reminder_id: int):
        deleted = await self.delete_reminder(reminder_id, interaction.user.id)
        if not deleted:
            await interaction.response.send_message(
                embed=Embed.error(description="Напоминание не найдено или уже выполнено."),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=Embed.success(
                title="Напоминание удалено",
                description=f"Удалено напоминание с ID {reminder_id}.",
            )
        )

    def format_time_diff(self, now, remind_at):
        diff = int((remind_at - now).total_seconds())
        if diff <= 0:
            return 0, "сейчас"
        return diff, _time.format_duration(diff)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))

