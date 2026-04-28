import discord
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService as Time
import Niludetsu.config as config
from discord.ext import tasks
from datetime import datetime
from Niludetsu.database import database
from Niludetsu.moderation.config import ActionType
from Niludetsu.moderation.embed import moderationembed
from Niludetsu.moderation.exceptions import ModerationError

from typing import Optional, Dict, Any, List

_time = Time()

class ModerationManager:
    """Центральний менеджер модерації: варни, мути, бани та їх автоматичне зняття."""

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.guild_id = str(config.SERVERS["MAIN_ID"])
        self._expire_task_started = False

    # --- Публічне API для команд ---

    async def warn(self, guild, target, moderator, reason="-", duration=None) -> Dict:
        return await self._execute(ActionType.WARN, guild, target, moderator, reason, duration)

    async def unwarn(self, guild, target, moderator, reason="-", rudiment=None) -> Dict:
        return await self._execute(ActionType.UNWARN, guild, target, moderator, reason, rudiment=rudiment)

    async def mute(self, guild, target, moderator, duration, reason="-") -> Dict:
        if not duration: raise ModerationError("Вкажіть тривалість муту.")
        # Discord timeout max 28 days
        duration = min(duration, 40320)
        return await self._execute(ActionType.MUTE, guild, target, moderator, reason, duration)

    async def unmute(self, guild, target, moderator, reason="-") -> Dict:
        return await self._execute(ActionType.UNMUTE, guild, target, moderator, reason)

    async def ban(self, guild, target, moderator, reason="-", duration=None, real=False) -> Dict:
        if real:
            await guild.ban(target, reason=f"Mod: {moderator} | {reason}", delete_message_seconds=0)
            return {"success": True, "embed": Embed.success(description=f"{target.mention} забанений назавжди.")}
        return await self._execute(ActionType.BAN, guild, target, moderator, reason, duration)

    async def unban(self, guild, target, moderator, reason="-") -> Dict:
        return await self._execute(ActionType.UNBAN, guild, target, moderator, reason)

    # --- Внутрішня логіка ---

    async def _execute(self, action, guild, target, moderator, reason, duration=None, rudiment=None) -> Dict:
        from Niludetsu.moderation.checks import check_moderation_target
        
        is_removal = action.lower().startswith("un")
        base_type = action[2:] if is_removal else action

        # Перевірка ієрархії
        ok, err = check_moderation_target(moderator, target, allow_bots_for_admin=(base_type == ActionType.BAN))
        if not ok: raise ModerationError(err)

        if is_removal:
            res = await self.remove_punishment(target.id, base_type, rudiment)
        else:
            res = await self.add_punishment(target.id, moderator.id, base_type, reason, duration)

        if not res.get("success"): raise ModerationError(res.get("error", "Помилка БД"))

        # Генеруємо ембед
        embed = moderationembed(base_type, target, moderator, res.get("rudiment"), reason, duration, mode='channel', is_removal=is_removal)
        
        # Логування
        try:
            log_ch = guild.get_channel(config.NOTIFICATION_CHANNEL_ID)
            if log_ch: await log_ch.send(embed=embed)
            await target.send(embed=moderationembed(base_type, target, moderator, res.get("rudiment"), reason, duration, mode='dm', is_removal=is_removal))
        except: pass

        return {"success": True, "embed": embed, "rudiment": res.get("rudiment")}

    async def add_punishment(self, user_id, moderator_id, action_type, reason, duration) -> Dict:
        expires_at = _time.add_duration(minutes=duration) if duration else None
        
        # Використовуємо атомарну вставку з генерацією рудименту через послідовність
        query = """
            INSERT INTO public.user_rudiments (
                guild_id, user_id, moderator_id, type, reason, 
                duration, expires_at, rudiment, active, created_at
            )
            VALUES (
                $1, $2, $3, $4, $5, 
                $6, $7, nextval('public.rudiment_seq')::text, true, now()
            )
            RETURNING rudiment;
        """
        
        row = await self.db._neon.fetchrow(
            query, 
            self.guild_id, str(user_id), str(moderator_id), 
            action_type, reason, duration, expires_at
        )
        
        if not row:
            return {"success": False}

        await self._discord_apply(user_id, action_type, reason, duration)
        return {"success": True, "rudiment": row["rudiment"]}

    async def remove_punishment(self, user_id, action_type, rudiment=None) -> Dict:
        filters = [{"column": "guild_id", "value": self.guild_id}, {"column": "user_id", "value": str(user_id)}, {"column": "type", "value": action_type}, {"column": "active", "value": True}]
        if rudiment: filters.append({"column": "rudiment", "value": str(rudiment)})

        rows = await self.db.where("user_rudiments", filters=filters, order=[{"column": "id", "ascending": False}], limit=1)
        if not rows: return {"success": False, "error": "Активне покарання не знайдене."}

        p = rows[0]
        await self.db.update_record("user_rudiments", {"id": p["id"]}, {"active": False})
        await self._discord_remove(user_id, action_type, p.get("metadata"))
        return {"success": True, "rudiment": p["rudiment"]}

    async def _discord_apply(self, user_id, action_type, reason, duration):
        guild = self.bot.get_guild(int(self.guild_id))
        member = guild.get_member(user_id) if guild else None
        if not member:
            return

        if action_type == ActionType.MUTE:
            until = _time.add_duration(minutes=duration or 40320)
            await member.timeout(until.in_timezone("UTC"), reason=reason)
        elif action_type == ActionType.BAN:
            role = guild.get_role(config.BAN_ROLE_ID)
            if role:
                await member.add_roles(role, reason=reason)

    async def _discord_remove(self, user_id, action_type, metadata):
        guild = self.bot.get_guild(int(self.guild_id))
        member = guild.get_member(user_id) if guild else None
        if not member:
            return

        if action_type == ActionType.MUTE:
            if member.timed_out_until:
                await member.timeout(None)
        elif action_type == ActionType.BAN:
            role = guild.get_role(config.BAN_ROLE_ID)
            if role and role in member.roles:
                await member.remove_roles(role)

    # --- Фонова задача ---

    def start_expire_system(self):
        if not self._expire_task_started:
            self.check_expired_task.start()
            self._expire_task_started = True

    @tasks.loop(seconds=60)
    async def check_expired_task(self):
        now = _time.now()
        expired = await self.db.where("user_rudiments", filters=[{"column": "active", "value": True}, {"column": "expires_at", "value": now, "op": "lt"}])
        for p in expired:
            await self.remove_punishment(int(p['user_id']), p['type'], p['rudiment'])
            # Тут можна додати логування про зняття

    @check_expired_task.before_loop
    async def before_check(self): await self.bot.wait_until_ready()

    async def get_active_punishments(self, user_id: int, action_type: Optional[str] = None) -> List[Dict]:
        filters = [{"column": "guild_id", "value": self.guild_id}, {"column": "user_id", "value": str(user_id)}, {"column": "active", "value": True}]
        if action_type: filters.append({"column": "type", "value": action_type})
        return await self.db.where("user_rudiments", filters=filters, order=[{"column": "created_at", "ascending": False}])

    async def get_all_punishments(self, user_id: int, action_type: Optional[str] = None, include_inactive: bool = True) -> List[Dict]:
        filters = [{"column": "guild_id", "value": self.guild_id}, {"column": "user_id", "value": str(user_id)}]
        if action_type: filters.append({"column": "type", "value": action_type})
        if not include_inactive: filters.append({"column": "active", "value": True})
        return await self.db.where("user_rudiments", filters=filters, order=[{"column": "created_at", "ascending": False}])

    async def get_punishment_by_rudiment(self, rudiment: str) -> Optional[Dict]:
        rows = await self.db.where("user_rudiments", filters=[{"column": "guild_id", "value": self.guild_id}, {"column": "rudiment", "value": str(rudiment)}], limit=1)
        return rows[0] if rows else None
