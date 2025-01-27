import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, EMOJIS
import traceback
import yaml
import datetime
import asyncio
import os
import io

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = "636570363605680139"
        self.log_channel = None
        self.invite_uses = {}
        bot.loop.create_task(self.initialize_logs())

    async def initialize_logs(self):
        """Инициализация канала логов с задержкой"""
        await self.bot.wait_until_ready()  # Ждем пока бот будет готов
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'logging' in config and 'main_channel' in config['logging']:
                    channel_id = int(config['logging']['main_channel'])
                    self.log_channel = self.bot.get_channel(channel_id)
                    if not self.log_channel:
                        print(f"❌ Канал логов не найден! ID: {channel_id}")
                        # Пробуем получить канал через fetch_channel
                        try:
                            self.log_channel = await self.bot.fetch_channel(channel_id)
                            print(f"✅ Канал логов успешно получен через fetch: {self.log_channel.name}")
                        except Exception as e:
                            print(f"❌ Не удалось получить канал через fetch: {e}")
                    else:
                        print(f"✅ Канал логов успешно установлен: {self.log_channel.name}")
                        # Отправляем тестовое сообщение
                        try:
                            await self.log_event(
                                title="✅ Система логирования активирована",
                                description="Канал логов успешно подключен и готов к работе."
                            )
                        except Exception as e:
                            print(f"❌ Ошибка при отправке тестового сообщения: {e}")
        except Exception as e:
            print(f"❌ Ошибка при инициализации логов: {e}")
            print(traceback.format_exc())

    def save_config(self, channel_id):
        """Сохранение конфигурации"""
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config['logging']['main_channel'] = str(channel_id)
            
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    async def get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        """Получает или создает вебхук для канала"""
        try:
            # Пытаемся найти существующий вебхук
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name='NiluBot Logs')
            
            # Если вебхук не найден, создаем новый
            if webhook is None:
                webhook = await channel.create_webhook(name='NiluBot Logs')
            
            return webhook
        except discord.Forbidden:
            print(f"❌ Нет прав для управления вебхуками в канале {channel.name}")
            return None

    async def log_event(self, title: str, description: str, file: discord.File = None, thumbnail_url: str = None, author: dict = None, footer: dict = None):
        """Отправляет сообщение в лог-канал"""
        if not self.log_channel:
            return

        embed = create_embed(title=title, description=description)
        
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
            
        if author:
            embed.set_author(**author)

        if footer:
            embed.set_footer(**footer)

        try:
            webhook = await self.get_webhook(self.log_channel)
            await webhook.send(embed=embed, file=file)
        except discord.HTTPException:
            pass

    @app_commands.command(name="logs", description="Показать текущий канал логов")
    @commands.has_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction):
        """Показывает информацию о текущем канале логов"""
        try:
            if self.log_channel:
                embed = create_embed(
                    title="📝 Информация о логах",
                    description=f"Текущий канал логов: {self.log_channel.mention}\n"
                              f"ID канала: `{self.log_channel.id}`"
                )
            else:
                embed = create_embed(
                    title="❌ Канал логов не настроен",
                    description="Проверьте настройки в файле config.json"
                )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка: {str(e)}"
            )

    async def log_error(self, error, command_name: str, author_mention: str, author_id: str, channel_mention: str):
        """Общий метод для логирования ошибок команд"""
        if self.log_channel:
            error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            await self.log_event(
                title="⚠️ Ошибка команды",
                description=f"{EMOJIS['DOT']} **Команда:** `{command_name}`\n"
                          f"{EMOJIS['DOT']} **Автор:** {author_mention} (`{author_id}`)\n"
                          f"{EMOJIS['DOT']} **Канал:** {channel_mention}\n"
                          f"{EMOJIS['DOT']} **Ошибка:**\n```py\n{error_trace[:1900]}```",
                author={'name': 'Command Error'}
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Логирование ошибок команд"""
        if self.log_channel:
            error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            
            if isinstance(ctx, discord.Interaction):
                command_name = f"/{ctx.command.parent.name if ctx.command.parent else ''}{' ' if ctx.command.parent else ''}{ctx.command.name}"
                author = ctx.user
            else:
                command_name = ctx.message.content
                author = ctx.author
                
            await self.log_event(
                title="⚠️ Ошибка команды",
                description=f"{EMOJIS['DOT']} **Команда:** `{command_name}`\n"
                          f"{EMOJIS['DOT']} **Автор:** {author.mention} (`{author.id}`)\n"
                          f"{EMOJIS['DOT']} **Канал:** {ctx.channel.mention}\n"
                          f"{EMOJIS['DOT']} **Ошибка:**\n```py\n{error_trace[:1900]}```",
                author={'name': 'Command Error'}
            )

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Перенаправление ошибок slash-команд в основной обработчик"""
        await self.on_command_error(interaction, error)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Логирование удаленных сообщений"""
        if not self.log_channel or not message.guild:
            return

        if message.author.bot and message.author != self.bot.user:
            return

        moderator = None
        try:
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                    moderator = entry.user
                    break
        except discord.Forbidden:
            pass

        await self.handle_message_event(
            message, 
            'delete',
            {'moderator': moderator} if moderator and moderator != message.author else None
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Логирование измененных сообщений"""
        if before.author.bot or before.content == after.content:
            return

        await self.handle_message_event(
            after, 
            'edit',
            {'before_content': before.content}
        )

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Логирование массового удаления сообщений"""
        if len(messages) < 2:
            return

        filtered_messages = [msg for msg in messages if not msg.author.bot or msg.author == self.bot.user]
        if not filtered_messages:
            return

        # Создаем текстовый файл
        content = [
            f"Удаленные сообщения из канала: #{filtered_messages[0].channel.name}",
            f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 50 + "\n"
        ]
        
        for message in sorted(filtered_messages, key=lambda m: m.created_at):
            content.append(f"[{message.created_at.strftime('%d/%m/%Y - %H:%M:%S')}] {message.author} ({message.author.id}): {message.content}")
            if message.attachments:
                content.append(f"Вложения: {', '.join([a.url for a in message.attachments])}")
            if message.embeds:
                content.append(f"Количество эмбедов: {len(message.embeds)}")
            content.append("")

        file = discord.File(
            io.BytesIO("\n".join(content).encode('utf-8')),
            filename=f"DeletedMessages_{datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.txt"
        )

        # Получаем информацию о модераторе
        moderator = None
        reason = None
        try:
            async for entry in filtered_messages[0].guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
                moderator = entry.user
                reason = entry.reason
                break
        except discord.Forbidden:
            pass

        await self.handle_message_event(
            filtered_messages[0],
            'bulk_delete',
            {
                'count': len(filtered_messages),
                'moderator': moderator.mention if moderator else 'Неизвестно',
                'reason': reason,
                'file': file
            }
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Логирование присоединения участников"""
        # Получаем информацию об инвайте
        invite_info = await self.get_invite_info(member)
        await self.handle_member_event(member, 'join', extra_data={'invite_info': invite_info})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Логирование выхода участников"""
        await self.handle_member_event(member, 'leave')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Логирование обновлений участников"""
        changes = []
        moderator = None
        reason = None
        
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        if before.nick != after.nick:
            changes.append(f"Никнейм: `{before.nick or 'Отсутствует'}` → `{after.nick or 'Отсутствует'}`")

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles:
                changes.append(f"Добавлены роли: {', '.join(role.mention for role in added_roles)}")
            if removed_roles:
                changes.append(f"Удалены роли: {', '.join(role.mention for role in removed_roles)}")

        if before.premium_since != after.premium_since:
            if after.premium_since:
                changes.append(f"Начал бустить сервер: <t:{int(after.premium_since.timestamp())}:F>")
            else:
                changes.append("Прекратил бустить сервер")

        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                await self.handle_member_event(after, 'timeout', extra_data={
                    'until': after.timed_out_until,
                    'moderator': moderator,
                    'reason': reason
                })
                return
            else:
                await self.handle_member_event(after, 'timeout_remove', extra_data={
                    'moderator': moderator,
                    'reason': reason
                })
                return

        if changes:
            await self.handle_member_event(after, 'update', extra_data={
                'changes': changes,
                'moderator': moderator,
                'reason': reason
            })

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Логирование банов"""
        moderator = None
        reason = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        await self.handle_member_event(user, 'ban', extra_data={
            'moderator': moderator,
            'reason': reason
        })

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Логирование разбанов"""
        moderator = None
        reason = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        await self.handle_member_event(user, 'unban', extra_data={
            'moderator': moderator,
            'reason': reason
        })

    async def handle_member_event(self, member, event_type: str, before=None, extra_data=None):
        """Общий обработчик событий участников"""
        if not self.log_channel:
            return

        title_map = {
            'join': '👋 Новый участник',
            'leave': '👋 Участник покинул сервер',
            'update': '👤 Участник обновлен',
            'ban': '🔨 Участник забанен',
            'unban': '🔓 Участник разбанен',
            'timeout': '⏰ Участник получил тайм-аут',
            'timeout_remove': '⏰ Тайм-аут снят'
        }

        description = []
        
        # Базовая информация об участнике
        description.append(f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)")
        description.append(f"{EMOJIS['DOT']} **Имя:** `{member.name}`")
        
        if event_type == 'join':
            # Информация о приглашении
            if extra_data and 'invite_info' in extra_data:
                description.append(f"\n**📨 Информация о приглашении:**\n{extra_data['invite_info']}")
            
            # Информация об аккаунте
            account_age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
            is_suspicious = account_age.days < 7
            
            description.append(f"\n**📅 Информация об аккаунте:**")
            description.extend([
                f"{EMOJIS['DOT']} **Аккаунт создан:** <t:{int(member.created_at.timestamp())}:F>",
                f"{EMOJIS['DOT']} **Возраст аккаунта:** `{account_age.days} дней`",
                f"{EMOJIS['DOT']} **Подозрительный:** `{'Да' if is_suspicious else 'Нет'}`",
                f"{EMOJIS['DOT']} **Бот:** `{'Да' if member.bot else 'Нет'}`",
                f"{EMOJIS['DOT']} **Система:** `{'Да' if member.system else 'Нет'}`",
                f"{EMOJIS['DOT']} **Флаги:** `{', '.join(flag.name for flag in member.public_flags.all()) or 'Нет'}`"
            ])
            
            # Информация о сервере
            description.append(f"\n**🌟 Информация о сервере:**")
            description.extend([
                f"{EMOJIS['DOT']} **Участник №:** `{member.guild.member_count}`",
                f"{EMOJIS['DOT']} **Присоединился:** <t:{int(member.joined_at.timestamp())}:F>"
            ])
            
        elif event_type == 'leave':
            description.extend([
                f"{EMOJIS['DOT']} **Присоединился:** <t:{int(member.joined_at.timestamp())}:F>",
                f"{EMOJIS['DOT']} **Пробыл на сервере:** `{(datetime.datetime.now(datetime.timezone.utc) - member.joined_at).days} дней`",
                f"{EMOJIS['DOT']} **Роли:** {', '.join(role.mention for role in member.roles[1:]) or 'Нет'}",
                f"{EMOJIS['DOT']} **Осталось участников:** `{member.guild.member_count}`"
            ])
            
        elif event_type == 'update':
            if extra_data and 'changes' in extra_data:
                description.append("\n**📝 Изменения:**")
                description.extend(extra_data['changes'])
            
            if extra_data and 'moderator' in extra_data:
                description.append(f"\n**👮 Модератор:**")
                description.append(f"{EMOJIS['DOT']} **Имя:** {extra_data['moderator'].mention}")
                if 'reason' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Причина:** `{extra_data['reason'] or 'Не указана'}`")
                    
        elif event_type in ['ban', 'unban']:
            if extra_data:
                if 'moderator' in extra_data:
                    description.append(f"\n**👮 Модератор:**")
                    description.append(f"{EMOJIS['DOT']} **Модератор:** {extra_data['moderator'].mention}")
                if 'reason' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Причина:** `{extra_data['reason'] or 'Не указана'}`")
                    
        elif event_type in ['timeout', 'timeout_remove']:
            if extra_data:
                if 'until' in extra_data:
                    duration = extra_data['until'] - datetime.datetime.now(datetime.timezone.utc)
                    duration_str = f"{duration.days} дней, {duration.seconds // 3600} часов, {(duration.seconds % 3600) // 60} минут"
                    description.extend([
                        f"{EMOJIS['DOT']} **Длительность:** `{duration_str}`",
                        f"{EMOJIS['DOT']} **До:** <t:{int(extra_data['until'].timestamp())}:F>"
                    ])
                if 'moderator' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Модератор:** {extra_data['moderator'].mention}")
                if 'reason' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Причина:** `{extra_data['reason'] or 'Не указана'}`")

        # Создаем автора для эмбеда если есть модератор
        author = None
        if extra_data and 'moderator' in extra_data and extra_data['moderator'].avatar:
            author = {
                'name': extra_data['moderator'].name,
                'icon_url': extra_data['moderator'].avatar.url
            }

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=member.avatar.url if member.avatar else None,
            author=author
        )

    @commands.Cog.listener()
    async def on_member_timeout(self, member, until):
        """Логирование тайм-аутов участников"""
        if not self.log_channel:
            return

        # Получаем информацию из аудит логов
        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        duration = until - datetime.datetime.now(datetime.timezone.utc)
        duration_str = f"{duration.days} дней, {duration.seconds // 3600} часов, {(duration.seconds % 3600) // 60} минут"

        embed = create_embed(
            title="⏰ Участник получил тайм-аут",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Длительность:** `{duration_str}`\n"
                      f"{EMOJIS['DOT']} **До:** <t:{int(until.timestamp())}:F>\n"
                      f"{EMOJIS['DOT']} **Модератор:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {member.id}"}
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_timeout_remove(self, member):
        """Логирование снятия тайм-аутов"""
        if not self.log_channel:
            return

        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        embed = create_embed(
            title="⏰ Тайм-аут снят",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Модератор:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {member.id}"}
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_nick_update(self, before, after):
        """Логирование изменений никнейма"""
        if not self.log_channel:
            return

        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        embed = create_embed(
            title="📝 Никнейм изменен",
            description=f"{EMOJIS['DOT']} **Участник:** {after.mention} (`{after.id}`)\n"
                      f"{EMOJIS['DOT']} **Старый никнейм:** `{before.display_name}`\n"
                      f"{EMOJIS['DOT']} **Новый никнейм:** `{after.display_name}`\n"
                      f"{EMOJIS['DOT']} **Модератор:** {moderator.mention if moderator else 'Сам пользователь'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {after.id}"}
        )
        if after.avatar:
            embed.set_thumbnail(url=after.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Логирование изменений пользователя"""
        if not self.log_channel:
            return

        changes = []
        if before.name != after.name:
            changes.append(f"Имя: `{before.name}` → `{after.name}`")
        if before.discriminator != after.discriminator:
            changes.append(f"Дискриминатор: `{before.discriminator}` → `{after.discriminator}`")
        if before.avatar != after.avatar:
            changes.append("Аватар изменен")
        if before.banner != after.banner:
            changes.append("Баннер изменен")

        if changes:
            description = (f"{EMOJIS['DOT']} **Пользователь:** {after.mention} (`{after.id}`)\n"
                         f"{EMOJIS['DOT']} **Изменения:**\n" + 
                         "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes))
            
            thumbnail_url = after.avatar.url if after.avatar else None
            
            await self.log_event(
                title="👤 Пользователь обновлен",
                description=description,
                thumbnail_url=thumbnail_url,
                footer={"text": f"ID: {after.id}"}
            )

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """Логирование изменений закрепленных сообщений"""
        if not self.log_channel:
            return

        try:
            pins = await channel.pins()
            pin_count = len(pins)
            latest_pin = pins[0] if pins else None
        except discord.Forbidden:
            pin_count = "Нет доступа"
            latest_pin = None

        embed = create_embed(
            title="📌 Закрепленные сообщения обновлены",
            description=f"{EMOJIS['DOT']} **Канал:** {channel.mention}\n"
                      f"{EMOJIS['DOT']} **Количество закрепленных:** `{pin_count}`\n"
                      f"{EMOJIS['DOT']} **Последнее обновление:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID канала: {channel.id}"}
        )

        if latest_pin:
            embed.add_field(
                name="📝 Последнее закрепленное сообщение",
                value=f"{EMOJIS['DOT']} **Автор:** {latest_pin.author.mention}\n"
                      f"{EMOJIS['DOT']} **Содержание:** ```\n{latest_pin.content[:1000]}```",
                inline=False
            )

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        """Логирование обновления интеграций сервера"""
        if not self.log_channel:
            return

        try:
            integrations = await guild.integrations()
            integration_list = "\n".join(f"{EMOJIS['DOT']} `{i.name}` ({i.type})" for i in integrations)
        except discord.Forbidden:
            integration_list = "Нет доступа к списку интеграций"

        embed = create_embed(
            title="🔄 Интеграции сервера обновлены",
            description=f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>\n"
                      f"{EMOJIS['DOT']} **Активные интеграции:**\n{integration_list}",
            footer={"text": f"ID сервера: {guild.id}"}
        )
        await self.log_event(embed)

    async def handle_message_event(self, message, event_type: str, extra_data=None):
        """Общий обработчик событий сообщений"""
        if not self.log_channel:
            return

        title_map = {
            'delete': '🗑️ Сообщение удалено',
            'bulk_delete': '🗑️ Сообщения удалены',
            'edit': '✏️ Сообщение изменено'
        }

        description = []
        
        # Базовая информация о сообщении
        description.extend([
            f"{EMOJIS['DOT']} **Автор:** {message.author.mention}",
            f"{EMOJIS['DOT']} **Канал:** {message.channel.mention}"
        ])

        # Информация о содержимом
        if event_type == 'delete':
            if message.content:
                description.append(f"\n**📝 Содержание:**\n{message.content}")
            
            if message.attachments:
                description.append("\n**📎 Вложения:**")
                for attachment in message.attachments:
                    description.append(f"{EMOJIS['DOT']} {attachment.filename}")
                    
        elif event_type == 'edit':
            before_content = extra_data.get('before', '')
            after_content = extra_data.get('after', '')
            
            if before_content != after_content:
                description.extend([
                    f"\n**До:**\n{before_content}",
                    f"\n**После:**\n{after_content}"
                ])

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            footer={"text": f"ID: {message.id}"}
        )

    async def handle_guild_event(self, guild, event_type: str, before=None, after=None, extra_data=None):
        """Общий обработчик событий сервера"""
        if not self.log_channel:
            return

        title_map = {
            'update': '⚙️ Сервер обновлен',
            'emojis': '😀 Эмодзи обновлены',
            'stickers': '🌟 Стикеры обновлены',
            'integrations': '🔄 Интеграции обновлены'
        }

        description = []
        
        if event_type == 'update' and before and after:
            changes = []
            
            # Основные изменения
            if before.name != after.name:
                changes.append(f"Название: `{before.name}` → `{after.name}`")
            if before.description != after.description:
                changes.append(f"Описание: `{before.description or 'Отсутствует'}` → `{after.description or 'Отсутствует'}`")
            if before.icon != after.icon:
                changes.append("Иконка изменена")
            if before.banner != after.banner:
                changes.append("Баннер изменен")
            if before.splash != after.splash:
                changes.append("Сплеш изменен")
            if before.discovery_splash != after.discovery_splash:
                changes.append("Сплеш дискавери изменен")
            if before.owner_id != after.owner_id:
                changes.append(f"Владелец: <@{before.owner_id}> → <@{after.owner_id}>")
            
            # Настройки безопасности
            if before.verification_level != after.verification_level:
                changes.append(f"Уровень верификации: `{before.verification_level}` → `{after.verification_level}`")
            if before.explicit_content_filter != after.explicit_content_filter:
                changes.append(f"Фильтр контента: `{before.explicit_content_filter}` → `{after.explicit_content_filter}`")
            if before.mfa_level != after.mfa_level:
                changes.append(f"Уровень 2FA: `{before.mfa_level}` → `{after.mfa_level}`")
            
            # Настройки уведомлений
            if before.default_notifications != after.default_notifications:
                changes.append(f"Уведомления по умолчанию: `{before.default_notifications}` → `{after.default_notifications}`")
            
            # Системные каналы
            if before.system_channel != after.system_channel:
                changes.append(f"Системный канал: {before.system_channel.mention if before.system_channel else 'Отсутствует'} → {after.system_channel.mention if after.system_channel else 'Отсутствует'}")
            if before.rules_channel != after.rules_channel:
                changes.append(f"Канал правил: {before.rules_channel.mention if before.rules_channel else 'Отсутствует'} → {after.rules_channel.mention if after.rules_channel else 'Отсутствует'}")
            
            if changes:
                description.append("**📝 Изменения:**")
                description.extend(f"{EMOJIS['DOT']} {change}" for change in changes)
                
                # Добавляем статистику
                description.extend([
                    f"\n**📊 Статистика сервера:**",
                    f"{EMOJIS['DOT']} **Участников:** `{after.member_count}`",
                    f"{EMOJIS['DOT']} **Каналов:** `{len(after.channels)}`",
                    f"{EMOJIS['DOT']} **Ролей:** `{len(after.roles)}`",
                    f"{EMOJIS['DOT']} **Эмодзи:** `{len(after.emojis)}`",
                    f"{EMOJIS['DOT']} **Стикеров:** `{len(after.stickers)}`",
                    f"{EMOJIS['DOT']} **Бустов:** `{after.premium_subscription_count}`"
                ])
                
        elif event_type == 'emojis':
            if extra_data:
                if 'added' in extra_data:
                    description.append("**✨ Добавленные эмодзи:**")
                    description.extend(f"{EMOJIS['DOT']} {emoji} `{emoji.name}`" for emoji in extra_data['added'])
                if 'removed' in extra_data:
                    description.append("\n**🗑️ Удаленные эмодзи:**")
                    description.extend(f"{EMOJIS['DOT']} `{emoji.name}`" for emoji in extra_data['removed'])
                    
        elif event_type == 'stickers':
            if extra_data:
                if 'added' in extra_data:
                    description.append("**✨ Добавленные стикеры:**")
                    description.extend(f"{EMOJIS['DOT']} `{sticker.name}`" for sticker in extra_data['added'])
                if 'removed' in extra_data:
                    description.append("\n**🗑️ Удаленные стикеры:**")
                    description.extend(f"{EMOJIS['DOT']} `{sticker.name}`" for sticker in extra_data['removed'])
                    
        elif event_type == 'integrations':
            if extra_data and 'integrations' in extra_data:
                description.extend([
                    f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
                    f"{EMOJIS['DOT']} **Активные интеграции:**\n{extra_data['integrations']}"
                ])

        # Получаем модератора из audit logs если возможно
        moderator = None
        reason = None
        if after:
            try:
                async for entry in after.audit_logs(limit=1):
                    moderator = entry.user
                    reason = entry.reason
                    break
            except discord.Forbidden:
                pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Создаем автора для эмбеда если есть модератор
        author = None
        if moderator and moderator.avatar:
            author = {
                'name': moderator.name,
                'icon_url': moderator.avatar.url
            }

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=after.icon.url if after and after.icon else None,
            author=author
        )

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Логирование изменений сервера"""
        await self.handle_guild_event(after, 'update', before, after)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Логирование изменений эмодзи"""
        new_emojis = [emoji for emoji in after if emoji not in before]
        removed_emojis = [emoji for emoji in before if emoji not in after]
        
        if new_emojis or removed_emojis:
            await self.handle_guild_event(guild, 'emojis', extra_data={
                'added': new_emojis,
                'removed': removed_emojis
            })

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        """Логирование изменений стикеров"""
        new_stickers = [sticker for sticker in after if sticker not in before]
        removed_stickers = [sticker for sticker in before if sticker not in after]
        
        if new_stickers or removed_stickers:
            await self.handle_guild_event(guild, 'stickers', extra_data={
                'added': new_stickers,
                'removed': removed_stickers
            })

    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        """Логирование обновления интеграций"""
        try:
            integrations = await guild.integrations()
            integration_list = "\n".join(f"{EMOJIS['DOT']} `{i.name}` ({i.type})" for i in integrations)
        except discord.Forbidden:
            integration_list = "Нет доступа к списку интеграций"
            
        await self.handle_guild_event(guild, 'integrations', extra_data={
            'integrations': integration_list
        })

    async def handle_channel_event(self, channel, event_type: str, before=None, after=None, extra_data=None):
        """Общий обработчик событий каналов"""
        if not self.log_channel:
            return

        title_map = {
            'create': '📝 Канал создан',
            'delete': '🗑️ Канал удален',
            'update': '📝 Канал обновлен',
            'pins': '📌 Закрепленные сообщения обновлены',
            'voice_status': '🎤 Статус голосового канала обновлен'
        }

        description = []
        
        # Базовая информация о канале
        if event_type != 'delete':
            description.extend([
                f"{EMOJIS['DOT']} **Канал:** {channel.mention}",
                f"{EMOJIS['DOT']} **Тип:** `{str(channel.type)}`",
                f"{EMOJIS['DOT']} **Категория:** `{channel.category.name if channel.category else 'Нет'}`"
            ])
        else:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{channel.name}`",
                f"{EMOJIS['DOT']} **Тип:** `{str(channel.type)}`",
                f"{EMOJIS['DOT']} **Категория:** `{channel.category.name if channel.category else 'Нет'}`"
            ])

        if event_type == 'update' and before and after:
            changes = []
            
            # Основные изменения
            if before.name != after.name:
                changes.append(f"Название: `{before.name}` → `{after.name}`")
            if before.position != after.position:
                changes.append(f"Позиция: `{before.position}` → `{after.position}`")
            if before.category != after.category:
                changes.append(f"Категория: `{before.category.name if before.category else 'Нет'}` → `{after.category.name if after.category else 'Нет'}`")
            
            # Изменения для текстовых каналов
            if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
                if before.topic != after.topic:
                    changes.append(f"Тема: `{before.topic or 'Нет'}` → `{after.topic or 'Нет'}`")
                if before.slowmode_delay != after.slowmode_delay:
                    changes.append(f"Медленный режим: `{before.slowmode_delay}с` → `{after.slowmode_delay}с`")
                if before.nsfw != after.nsfw:
                    changes.append(f"NSFW: `{'Да' if after.nsfw else 'Нет'}`")
                if hasattr(before, 'default_auto_archive_duration') and before.default_auto_archive_duration != after.default_auto_archive_duration:
                    changes.append(f"Время автоархивации: `{before.default_auto_archive_duration} минут` → `{after.default_auto_archive_duration} минут`")
                if hasattr(before, 'default_thread_slowmode_delay') and before.default_thread_slowmode_delay != after.default_thread_slowmode_delay:
                    changes.append(f"Медленный режим тредов: `{before.default_thread_slowmode_delay}с` → `{after.default_thread_slowmode_delay}с`")
            
            # Изменения для голосовых каналов
            if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
                if before.bitrate != after.bitrate:
                    changes.append(f"Битрейт: `{before.bitrate//1000}kbps` → `{after.bitrate//1000}kbps`")
                if before.user_limit != after.user_limit:
                    changes.append(f"Лимит пользователей: `{before.user_limit or 'Нет'}` → `{after.user_limit or 'Нет'}`")
                if before.rtc_region != after.rtc_region:
                    changes.append(f"Регион: `{before.rtc_region or 'Авто'}` → `{after.rtc_region or 'Авто'}`")
                if hasattr(before, 'video_quality_mode') and before.video_quality_mode != after.video_quality_mode:
                    changes.append(f"Качество видео: `{before.video_quality_mode}` → `{after.video_quality_mode}`")

            # Изменения для форумов
            if isinstance(before, discord.ForumChannel) and isinstance(after, discord.ForumChannel):
                if hasattr(before, 'available_tags') and before.available_tags != after.available_tags:
                    added_tags = [tag for tag in after.available_tags if tag not in before.available_tags]
                    removed_tags = [tag for tag in before.available_tags if tag not in after.available_tags]
                    if added_tags:
                        changes.append(f"Добавлены теги: `{', '.join(tag.name for tag in added_tags)}`")
                    if removed_tags:
                        changes.append(f"Удалены теги: `{', '.join(tag.name for tag in removed_tags)}`")
                
                if hasattr(before, 'default_reaction_emoji') and before.default_reaction_emoji != after.default_reaction_emoji:
                    changes.append(f"Эмодзи по умолчанию: `{before.default_reaction_emoji or 'Нет'}` → `{after.default_reaction_emoji or 'Нет'}`")
                
                if hasattr(before, 'default_sort_order') and before.default_sort_order != after.default_sort_order:
                    changes.append(f"Сортировка по умолчанию: `{before.default_sort_order}` → `{after.default_sort_order}`")
                
                if hasattr(before, 'default_layout') and before.default_layout != after.default_layout:
                    changes.append(f"Макет по умолчанию: `{before.default_layout}` → `{after.default_layout}`")

            # Изменения прав доступа
            if before.overwrites != after.overwrites:
                permission_changes = []
                for target, after_overwrite in after.overwrites.items():
                    before_overwrite = before.overwrites.get(target)
                    if before_overwrite != after_overwrite:
                        allow_changes = []
                        deny_changes = []
                        
                        # Проверяем измененные права
                        for perm, value in after_overwrite.pair():
                            before_allow, before_deny = before_overwrite.pair() if before_overwrite else (None, None)
                            if value != (before_allow.value if before_allow else 0):
                                if value:
                                    allow_changes.append(f"`{perm}`")
                                else:
                                    deny_changes.append(f"`{perm}`")
                        
                        if allow_changes or deny_changes:
                            permission_changes.append(f"\n**Изменения для {target.mention if hasattr(target, 'mention') else target.name}:**")
                            if allow_changes:
                                permission_changes.append(f"{EMOJIS['DOT']} **Разрешено:** {', '.join(allow_changes)}")
                            if deny_changes:
                                permission_changes.append(f"{EMOJIS['DOT']} **Запрещено:** {', '.join(deny_changes)}")
                
                if permission_changes:
                    changes.append("\n**🔒 Изменения прав доступа:**")
                    changes.extend(permission_changes)
            
            if changes:
                description.append("\n**📝 Изменения:**")
                description.extend(f"{EMOJIS['DOT']} {change}" for change in changes)

        elif event_type == 'pins':
            if extra_data:
                if 'count' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Количество закрепленных:** `{extra_data['count']}`")
                if 'last_pin' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Последнее закрепление:** <t:{int(extra_data['last_pin'].timestamp())}:F>")

        elif event_type == 'voice_status':
            if extra_data:
                if 'members' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Участники в канале:** {', '.join(member.mention for member in extra_data['members'])}")
                if 'status' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Статус:** `{extra_data['status']}`")

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.channel_create,
                'delete': discord.AuditLogAction.channel_delete,
                'update': discord.AuditLogAction.channel_update,
                'pins': discord.AuditLogAction.message_pin
            }.get(event_type)
            
            if action:
                async for entry in channel.guild.audit_logs(limit=1, action=action):
                    if entry.target.id == channel.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование изменений голосового статуса"""
        if not self.log_channel:
            return

        if before.channel != after.channel:
            if after.channel:
                status = f"присоединился к {after.channel.mention}"
                channel = after.channel
            elif before.channel:
                status = f"покинул {before.channel.name}"
                channel = before.channel
            else:
                return

            await self.handle_channel_event(
                channel,
                'voice_status',
                extra_data={
                    'status': status,
                    'members': channel.members
                }
            )

    async def handle_role_event(self, role, event_type: str, before=None, after=None):
        """Общий обработчик событий ролей"""
        if not self.log_channel:
            return

        title_map = {
            'create': '🎭 Роль создана',
            'delete': '🗑️ Роль удалена',
            'update': '📝 Роль обновлена',
            'position': '📊 Позиция роли изменена',
            'permissions': '🔒 Права роли изменены',
            'name': '✏️ Название роли изменено',
            'color': '🎨 Цвет роли изменен',
            'hoist': '📌 Отображение роли изменено',
            'mentionable': '💬 Упоминание роли изменено'
        }

        description = []
        
        # Базовая информация о роли
        description.extend([
            f"{EMOJIS['DOT']} **Роль:** {role.mention}",
            f"{EMOJIS['DOT']} **ID:** `{role.id}`"
        ])

        # Информация об изменениях
        if event_type == 'create':
            description.extend([
                f"{EMOJIS['DOT']} **Цвет:** `{str(role.color)}`",
                f"{EMOJIS['DOT']} **Позиция:** `{role.position}`",
                f"{EMOJIS['DOT']} **Отображается отдельно:** `{'Да' if role.hoist else 'Нет'}`",
                f"{EMOJIS['DOT']} **Можно упоминать:** `{'Да' if role.mentionable else 'Нет'}`"
            ])
            
        elif event_type == 'delete':
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{role.name}`",
                f"{EMOJIS['DOT']} **Цвет:** `{str(role.color)}`",
                f"{EMOJIS['DOT']} **Позиция:** `{role.position}`"
            ])
            
        elif event_type == 'update':
            if before.name != after.name:
                description.extend([
                    f"\n**📝 Название:**",
                    f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                    f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
                ])
                
            if before.color != after.color:
                description.extend([
                    f"\n**🎨 Цвет:**",
                    f"{EMOJIS['DOT']} **Старый:** `{str(before.color)}`",
                    f"{EMOJIS['DOT']} **Новый:** `{str(after.color)}`"
                ])
                
            if before.position != after.position:
                description.extend([
                    f"\n**📊 Позиция:**",
                    f"{EMOJIS['DOT']} **Старая:** `{before.position}`",
                    f"{EMOJIS['DOT']} **Новая:** `{after.position}`"
                ])
                
            if before.permissions != after.permissions:
                old_perms = set([perm[0] for perm in before.permissions if perm[1]])
                new_perms = set([perm[0] for perm in after.permissions if perm[1]])
                
                added_perms = new_perms - old_perms
                removed_perms = old_perms - new_perms
                
                if added_perms:
                    description.append(f"\n**✅ Добавленные права:**")
                    for perm in added_perms:
                        description.append(f"{EMOJIS['DOT']} `{perm}`")
                        
                if removed_perms:
                    description.append(f"\n**❌ Удаленные права:**")
                    for perm in removed_perms:
                        description.append(f"{EMOJIS['DOT']} `{perm}`")
                        
            if before.hoist != after.hoist:
                description.extend([
                    f"\n**📌 Отображение отдельно:**",
                    f"{EMOJIS['DOT']} **Старое:** `{'Да' if before.hoist else 'Нет'}`",
                    f"{EMOJIS['DOT']} **Новое:** `{'Да' if after.hoist else 'Нет'}`"
                ])
                
            if before.mentionable != after.mentionable:
                description.extend([
                    f"\n**💬 Возможность упоминания:**",
                    f"{EMOJIS['DOT']} **Старое:** `{'Да' if before.mentionable else 'Нет'}`",
                    f"{EMOJIS['DOT']} **Новое:** `{'Да' if after.mentionable else 'Нет'}`"
                ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.role_create,
                'delete': discord.AuditLogAction.role_delete,
                'update': discord.AuditLogAction.role_update
            }.get(event_type)
            
            if action:
                async for entry in role.guild.audit_logs(limit=1, action=action):
                    if entry.target.id == role.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Логирование создания роли"""
        await self.handle_role_event(role, 'create')

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Логирование удаления роли"""
        await self.handle_role_event(role, 'delete')

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Логирование обновления ролей"""
        # Проверяем, есть ли вообще какие-то изменения
        if (before.name != after.name or 
            before.color != after.color or 
            before.hoist != after.hoist or 
            before.mentionable != after.mentionable or 
            before.permissions != after.permissions or 
            (hasattr(before, 'icon') and hasattr(after, 'icon') and before.icon != after.icon)):
            await self.handle_role_event(after, 'update', before=before, after=after)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Логирование создания каналов"""
        await self.handle_channel_event(channel, 'create')

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Логирование удаления каналов"""
        await self.handle_channel_event(channel, 'delete')

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Логирование обновления каналов"""
        await self.handle_channel_event(after, 'update', before, after)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        try:
            pins = await channel.pins()
            await self.handle_channel_event(channel, 'pins', extra_data={
                'count': len(pins),
                'last_pin': last_pin
            })
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Логирование создания ролей"""
        await self.handle_role_event(role, 'create')

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Логирование удаления ролей"""
        await self.handle_role_event(role, 'delete')

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Логирование обновления ролей"""
        await self.handle_role_event(after, 'update', before, after)

    async def handle_application_event(self, guild, event_type: str, app=None, extra_data=None):
        """Общий обработчик событий приложений"""
        if not self.log_channel:
            return

        title_map = {
            'add': '📱 Приложение добавлено',
            'remove': '🗑️ Приложение удалено',
            'permission_update': '🔒 Права приложения обновлены'
        }

        description = []
        
        # Базовая информация о приложении
        if app:
            description.extend([
                f"{EMOJIS['DOT']} **Приложение:** `{app.name}`",
                f"{EMOJIS['DOT']} **ID:** `{app.id}`",
                f"{EMOJIS['DOT']} **Описание:** `{app.description or 'Нет описания'}`",
                f"{EMOJIS['DOT']} **Публичное:** `{'Да' if app.bot_public else 'Нет'}`",
                f"{EMOJIS['DOT']} **Требует OAuth2:** `{'Да' if app.require_code_grant else 'Нет'}`"
            ])

            # Добавляем информацию о владельце
            if hasattr(app, 'owner'):
                description.append(f"{EMOJIS['DOT']} **Владелец:** {app.owner.mention if isinstance(app.owner, discord.User) else app.owner}")

            # Добавляем информацию о тегах и кастомных URL
            if hasattr(app, 'tags') and app.tags:
                description.append(f"{EMOJIS['DOT']} **Теги:** `{', '.join(app.tags)}`")
            if hasattr(app, 'custom_install_url') and app.custom_install_url:
                description.append(f"{EMOJIS['DOT']} **URL установки:** `{app.custom_install_url}`")

        # Информация о правах (если это обновление прав)
        if event_type == 'permission_update' and extra_data:
            if 'permissions' in extra_data:
                description.append("\n**🔒 Обновленные права:**")
                for cmd, perms in extra_data['permissions'].items():
                    allowed = []
                    denied = []
                    for target, allowed_state in perms.items():
                        if allowed_state:
                            allowed.append(f"`{target}`")
                        else:
                            denied.append(f"`{target}`")
                    
                    description.append(f"\n{EMOJIS['DOT']} **Команда:** `{cmd}`")
                    if allowed:
                        description.append(f"{EMOJIS['DOT']} **Разрешено для:** {', '.join(allowed)}")
                    if denied:
                        description.append(f"{EMOJIS['DOT']} **Запрещено для:** {', '.join(denied)}")

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'add': discord.AuditLogAction.integration_create,
                'remove': discord.AuditLogAction.integration_delete,
                'permission_update': discord.AuditLogAction.application_command_permission_update
            }.get(event_type)
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if app and entry.target.id == app.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        # Создаем автора для эмбеда если есть модератор
        author = None
        if moderator and moderator.avatar:
            author = {
                'name': moderator.name,
                'icon_url': moderator.avatar.url
            }

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=app.icon.url if app and hasattr(app, 'icon') and app.icon else None,
            author=author
        )

    @commands.Cog.listener()
    async def on_application_command_permissions_update(self, app_command):
        """Логирование обновления прав команд приложения"""
        permissions = {}
        for perm in app_command.permissions:
            cmd_name = app_command.command.name if hasattr(app_command, 'command') else 'unknown'
            if cmd_name not in permissions:
                permissions[cmd_name] = {}
            
            target_name = perm.target.name if hasattr(perm.target, 'name') else str(perm.target.id)
            permissions[cmd_name][target_name] = perm.permission
        
        await self.handle_application_event(
            app_command.guild,
            'permission_update',
            extra_data={'permissions': permissions}
        )

    @commands.Cog.listener()
    async def on_integration_create(self, integration):
        """Логирование добавления приложения"""
        if isinstance(integration, discord.ApplicationIntegration):
            await self.handle_application_event(
                integration.guild,
                'add',
                app=integration.application
            )

    @commands.Cog.listener()
    async def on_integration_delete(self, integration):
        """Логирование удаления приложения"""
        if isinstance(integration, discord.ApplicationIntegration):
            await self.handle_application_event(
                integration.guild,
                'remove',
                app=integration.application
            )

    async def handle_automod_event(self, guild, event_type: str, rule=None, before=None, after=None, extra_data=None):
        """Общий обработчик событий AutoMod"""
        if not self.log_channel:
            return

        title_map = {
            'create': '🛡️ Правило AutoMod создано',
            'delete': '🗑️ Правило AutoMod удалено',
            'toggle': '🔄 Правило AutoMod переключено',
            'update_name': '📝 Название правила AutoMod изменено',
            'update_actions': '⚡ Действия правила AutoMod обновлены',
            'update_content': '📄 Содержание правила AutoMod обновлено',
            'update_roles': '👥 Роли правила AutoMod обновлены',
            'update_channels': '📺 Каналы правила AutoMod обновлены',
            'update_whitelist': '✅ Белый список правила AutoMod обновлен'
        }

        description = []
        
        # Базовая информация о правиле
        if rule:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{rule.name}`",
                f"{EMOJIS['DOT']} **ID:** `{rule.id}`",
                f"{EMOJIS['DOT']} **Создатель:** {rule.creator.mention if hasattr(rule, 'creator') else 'Неизвестно'}",
                f"{EMOJIS['DOT']} **Триггер:** `{rule.trigger_type}`",
                f"{EMOJIS['DOT']} **Включено:** `{'Да' if rule.enabled else 'Нет'}`",
                f"{EMOJIS['DOT']} **Событие:** `{rule.event_type if hasattr(rule, 'event_type') else 'Неизвестно'}`"
            ])

        # Информация об изменениях
        if event_type == 'toggle':
            if extra_data and 'enabled' in extra_data:
                description.append(f"\n**🔄 Статус:**")
                description.append(f"{EMOJIS['DOT']} **Состояние:** `{'Включено' if extra_data['enabled'] else 'Выключено'}`")

        elif event_type == 'update_name':
            if before and after:
                description.append(f"\n**📝 Изменение названия:**")
                description.extend([
                    f"{EMOJIS['DOT']} **Старое:** `{before}`",
                    f"{EMOJIS['DOT']} **Новое:** `{after}`"
                ])

        elif event_type == 'update_actions':
            if extra_data and 'actions' in extra_data:
                description.append(f"\n**⚡ Действия:**")
                for action in extra_data['actions']:
                    action_type = action.get('type', 'Неизвестно')
                    duration = action.get('duration', 'Постоянно')
                    channel_id = action.get('channel_id')
                    
                    action_desc = f"{EMOJIS['DOT']} **Тип:** `{action_type}`"
                    if duration != 'Постоянно':
                        action_desc += f"\n{EMOJIS['DOT']} **Длительность:** `{duration}`"
                    if channel_id:
                        channel = guild.get_channel(int(channel_id))
                        action_desc += f"\n{EMOJIS['DOT']} **Канал:** {channel.mention if channel else f'`{channel_id}`'}"
                    
                    description.append(action_desc)

        elif event_type == 'update_content':
            if extra_data and 'content' in extra_data:
                description.append(f"\n**📄 Содержание:**")
                if 'keywords' in extra_data['content']:
                    description.append(f"{EMOJIS['DOT']} **Ключевые слова:** `{', '.join(extra_data['content']['keywords'])}`")
                if 'patterns' in extra_data['content']:
                    description.append(f"{EMOJIS['DOT']} **Паттерны:** `{', '.join(extra_data['content']['patterns'])}`")
                if 'presets' in extra_data['content']:
                    description.append(f"{EMOJIS['DOT']} **Пресеты:** `{', '.join(extra_data['content']['presets'])}`")

        elif event_type in ['update_roles', 'update_channels']:
            if before and after:
                added = [x for x in after if x not in before]
                removed = [x for x in before if x not in after]
                
                if added:
                    description.append(f"\n**✨ Добавлено:**")
                    for item in added:
                        description.append(f"{EMOJIS['DOT']} {item.mention if hasattr(item, 'mention') else f'`{item}`'}")
                if removed:
                    description.append(f"\n**🗑️ Удалено:**")
                    for item in removed:
                        description.append(f"{EMOJIS['DOT']} {item.mention if hasattr(item, 'mention') else f'`{item}`'}")

        elif event_type == 'update_whitelist':
            if extra_data and 'whitelist' in extra_data:
                description.append(f"\n**✅ Белый список:**")
                if 'keywords' in extra_data['whitelist']:
                    description.append(f"{EMOJIS['DOT']} **Ключевые слова:** `{', '.join(extra_data['whitelist']['keywords'])}`")
                if 'regex' in extra_data['whitelist']:
                    description.append(f"{EMOJIS['DOT']} **Регулярные выражения:** `{', '.join(extra_data['whitelist']['regex'])}`")

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.automod_rule_create,
                'delete': discord.AuditLogAction.automod_rule_delete,
                'update': discord.AuditLogAction.automod_rule_update
            }.get(event_type.split('_')[0], discord.AuditLogAction.automod_rule_update)
            
            async for entry in guild.audit_logs(limit=1, action=action):
                if rule and entry.target.id == rule.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=rule.icon.url if rule and rule.icon else None
        )

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule):
        """Логирование создания правила AutoMod"""
        await self.handle_automod_event(rule.guild, 'create', rule=rule)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule):
        """Логирование удаления правила AutoMod"""
        await self.handle_automod_event(rule.guild, 'delete', rule=rule)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, before, after):
        """Логирование обновления правила AutoMod"""
        # Определяем тип изменения
        if before.enabled != after.enabled:
            await self.handle_automod_event(after.guild, 'toggle', rule=after, extra_data={'enabled': after.enabled})
            
        if before.name != after.name:
            await self.handle_automod_event(after.guild, 'update_name', rule=after, before=before.name, after=after.name)
            
        if before.actions != after.actions:
            await self.handle_automod_event(after.guild, 'update_actions', rule=after, extra_data={'actions': after.actions})
            
        if before.trigger_metadata != after.trigger_metadata:
            await self.handle_automod_event(after.guild, 'update_content', rule=after, extra_data={'content': after.trigger_metadata})
            
        if before.exempt_roles != after.exempt_roles:
            await self.handle_automod_event(after.guild, 'update_roles', rule=after, before=before.exempt_roles, after=after.exempt_roles)
            
        if before.exempt_channels != after.exempt_channels:
            await self.handle_automod_event(after.guild, 'update_channels', rule=after, before=before.exempt_channels, after=after.exempt_channels)
            
        if hasattr(before, 'whitelist') and hasattr(after, 'whitelist') and before.whitelist != after.whitelist:
            await self.handle_automod_event(after.guild, 'update_whitelist', rule=after, extra_data={'whitelist': after.whitelist})

    async def handle_emoji_event(self, guild, event_type: str, emoji=None, before=None, after=None, extra_data=None):
        """Общий обработчик событий эмодзи"""
        if not self.log_channel:
            return

        title_map = {
            'create': '😀 Эмодзи создан',
            'delete': '🗑️ Эмодзи удален',
            'update_name': '📝 Название эмодзи изменено',
            'update_roles': '👥 Роли эмодзи обновлены'
        }

        description = []
        
        # Базовая информация об эмодзи
        if emoji:
            description.extend([
                f"{EMOJIS['DOT']} **Эмодзи:** {emoji if event_type != 'delete' else '`Удален`'}",
                f"{EMOJIS['DOT']} **Название:** `{emoji.name}`",
                f"{EMOJIS['DOT']} **ID:** `{emoji.id}`",
                f"{EMOJIS['DOT']} **Анимированный:** `{'Да' if emoji.animated else 'Нет'}`"
            ])

        # Информация об изменениях
        if event_type == 'update_name' and before and after:
            description.append(f"\n**📝 Изменение названия:**")
            description.extend([
                f"{EMOJIS['DOT']} **Старое:** `{before}`",
                f"{EMOJIS['DOT']} **Новое:** `{after}`"
            ])

        elif event_type == 'update_roles':
            if extra_data and 'roles' in extra_data:
                added_roles = extra_data['roles'].get('added', [])
                removed_roles = extra_data['roles'].get('removed', [])
                
                if added_roles:
                    description.append(f"\n**✨ Добавленные роли:**")
                    for role in added_roles:
                        description.append(f"{EMOJIS['DOT']} {role.mention}")
                
                if removed_roles:
                    description.append(f"\n**🗑️ Удаленные роли:**")
                    for role in removed_roles:
                        description.append(f"{EMOJIS['DOT']} {role.mention}")

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.emoji_create,
                'delete': discord.AuditLogAction.emoji_delete,
                'update_name': discord.AuditLogAction.emoji_update,
                'update_roles': discord.AuditLogAction.emoji_update
            }.get(event_type)
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if emoji and entry.target.id == emoji.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=emoji.url if emoji and event_type != 'delete' else None
        )

    @commands.Cog.listener()
    async def on_guild_emoji_create(self, emoji):
        """Логирование создания эмодзи"""
        await self.handle_emoji_event(emoji.guild, 'create', emoji=emoji)

    @commands.Cog.listener()
    async def on_guild_emoji_delete(self, emoji):
        """Логирование удаления эмодзи"""
        await self.handle_emoji_event(emoji.guild, 'delete', emoji=emoji)

    @commands.Cog.listener()
    async def on_guild_emoji_update(self, before, after):
        """Логирование обновления эмодзи"""
        if before.name != after.name:
            await self.handle_emoji_event(after.guild, 'update_name', emoji=after, before=before.name, after=after.name)
        
        if before.roles != after.roles:
            await self.handle_emoji_event(
                after.guild,
                'update_roles',
                emoji=after,
                extra_data={
                    'roles': {
                        'added': [role for role in after.roles if role not in before.roles],
                        'removed': [role for role in before.roles if role not in after.roles]
                    }
                }
            )

    @commands.Cog.listener()
    async def on_guild_scheduled_event_create(self, event):
        """Логирование создания события"""
        await self.handle_scheduled_event(event.guild, 'create', event=event)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(self, event):
        """Логирование удаления события"""
        await self.handle_scheduled_event(event.guild, 'delete', event=event)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(self, before, after):
        """Логирование обновления события"""
        if before.location != after.location:
            await self.handle_scheduled_event(after.guild, 'update_location', event=after, before=before, after=after)
        
        if before.description != after.description:
            await self.handle_scheduled_event(after.guild, 'update_description', event=after, before=before, after=after)
        
        if before.name != after.name:
            await self.handle_scheduled_event(after.guild, 'update_name', event=after, before=before, after=after)
        
        if before.privacy_level != after.privacy_level:
            await self.handle_scheduled_event(after.guild, 'update_privacy', event=after, before=before, after=after)
        
        if before.start_time != after.start_time:
            await self.handle_scheduled_event(after.guild, 'update_start', event=after, before=before, after=after)
        
        if before.end_time != after.end_time:
            await self.handle_scheduled_event(after.guild, 'update_end', event=after, before=before, after=after)
        
        if before.status != after.status:
            await self.handle_scheduled_event(after.guild, 'update_status', event=after, before=before, after=after)
        
        if before.image != after.image:
            await self.handle_scheduled_event(after.guild, 'update_image', event=after, before=before, after=after)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_user_add(self, event, user):
        """Логирование присоединения пользователя к событию"""
        await self.handle_scheduled_event(event.guild, 'user_add', event=event, extra_data={'user': user})

    @commands.Cog.listener()
    async def on_guild_scheduled_event_user_remove(self, event, user):
        """Логирование выхода пользователя из события"""
        await self.handle_scheduled_event(event.guild, 'user_remove', event=event, extra_data={'user': user})

    async def handle_scheduled_event(self, guild, event_type: str, event=None, before=None, after=None, extra_data=None):
        """Общий обработчик запланированных событий"""
        if not self.log_channel:
            return

        title_map = {
            'create': '📅 Событие создано',
            'delete': '🗑️ Событие удалено',
            'update_location': '📍 Локация события изменена',
            'update_description': '📝 Описание события изменено',
            'update_name': '📝 Название события изменено',
            'update_privacy': '🔒 Приватность сцены изменена',
            'update_start': '⏰ Время начала события изменено',
            'update_end': '⏰ Время окончания события изменено',
            'update_status': '📊 Статус события изменен',
            'update_image': '🖼️ Изображение события изменено',
            'user_add': '👤 Пользователь присоединился к событию',
            'user_remove': '👤 Пользователь покинул событие'
        }

        description = []
        
        # Базовая информация о событии
        if event:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{event.name}`",
                f"{EMOJIS['DOT']} **ID:** `{event.id}`",
                f"{EMOJIS['DOT']} **Создатель:** {event.creator.mention if event.creator else 'Неизвестно'}",
                f"{EMOJIS['DOT']} **Тип:** `{event.entity_type}`",
                f"{EMOJIS['DOT']} **Статус:** `{event.status}`",
                f"{EMOJIS['DOT']} **Начало:** <t:{int(event.start_time.timestamp())}:F>",
                f"{EMOJIS['DOT']} **Конец:** {f'<t:{int(event.end_time.timestamp())}:F>' if event.end_time else 'Не указано'}"
            ])

            if event.description:
                description.append(f"{EMOJIS['DOT']} **Описание:** `{event.description}`")

            location = event.location if isinstance(event.location, str) else "Нет"
            if event.channel:
                location = event.channel.mention
            description.append(f"{EMOJIS['DOT']} **Локация:** {location}")

        # Информация об изменениях
        if event_type.startswith('update_'):
            if before and after:
                if event_type == 'update_location':
                    old_loc = before.location if isinstance(before.location, str) else (before.channel.mention if before.channel else "Нет")
                    new_loc = after.location if isinstance(after.location, str) else (after.channel.mention if after.channel else "Нет")
                    description.append(f"\n**📍 Изменение локации:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старая:** {old_loc}",
                        f"{EMOJIS['DOT']} **Новая:** {new_loc}"
                    ])
                
                elif event_type == 'update_description':
                    description.append(f"\n**📝 Изменение описания:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старое:** `{before.description or 'Нет'}`",
                        f"{EMOJIS['DOT']} **Новое:** `{after.description or 'Нет'}`"
                    ])
                
                elif event_type == 'update_name':
                    description.append(f"\n**📝 Изменение названия:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                        f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
                    ])
                
                elif event_type == 'update_privacy':
                    description.append(f"\n**🔒 Изменение приватности:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старая:** `{before.privacy_level}`",
                        f"{EMOJIS['DOT']} **Новая:** `{after.privacy_level}`"
                    ])
                
                elif event_type == 'update_start':
                    description.append(f"\n**⏰ Изменение времени начала:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старое:** <t:{int(before.start_time.timestamp())}:F>",
                        f"{EMOJIS['DOT']} **Новое:** <t:{int(after.start_time.timestamp())}:F>"
                    ])
                
                elif event_type == 'update_end':
                    description.append(f"\n**⏰ Изменение времени окончания:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старое:** {f'<t:{int(before.end_time.timestamp())}:F>' if before.end_time else 'Не указано'}",
                        f"{EMOJIS['DOT']} **Новое:** {f'<t:{int(after.end_time.timestamp())}:F>' if after.end_time else 'Не указано'}"
                    ])
                
                elif event_type == 'update_status':
                    description.append(f"\n**📊 Изменение статуса:**")
                    description.extend([
                        f"{EMOJIS['DOT']} **Старый:** `{before.status}`",
                        f"{EMOJIS['DOT']} **Новый:** `{after.status}`"
                    ])

        elif event_type in ['user_add', 'user_remove'] and extra_data and 'user' in extra_data:
            user = extra_data['user']
            description.extend([
                f"\n**👤 Информация о пользователе:**",
                f"{EMOJIS['DOT']} **Пользователь:** {user.mention}",
                f"{EMOJIS['DOT']} **ID:** `{user.id}`"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.guild_scheduled_event_create,
                'delete': discord.AuditLogAction.guild_scheduled_event_delete,
                'update': discord.AuditLogAction.guild_scheduled_event_update
            }.get(event_type.split('_')[0], discord.AuditLogAction.guild_scheduled_event_update)
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if event and entry.target.id == event.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=event.image.url if event and event.image else None
        )

    async def handle_invite_event(self, guild, event_type: str, invite=None, extra_data=None):
        """Общий обработчик событий приглашений"""
        if not self.log_channel:
            return

        title_map = {
            'create': '📨 Приглашение создано',
            'delete': '🗑️ Приглашение удалено',
            'post': '📝 Приглашение опубликовано'
        }

        description = []
        
        # Базовая информация о приглашении
        if invite:
            description.extend([
                f"{EMOJIS['DOT']} **Код:** `{invite.code}`",
                f"{EMOJIS['DOT']} **Создатель:** {invite.inviter.mention if invite.inviter else 'Неизвестно'}",
                f"{EMOJIS['DOT']} **Канал:** {invite.channel.mention}",
                f"{EMOJIS['DOT']} **Максимум использований:** `{invite.max_uses or 'Не ограничено'}`",
                f"{EMOJIS['DOT']} **Срок действия:** `{invite.max_age or 'Не ограничено'} секунд`",
                f"{EMOJIS['DOT']} **Временное:** `{'Да' if invite.temporary else 'Нет'}`"
            ])

            if hasattr(invite, 'uses'):
                description.append(f"{EMOJIS['DOT']} **Использований:** `{invite.uses}`")

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.invite_create,
                'delete': discord.AuditLogAction.invite_delete
            }.get(event_type)
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if invite and entry.target.code == invite.code:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    async def handle_poll_event(self, guild, event_type: str, poll=None, extra_data=None):
        """Общий обработчик событий опросов"""
        if not self.log_channel:
            return

        title_map = {
            'create': '📊 Опрос создан',
            'delete': '🗑️ Опрос удален',
            'finalize': '✅ Опрос завершен',
            'vote_add': '👍 Голос добавлен',
            'vote_remove': '👎 Голос удален'
        }

        description = []
        
        # Базовая информация об опросе
        if poll:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{poll.question}`",
                f"{EMOJIS['DOT']} **Создатель:** {poll.author.mention}",
                f"{EMOJIS['DOT']} **Канал:** {poll.channel.mention}"
            ])

            if hasattr(poll, 'options'):
                description.append("\n**📋 Варианты ответов:**")
                for i, option in enumerate(poll.options, 1):
                    description.append(f"{EMOJIS['DOT']} **{i}.** `{option}`")

            if hasattr(poll, 'votes') and poll.votes:
                description.append("\n**📊 Результаты:**")
                for option, votes in poll.votes.items():
                    description.append(f"{EMOJIS['DOT']} `{option}`: **{len(votes)}** голосов")

        # Информация о голосовании
        if event_type in ['vote_add', 'vote_remove'] and extra_data:
            if 'user' in extra_data:
                description.extend([
                    f"\n**👤 Информация о голосе:**",
                    f"{EMOJIS['DOT']} **Пользователь:** {extra_data['user'].mention}",
                    f"{EMOJIS['DOT']} **Выбор:** `{extra_data.get('choice', 'Неизвестно')}`"
                ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.message_pin,
                'delete': discord.AuditLogAction.message_unpin
            }.get(event_type)
            
            if action and poll:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if entry.target.id == poll.message.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    async def handle_stage_event(self, guild, event_type: str, stage=None, before=None, after=None):
        """Общий обработчик событий сцены"""
        if not self.log_channel:
            return

        title_map = {
            'start': '🎭 Сцена открыта',
            'end': '🎭 Сцена закрыта',
            'topic_update': '📝 Тема сцены изменена',
            'privacy_update': '🔒 Приватность сцены изменена'
        }

        description = []
        
        # Базовая информация о сцене
        if stage:
            description.extend([
                f"{EMOJIS['DOT']} **Канал:** {stage.channel.mention}",
                f"{EMOJIS['DOT']} **Тема:** `{stage.topic or 'Не указана'}`",
                f"{EMOJIS['DOT']} **Приватность:** `{stage.privacy_level}`"
            ])

            if hasattr(stage, 'speakers') and stage.speakers:
                description.append("\n**🎤 Спикеры:**")
                for speaker in stage.speakers:
                    description.append(f"{EMOJIS['DOT']} {speaker.mention}")

            if hasattr(stage, 'listeners') and stage.listeners:
                description.append(f"\n**👥 Слушателей:** `{len(stage.listeners)}`")

        # Информация об изменениях
        if event_type == 'topic_update' and before and after:
            description.extend([
                f"\n**📝 Изменение темы:**",
                f"{EMOJIS['DOT']} **Старая:** `{before.topic or 'Нет'}`",
                f"{EMOJIS['DOT']} **Новая:** `{after.topic or 'Нет'}`"
            ])
            
        elif event_type == 'privacy_update' and before and after:
            description.extend([
                f"\n**🔒 Изменение приватности:**",
                f"{EMOJIS['DOT']} **Старая:** `{before.privacy_level}`",
                f"{EMOJIS['DOT']} **Новая:** `{after.privacy_level}`"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'start': discord.AuditLogAction.stage_instance_create,
                'end': discord.AuditLogAction.stage_instance_delete,
                'update': discord.AuditLogAction.stage_instance_update
            }.get(event_type.split('_')[0])
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if stage and entry.target.id == stage.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Логирование создания приглашения"""
        await self.handle_invite_event(invite.guild, 'create', invite=invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Логирование удаления приглашения"""
        await self.handle_invite_event(invite.guild, 'delete', invite=invite)

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage):
        """Логирование создания сцены"""
        await self.handle_stage_event(stage.guild, 'start', stage=stage)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage):
        """Логирование удаления сцены"""
        await self.handle_stage_event(stage.guild, 'end', stage=stage)

    @commands.Cog.listener()
    async def on_stage_instance_update(self, before, after):
        """Логирование обновления сцены"""
        if before.topic != after.topic:
            await self.handle_stage_event(after.guild, 'topic_update', stage=after, before=before, after=after)
            
        if before.privacy_level != after.privacy_level:
            await self.handle_stage_event(after.guild, 'privacy_update', stage=after, before=before, after=after)

    async def handle_sticker_event(self, guild, event_type: str, sticker=None, before=None, after=None):
        """Общий обработчик событий стикеров"""
        if not self.log_channel:
            return

        title_map = {
            'create': '🌟 Стикер создан',
            'delete': '🗑️ Стикер удален',
            'update_name': '📝 Название стикера изменено',
            'update_description': '📝 Описание стикера изменено',
            'update_emoji': '😀 Связанный эмодзи стикера изменен'
        }

        description = []
        
        # Базовая информация о стикере
        if sticker:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{sticker.name}`",
                f"{EMOJIS['DOT']} **ID:** `{sticker.id}`",
                f"{EMOJIS['DOT']} **Описание:** `{sticker.description or 'Нет'}`",
                f"{EMOJIS['DOT']} **Формат:** `{sticker.format}`",
                f"{EMOJIS['DOT']} **Связанный эмодзи:** {sticker.emoji if hasattr(sticker, 'emoji') else 'Нет'}"
            ])

        # Информация об изменениях
        if event_type == 'update_name' and before and after:
            description.extend([
                f"\n**📝 Изменение названия:**",
                f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
            ])
            
        elif event_type == 'update_description' and before and after:
            description.extend([
                f"\n**📝 Изменение описания:**",
                f"{EMOJIS['DOT']} **Старое:** `{before.description or 'Нет'}`",
                f"{EMOJIS['DOT']} **Новое:** `{after.description or 'Нет'}`"
            ])
            
        elif event_type == 'update_emoji' and before and after:
            description.extend([
                f"\n**😀 Изменение связанного эмодзи:**",
                f"{EMOJIS['DOT']} **Старый:** {before.emoji if hasattr(before, 'emoji') else 'Нет'}",
                f"{EMOJIS['DOT']} **Новый:** {after.emoji if hasattr(after, 'emoji') else 'Нет'}"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.sticker_create,
                'delete': discord.AuditLogAction.sticker_delete,
                'update': discord.AuditLogAction.sticker_update
            }.get(event_type.split('_')[0])
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if sticker and entry.target.id == sticker.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=sticker.url if sticker else None
        )

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker):
        """Логирование создания стикера"""
        await self.handle_sticker_event(sticker.guild, 'create', sticker=sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker):
        """Логирование удаления стикера"""
        await self.handle_sticker_event(sticker.guild, 'delete', sticker=sticker)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before, after):
        """Логирование обновления стикера"""
        if before.name != after.name:
            await self.handle_sticker_event(after.guild, 'update_name', sticker=after, before=before, after=after)
            
        if before.description != after.description:
            await self.handle_sticker_event(after.guild, 'update_description', sticker=after, before=before, after=after)
            
        if hasattr(before, 'emoji') and hasattr(after, 'emoji') and before.emoji != after.emoji:
            await self.handle_sticker_event(after.guild, 'update_emoji', sticker=after, before=before, after=after)

    async def handle_server_event(self, guild, event_type: str, before=None, after=None, extra_data=None):
        """Общий обработчик событий сервера"""
        if not self.log_channel:
            return

        title_map = {
            'ban_add': '🔨 Участник забанен',
            'ban_remove': '🔓 Участник разбанен',
            'member_join': '👋 Участник присоединился',
            'member_leave': '👋 Участник покинул сервер',
            'member_kick': '👢 Участник кикнут',
            'member_prune': '🧹 Очистка участников',
            'afk_channel_update': '💤 Канал AFK изменен',
            'afk_timeout_update': '⏰ Тайм-аут AFK изменен',
            'banner_update': '🖼️ Баннер сервера изменен',
            'notification_update': '🔔 Настройки уведомлений изменены',
            'discovery_splash_update': '🌟 Сплеш дискавери изменен',
            'content_filter_update': '🔞 Уровень фильтра контента изменен',
            'features_update': '✨ Функции сервера обновлены',
            'icon_update': '🖼️ Иконка сервера изменена',
            'mfa_update': '🔒 Уровень MFA изменен',
            'name_update': '📝 Название сервера изменено',
            'description_update': '📝 Описание сервера изменено',
            'owner_update': '👑 Владелец сервера изменен',
            'partner_update': '🤝 Статус партнерства изменен',
            'boost_level_update': '⭐ Уровень буста изменен',
            'boost_bar_update': '📊 Отображение прогресса бустов изменено',
            'public_updates_channel_update': '📢 Канал публичных обновлений изменен',
            'rules_channel_update': '📜 Канал правил изменен',
            'splash_update': '🖼️ Сплеш сервера изменен',
            'system_channel_update': '⚙️ Системный канал изменен',
            'vanity_update': '🔗 Ванити URL изменен',
            'verification_update': '✅ Уровень верификации изменен',
            'verified_update': '✓ Статус верификации изменен',
            'widget_update': '🔧 Виджет сервера изменен',
            'locale_update': '🌐 Основной язык сервера изменен',
            'onboarding_toggle': '🎯 Онбординг переключен',
            'onboarding_channels_update': '📺 Каналы онбординга обновлены',
            'onboarding_question_add': '❓ Вопрос онбординга добавлен',
            'onboarding_question_remove': '❌ Вопрос онбординга удален',
            'onboarding_question_update': '📝 Вопрос онбординга обновлен'
        }

        description = []
        
        # Базовая информация о сервере
        description.extend([
            f"{EMOJIS['DOT']} **Сервер:** `{guild.name}`",
            f"{EMOJIS['DOT']} **ID:** `{guild.id}`"
        ])

        # Информация об изменениях
        if event_type.endswith('_update') and before and after:
            if event_type == 'name_update':
                description.extend([
                    f"\n**📝 Изменение названия:**",
                    f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                    f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
                ])
                
            elif event_type == 'description_update':
                description.extend([
                    f"\n**📝 Изменение описания:**",
                    f"{EMOJIS['DOT']} **Старое:** `{before.description or 'Нет'}`",
                    f"{EMOJIS['DOT']} **Новое:** `{after.description or 'Нет'}`"
                ])
                
            elif event_type == 'owner_update':
                description.extend([
                    f"\n**👑 Изменение владельца:**",
                    f"{EMOJIS['DOT']} **Старый:** {before.owner.mention}",
                    f"{EMOJIS['DOT']} **Новый:** {after.owner.mention}"
                ])
                
            elif event_type == 'verification_update':
                description.extend([
                    f"\n**✅ Изменение уровня верификации:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.verification_level}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.verification_level}`"
                ])
                
            elif event_type == 'content_filter_update':
                description.extend([
                    f"\n**🔞 Изменение фильтра контента:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.explicit_content_filter}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.explicit_content_filter}`"
                ])
                
            elif event_type == 'system_channel_update':
                description.extend([
                    f"\n**⚙️ Изменение системного канала:**",
                    f"{EMOJIS['DOT']} **Старый:** {before.system_channel.mention if before.system_channel else 'Нет'}",
                    f"{EMOJIS['DOT']} **Новый:** {after.system_channel.mention if after.system_channel else 'Нет'}"
                ])
                
            elif event_type == 'rules_channel_update':
                description.extend([
                    f"\n**📜 Изменение канала правил:**",
                    f"{EMOJIS['DOT']} **Старый:** {before.rules_channel.mention if before.rules_channel else 'Нет'}",
                    f"{EMOJIS['DOT']} **Новый:** {after.rules_channel.mention if after.rules_channel else 'Нет'}"
                ])
                
            elif event_type == 'afk_channel_update':
                description.extend([
                    f"\n**💤 Изменение AFK канала:**",
                    f"{EMOJIS['DOT']} **Старый:** {before.afk_channel.mention if before.afk_channel else 'Нет'}",
                    f"{EMOJIS['DOT']} **Новый:** {after.afk_channel.mention if after.afk_channel else 'Нет'}"
                ])
                
            elif event_type == 'afk_timeout_update':
                description.extend([
                    f"\n**⏰ Изменение тайм-аута AFK:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.afk_timeout} секунд`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.afk_timeout} секунд`"
                ])
                
            elif event_type == 'mfa_update':
                description.extend([
                    f"\n**🔒 Изменение уровня MFA:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.mfa_level}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.mfa_level}`"
                ])
                
            elif event_type == 'notification_update':
                description.extend([
                    f"\n**🔔 Изменение настроек уведомлений:**",
                    f"{EMOJIS['DOT']} **Старые:** `{before.default_notifications}`",
                    f"{EMOJIS['DOT']} **Новые:** `{after.default_notifications}`"
                ])
                
            elif event_type == 'vanity_update':
                description.extend([
                    f"\n**🔗 Изменение ванити URL:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.vanity_url_code or 'Нет'}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.vanity_url_code or 'Нет'}`"
                ])
                
            elif event_type == 'features_update':
                added_features = [f for f in after.features if f not in before.features]
                removed_features = [f for f in before.features if f not in after.features]
                
                if added_features:
                    description.append(f"\n**✨ Добавленные функции:**")
                    description.extend(f"{EMOJIS['DOT']} `{feature}`" for feature in added_features)
                if removed_features:
                    description.append(f"\n**🗑️ Удаленные функции:**")
                    description.extend(f"{EMOJIS['DOT']} `{feature}`" for feature in removed_features)
                    
            elif event_type == 'boost_level_update':
                description.extend([
                    f"\n**⭐ Изменение уровня буста:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.premium_tier}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.premium_tier}`"
                ])
                
            elif event_type == 'locale_update':
                description.extend([
                    f"\n**🌐 Изменение основного языка:**",
                    f"{EMOJIS['DOT']} **Старый:** `{before.preferred_locale}`",
                    f"{EMOJIS['DOT']} **Новый:** `{after.preferred_locale}`"
                ])

        # Информация о пруне
        elif event_type == 'member_prune' and extra_data:
            if 'pruned' in extra_data:
                description.extend([
                    f"\n**🧹 Информация об очистке:**",
                    f"{EMOJIS['DOT']} **Удалено участников:** `{extra_data['pruned']}`",
                    f"{EMOJIS['DOT']} **Дней неактивности:** `{extra_data.get('days', 'Неизвестно')}`"
                ])

        # Информация об онбординге
        elif event_type.startswith('onboarding_'):
            if extra_data:
                if 'enabled' in extra_data:
                    description.append(f"{EMOJIS['DOT']} **Статус:** `{'Включен' if extra_data['enabled'] else 'Выключен'}`")
                if 'channels' in extra_data:
                    description.append(f"\n**📺 Каналы:**")
                    for channel in extra_data['channels']:
                        description.append(f"{EMOJIS['DOT']} {channel.mention}")
                if 'question' in extra_data:
                    description.extend([
                        f"\n**❓ Информация о вопросе:**",
                        f"{EMOJIS['DOT']} **Текст:** `{extra_data['question']}`"
                    ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'ban_add': discord.AuditLogAction.ban,
                'ban_remove': discord.AuditLogAction.unban,
                'member_kick': discord.AuditLogAction.kick,
                'member_prune': discord.AuditLogAction.member_prune,
                'update': discord.AuditLogAction.guild_update
            }.get(event_type.split('_')[0])
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=guild.icon.url if guild.icon else None
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Логирование бана участника"""
        await self.handle_server_event(guild, 'ban_add', extra_data={'user': user})

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Логирование разбана участника"""
        await self.handle_server_event(guild, 'ban_remove', extra_data={'user': user})

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Логирование присоединения участника"""
        await self.handle_server_event(member.guild, 'member_join', extra_data={'member': member})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Логирование выхода участника"""
        await self.handle_server_event(member.guild, 'member_leave', extra_data={'member': member})

    @commands.Cog.listener()
    async def on_member_prune(self, guild, members):
        """Логирование очистки участников"""
        await self.handle_server_event(guild, 'member_prune', extra_data={'pruned': len(members)})

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Логирование обновлений сервера"""
        if before.name != after.name:
            await self.handle_server_event(after, 'name_update', before=before, after=after)
            
        if before.description != after.description:
            await self.handle_server_event(after, 'description_update', before=before, after=after)
            
        if before.owner_id != after.owner_id:
            await self.handle_server_event(after, 'owner_update', before=before, after=after)
            
        if before.verification_level != after.verification_level:
            await self.handle_server_event(after, 'verification_update', before=before, after=after)
            
        if before.explicit_content_filter != after.explicit_content_filter:
            await self.handle_server_event(after, 'content_filter_update', before=before, after=after)
            
        if before.system_channel != after.system_channel:
            await self.handle_server_event(after, 'system_channel_update', before=before, after=after)
            
        if before.rules_channel != after.rules_channel:
            await self.handle_server_event(after, 'rules_channel_update', before=before, after=after)
            
        if before.afk_channel != after.afk_channel:
            await self.handle_server_event(after, 'afk_channel_update', before=before, after=after)
            
        if before.afk_timeout != after.afk_timeout:
            await self.handle_server_event(after, 'afk_timeout_update', before=before, after=after)
            
        if before.mfa_level != after.mfa_level:
            await self.handle_server_event(after, 'mfa_update', before=before, after=after)
            
        if before.default_notifications != after.default_notifications:
            await self.handle_server_event(after, 'notification_update', before=before, after=after)
            
        if before.vanity_url_code != after.vanity_url_code:
            await self.handle_server_event(after, 'vanity_update', before=before, after=after)
            
        if before.features != after.features:
            await self.handle_server_event(after, 'features_update', before=before, after=after)
            
        if before.premium_tier != after.premium_tier:
            await self.handle_server_event(after, 'boost_level_update', before=before, after=after)
            
        if before.preferred_locale != after.preferred_locale:
            await self.handle_server_event(after, 'locale_update', before=before, after=after)
            
        if before.icon != after.icon:
            await self.handle_server_event(after, 'icon_update')
            
        if before.banner != after.banner:
            await self.handle_server_event(after, 'banner_update')
            
        if before.splash != after.splash:
            await self.handle_server_event(after, 'splash_update')
            
        if before.discovery_splash != after.discovery_splash:
            await self.handle_server_event(after, 'discovery_splash_update')

    async def handle_soundboard_event(self, guild, event_type: str, sound=None, before=None, after=None):
        """Общий обработчик событий звуковой панели"""
        if not self.log_channel:
            return

        title_map = {
            'upload': '🎵 Звук добавлен',
            'delete': '🗑️ Звук удален',
            'update_name': '📝 Название звука изменено',
            'update_volume': '🔊 Громкость звука изменена',
            'update_emoji': '😀 Эмодзи звука изменен'
        }

        description = []
        
        # Базовая информация о звуке
        if sound:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{sound.name}`",
                f"{EMOJIS['DOT']} **ID:** `{sound.id}`",
                f"{EMOJIS['DOT']} **Громкость:** `{sound.volume}%`",
                f"{EMOJIS['DOT']} **Эмодзи:** {sound.emoji if hasattr(sound, 'emoji') else 'Нет'}"
            ])

        # Информация об изменениях
        if event_type == 'update_name' and before and after:
            description.extend([
                f"\n**📝 Изменение названия:**",
                f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
            ])
            
        elif event_type == 'update_volume' and before and after:
            description.extend([
                f"\n**🔊 Изменение громкости:**",
                f"{EMOJIS['DOT']} **Старая:** `{before.volume}%`",
                f"{EMOJIS['DOT']} **Новая:** `{after.volume}%`"
            ])
            
        elif event_type == 'update_emoji' and before and after:
            description.extend([
                f"\n**😀 Изменение эмодзи:**",
                f"{EMOJIS['DOT']} **Старый:** {before.emoji if hasattr(before, 'emoji') else 'Нет'}",
                f"{EMOJIS['DOT']} **Новый:** {after.emoji if hasattr(after, 'emoji') else 'Нет'}"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = discord.AuditLogAction.soundboard_sound_update
            async for entry in guild.audit_logs(limit=1, action=action):
                if sound and entry.target.id == sound.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    async def handle_thread_event(self, thread, event_type: str, before=None, after=None):
        """Общий обработчик событий тредов"""
        if not self.log_channel:
            return

        title_map = {
            'create': '🧵 Тред создан',
            'delete': '🗑️ Тред удален',
            'update_name': '📝 Название треда изменено',
            'update_slowmode': '⏰ Медленный режим треда изменен',
            'update_archive_duration': '📅 Длительность архивации изменена',
            'archive': '📦 Тред архивирован',
            'unarchive': '📂 Тред разархивирован',
            'lock': '🔒 Тред заблокирован',
            'unlock': '🔓 Тред разблокирован'
        }

        description = []
        
        # Базовая информация о треде
        if thread:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{thread.name}`",
                f"{EMOJIS['DOT']} **ID:** `{thread.id}`",
                f"{EMOJIS['DOT']} **Родительский канал:** {thread.parent.mention if thread.parent else 'Неизвестно'}",
                f"{EMOJIS['DOT']} **Создатель:** {thread.owner.mention if thread.owner else 'Неизвестно'}",
                f"{EMOJIS['DOT']} **Медленный режим:** `{thread.slowmode_delay}с`",
                f"{EMOJIS['DOT']} **Архивация через:** `{thread.auto_archive_duration} минут`",
                f"{EMOJIS['DOT']} **Заблокирован:** `{'Да' if thread.locked else 'Нет'}`",
                f"{EMOJIS['DOT']} **Архивирован:** `{'Да' if thread.archived else 'Нет'}`"
            ])

        # Информация об изменениях
        if event_type == 'update_name' and before and after:
            description.extend([
                f"\n**📝 Изменение названия:**",
                f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
            ])
            
        elif event_type == 'update_slowmode' and before and after:
            description.extend([
                f"\n**⏰ Изменение медленного режима:**",
                f"{EMOJIS['DOT']} **Старый:** `{before.slowmode_delay}с`",
                f"{EMOJIS['DOT']} **Новый:** `{after.slowmode_delay}с`"
            ])
            
        elif event_type == 'update_archive_duration' and before and after:
            description.extend([
                f"\n**📅 Изменение длительности архивации:**",
                f"{EMOJIS['DOT']} **Старая:** `{before.auto_archive_duration} минут`",
                f"{EMOJIS['DOT']} **Новая:** `{after.auto_archive_duration} минут`"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.thread_create,
                'delete': discord.AuditLogAction.thread_delete,
                'update': discord.AuditLogAction.thread_update,
                'archive': discord.AuditLogAction.thread_update,
                'unarchive': discord.AuditLogAction.thread_update,
                'lock': discord.AuditLogAction.thread_update,
                'unlock': discord.AuditLogAction.thread_update
            }.get(event_type.split('_')[0])
            
            if action:
                async for entry in thread.guild.audit_logs(limit=1, action=action):
                    if entry.target.id == thread.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    @commands.Cog.listener()
    async def on_soundboard_sound_create(self, sound):
        """Логирование добавления звука"""
        await self.handle_soundboard_event(sound.guild, 'upload', sound=sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        """Логирование удаления звука"""
        await self.handle_soundboard_event(sound.guild, 'delete', sound=sound)

    @commands.Cog.listener()
    async def on_soundboard_sound_update(self, before, after):
        """Логирование обновления звука"""
        if before.name != after.name:
            await self.handle_soundboard_event(after.guild, 'update_name', sound=after, before=before, after=after)
            
        if before.volume != after.volume:
            await self.handle_soundboard_event(after.guild, 'update_volume', sound=after, before=before, after=after)
            
        if hasattr(before, 'emoji') and hasattr(after, 'emoji') and before.emoji != after.emoji:
            await self.handle_soundboard_event(after.guild, 'update_emoji', sound=after, before=before, after=after)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """Логирование создания треда"""
        await self.handle_thread_event(thread, 'create')

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        """Логирование удаления треда"""
        await self.handle_thread_event(thread, 'delete')

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        """Логирование обновления треда"""
        if before.name != after.name:
            await self.handle_thread_event(after, 'update_name', before=before, after=after)
            
        if before.slowmode_delay != after.slowmode_delay:
            await self.handle_thread_event(after, 'update_slowmode', before=before, after=after)
            
        if before.auto_archive_duration != after.auto_archive_duration:
            await self.handle_thread_event(after, 'update_archive_duration', before=before, after=after)
            
        if not before.archived and after.archived:
            await self.handle_thread_event(after, 'archive')
            
        if before.archived and not after.archived:
            await self.handle_thread_event(after, 'unarchive')
            
        if not before.locked and after.locked:
            await self.handle_thread_event(after, 'lock')
            
        if before.locked and not after.locked:
            await self.handle_thread_event(after, 'unlock')

    async def handle_voice_event(self, guild, event_type: str, member=None, before=None, after=None, extra_data=None):
        """Общий обработчик голосовых событий"""
        if not self.log_channel:
            return

        title_map = {
            'join': '🎙️ Пользователь присоединился к голосовому каналу',
            'leave': '🎙️ Пользователь покинул голосовой канал',
            'switch': '🔄 Пользователь переключил голосовой канал',
            'move': '➡️ Пользователь перемещен в другой канал',
            'kick': '👢 Пользователь кикнут из голосового канала',
            'full': '⚠️ Голосовой канал заполнен'
        }

        description = []
        
        # Базовая информация о пользователе
        if member:
            description.extend([
                f"{EMOJIS['DOT']} **Пользователь:** {member.mention}",
                f"{EMOJIS['DOT']} **ID:** `{member.id}`"
            ])

        # Информация о каналах
        if event_type == 'join':
            description.append(f"{EMOJIS['DOT']} **Канал:** {after.channel.mention}")
            
        elif event_type == 'leave':
            description.append(f"{EMOJIS['DOT']} **Канал:** {before.channel.mention}")
            
        elif event_type in ['switch', 'move']:
            description.extend([
                f"{EMOJIS['DOT']} **Из канала:** {before.channel.mention}",
                f"{EMOJIS['DOT']} **В канал:** {after.channel.mention}"
            ])
            
        elif event_type == 'kick':
            description.append(f"{EMOJIS['DOT']} **Канал:** {before.channel.mention}")
            
        elif event_type == 'full':
            if extra_data and 'channel' in extra_data:
                channel = extra_data['channel']
                description.extend([
                    f"{EMOJIS['DOT']} **Канал:** {channel.mention}",
                    f"{EMOJIS['DOT']} **Лимит:** `{channel.user_limit}`",
                    f"{EMOJIS['DOT']} **Текущее количество:** `{len(channel.members)}`"
                ])

        # Получаем модератора из audit logs для перемещений и киков
        moderator = None
        reason = None
        if event_type in ['move', 'kick']:
            try:
                action = discord.AuditLogAction.member_move if event_type == 'move' else discord.AuditLogAction.member_disconnect
                async for entry in guild.audit_logs(limit=1, action=action):
                    if entry.target.id == member.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
            except discord.Forbidden:
                pass

            if moderator:
                description.append(f"\n**👮 Модератор:**")
                description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
                if reason:
                    description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description)
        )

    async def handle_webhook_event(self, guild, event_type: str, webhook=None, before=None, after=None):
        """Общий обработчик событий вебхуков"""
        if not self.log_channel:
            return

        title_map = {
            'create': '🔗 Вебхук создан',
            'delete': '🗑️ Вебхук удален',
            'update_name': '📝 Название вебхука изменено',
            'update_avatar': '🖼️ Аватар вебхука изменен',
            'update_channel': '📺 Канал вебхука изменен'
        }

        description = []
        
        # Базовая информация о вебхуке
        if webhook:
            description.extend([
                f"{EMOJIS['DOT']} **Название:** `{webhook.name}`",
                f"{EMOJIS['DOT']} **ID:** `{webhook.id}`",
                f"{EMOJIS['DOT']} **Канал:** {webhook.channel.mention}",
                f"{EMOJIS['DOT']} **Создатель:** {webhook.user.mention if webhook.user else 'Неизвестно'}"
            ])

        # Информация об изменениях
        if event_type == 'update_name' and before and after:
            description.extend([
                f"\n**📝 Изменение названия:**",
                f"{EMOJIS['DOT']} **Старое:** `{before.name}`",
                f"{EMOJIS['DOT']} **Новое:** `{after.name}`"
            ])
            
        elif event_type == 'update_avatar':
            description.append(f"\n**🖼️ Аватар вебхука был изменен**")
            
        elif event_type == 'update_channel' and before and after:
            description.extend([
                f"\n**📺 Изменение канала:**",
                f"{EMOJIS['DOT']} **Старый:** {before.channel.mention}",
                f"{EMOJIS['DOT']} **Новый:** {after.channel.mention}"
            ])

        # Получаем модератора из audit logs
        moderator = None
        reason = None
        try:
            action = {
                'create': discord.AuditLogAction.webhook_create,
                'delete': discord.AuditLogAction.webhook_delete,
                'update': discord.AuditLogAction.webhook_update
            }.get(event_type.split('_')[0])
            
            if action:
                async for entry in guild.audit_logs(limit=1, action=action):
                    if webhook and entry.target.id == webhook.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
        except discord.Forbidden:
            pass

        if moderator:
            description.append(f"\n**👮 Модератор:**")
            description.append(f"{EMOJIS['DOT']} **Имя:** {moderator.mention}")
            if reason:
                description.append(f"{EMOJIS['DOT']} **Причина:** `{reason}`")

        # Добавляем время события
        description.append(f"\n{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>")

        await self.log_event(
            title=title_map[event_type],
            description="\n".join(description),
            thumbnail_url=webhook.avatar.url if webhook and webhook.avatar else None
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование изменений голосового состояния"""
        if not before.channel and after.channel:
            await self.handle_voice_event(member.guild, 'join', member=member, after=after)
            
        elif before.channel and not after.channel:
            await self.handle_voice_event(member.guild, 'leave', member=member, before=before)
            
        elif before.channel and after.channel and before.channel != after.channel:
            # Проверяем, было ли это перемещением модератором
            try:
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_move):
                    if entry.target.id == member.id:
                        await self.handle_voice_event(member.guild, 'move', member=member, before=before, after=after)
                        return
            except discord.Forbidden:
                pass
            
            await self.handle_voice_event(member.guild, 'switch', member=member, before=before, after=after)
            
        # Проверяем кик из голосового канала
        if before.channel and not after.channel:
            try:
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    if entry.target.id == member.id:
                        await self.handle_voice_event(member.guild, 'kick', member=member, before=before)
                        break
            except discord.Forbidden:
                pass
            
        # Проверяем заполнение канала
        if after.channel and len(after.channel.members) >= after.channel.user_limit > 0:
            await self.handle_voice_event(
                member.guild,
                'full',
                extra_data={'channel': after.channel}
            )

    @commands.Cog.listener()
    async def on_webhook_create(self, webhook):
        """Логирование создания вебхука"""
        await self.handle_webhook_event(webhook.guild, 'create', webhook=webhook)

    @commands.Cog.listener()
    async def on_webhook_delete(self, webhook):
        """Логирование удаления вебхука"""
        await self.handle_webhook_event(webhook.guild, 'delete', webhook=webhook)

    @commands.Cog.listener()
    async def on_webhook_update(self, before, after):
        """Логирование обновления вебхука"""
        if before.name != after.name:
            await self.handle_webhook_event(after.guild, 'update_name', webhook=after, before=before, after=after)
            
        if before.avatar != after.avatar:
            await self.handle_webhook_event(after.guild, 'update_avatar', webhook=after)
            
        if before.channel != after.channel:
            await self.handle_webhook_event(after.guild, 'update_channel', webhook=after, before=before, after=after)

async def setup(bot):
    await bot.add_cog(Logs(bot)) 