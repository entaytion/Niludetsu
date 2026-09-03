import asyncio, discord, re
from .PartnershipCore import PartnershipManager
from discord.ext import commands
from Niludetsu import config
from Niludetsu.locale import _
from Niludetsu.database import database

_INVITE_RE = re.compile(r'(?:https?://)?(?:www\.)?discord\.(?:gg|io|com/invite)/([a-zA-Z0-9-]+)')


class Partnership(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.partnership_channel_id = 1373720394418360524
        self.invite_channel_id = 1125546967217471609
        self.partner_manager_role_id = 1125344222065725543
        self.stats_channel_id = 1370456956757610496
        self.creator_id = "636570363605680139"
        self.partnership_manager = PartnershipManager(bot, config.SERVERS["MAIN_ID"])


    async def _remove_reaction_after_delay(self, message, emoji: str, delay: int):
        await asyncio.sleep(delay)
        try:
            await message.remove_reaction(emoji, self.bot.user)
        except:
            pass

    async def _reject_message(self, message) -> None:
        try:
            await message.add_reaction("❌")
            await asyncio.sleep(5)
            await message.delete()
        except:
            pass

    async def send_error_notification(self, user_id: str, server_name: str, reason: str):
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            stats_channel = self.bot.get_channel(self.stats_channel_id)
            user = self.bot.get_user(int(user_id))
            if not stats_channel or not user:
                return
            embed = discord.Embed(
                description=t("partnership", "partner_error_rejected", server_name=server_name, reason=reason),
                color=0xFF0000,
            )
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            await stats_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка при отправке уведомления об ошибке: {e}")

    async def send_partnership_stats(self, user_id: str, server_name: str, points_earned: int, is_new: bool, renewed_count: int = 0):
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            stats_channel = self.bot.get_channel(self.stats_channel_id)
            user = self.bot.get_user(int(user_id))
            if not stats_channel or not user:
                return

            pm_stats = await self.partnership_manager.get_manager_stats(user_id)

            if is_new:
                update_text = t("partnership", "partner_stats_new", server_name=server_name)
                action_emoji = "🆕"
                action_text = t("partnership", "partner_stats_new_action")
            else:
                update_text = t("partnership", "partner_stats_renewed", server_name=server_name, count=renewed_count)
                action_emoji = "🔄"
                action_text = t("partnership", "partner_stats_renew_action")

            points_info = f"[+{points_earned}]" if points_earned > 0 else "[+0]"
            points_word = t("partnership", f"partner_points_word_{1 if points_earned == 1 else 2 if points_earned <= 4 else 5}")

            embed = discord.Embed(
                description=(
                    f"{update_text}\n"
                    f"{t('partnership', 'partner_stats_points', user_name=user.display_name, points=points_earned, points_word=points_word, total=pm_stats['points'])}"
                ),
                color=0x000000,
            )
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            embed.add_field(
                name=t("partnership", "partner_stats_header"),
                value=(
                    f"- {t('partnership', 'partner_stats_new_partners', count=pm_stats['new_partnerships'])}, "
                    f"{t('partnership', 'partner_stats_renewed_partners', count=pm_stats['renewed_partnerships'])}\n"
                    f"- {t('partnership', 'partner_stats_last_action', emoji=action_emoji, action=action_text, points_info=points_info)}"
                ),
                inline=False,
            )
            await stats_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка при отправке статистики: {e}")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.guild.id != config.SERVERS["MAIN_ID"]:
            return
        if message.channel.id != self.invite_channel_id:
            return

        invite_match = _INVITE_RE.search(message.content)
        if not invite_match:
            return

        invite_code = invite_match.group(1)
        invite_info = await self.partnership_manager.get_invite_info(invite_code)
        if not invite_info:
            try:
                await message.add_reaction("❌")
                await asyncio.sleep(5)
                await message.delete()
            except:
                pass
            return

        server_id = invite_info["server_id"]
        server_name = invite_info["server_name"]

        server_lock = await self.partnership_manager.processing_queue.acquire_server_lock(server_id)
        async with server_lock:
            user_id = str(message.author.id)
            user_lock = await self.partnership_manager.processing_queue.acquire_user_lock(user_id)
            async with user_lock:
                full_invite_info = {
                    "server_id": server_id,
                    "server_name": server_name,
                    "invite_code": invite_code,
                    **invite_info,
                }
                await self.process_invite(message, full_invite_info)

                if not invite_info.get("from_db"):
                    asyncio.create_task(
                        self.delete_server_duplicates_async(server_id, server_name, message)
                    )

    async def delete_server_duplicates_async(self, server_id, server_name, current_message):
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            await asyncio.sleep(1)
            channel = current_message.channel
            deleted_count = 0
            invite_cache = {}

            async for msg in channel.history(limit=50):
                if msg.id == current_message.id or msg.author.bot:
                    continue

                invite_match = _INVITE_RE.search(msg.content)
                if invite_match:
                    invite_code = invite_match.group(1)
                    if invite_code in invite_cache:
                        msg_server_id = invite_cache[invite_code]
                    else:
                        try:
                            invite = await self.bot.fetch_invite(invite_code)
                            msg_server_id = str(invite.guild.id)
                            invite_cache[invite_code] = msg_server_id
                        except:
                            continue

                    if msg_server_id == server_id:
                        try:
                            await msg.delete()
                            deleted_count += 1
                        except:
                            pass

            if deleted_count > 0:
                log_channel = self.bot.get_channel(self.stats_channel_id)
                if log_channel:
                    await log_channel.send(
                        t("partnership", "partner_duplicates_deleted", count=deleted_count, server_name=server_name, server_id=server_id)
                    )
        except Exception as e:
            print(f"Ошибка при удалении дубликатов: {e}")

    async def process_invite(self, message, invite_info):
        server_id = str(invite_info.get("server_id") or message.guild.id)
        server_name = invite_info.get("server_name", "Неизвестно")
        user_id = str(message.author.id)

        result = await self.partnership_manager.process_partnership(
            server_id=server_id,
            server_name=server_name,
            invite_code=invite_info.get("invite_code", ""),
            manager_id=user_id,
        )

        error = result.get('error')
        if error == 'self_invite':
            try:
                await message.delete()
            except:
                pass
            await self.send_error_notification(user_id, server_name, "☠️☠️☠️☠️☠️")
            return False

        if error == 'blacklisted':
            await self._reject_message(message)
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            await self.send_error_notification(user_id, server_name, t("partnership", "partner_error_blacklisted"))
            return False

        if error and error not in ('self_invite', 'blacklisted'):
            await self._reject_message(message)
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            await self.send_error_notification(user_id, server_name, result.get('message', t("partnership", "partner_error_unknown")))
            return False

        if result.get('success', False) and not result.get('is_new', False) and result.get('points', 0) == 0:
            try:
                await message.add_reaction("⏳")
                await asyncio.sleep(5)
                await message.remove_reaction("⏳", self.bot.user)
            except:
                pass
            return True

        try:
            await message.add_reaction("✅")
        except:
            pass

        if result.get('success', False):
            partnership = await self.partnership_manager.db.get_row("partnership", server_id=server_id)
            renewed_count = partnership.get("renewed_count", 0) if partnership else 0
            await self.send_partnership_stats(
                user_id=user_id,
                server_name=server_name,
                points_earned=result.get('points', 0),
                is_new=result.get('is_new', False),
                renewed_count=renewed_count,
            )
        return True

    @commands.command(name="pmserver")
    async def pmserver(self, ctx, action: str = None, server: str = None):
        t = _(ctx=ctx)

        if str(ctx.author.id) != self.creator_id:
            await ctx.reply(t("partnership", "partner_no_permission"))
            return

        blacklist = self.partnership_manager.blacklist

        if action == "list":
            blacklisted = await blacklist.get_blacklisted_servers()
            if not blacklisted:
                await ctx.reply(t("partnership", "partner_blacklist_empty"))
                return
            text = "\n".join(f"- **{s['server_name']}** ``{s['server_id']}``" for s in blacklisted)
            await ctx.reply(f"{t('partnership', 'partner_blacklist_title')}\n{text.strip()}")
            return

        if action not in ("add", "remove") or not server:
            await ctx.reply(t("partnership", "partner_blacklist_usage"))
            return

        match = re.search(r'(\d{15,})', server)
        if match:
            server_id = match.group(1)
            server_name = None
        else:
            invite_match = _INVITE_RE.search(server)
            if invite_match:
                try:
                    invite = await self.bot.fetch_invite(invite_match.group(1))
                    server_id = str(invite.guild.id)
                    server_name = invite.guild.name
                except Exception:
                    await ctx.reply(t("partnership", "partner_blacklist_invite_error"))
                    return
            else:
                await ctx.reply(t("partnership", "partner_blacklist_specify"))
                return

        if action == "add":
            success = await blacklist.add_to_blacklist(server_id, server_name)
            if success:
                final_name = server_name or await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"✅ {t('partnership', 'partner_blacklist_added', server_name=final_name, server_id=server_id)}")
            else:
                final_name = server_name or server_id
                await ctx.reply(f"❌ {t('partnership', 'partner_blacklist_add_failed', server_name=final_name, server_id=server_id)}")
        elif action == "remove":
            success = await blacklist.remove_from_blacklist(server_id)
            if success:
                final_name = server_name or await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"✅ {t('partnership', 'partner_blacklist_removed', server_name=final_name, server_id=server_id)}")
            else:
                final_name = server_name or server_id
                await ctx.reply(f"❌ {t('partnership', 'partner_blacklist_remove_failed', server_name=final_name, server_id=server_id)}")


async def setup(bot):
    await bot.add_cog(Partnership(bot))
