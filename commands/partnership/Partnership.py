import asyncio, discord, re
from .PartnershipCore import PartnershipManager
from discord.ext import commands
from Niludetsu import Embed, config
from Niludetsu.database.supabase_database import database
from typing import Optional

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
                description=(
                    f"Ваше партнёрство с сервером **{server_name}** было отклонено.\n"
                    f"- Причина: {reason}"
                ),
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
                update_text = f"**{server_name}** был добавлен."
                action_emoji = "🆕"
                action_text = f"**1** новое партнерство"
            else:
                update_text = f"**{server_name}** был обновлён **{renewed_count}** раз."
                action_emoji = "🔄"
                action_text = f"**1** обновление партнерства"

            # Добавляем информацию о баллах к действию
            points_info = f"[+{points_earned}]" if points_earned > 0 else "[+0]"

            # Создаем эмбед
            embed = discord.Embed(
                description=(
                    f"{update_text}\n"
                    f"**{user.display_name}** получил **{points_earned}** {'балла' if points_earned == 2 else 'балл' if points_earned == 1 else 'баллов'}, "
                    f"всего у него **{pm_stats['points']}** баллов."
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
                name="> Статистика ПМа:",
                value=(
                    f"- 🆕 **{pm_stats['new_partnerships']}** новых партнерств, 🔄 **{pm_stats['renewed_partnerships']}** обновлений партнерств\n"
                    f"- Последнее действие: {action_emoji} {action_text} {points_info}"
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
                        f"🗑️ Удалено {deleted_count} дубликатов инвайтов для сервера **{server_name}** (ID: {server_id})"
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
            await self.send_error_notification(
                user_id=user_id,
                server_name=server_name,
                reason="сервер в чёрном списке."
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
            await self.send_error_notification(
                user_id=user_id,
                server_name=server_name,
                reason=result.get('message', 'Неизвестная ошибка')
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
        if str(ctx.author.id) != self.creator_id:
            await ctx.reply("У вас нет прав для использования этой команды.")
            return

        # Используем BlacklistManager из нового менеджера
        blacklist = self.partnership_manager.blacklist

        if action == "list":
            # Получаем список серверов в черном списке
            blacklisted = await blacklist.get_blacklisted_servers()

            if not blacklisted:
                await ctx.reply("Чёрный список пуст.")
                return

            text = ""
            for server_info in blacklisted:
                text += f"- **{server_info['server_name']}** ``{server_info['server_id']}``\n"

            await ctx.reply(f"**Чёрный список серверов:**\n{text.strip()}")
            return

        if action not in ["add", "remove"] or not server:
            await ctx.reply("Используй: !pmserver add <id/инвайт> или !pmserver remove <id/инвайт>")
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
                    await ctx.reply("Не удалось получить ID сервера по ссылке.")
                    return
            else:
                await ctx.reply("Укажи ID сервера или ссылку на инвайт.")
                return

        if action == "add":
            # Добавляем сервер в черный список
            success = await blacklist.add_to_blacklist(server_id, server_name)

            if success:
                final_name = server_name or await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"{Emoji.SUCCESS} Сервер **{final_name}** (`{server_id}`) добавлен в чёрный список.")
            else:
                await ctx.reply(f"{Emojis.ERROR} Не удалось добавить сервер в черный список.")

        elif action == "remove":
            # Удаляем сервер из черного списка
            success = await blacklist.remove_from_blacklist(server_id)

            if success:
                server_name = await blacklist.get_server_name(server_id) or server_id
                await ctx.reply(f"{Emoji.SUCCESS} Сервер **{server_name}** (`{server_id}`) удалён из чёрного списка.")
            else:
                await ctx.reply(f"{Emojis.ERROR} Сервер не найден в черном списке.")

async def setup(bot):
    """Настройка расширения"""
    await bot.add_cog(Partnership(bot))

