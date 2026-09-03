import asyncio, discord, re
from discord.ext import commands, tasks
from Niludetsu import config, EconomyManager, QuestTracker
from Niludetsu import Emojis, Embed, Time
from Niludetsu.locale import _, DEFAULT_LOCALE

from typing import Optional, Dict, Tuple, Any, Callable

_time = Time()
B = DEFAULT_LOCALE.get("bump", {})


class MonitoringBotsManager:

    BUMP_COMMANDS = {
        302050872383242240: "</bump:947088344167366698>",
        1059103014025171014: "</bump:1059103014025171015>",
        315926021457051650: "</bump:956435492398841858>",
        464272403766444044: "</up:891377101494681660>",
        575776004233232386: "</like:788801838828879933>",
        1327714529223901186: "</bump:1327714529223901187>",
        789751844821401630: "</partner:789751844821401631>",
    }

    def __init__(self) -> None:
        self.bots: Dict[int, Dict[str, Any]] = {
            302050872383242240: {
                "name": "DISBOARD", "delay": 2,
                "success_patterns": ["bump done"],
                "reward": 50, "emoji": Emojis.DISBOARD,
            },
            1059103014025171014: {
                "name": "DSGroup", "delay": 4,
                "success_patterns": [""],
                "reward": 50, "emoji": Emojis.DSGROUP,
            },
            315926021457051650: {
                "name": "Server Monitoring", "delay": 4,
                "success_patterns": ["server bumped by"],
                "reward": 50, "emoji": Emojis.SERVER_MONITORING,
            },
            464272403766444044: {
                "name": "SD.C Monitoring", "delay": 4,
                "success_patterns": ["успешный up", "время фиксации апа"],
                "reward": 50, "emoji": Emojis.SDC_MONITORING,
            },
            575776004233232386: {
                "name": "DSMonitoring", "delay": 4,
                "success_patterns": [
                    "вы успешно лайкнули сервер",
                    "you successfully liked the server",
                    "ви успішно лайкнули сервер",
                ],
                "reward": 50, "emoji": Emojis.DSMONITORING,
            },
            1327714529223901186: {
                "name": "BumPing", "delay": 2,
                "success_patterns": [],
                "reward": 25, "emoji": Emojis.BUMPING,
            },
            789751844821401630: {
                "name": "AutoPartnership", "delay": 2,
                "success_patterns": [],
                "reward": 25, "emoji": Emojis.AUTOPARTNERSHIP,
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


def _extract_content(message: discord.Message) -> str:
    content = (message.content or "").lower()
    if message.embeds:
        for emb in message.embeds:
            parts = [emb.description or "", emb.title or ""]
            parts += [f.name for f in emb.fields]
            parts += [f.value for f in emb.fields]
            content += "\n" + "\n".join(p.lower() for p in parts)
    return content


class BumpProcessor:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.economy = EconomyManager(self.db)
        self.config_manager = bot.config_manager
        self.bots_manager = MonitoringBotsManager()
        self.processing_messages: Dict[int, asyncio.Task] = {}
        self.quest_tracker = QuestTracker()


    def parse_discord_timestamp(self, content: str):
        match = re.search(r"<t:(\d+):", content)
        if match:
            try:
                return _time.from_timestamp(int(match.group(1)))
            except Exception:
                pass
        return None


    def _handle_dsgroup(self, message: discord.Message):
        bot_config = self.bots_manager.get_bot(1059103014025171014)
        if not message.content and not message.embeds:
            return _time.add_duration(_time.now(), hours=bot_config["delay"])
        content = (message.content or "").lower()
        if any(phrase in content for phrase in ("стой стой", "сервер успешно поднят")):
            return _time.add_duration(_time.now(), hours=bot_config["delay"])
        ts_match = re.search(r"<t:(\d+):R>", content)
        if ts_match:
            try:
                return _time.add_duration(_time.from_timestamp(int(ts_match.group(1))), hours=bot_config["delay"])
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
                    return _time.add_duration(_time.now(), hours=int(time_match.group(1)))
                except Exception:
                    pass
        return None

    def _handle_sdc_monitoring(self, message: discord.Message):
        bot_config = self.bots_manager.get_bot(464272403766444044)
        content = _extract_content(message)
        if "время фиксации апа" in content:
            stamp = self.parse_discord_timestamp(content)
            if stamp:
                return _time.add_duration(stamp, hours=4)
        success_keywords = [
            "сервер успешно поднят", "bump successful",
            "успешно забамплен", "сервер поднят",
        ]
        if any(keyword in content for keyword in success_keywords):
            stamp = self.parse_discord_timestamp(content)
            if stamp:
                return _time.add_duration(stamp, hours=bot_config["delay"])
        return None

    def _handle_server_monitoring(self, message: discord.Message):
        bot_config = self.bots_manager.get_bot(315926021457051650)
        if not message.embeds:
            return None
        for embed in message.embeds:
            if embed.title and "server bumped by" in embed.title.lower():
                return _time.add_duration(_time.now(), hours=bot_config["delay"])
        return None

    def _handle_bumping(self, message: discord.Message):
        bot_config = self.bots_manager.get_bot(1327714529223901186)
        content = _extract_content(message)
        if "сервер успешно бампнут" in content or "bump done" in content:
            return _time.add_duration(_time.now(), hours=bot_config["delay"])
        return None

    def _handle_autopartnership(self, message: discord.Message):
        bot_config = self.bots_manager.get_bot(789751844821401630)
        if not message.embeds:
            return None
        for embed in message.embeds:
            title = (embed.title or "").lower()
            description = (embed.description or "").lower()
            if ":rocket:" in title or "рассылается" in description:
                return _time.add_duration(_time.now(), hours=bot_config["delay"])
        return None

    _SPECIAL_HANDLERS: Dict[int, Callable] = {}

    @classmethod
    def _init_handlers(cls):
        if cls._SPECIAL_HANDLERS:
            return
        cls._SPECIAL_HANDLERS = {
            1059103014025171014: lambda self, m: self._handle_dsgroup(m),
            464272403766444044: lambda self, m: self._handle_sdc_monitoring(m),
            315926021457051650: lambda self, m: self._handle_server_monitoring(m),
            1327714529223901186: lambda self, m: self._handle_bumping(m),
            789751844821401630: lambda self, m: self._handle_autopartnership(m),
        }

    def process_bump_message(self, message: discord.Message):
        bot_id = message.author.id
        bot_config = self.bots_manager.get_bot(bot_id)
        if not bot_config:
            return None

        self._init_handlers()
        handler = self._SPECIAL_HANDLERS.get(bot_id)
        if handler:
            result = handler(self, message)
            if result is not None:
                return result

        content = _extract_content(message)
        for pattern in bot_config["success_patterns"]:
            if pattern and re.search(pattern, content):
                return _time.add_duration(_time.now(), hours=bot_config["delay"])
        return None


    async def update_bump_time(self, bot_id: int, guild_id: int, next_bump):
        bot_config = self.bots_manager.get_bot(bot_id)
        now = _time.now()
        if next_bump is None:
            delay = bot_config.get("delay", 4) if bot_config else 4
            next_bump = _time.add_duration(now, hours=delay)

        last_bump_iso = _time.to_iso(now)
        next_bump_iso = _time.to_iso(next_bump)
        where = {"guild_id": str(guild_id), "bot_id": str(bot_id)}
        current = await self.db.get_row("bump_reminders", **where)
        payload = {"last_bump": last_bump_iso, "next_bump": next_bump_iso, "notified": False}
        if current:
            await self.db.update_record("bump_reminders", where=where, values=payload)
        else:
            await self.db.insert("bump_reminders", {**where, **payload})

    async def get_next_bump(self, guild_id: int, bot_id: Optional[int] = None):
        filters = [{"column": "guild_id", "op": "eq", "value": str(guild_id)}]
        if bot_id is not None:
            filters.append({"column": "bot_id", "op": "eq", "value": str(bot_id)})
        rows = await self.db.where(
            "bump_reminders", filters=filters,
            columns=["guild_id", "bot_id", "last_bump", "next_bump", "notified"],
        )
        if bot_id is not None:
            return rows[:1]
        return sorted(rows, key=lambda row: row.get("next_bump") or "")

    async def get_interaction_user_id(self, message: discord.Message) -> Optional[str]:
        if message.author.id == 315926021457051650 and message.embeds:
            for embed in message.embeds:
                if embed.title and "server bumped by" in embed.title.lower():
                    match = re.search(r"<@!?(\d{17,20})>", embed.title)
                    if match: return match.group(1)
                    id_match = re.search(r"(\d{17,20})", embed.title)
                    if id_match: return id_match.group(1)
        if hasattr(message, "interaction_metadata") and message.interaction_metadata:
            return str(message.interaction_metadata.user.id)
        if message.mentions:
            return str(message.mentions[0].id)
        if message.content:
            mention = re.search(r"<@!?(\d+)>", message.content)
            if mention: return mention.group(1)
        if message.embeds:
            for embed in message.embeds:
                for field in embed.fields:
                    mention = re.search(r"<@!?(\d+)>", field.value)
                    if mention: return mention.group(1)
                    id_match = re.search(r"(\d{17,20})", field.value)
                    if id_match: return id_match.group(1)
        return None

    async def _refetch_message(self, message: discord.Message) -> Optional[discord.Message]:
        try:
            return await message.channel.fetch_message(message.id)
        except discord.NotFound:
            return None

    async def _update_bump_time_from_message(self, message: discord.Message):
        next_bump = self.process_bump_message(message)
        if not next_bump:
            return None
        await self.update_bump_time(message.author.id, message.guild.id, next_bump)
        return next_bump

    async def _get_reward_context(self, message: discord.Message):
        user_id = await self.get_interaction_user_id(message)
        if not user_id or int(message.guild.id) != config.SERVERS["MAIN_ID"]:
            return None, None
        bot_config = self.bots_manager.get_bot(message.author.id)
        if not bot_config:
            return None, None
        return user_id, bot_config

    async def award_bump_reward(self, message: discord.Message, action_name: str) -> bool:
        user_id, bot_config = await self._get_reward_context(message)
        if not user_id or not bot_config:
            return False

        reward = bot_config.get("reward", 50)
        emoji = bot_config.get("emoji", "")
        bot_name = bot_config.get("name", "")
        guild_id = message.guild.id

        success = await self.economy.add_money(
            user_id, str(guild_id), reward,
            event="bump", metadata={"bot": bot_name},
        )
        if not success:
            return False

        default_title = B.get("reward_title", "{emoji} Благодарим за {action} на {bot}!").format(emoji=emoji, action=action_name, bot=bot_name)
        default_desc = B.get("reward_desc", "<@{user}>, вам зачислено {reward} {currency} на ваш баланс!").format(user=user_id, reward=reward, currency=Emojis.MONEY)
        custom_data = self.config_manager.get_custom_embed(
            guild_id, "bump_reminder", "reward_embed",
            default_embed_data={
                "title": default_title,
                "description": default_desc,
            },
            emoji=emoji,
            action_name=action_name,
            bot_name=bot_name,
            user_id=user_id,
            reward=reward,
            currency=Emojis.MONEY,
        )
        embed = Embed(**custom_data)

        member = message.guild.get_member(int(user_id))
        if member:
            embed.set_thumbnail(url=member.display_avatar.url)

        await message.channel.send(embed=embed)
        asyncio.create_task(
            self.quest_tracker.on_bump(str(guild_id), user_id)
        )
        return True

    async def process_message_with_delay(self, message: discord.Message):
        await asyncio.sleep(3)
        try:
            message = await self._refetch_message(message)
            if not message:
                return
            if not await self._update_bump_time_from_message(message):
                return
            action_name = B.get("action_bump", "бамп")
            await self.award_bump_reward(message, action_name)
        except Exception as exc:
            print(f"{B.get('process_error', 'Ошибка при обработке сообщения: {error}').format(error=exc)}")

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
                    default_title = B.get("remind_title", "Время бампать сервер!")
                    default_desc = B.get("remind_desc", "{emoji} Можно сделать бамп на {bot}!").format(emoji=bot.get("emoji", ""), bot=bot["name"])
                    custom_data = self.config_manager.get_custom_embed(
                        guild_id, "bump_reminder", "remind_embed",
                        default_embed_data={
                            "title": default_title,
                            "description": default_desc,
                        },
                        bot_name=bot["name"],
                        bot_emoji=bot.get("emoji", ""),
                    )
                    embed = Embed(**custom_data)
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
        if bool(record.get("notified")):
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
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.processor = BumpProcessor(bot)
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

    def _matches_special_bump_embed(self, message: discord.Message, phrase: str) -> bool:
        for embed in message.embeds:
            title = (embed.title or "").lower()
            description = (embed.description or "").lower()
            if phrase in title or phrase in description:
                return True
        return False

    async def _handle_special_bot(self, message: discord.Message, expected_phrase: str, action_name: str):
        if not self._matches_special_bump_embed(message, expected_phrase):
            return False
        await self._finalize_special_bump(message, action_name)
        return True

    async def handle_special_bump(self, message: discord.Message):
        action_bump = B.get("action_bump", "бамп")
        action_broadcast = B.get("action_broadcast", "рассылку")
        if message.author.id == 1327714529223901186:
            if await self._handle_special_bot(message, "сервер успешно бампнут", action_bump):
                return
        if message.author.id == 789751844821401630:
            await self._handle_special_bot(message, "объявление рассылается", action_broadcast)

    async def _finalize_special_bump(self, message: discord.Message, action_name: str):
        if not await self.processor._update_bump_time_from_message(message):
            return
        await self.processor.award_bump_reward(message, action_name)

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
        t = _(ctx=ctx)
        embed = Embed.info(
            title=t("bump", "checkbump_title"),
            description=t("bump", "checkbump_desc"),
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
            slash_cmd = MonitoringBotsManager.BUMP_COMMANDS.get(bot_id, t("bump", "slash_cmd_unknown"))
            if not records:
                status = t("bump", "bump_available", cmd=slash_cmd)
            else:
                record = records[0]
                next_bump = record.get("next_bump")
                notified = bool(record.get("notified"))
                is_ready = _time.is_time_passed(next_bump)
                if is_ready and not notified:
                    status = t("bump", "bump_available", cmd=slash_cmd)
                elif is_ready and notified:
                    parsed_next = _time.ensure_datetime(next_bump)
                    next_available = _time.add_duration(parsed_next, hours=cfg["delay"])
                    ts = int(next_available.timestamp())
                    status = t("bump", "bump_available_at", ts=ts, cmd=slash_cmd)
                else:
                    parsed = _time.ensure_datetime(next_bump)
                    ts = int(parsed.timestamp())
                    status = t("bump", "bump_available_at", ts=ts, cmd=slash_cmd)
            embed.add_field(
                name=f"{cfg['emoji']} {cfg['name']}",
                value=status,
                inline=False,
            )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(BumpReminder(bot))
