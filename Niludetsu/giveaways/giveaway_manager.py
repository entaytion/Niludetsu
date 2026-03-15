import discord, json, random
from discord.ext import commands
from Niludetsu.config import GIVEAWAY_ROLE
from Niludetsu.database.supabase_database import database
from Niludetsu.giveaways.conditions import GiveawayConditions
from Niludetsu.giveaways.repository import GiveawayRepository
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Time import TimeService
from typing import Any, Dict, List, Optional

_time = TimeService()

class GiveawayManager:
    """Высокоуровневая логика розыгрышей."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.repo = GiveawayRepository(self.db)
        self.active: Dict[int, Dict[str, Any]] = {}
        bot.loop.create_task(self._restore())

    async def _restore(self) -> None:
        await self.bot.wait_until_ready()
        await self.load_active()

    async def setup_database(self):
        await self.load_active()
        from .ui import GiveawayParticipationView

        self.bot.add_view(GiveawayParticipationView())

    async def load_active(self):
        self.active.clear()
        now = _time.now()

        rows = await self.db.where(
            "giveaways",
            filters=[{"column": "is_ended", "value": False}],
            columns=[
                "giveaway_id",
                "end_time",
                "guild_id",
                "channel_id",
                "message_id",
                "mention_role_id",
                "settings",
            ],
        )

        expired_ids: List[int] = []

        for row in rows:
            giveaway_id = row["giveaway_id"]
            end_time = _time.parse(row["end_time"])

            if not end_time or end_time <= now:
                expired_ids.append(giveaway_id)
                continue

            meta = {
                "message_id": int(row["message_id"]),
                "channel_id": int(row["channel_id"]),
                "guild_id": int(row["guild_id"]),
                "end_time": end_time,
                "last_update": 0,
                "mention_role_id": (
                    int(row["mention_role_id"]) if row.get("mention_role_id") else None
                ),
                "settings": row.get("settings") or {},
            }
            self.active[giveaway_id] = meta

            participants = await self.repo.list_participants(giveaway_id, active_only=True)
            await self._register_view(giveaway_id, len(participants))

        for giveaway_id in expired_ids:
            await self.end_giveaway(giveaway_id)

    async def _register_view(self, giveaway_id: int, participants_count: int) -> None:
        from .ui import GiveawayParticipationView

        view = GiveawayParticipationView(self, giveaway_id, participants_count)
        self.bot.add_view(view)

    async def get_giveaway(self, giveaway_id: int) -> Optional[Dict[str, Any]]:
        return await self.repo.fetch_one(giveaway_id)

    # 
    def _compose_conditions(self, settings: Dict[str, Any]) -> Optional[str]:
        lines: List[str] = []
        if settings["min_server_time"]:
            lines.append(f"• Минимум {settings['min_server_time']} дн. на сервере")
        if settings["min_voice_time"]:
            lines.append(f"• Голосовой стаж: {settings['min_voice_time']} минут")
        if settings["required_role"]:
            lines.append(f"• Роль: <@&{settings['required_role']}>")
        if settings["min_level"]:
            lines.append(f"• Уровень: {settings['min_level']}")
        if settings["booster_only"]:
            lines.append("• Только для бустеров")
        if settings["no_revote"]:
            lines.append("• Повторное участие запрещено")
        return "\n".join(lines) if lines else None

    def _build_giveaway_embed(
        self,
        *,
        prize: str,
        host_id: str,
        end_time,
        winners_count: int,
        settings: Dict[str, Any],
        participants_count: int = 0,
    ) -> Embed:
        embed = Embed(
            title=f"{Emojis.GIVEAWAY} {prize}",
            description="Нажмите кнопку ниже, чтобы участвовать!",
            color=Colors.INFO,
        )
        embed.add_field(name="> Призовых мест:", value=str(winners_count), inline=True)
        embed.add_field(
            name="> Завершится:",
            value=f"<t:{int(end_time.timestamp())}:R>",
            inline=True,
        )
        embed.add_field(name="> Организатор:", value=f"<@{host_id}>", inline=True)

        if participants_count:
            embed.add_field(
                name="> Участников сейчас:",
                value=str(participants_count),
                inline=True,
            )

        conditions_text = self._compose_conditions(settings)
        if conditions_text:
            embed.add_field(name="> Условия:", value=conditions_text, inline=False)
        return embed

    async def _refresh_view(self, giveaway_id: int, participants_count: int) -> None:
        meta = self.active.get(giveaway_id)
        if not meta:
            return

        guild = self.bot.get_guild(meta["guild_id"])
        channel = guild.get_channel(meta["channel_id"]) if guild else None
        if not isinstance(channel, discord.TextChannel):
            return

        from .ui import GiveawayParticipationView

        view = GiveawayParticipationView(self, giveaway_id, participants_count)

        try:
            message = await channel.fetch_message(meta["message_id"])
            await message.edit(view=view)
        except discord.NotFound:
            giveaway = await self.repo.fetch_one(giveaway_id)
            if not giveaway:
                return

            settings = {
                **GiveawayConditions.defaults(),
                **(giveaway.get("settings") or {}),
            }
            end_time = _time.parse(giveaway["end_time"]) or _time.now()
            embed = self._build_giveaway_embed(
                prize=giveaway["prize"],
                host_id=giveaway["host_id"],
                end_time=end_time,
                winners_count=giveaway["winners_count"],
                settings=settings,
                participants_count=participants_count,
            )
            mention_role_id = meta.get("mention_role_id") or GIVEAWAY_ROLE
            content = f"<@&{mention_role_id}>" if mention_role_id else None

            new_message = await channel.send(content=content, embed=embed, view=view)
            await self.repo.update_giveaway(
                giveaway_id,
                {"message_id": str(new_message.id)},
            )
            meta["message_id"] = new_message.id
        except discord.HTTPException:
            return

        meta["last_update"] = int(_time.now().timestamp())

    async def _announce_winners(
        self,
        giveaway: Dict[str, Any],
        message: discord.Message,
        winners: List[str],
    ) -> None:
        prize = giveaway["prize"]
        winners_mentions = "\n".join(f"<@{wid}>" for wid in winners) or "— Победителей нет."
        winners_count = giveaway["winners_count"]

        embed = Embed(
            title=f"{Emojis.GIVEAWAY} {prize} | Завершён!",
            description=f"**Победители:**\n{winners_mentions}",
            color=Colors.SUCCESS if winners else Colors.WARNING,
        )
        unix_ts = int(_time.now().timestamp())
        embed.add_field(name="> Призовых мест:", value=str(winners_count), inline=True)
        embed.add_field(
            name="> Организатор:",
            value=f"<@{giveaway['host_id']}>",
            inline=True,
        )
        embed.add_field(name="> Завершён:", value=f"<t:{unix_ts}:F>", inline=True)

        await message.edit(embed=embed, view=None)
        if winners:
            await message.channel.send(
                f"{Emojis.GIVEAWAY} Победители розыгрыша [{prize}]({message.jump_url}):\n{winners_mentions}"
            )

    async def _notify_users(
        self,
        winner_ids: List[str],
        giveaway: Dict[str, Any],
        message: discord.Message,
    ):
        if not winner_ids:
            return

        host = await self.bot.fetch_user(int(giveaway["host_id"]))
        host_mention = host.mention if host else f"<@{giveaway['host_id']}>"
        for uid in winner_ids:
            try:
                user = await self.bot.fetch_user(int(uid))
                if not user:
                    continue
                embed = Embed(
                    title=f"{Emojis.GIVEAWAY} Поздравляем! Вы выиграли!",
                    description=(
                        f"Вы победили в розыгрыше **{giveaway['prize']}**\n"
                        f"- Свяжитесь с организатором: {host_mention}\n"
                        f"- Сообщение: [перейти]({message.jump_url})"
                    ),
                    color=Colors.SUCCESS,
                )
                await user.send(embed=embed)
            except Exception:
                continue

    async def create_giveaway(
        self,
        channel: discord.TextChannel,
        host: discord.Member,
        prize: str,
        duration_input: str,
        winners: int = 1,
        settings: Optional[Dict[str, Any]] = None,
        mention_role_id: Optional[int] = None,
    ) -> discord.Message:
        settings = {**GiveawayConditions.defaults(), **(settings or {})}
        seconds, _, error = _time.validate(duration_input, max_days=30)
        if error:
            raise ValueError(error)
        end_time = _time.add_duration(seconds=seconds)
        await self.db.ensure_record(
            "users",
            user_id=str(host.id),
            guild_id=str(channel.guild.id),
        )
        record = await self.repo.create_giveaway(
            {
                "channel_id": str(channel.id),
                "guild_id": str(channel.guild.id),
                "host_id": str(host.id),
                "prize": prize,
                "winners_count": winners,
                "end_time": end_time.to_iso8601_string(),
                "description": settings.get("description"),
                "mention_role_id": str(mention_role_id) if mention_role_id else None,
                "settings": settings,
            }
        )
        giveaway_id = record["giveaway_id"]

        embed = self._build_giveaway_embed(
            prize=prize,
            host_id=str(host.id),
            end_time=end_time,
            winners_count=winners,
            settings=settings,
        )
        content = f"<@&{mention_role_id or GIVEAWAY_ROLE}>" if (mention_role_id or GIVEAWAY_ROLE) else None
        message = await channel.send(content=content, embed=embed)
        await self.repo.update_giveaway(
            giveaway_id,
            {"message_id": str(message.id)},
        )

        await self._register_view(giveaway_id, participants_count=0)
        await message.edit(view=None)  # view уже добавлен как persistent
        await self._refresh_view(giveaway_id, 0)

        self.active[giveaway_id] = {
            "message_id": message.id,
            "channel_id": channel.id,
            "guild_id": channel.guild.id,
            "end_time": end_time,
            "last_update": int(_time.now().timestamp()),
            "mention_role_id": mention_role_id,
            "settings": settings,
        }

        return message

    async def toggle_participation(self, giveaway_id: int, user_id: str) -> str:
        giveaway = await self.repo.fetch_one(giveaway_id)
        if not giveaway or giveaway["is_ended"]:
            return "inactive"

        participant_ids = await self.repo.list_participants(giveaway_id, active_only=True)
        is_joined = user_id in participant_ids

        if is_joined:
            await self.repo.remove_participant(giveaway_id, user_id)
            status = "left"
            new_count = max(len(participant_ids) - 1, 0)
        else:
            await self.repo.upsert_participant(giveaway_id, user_id)
            status = "joined"
            new_count = len(participant_ids) + 1

        await self._refresh_view(giveaway_id, new_count)
        return status

    async def end_giveaway(self, giveaway_id: int) -> None:
        giveaway = await self.repo.fetch_one(giveaway_id)
        if not giveaway or giveaway["is_ended"]:
            return

        participants = await self.repo.list_participants(giveaway_id, active_only=True)
        channel = self.bot.get_channel(int(giveaway["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            await self.repo.update_giveaway(giveaway_id, {"is_ended": True})
            self.active.pop(giveaway_id, None)
            return

        try:
            message = await channel.fetch_message(int(giveaway["message_id"]))
        except discord.NotFound:
            message = None

        if not participants:
            embed = Embed(
                title=f"{Emojis.GIVEAWAY} {giveaway['prize']} | Завершён!",
                description="- Никто не участвовал, победителей нет.",
                color=Colors.WARNING,
            )
            unix_ts = int(_time.now().timestamp())
            embed.add_field(name="> Призовых мест:", value=str(giveaway["winners_count"]), inline=True)
            embed.add_field(name="> Организатор:", value=f"<@{giveaway['host_id']}>", inline=True)
            embed.add_field(name="> Завершён:", value=f"<t:{unix_ts}:F>", inline=True)

            if message:
                await message.edit(embed=embed, view=None)
            else:
                await channel.send(embed=embed)

            await self.repo.update_giveaway(
                giveaway_id,
                {"is_ended": True, "ended_at": _time.now().to_iso8601_string()},
            )
            self.active.pop(giveaway_id, None)
            return

        winners_count = min(giveaway["winners_count"], len(participants))
        winner_ids = random.sample(participants, winners_count) if winners_count else []

        await self.repo.update_giveaway(
            giveaway_id,
            {
                "is_ended": True,
                "ended_at": _time.now().to_iso8601_string(),
                "last_winners": json.dumps(winner_ids),
            },
        )
        self.active.pop(giveaway_id, None)

        if not message:
            settings = {
                **GiveawayConditions.defaults(),
                **(giveaway.get("settings") or {}),
            }
            end_time = _time.parse(giveaway["end_time"]) or _time.now()
            embed = self._build_giveaway_embed(
                prize=giveaway["prize"],
                host_id=giveaway["host_id"],
                end_time=end_time,
                winners_count=giveaway["winners_count"],
                settings=settings,
                participants_count=len(participants),
            )
            mention_role_id = giveaway.get("mention_role_id")
            mention_role_id = int(mention_role_id) if mention_role_id else GIVEAWAY_ROLE
            content = f"<@&{mention_role_id}>" if mention_role_id else None
            message = await channel.send(content=content, embed=embed)

        await self._announce_winners(giveaway, message, winner_ids)
        await self._notify_users(winner_ids, giveaway, message)

    async def reroll(self, giveaway_id: int) -> List[discord.Member]:
        giveaway = await self.repo.fetch_one(giveaway_id)
        if not giveaway:
            raise ValueError("Розыгрыш не найден.")
        if not giveaway["is_ended"]:
            raise ValueError("Розыгрыш ещё активен.")

        participants = await self.repo.list_participants(giveaway_id, active_only=True)
        if not participants:
            raise ValueError("Нет участников для перерозыгрыша.")

        guild = self.bot.get_guild(int(giveaway["guild_id"]))
        if not guild:
            raise ValueError("Сервер недоступен.")

        valid_members: List[discord.Member] = []
        for pid in participants:
            member = guild.get_member(int(pid))
            if not member:
                continue
            result = await GiveawayConditions.check(
                self.bot,
                member,
                {"settings": giveaway.get("settings", {}), "host_id": giveaway["host_id"]},
                guild=guild,
            )
            if result.get("success"):
                valid_members.append(member)

        if not valid_members:
            raise ValueError("Не найдено участников, соответствующих условиям.")

        winners_count = min(giveaway["winners_count"], len(valid_members))
        winners = random.sample(valid_members, winners_count)
        winner_ids = [str(m.id) for m in winners]

        await self.repo.update_giveaway(
            giveaway_id,
            {
                "reroll_count": giveaway.get("reroll_count", 0) + 1,
                "last_winners": json.dumps(winner_ids),
                "ended_at": _time.now().to_iso8601_string(),
            },
        )

        channel = self.bot.get_channel(int(giveaway["channel_id"]))
        message = await channel.fetch_message(int(giveaway["message_id"]))

        embed = Embed.success(
            title=f"{Emojis.GIVEAWAY} Перерозыгрыш #{giveaway.get('reroll_count', 0) + 1}",
            description="\n".join(f"🎉 {member.mention}" for member in winners),
        )
        embed.set_footer(text=f"ID розыгрыша: {giveaway_id}")
        await channel.send(embed=embed)

        await self._notify_users(winner_ids, giveaway, message)
        return winners

