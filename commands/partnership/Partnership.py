import asyncio, discord, re
from .PartnershipCore import PartnershipManager
from discord.ext import commands
from Niludetsu import config
from Niludetsu.locale import _
from Niludetsu.database import database

class Partnership(commands.Cog):
    """Команды для управления партнерствами"""

    def __init__(self, bot):
        self.bot = bot
        self.db = database
        self.partnership_channel_id = 1373720394418360524
        self.invite_channel_id = 1125546967217471609
        self.partner_manager_role_id = 1125344222065725543
        self.stats_channel_id = 1370456956757610496  # Канал для статистики и уведомлений
        self.creator_id = "636570363605680139"
        self.partnership_manager = PartnershipManager(bot, config.SERVERS["MAIN_ID"])

    async def remove_reaction_after_delay(self, message, emoji: str, delay: int):
        """Удаляет реакцию после задержки"""
        await asyncio.sleep(delay)
        try:
            await message.remove_reaction(emoji, self.bot.user)
        except:
            pass

    async def send_error_notification(self, user_id: str, server_name: str, reason: str):
        """Отправляет уведомление об ошибке в канал статистики"""
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)

            # Получаем канал статистики
            stats_channel = self.bot.get_channel(self.stats_channel_id)
            if not stats_channel:
                return

            # Получаем пользователя
            user = self.bot.get_user(int(user_id))
            if not user:
                return

            # Создаем эмбед с уведомлением об ошибке
            embed = discord.Embed(
                description=t("partnership", "partner_error_rejected", server_name=server_name, reason=reason),
                color=0xFF0000  # Красный цвет для ошибок
            )

            # Устанавливаем автора
            embed.set_author(
                name=user.display_name,
                icon_url=user.display_avatar.url
            )

            # Отправляем сообщение с пингом пользователя
            await stats_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка при отправке уведомления об ошибке: {e}")

    async def send_partnership_stats(self, user_id: str, server_name: str, points_earned: int, is_new: bool, renewed_count: int = 0):
        """Отправляет статистику партнерства в специальный канал"""
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)

            # Получаем канал
            stats_channel = self.bot.get_channel(self.stats_channel_id)
            if not stats_channel:
                return

            # Получаем пользователя
            user = self.bot.get_user(int(user_id))
            if not user:
                return

            # Получаем полную статистику ПМа
            pm_stats = await self.partnership_manager.get_manager_stats(user_id)

            # Определяем текст для обновления
            if is_new:
                update_text = t("partnership", "partner_stats_new", server_name=server_name)
                action_emoji = "🆕"
                action_text = t("partnership", "partner_stats_new_action")
            else:
                update_text = t("partnership", "partner_stats_renewed", server_name=server_name, count=renewed_count)
                action_emoji = "🔄"
                action_text = t("partnership", "partner_stats_renew_action")

            # Добавляем информацию о баллах к действию
            points_info = f"[+{points_earned}]" if points_earned > 0 else "[+0]"

            # Определяем слово "балл"
            if points_earned == 1:
                points_word = t("partnership", "partner_points_word_1")
            elif 2 <= points_earned <= 4:
                points_word = t("partnership", "partner_points_word_2")
            else:
                points_word = t("partnership", "partner_points_word_5")

            # Создаем эмбед
            embed = discord.Embed(
                description=(
                    f"{update_text}\n"
                    f"{t('partnership', 'partner_stats_points', user_name=user.display_name, points=points_earned, points_word=points_word, total=pm_stats['points'])}"
                ),
                color=0x000000  # Черный цвет
            )

            # Устанавливаем автора
            embed.set_author(
                name=user.display_name,
                icon_url=user.display_avatar.url
            )

            # Добавляем field со статистикой (одной строкой)
            embed.add_field(
                name=t("partnership", "partner_stats_header"),
                value=(
                    f"- {t('partnership', 'partner_stats_new_partners', count=pm_stats['new_partnerships'])}, "
                    f"{t('partnership', 'partner_stats_renewed_partners', count=pm_stats['renewed_partnerships'])}\n"
                    f"- {t('partnership', 'partner_stats_last_action', emoji=action_emoji, action=action_text, points_info=points_info)}"
                ),
                inline=False
            )

            await stats_channel.send(embed=embed)

        except Exception as e:
            print(f"Ошибка при отправке статистики: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Обрабатывает инвайт-ссылки в сообщениях"""
        # Проверки
        if message.author.bot or not message.guild or message.guild.id != config.SERVERS["MAIN_ID"]:
            return

        if message.channel.id != self.invite_channel_id:
            return

        # Ищем инвайт
        invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?discord\.(?:gg|io|com/invite)/([a-zA-Z0-9-]+)')
        invite_match = invite_pattern.search(message.content)

        if not invite_match:
            return

        invite_code = invite_match.group(1)

        invite_info = await self.partnership_manager.get_invite_info(invite_code)

        if not invite_info:
            # Не удалось получить информацию об инвайте
            try:
                await message.add_reaction("❌")
                await asyncio.sleep(5)
                await message.delete()
            except:
                pass
            return

        server_id = invite_info["server_id"]
        server_name = invite_info["server_name"]

        # Используем блокировку для сервера
        server_lock = await self.partnership_manager.processing_queue.acquire_server_lock(server_id)
        async with server_lock:
            user_id = str(message.author.id)
            user_lock = await self.partnership_manager.processing_queue.acquire_user_lock(user_id)
            async with user_lock:
                # Полная информация об инвайте для обработки
                full_invite_info = {
                    "server_id": server_id,
                    "server_name": server_name,
                    "invite_code": invite_code,
                    **invite_info
                }

                await self.process_invite(message, full_invite_info)

                # Удаление дубликатов асинхронно
                if not invite_info.get("from_db"):  # Удаляем только если это новый инвайт
                    asyncio.create_task(
                        self.delete_server_duplicates_async(server_id, server_name, message)
                    )

    async def delete_server_duplicates_async(self, server_id, server_name, current_message):
        """Асинхронно удаляет дубликаты инвайтов (оптимизированная версия)"""
        try:
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)

            # Ждем немного, чтобы основная обработка завершилась
            await asyncio.sleep(1)

            channel = current_message.channel
            deleted_count = 0
            invite_cache = {}  # Кеш для инвайтов

            # Ограничиваем историю последними 50 сообщениями для оптимизации
            async for msg in channel.history(limit=50):
                # Пропускаем текущее сообщение и сообщения ботов
                if msg.id == current_message.id or msg.author.bot:
                    continue

                # Ищем инвайт в сообщении
                invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?discord\.(?:gg|io|com/invite)/([a-zA-Z0-9-]+)')
                invite_match = invite_pattern.search(msg.content)

                if invite_match:
                    invite_code = invite_match.group(1)

                    # Проверяем кеш
                    if invite_code in invite_cache:
                        msg_server_id = invite_cache[invite_code]
                    else:
                        # Пробуем получить инвайт
                        try:
                            invite = await self.bot.fetch_invite(invite_code)
                            msg_server_id = str(invite.guild.id)
                            invite_cache[invite_code] = msg_server_id
                        except:
                            continue

                    # Если это тот же сервер, удаляем дубликат
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

        return deleted_count

    async def process_invite(self, message, invite_info):
        server_id = str(invite_info.get("server_id") or message.guild.id)
        server_name = invite_info.get("server_name", "Неизвестно")
        user_id = str(message.author.id)

        # Обрабатываем партнерство с новым менеджером
        result = await self.partnership_manager.process_partnership(
            server_id=server_id,
            server_name=server_name,
            invite_code=invite_info.get("invite_code", ""),
            manager_id=user_id
        )

        # Проверяем результат
        if result.get('error') == 'self_invite':
            # Self-invite - удаляем и отправляем уведомление в канал статистики
            try:
                await message.delete()
            except:
                pass

            # Отправляем уведомление в канал статистики
            await self.send_error_notification(
                user_id=user_id,
                server_name=server_name,
                reason="☠️☠️☠️☠️☠️"
            )
            return False

        elif result.get('error') == 'blacklisted':
            # Сервер в черном списке - добавляем реакцию крестик и удаляем сообщение через 5 секунд
            try:
                await message.add_reaction("❌")
                await asyncio.sleep(5)
                await message.delete()
            except:
                pass

            # Отправляем уведомление в канал статистики
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            await self.send_error_notification(
                user_id=user_id,
                server_name=server_name,
                reason=t("partnership", "partner_error_blacklisted")
            )
            return False

        elif result.get('error') and result.get('error') not in ['self_invite', 'blacklisted']:
            # Ошибка обработки - добавляем реакцию крестик и удаляем сообщение через 5 секунд
            try:
                await message.add_reaction("❌")
                await asyncio.sleep(5)
                await message.delete()
            except:
                pass

            # Отправляем уведомление в канал статистики
            t = _(guild_id=config.SERVERS["MAIN_ID"], bot=self.bot)
            await self.send_error_notification(
                user_id=user_id,
                server_name=server_name,
                reason=result.get('message', t("partnership", "partner_error_unknown"))
            )
            return False

        # Проверяем, если это обновление партнёрства, но прошло меньше 12 часов
        if result.get('success', False) and not result.get('is_new', False) and result.get('points', 0) == 0:
            # Обновление партнёрства меньше чем через 12 часов - показываем часики на 5 секунд
            try:
                await message.add_reaction("⏳")
                await asyncio.sleep(5)
                await message.remove_reaction("⏳", self.bot.user)
            except:
                pass
            return True

        # Успешная обработка — просто добавляем галочку к текущему сообщению (ничего не удаляем)
        try:
            # Добавляем галочку к текущему сообщению (оставляем все остальные реакции)
            await message.add_reaction("✅")
        except:
            pass

        # Отправляем статистику в канал (только для успешных партнерств)
        if result.get('success', False):  # Отправляем только для успешных партнерств
            # Получаем количество обновлений для сервера
            partnership = await self.partnership_manager.db.get_row("partnership", server_id=server_id)
            renewed_count = partnership.get("renewed_count", 0) if partnership else 0

            await self.send_partnership_stats(
                user_id=user_id,
                server_name=server_name,
                points_earned=result.get('points', 0),
                is_new=result.get('is_new', False),
                renewed_count=renewed_count
            )

        return True

    @commands.command(name="pmserver")
    async def pmserver(self, ctx, action: str = None, server: str = None):
        """Управление баном серверов для партнёрств"""
        t = _(ctx=ctx)

        if str(ctx.author.id) != self.creator_id:
            await ctx.reply(t("partnership", "partner_no_permission"))
            return

        # Используем BlacklistManager из нового менеджера
        blacklist = self.partnership_manager.blacklist

        if action == "list":
            # Получаем список серверов в черном списке
            blacklisted = await blacklist.get_blacklisted_servers()

            if not blacklisted:
                await ctx.reply(t("partnership", "partner_blacklist_empty"))
                return

            text = ""
            for server_info in blacklisted:
                text += f"- **{server_info['server_name']}** ``{server_info['server_id']}``\n"

            await ctx.reply(f"{t('partnership', 'partner_blacklist_title')}\n{text.strip()}")
            return

        if action not in ["add", "remove"] or not server:
            await ctx.reply(t("partnership", "partner_blacklist_usage"))
            return

        # Парсим ID сервера
        match = re.search(r'(\d{15,})', server)
        if match:
            server_id = match.group(1)
            server_name = None
        else:
            invite_pattern = re.compile(r'(?:https?://)?(?:www\.)?discord\.(?:gg|io|com/invite)/([a-zA-Z0-9-]+)')
            invite_match = invite_pattern.search(server)
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
            # Добавляем сервер в черный список
            success = await blacklist.add_to_blacklist(server_id, server_name)

            if success:
                final_name = server_name or await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"{Emoji.SUCCESS} {t('partnership', 'partner_blacklist_added', server_name=final_name, server_id=server_id)}")
            else:
                await ctx.reply(f"{Emojis.ERROR} {t('partnership', 'partner_blacklist_add_error')}")

        elif action == "remove":
            # Удаляем сервер из черного списка
            success = await blacklist.remove_from_blacklist(server_id)

            if success:
                server_name = await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"{Emoji.SUCCESS} {t('partnership', 'partner_blacklist_removed', server_name=server_name, server_id=server_id)}")
            else:
                await ctx.reply(f"{Emojis.ERROR} {t('partnership', 'partner_blacklist_not_found')}")

async def setup(bot):
    """Настройка расширения"""
    await bot.add_cog(Partnership(bot))
