from __future__ import annotations

import discord
from discord.ext import commands

from Niludetsu import safe_delete, ModerationManager, AutoModManager, config
from Niludetsu.moderation.automod.rules import AutoModRuleType

MAIN_GUILD = config.SERVERS["MAIN_ID"]


class AutoModListener(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.automod = AutoModManager()
        self.mod = ModerationManager(bot)

    def invalidate_cache(self) -> None:
        self.automod.invalidate()


    async def check_message_violations(self, message: discord.Message) -> bool:
        rules = await self.automod.build_active_rules()
        session = getattr(self.bot, "http_session", None)
        for rule in rules:
            if await rule.check(message, http_session=session):
                return True
        return False


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild or message.guild.id != MAIN_GUILD:
            return

        rules = await self.automod.build_active_rules()
        if not rules:
            return

        session = getattr(self.bot, "http_session", None)

        for rule in rules:
            if not await rule.check(message, http_session=session):
                continue

            await safe_delete(message)

            if rule.rule_type == AutoModRuleType.INVITES:
                await self.mod.warn(message.guild, message.author, message.guild.me, "1.4")
                await self.mod.ban(message.guild, message.author, message.guild.me, "1.4")
            else:
                reason = f"Автомод: {rule.rule_type.label}"
                await self.mod.warn(message.guild, message.author, message.guild.me, reason)

            break


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoModListener(bot))
