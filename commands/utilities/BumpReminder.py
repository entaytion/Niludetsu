import asyncio, discord, re
from discord.ext import commands, tasks
from Niludetsu import config
from Niludetsu import Emojis, Embed, Time, Colors
from Niludetsu.database.supabase_database import SupabaseDatabase
from Niludetsu.economy.manager import EconomyManager
from typing import Optional, Dict, Tuple, Any

_time = Time()

class MonitoringBotsManager:
    """Управление ботами мониторинга и их настройками"""

    def __init__(self) -> None:
        self.bots: Dict[int, Dict[str, Any]] = {
            302050872383242240: {  # DISBOARD
                "name": "DISBOARD",
                "delay": 2,
                "success_patterns": ["bump done"],
                "reward": 50,
                "emoji": Emojis.DISBOARD,
            },
            1059103014025171014: {  # DSGroup
                "name": "DSGroup",
                "delay": 4,
                "success_patterns": [""],
                "reward": 50,
                "emoji": Emojis.DSGROUP,
            },
            315926021457051650: {  # Server Monitoring
                "name": "Server Monitoring",
                "delay": 4,
                "success_patterns": ["server bumped by"],
                "reward": 50,
                "emoji": Emojis.SERVER_MONITORING,
            },
            464272403766444044: {  # SD.C Monitoring
                "name": "SD.C Monitoring",
                "delay": 4,
                "success_patterns": ["успешный up", "время фиксации апа"],
                "reward": 50,
                "emoji": Emojis.SDC_MONITORING,
            },
            575776004233232386: {  # DSMonitoring
                "name": "DSMonitoring",
                "delay": 4,
                "success_patterns": [
                    "вы успешно лайкнули сервер",
                    "you successfully liked the server",
                    "ви успішно лайкнули сервер",
                ],
                "reward": 50,
                "emoji": Emojis.DSMONITORING,
            },
            1327714529223901186: {  # BumPing
                "name": "BumPing",
                "delay": 2,
                "success_patterns": [],
                "reward": 25,
                "emoji": Emojis.BUMPING,
            },
            789751844821401630: {  # AutoPartnership
                "name": "AutoPartnership",
                "delay": 2,
                "success_patterns": [],
                "reward": 25,
                "emoji": Emojis.AUTOPARTNERSHIP,
            },
        }

    def get_bot(self, bot_id: int) -> Optional[Dict[str, Any]]:
        return self.bots.get(bot_id)

    def get_all_bots(self) -> Dict[int, Dict[str, Any]]:
        return self.bots

    def is_monitoring_bot(self, bot_id: int) -> bool:
        return bot_id in self.bots

    def find_bot_by_name(self, name: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        pattern = name.lower()
        for bot_id, cfg in self.bots.items():
            if pattern in cfg["name"].lower():
                return bot_id, cfg
        return None

class BumpProcessor:
    """Обработка бамп-сообщений и взаимодействие с базой"""

    def __init__(self, bot: commands.Bot, db: SupabaseDatabase) -> None:
        self.bot = bot
        self.db = db
        self.economy = EconomyManager(self.db)
        self.bots_manager = MonitoringBotsManager()
        self.processing_messages: Dict[int, asyncio.Task] = {}

    def parse_discord_timestamp(self, content: str):
        match = re.search(r"<t:(\d+):", content)
        if match:
            try:
                return _time.from_timestamp(int(match.group(1)))
            except Exception:
                pass
        return None

    async def update_bump_time(self, bot_id: int, guild_id: int, next_bump):
        bot_config = self.bots_manager.get_bot(bot_id)
        now = _time.now()

        if next_bump is None:
            delay = bot_config.get("delay", 4) if bot_config else 4
            next_bump = _time.add_duration(now, hours=delay)

        last_bump_iso = now.to_iso8601_string()
        next_bump_iso = next_bump.to_iso8601_string()

        where = {"guild_id": str(guild_id), "bot_id": str(bot_id)}
        current = await self.db.get_row("bump_reminders", **where)

        payload = {
            "last_bump": last_bump_iso,
            "next_bump": next_bump_iso,
            "notified": False,
        }

        if current:
            await self.db.update_record("bump_reminders", where=where, values=payload)
        else:
            await self.db.insert(
                "bump_reminders", {**where, **payload}
            )

    async def get_next_bump(self, guild_id: int, bot_id: Optional[int] = None):
        filters = [
            {"column": "guild_id", "op": "eq", "value": str(guild_id)},
        ]
        if bot_id is not None:
            filters.append({"column": "bot_id", "op": "eq", "value": str(bot_id)})

        rows = await self.db.where(
            "bump_reminders",
            filters=filters,
            columns=["guild_id", "bot_id", "last_bump", "next_bump", "notified"],
        )

        if bot_id is not None:
            return rows[:1]
        return sorted(rows, key=lambda row: row.get("next_bump") or "")

    def process_bump_message(self, message: discord.Message):
        bot_id = message.author.id
        bot_config = self.bots_manager.get_bot(bot_id)
        if not bot_config:
            return None

        if bot_id == 1059103014025171014:
            if not message.content and not message.embeds:
                now = _time.now()
                return _time.add_duration(now, hours=bot_config["delay"])

            content = (message.content or "").lower()

            if any(phrase in content for phrase in ("стой стой", "сервер успешно поднят")):
                now = _time.now()
                return _time.add_duration(now, hours=bot_config["delay"])

            ts_match = re.search(r"<t:(\d+):R>", content)
            if ts_match:
                try:
                    ts = _time.from_timestamp(int(ts_match.group(1)))
                    return _time.add_duration(ts, hours=bot_config["delay"])
                except Exception:
                    pass

            for pattern in (
                r"через (\d+) час[а-я]*",
                r"только через (\d+) час[а-я]*",
                r"через (\d+) ч[а-я]*",
            ):
                time_match = re.search(pattern, content)
                if time_match:
                    try:
                        hours = int(time_match.group(1))
                        now = _time.now()
                        return _time.add_duration(now, hours=hours)
                    except Exception:
                        pass
            return None

        content = (message.content or "").lower()

        if message.embeds:
            for embed in message.embeds:
                if embed.description:
                    content += f"\n{embed.description.lower()}"
                if embed.title:
                    content += f"\n{embed.title.lower()}"
                for field in embed.fields:
                    content += f"\n{field.name.lower()}"
                    content += f"\n{field.value.lower()}"

        if bot_id == 464272403766444044:
            if "время фиксации апа" in content:
                stamp = self.parse_discord_timestamp(content)
                if stamp:
                    return _time.add_duration(stamp, hours=4)

            success_keywords = [
                "сервер успешно поднят",
                "bump successful",
                "успешно забамплен",
                "сервер поднят",
            ]
            if any(keyword in content for keyword in success_keywords):
                stamp = self.parse_discord_timestamp(content)
                if stamp:
                    return _time.add_duration(stamp, hours=bot_config["delay"])
            return None

        if bot_id == 315926021457051650 and message.embeds:
            for embed in message.embeds:
                if embed.title and "server bumped by" in embed.title.lower():
                    now = _time.now()
                    return _time.add_duration(now, hours=bot_config["delay"])

        if bot_id == 1327714529223901186:
            if "сервер успешно бампнут" in content or "bump done" in content:
                now = _time.now()
                return _time.add_duration(now, hours=bot_config["delay"])
            return None

        if bot_id == 789751844821401630 and message.embeds:
            for embed in message.embeds:
                title = (embed.title or "").lower()
                description = (embed.description or "").lower()
                if ":rocket: | объявление рассылается" in title or "объявление рассылается" in description:
                    now = _time.now()
                    return _time.add_duration(now, hours=bot_config["delay"])
            return None

        for pattern in bot_config["success_patterns"]:
            if pattern and re.search(pattern, content):
                now = _time.now()
                return _time.add_duration(now, hours=bot_config["delay"])

        return None

    async def get_interaction_user_id(self, message: discord.Message) -> Optional[str]:
        if message.author.id == 315926021457051650 and message.embeds:
            for embed in message.embeds:
                if embed.title and "server bumped by" in embed.title.lower():
                    match = re.search(r"<@!?(\d{17,20})>", embed.title)
                    if match:
                        return match.group(1)
                    id_match = re.search(r"(\d{17,20})", embed.title)
                    if id_match:
                        return id_match.group(1)

        if hasattr(message, "interaction_metadata") and message.interaction_metadata:
            return str(message.interaction_metadata.user.id)

        if message.mentions:
            return str(message.mentions[0].id)

        if message.content:
            mention = re.search(r"<@!?(\d+)>", message.content)
            if mention:
                return mention.group(1)

            for pattern in (
                r"(?:поднят|bumped by|user)[^\d]*(\d{17,20})",
                r"(?:пользователем|bumped by|user)[^\d]*<@!?(\d+)>",
            ):
                user_match = re.search(pattern, message.content.lower())
                if user_match:
                    return user_match.group(1)

        if message.embeds:
            for embed in message.embeds:
                if embed.description:
                    mention = re.search(r"<@!?(\d+)>", embed.description)
                    if mention:
                        return mention.group(1)

                for field in embed.fields:
                    mention = re.search(r"<@!?(\d+)>", field.value)
                    if mention:
                        return mention.group(1)
                    id_match = re.search(r"(\d{17,20})", field.value)
                    if id_match:
                        return id_match.group(1)

                if embed.footer and embed.footer.text:
                    mention = re.search(r"<@!?(\d+)>", embed.footer.text)
                    if mention:
                        return mention.group(1)

        return None

    async def process_message_with_delay(self, message: discord.Message):
        await asyncio.sleep(3)

        try:
            try:
                message = await message.channel.fetch_message(message.id)
            except discord.NotFound:
                return

            next_bump = self.process_bump_message(message)
            if not next_bump:
                return

            await self.update_bump_time(message.author.id, message.guild.id, next_bump)

            user_id = await self.get_interaction_user_id(message)
            if (
                not user_id
                or int(message.guild.id) != config.SERVERS["MAIN_ID"]
            ):
                return

            bot_config = self.bots_manager.get_bot(message.author.id)
            if not bot_config:
                return

            reward = bot_config.get("reward", 50)
            emoji = bot_config.get("emoji", "")
            bot_name = bot_config.get("name", "")

            success = await self.economy.add_money(user_id, str(message.guild.id), reward)
            if not success:
                return

            reward_embed = Embed(
                title=f"{emoji} Благодарим за бамп на {bot_name}!",
                description=f"<@{user_id}>, вам зачислено {reward} {Emojis.MONEY} на ваш баланс!",
            )

            member = message.guild.get_member(int(user_id))
            if member:
                reward_embed.set_thumbnail(url=member.display_avatar.url)

            await message.channel.send(embed=reward_embed)
        except Exception as exc:
            print(f"Ошибка при обработке сообщения: {exc}")

    async def check_bumps_task(self):
        reminders = await self.db.where(
            "bump_reminders",
            filters=[{"column": "notified", "op": "eq", "value": False}],
            columns=["guild_id", "bot_id", "next_bump", "notified"],
        )

        for reminder in reminders:
            next_bump = reminder.get("next_bump")
            if not next_bump:
                continue

            guild_id = int(reminder["guild_id"])
            bot_id = int(reminder["bot_id"])

            if not _time.is_time_passed(next_bump):
                continue

            bot = self.bots_manager.get_bot(bot_id)
            if not bot:
                continue

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            message_sent = False
            if guild_id == config.SERVERS["MAIN_ID"]:
                channel = guild.get_channel(1125546970522583070)
                if channel:
                    embed = Embed.success(
                        title="Время бампать сервер!",
                        description=f"{bot.get('emoji', '')} Можно сделать бамп на {bot['name']}!",
                    )
                    await channel.send(embed=embed)
                    message_sent = True

            if message_sent:
                await self.db.update_record(
                    "bump_reminders",
                    where={"guild_id": str(guild_id), "bot_id": str(bot_id)},
                    values={"notified": True},
                )

    async def check_bump(self, guild_id: int, bot_id: int) -> bool:
        rows = await self.get_next_bump(guild_id, bot_id)
        if not rows:
            return False

        record = rows[0]
        next_bump = record.get("next_bump")
        notified = bool(record.get("notified"))

        if notified:
            return False

        if not _time.is_time_passed(next_bump):
            return False

        await self.db.update_record(
            "bump_reminders",
            where={"guild_id": str(guild_id), "bot_id": str(bot_id)},
            values={"notified": True},
        )
        return True

class BumpReminder(commands.Cog):
    """Напоминания и награды за бампы"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = SupabaseDatabase()
        self.processor = BumpProcessor(bot, self.db)
        self.check_bumps.start()

    def cog_unload(self):
        self.check_bumps.cancel()
        for task in self.processor.processing_messages.values():
            if isinstance(task, asyncio.Task) and not task.done():
                task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            not message.guild
            or not self.processor.bots_manager.is_monitoring_bot(message.author.id)
        ):
            return

        special_bots = {1327714529223901186, 789751844821401630}

        if message.author.id in special_bots:
            if not message.content and not message.embeds:
                self.bot.loop.create_task(self.wait_for_special_bump(message))
                return
            if message.embeds:
                await self.handle_special_bump(message)
                return

        task = asyncio.create_task(self.processor.process_message_with_delay(message))
        self.processor.processing_messages[message.id] = task
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            print(f"Ошибка при обработке сообщения: {exc}")
        finally:
            self.processor.processing_messages.pop(message.id, None)

    async def wait_for_special_bump(self, message: discord.Message, timeout=300, check_interval=5):
        for _ in range(timeout // check_interval):
            try:
                msg = await message.channel.fetch_message(message.id)
            except discord.NotFound:
                return
            if msg.embeds:
                await self.handle_special_bump(msg)
                return
            await asyncio.sleep(check_interval)

    async def handle_special_bump(self, message: discord.Message):
        if message.author.id == 1327714529223901186:
            for embed in message.embeds:
                title = (embed.title or "").lower()
                description = (embed.description or "").lower()
                if "сервер успешно бампнут" in title or "сервер успешно бампнут" in description:
                    await self._finalize_special_bump(message, "бамп")
                    return

        if message.author.id == 789751844821401630:
            for embed in message.embeds:
                title = (embed.title or "").lower()
                description = (embed.description or "").lower()
                if "объявление рассылается" in title or "объявление рассылается" in description:
                    await self._finalize_special_bump(message, "рассылку")
                    return

    async def _finalize_special_bump(self, message: discord.Message, action_name: str):
        next_bump = self.processor.process_bump_message(message)
        if not next_bump:
            return

        await self.processor.update_bump_time(message.author.id, message.guild.id, next_bump)

        user_id = await self.processor.get_interaction_user_id(message)
        if not user_id or int(message.guild.id) != config.SERVERS["MAIN_ID"]:
            return

        bot_config = self.processor.bots_manager.get_bot(message.author.id)
        if not bot_config:
            return

        reward = bot_config.get("reward", 50)
        emoji = bot_config.get("emoji", "")
        bot_name = bot_config.get("name", "")

        success = await self.processor.economy.add_money(user_id, str(message.guild.id), reward)
        if not success:
            return

        embed = Embed(
            title=f"{emoji} Благодарим за {action_name} на {bot_name}!",
            description=f"<@{user_id}>, вам зачислено {reward} {Emojis.MONEY} на ваш баланс!",
        )

        member = message.guild.get_member(int(user_id))
        if member:
            embed.set_thumbnail(url=member.display_avatar.url)

        await message.channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def check_bumps(self):
        await self.processor.check_bumps_task()

    @check_bumps.before_loop
    async def before_check_bumps(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name="checkbump",
        aliases=["checkb", "bump", "бамп"],
        help="Показывает информацию о следующем бампе",
    )
    async def checkbump_command(self, ctx: commands.Context):
        embed = Embed.info(
            title="Статус бампов",
            description="Информация о доступности бампов:",
        )

        monitoring_members = {
            member.id
            for member in ctx.guild.members
            if member.bot and self.processor.bots_manager.is_monitoring_bot(member.id)
        }

        for bot_id, cfg in self.processor.bots_manager.get_all_bots().items():
            if bot_id not in monitoring_members:
                continue

            records = await self.processor.get_next_bump(ctx.guild.id, bot_id)

            if not records:
                status = "**Доступен для бампа**"
            else:
                record = records[0]
                next_bump = record.get("next_bump")
                notified = bool(record.get("notified"))
                is_ready = _time.is_time_passed(next_bump)

                if is_ready and not notified:
                    status = "**Доступен для бампа**"
                elif is_ready and notified:
                    parsed_next = _time.parse(next_bump)
                    next_available = _time.add_hours(parsed_next, cfg["delay"])
                    remaining = _time.format_remaining_time(next_available)
                    status = f"Доступен через **`{remaining[1]}`**"
                else:
                    remaining = _time.format_remaining_time(next_bump)
                    status = f"Доступен через **`{remaining[1]}`**"

            embed.add_field(
                name=f"{cfg['emoji']} {cfg['name']}",
                value=status,
                inline=False,
            )

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(BumpReminder(bot))

