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
        bot.loop.create_task(self.track_invite_uses())

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
                            embed = create_embed(
                                title="✅ Система логирования активирована",
                                description="Канал логов успешно подключен и готов к работе.",
                                footer={"text": f"ID канала: {self.log_channel.id}"}
                            )
                            await self.log_event(embed)
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

    async def log_event(self, embed, file: discord.File = None):
        """Отправка лога через вебхук"""
        if not self.log_channel:
            await self.initialize_logs()
            return
            
        if not embed:
            print("❌ Эмбед не был передан")
            return
            
        try:
            # Проверяем, что эмбед является инстансом discord.Embed
            if not isinstance(embed, discord.Embed):
                print("❌ Переданный объект не является discord.Embed")
                return
                
            # Проверяем обязательные поля эмбеда
            if not hasattr(embed, 'title') and not hasattr(embed, 'description'):
                print("❌ У эмбеда отсутствуют обязательные поля (title или description)")
                return
                
            webhook = await self.get_webhook(self.log_channel)
            
            try:
                if webhook:
                    if file:
                        # Создаем новый файл для каждой отправки
                        new_file = discord.File(
                            io.BytesIO(file.fp.read()),
                            filename=file.filename,
                            description=file.description,
                            spoiler=file.spoiler
                        )
                        file.fp.seek(0)  # Сбрасываем позицию чтения для возможного повторного использования
                        await webhook.send(embed=embed, file=new_file)
                    else:
                        await webhook.send(embed=embed)
                else:
                    # Если не удалось получить вебхук, отправляем обычным способом
                    await self.log_channel.send(embed=embed, file=file)
            except discord.HTTPException as e:
                print(f"❌ Ошибка отправки через вебхук: {e}")
                # Пробуем отправить через обычный канал
                await self.log_channel.send(embed=embed, file=file)
                
        except Exception as e:
            print(f"❌ Ошибка отправки лога: {str(e)}")
            if hasattr(e, '__traceback__'):
                print(''.join(traceback.format_tb(e.__traceback__)))

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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Логирование ошибок команд"""
        if self.log_channel:
            error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            embed = create_embed(
                title="⚠️ Ошибка команды",
                description=f"{EMOJIS['DOT']} **Команда:** `{ctx.message.content}`\n"
                          f"{EMOJIS['DOT']} **Автор:** {ctx.author.mention} (`{ctx.author.id}`)\n"
                          f"{EMOJIS['DOT']} **Канал:** {ctx.channel.mention}\n"
                          f"{EMOJIS['DOT']} **Ошибка:**\n```py\n{error_trace[:1900]}```"
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Логирование удаленных сообщений"""
        if message.author.bot:
            return

        embed = create_embed(
            title="🗑️ Сообщение удалено",
            description=f"{EMOJIS['DOT']} **Автор:** {message.author.mention} (`{message.author.id}`)\n"
                      f"{EMOJIS['DOT']} **Канал:** {message.channel.mention}\n"
                      f"{EMOJIS['DOT']} **Содержание:**\n```\n{message.content[:1900]}```",
            footer={"text": f"ID сообщения: {message.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Логирование измененных сообщений"""
        if before.author.bot or before.content == after.content:
            return

        embed = create_embed(
            title="✏️ Сообщение изменено",
            description=f"{EMOJIS['DOT']} **Автор:** {before.author.mention} (`{before.author.id}`)\n"
                      f"{EMOJIS['DOT']} **Канал:** {before.channel.mention}\n"
                      f"{EMOJIS['DOT']} **До:**\n```\n{before.content[:900]}```\n"
                      f"{EMOJIS['DOT']} **После:**\n```\n{after.content[:900]}```",
            footer={"text": f"ID сообщения: {before.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Расширенное логирование присоединения участников с отслеживанием инвайтов"""
        if not self.log_channel:
            return

        # Получаем информацию об инвайте
        invite_info = "Не удалось определить приглашение"
        used_invite = None
        inviter = None

        try:
            # Получаем текущие приглашения
            current_invites = {invite.code: invite.uses async for invite in member.guild.invites()}
            
            # Сравниваем с предыдущими использованиями
            if member.guild.id in self.invite_uses:
                for code, old_data in self.invite_uses[member.guild.id].items():
                    if code in current_invites:
                        if current_invites[code] > old_data['uses']:
                            used_invite = code
                            inviter = old_data['inviter']
                            channel = old_data['channel']
                            created_at = old_data['created_at']
                            
                            invite_info = (
                                f"{EMOJIS['DOT']} **Код приглашения:** `{code}`\n"
                                f"{EMOJIS['DOT']} **Пригласил:** {inviter.mention} (`{inviter.id}`)\n"
                                f"{EMOJIS['DOT']} **Канал:** {channel.mention}\n"
                                f"{EMOJIS['DOT']} **Создано:** <t:{int(created_at.timestamp())}:F>\n"
                                f"{EMOJIS['DOT']} **Временное:** `{'Да' if old_data['temporary'] else 'Нет'}`\n"
                                f"{EMOJIS['DOT']} **Использований:** `{current_invites[code]}/{old_data['max_uses'] if old_data['max_uses'] else '∞'}`\n"
                            )
                            break

            # Обновляем отслеживание
            await self.track_invite_uses()

        except discord.Forbidden:
            pass

        # Проверяем на подозрительные аккаунты
        account_age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
        is_suspicious = account_age.days < 7

        # Собираем информацию об аккаунте
        account_info = (
            f"{EMOJIS['DOT']} **Аккаунт создан:** <t:{int(member.created_at.timestamp())}:F>\n"
            f"{EMOJIS['DOT']} **Возраст аккаунта:** `{account_age.days} дней`\n"
            f"{EMOJIS['DOT']} **Подозрительный:** `{'Да' if is_suspicious else 'Нет'}`\n"
            f"{EMOJIS['DOT']} **Бот:** `{'Да' if member.bot else 'Нет'}`\n"
            f"{EMOJIS['DOT']} **Система:** `{'Да' if member.system else 'Нет'}`\n"
            f"{EMOJIS['DOT']} **Флаги:** `{', '.join(flag.name for flag in member.public_flags.all()) or 'Нет'}`"
        )

        # Собираем информацию о сервере
        server_info = (
            f"{EMOJIS['DOT']} **Участник №:** `{member.guild.member_count}`\n"
            f"{EMOJIS['DOT']} **Присоединился:** <t:{int(member.joined_at.timestamp())}:F>"
        )

        # Проверяем, был ли пользователь ранее на сервере
        try:
            async for ban in member.guild.bans():
                if ban.user.id == member.id:
                    server_info += f"\n{EMOJIS['DOT']} **⚠️ Ранее был забанен!**"
                    break
        except discord.Forbidden:
            pass

        embed = create_embed(
            title=f"{'🤖' if member.bot else '👋'} Новый участник",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Имя:** `{member.name}`\n\n"
                      f"**📅 Информация об аккаунте:**\n{account_info}\n\n"
                      f"**🌟 Информация о сервере:**\n{server_info}\n\n"
                      f"**📨 Информация о приглашении:**\n{invite_info}",
            footer={"text": f"ID: {member.id}"}
        )

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        if inviter and inviter.avatar:
            embed.set_author(name=f"Приглашен пользователем {inviter.name}", icon_url=inviter.avatar.url)

        if is_suspicious:
            embed.color = discord.Color.red()
            embed.add_field(
                name="⚠️ Внимание",
                value="Аккаунт создан менее недели назад!",
                inline=False
            )

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Расширенное логирование выхода участников"""
        if not self.log_channel:
            return

        # Проверяем, был ли участник кикнут
        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    moderator = entry.user
                    reason = entry.reason
                    embed = create_embed(
                        title="👢 Участник кикнут",
                        description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                                  f"{EMOJIS['DOT']} **Модератор:** {moderator.mention}\n"
                                  f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`\n\n"
                                  f"**📊 Статистика:**\n"
                                  f"{EMOJIS['DOT']} **Присоединился:** <t:{int(member.joined_at.timestamp())}:F>\n"
                                  f"{EMOJIS['DOT']} **Пробыл на сервере:** `{(datetime.datetime.now(datetime.timezone.utc) - member.joined_at).days} дней`\n"
                                  f"{EMOJIS['DOT']} **Роли:** {', '.join(role.mention for role in member.roles[1:]) or 'Нет'}",
                        footer={"text": f"ID: {member.id}"}
                    )
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    await self.log_event(embed)
                    return
        except discord.Forbidden:
            pass

        # Если не был кикнут, значит вышел сам
        embed = create_embed(
            title="👋 Участник покинул сервер",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Имя:** `{member.name}`\n\n"
                      f"**📊 Статистика:**\n"
                      f"{EMOJIS['DOT']} **Присоединился:** <t:{int(member.joined_at.timestamp())}:F>\n"
                      f"{EMOJIS['DOT']} **Пробыл на сервере:** `{(datetime.datetime.now(datetime.timezone.utc) - member.joined_at).days} дней`\n"
                      f"{EMOJIS['DOT']} **Роли:** {', '.join(role.mention for role in member.roles[1:]) or 'Нет'}\n"
                      f"{EMOJIS['DOT']} **Осталось участников:** `{member.guild.member_count}`",
            footer={"text": f"ID: {member.id}"}
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Расширенное логирование банов"""
        if not self.log_channel:
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        # Получаем информацию о предыдущих банах
        try:
            bans = [ban async for ban in guild.bans()]
            previous_bans = sum(1 for ban in bans if ban.user.id == user.id)
        except discord.Forbidden:
            previous_bans = 0

        embed = create_embed(
            title="🔨 Участник забанен",
            description=f"{EMOJIS['DOT']} **Участник:** {user.mention} (`{user.id}`)\n"
                      f"{EMOJIS['DOT']} **Модератор:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`\n\n"
                      f"**📊 Статистика:**\n"
                      f"{EMOJIS['DOT']} **Предыдущие баны:** `{previous_bans}`\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID: {user.id}"}
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Логирование разбанов"""
        embed = create_embed(
            title="🔓 Участник разбанен",
            description=f"{EMOJIS['DOT']} **Участник:** {user.mention} (`{user.id}`)",
            footer={"text": f"ID: {user.id}"}
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Расширенное логирование создания каналов"""
        if not self.log_channel:
            return

        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        channel_info = f"{EMOJIS['DOT']} **Название:** {channel.mention}\n" \
                      f"{EMOJIS['DOT']} **Тип:** `{str(channel.type)}`\n" \
                      f"{EMOJIS['DOT']} **Категория:** `{channel.category.name if channel.category else 'Нет'}`\n" \
                      f"{EMOJIS['DOT']} **Позиция:** `{channel.position}`\n"

        if isinstance(channel, discord.TextChannel):
            channel_info += f"{EMOJIS['DOT']} **Медленный режим:** `{channel.slowmode_delay}с`\n" \
                          f"{EMOJIS['DOT']} **NSFW:** `{'Да' if channel.nsfw else 'Нет'}`\n"
        elif isinstance(channel, discord.VoiceChannel):
            channel_info += f"{EMOJIS['DOT']} **Битрейт:** `{channel.bitrate//1000}kbps`\n" \
                          f"{EMOJIS['DOT']} **Лимит пользователей:** `{channel.user_limit or 'Без лимита'}`\n"

        embed = create_embed(
            title="📝 Канал создан",
            description=f"{channel_info}\n"
                      f"**👮 Модератор:**\n"
                      f"{EMOJIS['DOT']} **Создал:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {channel.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Расширенное логирование удаления каналов"""
        if not self.log_channel:
            return

        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        channel_info = f"{EMOJIS['DOT']} **Название:** `{channel.name}`\n" \
                      f"{EMOJIS['DOT']} **Тип:** `{str(channel.type)}`\n" \
                      f"{EMOJIS['DOT']} **Категория:** `{channel.category.name if channel.category else 'Нет'}`\n" \
                      f"{EMOJIS['DOT']} **Позиция:** `{channel.position}`\n" \
                      f"{EMOJIS['DOT']} **Создан:** <t:{int(channel.created_at.timestamp())}:F>"

        if isinstance(channel, discord.TextChannel):
            channel_info += f"\n{EMOJIS['DOT']} **Тема:** `{channel.topic or 'Отсутствует'}`"
            if channel.last_message:
                channel_info += f"\n{EMOJIS['DOT']} **Последнее сообщение от:** {channel.last_message.author.mention}"

        embed = create_embed(
            title="🗑️ Канал удален",
            description=f"{channel_info}\n\n"
                      f"**👮 Модератор:**\n"
                      f"{EMOJIS['DOT']} **Удалил:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {channel.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Расширенное логирование создания ролей"""
        if not self.log_channel:
            return

        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        permissions = []
        for perm, value in role.permissions:
            if value:
                permissions.append(perm)

        embed = create_embed(
            title="👑 Роль создана",
            description=f"{EMOJIS['DOT']} **Название:** {role.mention}\n"
                      f"{EMOJIS['DOT']} **Цвет:** `{role.color}`\n"
                      f"{EMOJIS['DOT']} **Позиция:** `{role.position}`\n"
                      f"{EMOJIS['DOT']} **Отображается отдельно:** `{'Да' if role.hoist else 'Нет'}`\n"
                      f"{EMOJIS['DOT']} **Упоминаемая:** `{'Да' if role.mentionable else 'Нет'}`\n"
                      f"{EMOJIS['DOT']} **Интеграция:** `{'Да' if role.managed else 'Нет'}`\n\n"
                      f"**🔑 Права роли:**\n`{', '.join(permissions) or 'Нет прав'}`\n\n"
                      f"**👮 Модератор:**\n"
                      f"{EMOJIS['DOT']} **Создал:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
            footer={"text": f"ID: {role.id}"}
        )

        if role.icon:
            embed.set_thumbnail(url=role.icon.url)

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Расширенное логирование удаления ролей"""
        if not self.log_channel:
            return

        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = None
            reason = None

        embed = create_embed(
            title="🗑️ Роль удалена",
            description=f"{EMOJIS['DOT']} **Название:** `{role.name}`\n"
                      f"{EMOJIS['DOT']} **Цвет:** `{role.color}`\n"
                      f"{EMOJIS['DOT']} **Позиция:** `{role.position}`\n"
                      f"{EMOJIS['DOT']} **Создана:** <t:{int(role.created_at.timestamp())}:F>",
            footer={"text": f"ID: {role.id}"}
        )

        if moderator:
            embed.add_field(
                name="👮 Модератор",
                value=f"{EMOJIS['DOT']} **Модератор:** {moderator.mention}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
                inline=False
            )

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Логирование голосовых событий"""
        if not self.log_channel:
            return

        if before.channel != after.channel:
            if after.channel and not before.channel:
                action = f"присоединился к {after.channel.mention}"
            elif before.channel and not after.channel:
                action = f"покинул {before.channel.name}"
            else:
                action = f"перешел из {before.channel.name} в {after.channel.mention}"

            embed = create_embed(
                title="🎤 Голосовой канал",
                description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                          f"{EMOJIS['DOT']} **Действие:** {action}",
                footer={"text": f"ID: {member.id}"}
            )
            await self.log_event(embed)

        # Логируем изменения состояния
        changes = []
        if before.deaf != after.deaf:
            changes.append(f"Серверный мут: `{'Включен' if after.deaf else 'Выключен'}`")
        if before.mute != after.mute:
            changes.append(f"Серверное заглушение: `{'Включено' if after.mute else 'Выключено'}`")
        if before.self_deaf != after.self_deaf:
            changes.append(f"Личный мут: `{'Включен' if after.self_deaf else 'Выключен'}`")
        if before.self_mute != after.self_mute:
            changes.append(f"Личное заглушение: `{'Включено' if after.self_mute else 'Выключено'}`")
        if before.self_stream != after.self_stream:
            changes.append(f"Стрим: `{'Начат' if after.self_stream else 'Закончен'}`")
        if before.self_video != after.self_video:
            changes.append(f"Видео: `{'Включено' if after.self_video else 'Выключено'}`")
        if before.requested_to_speak_at != after.requested_to_speak_at:
            changes.append(f"Запрос на выступление: `{'Отправлен' if after.requested_to_speak_at else 'Отменен'}`")

        if changes:
            embed = create_embed(
                title="🎤 Изменение голосового состояния",
                description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                          f"{EMOJIS['DOT']} **Канал:** {after.channel.mention if after.channel else 'Нет'}\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes),
                footer={"text": f"ID: {member.id}"}
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Расширенное логирование изменений сервера"""
        if not self.log_channel:
            return

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
        if before.public_updates_channel != after.public_updates_channel:
            changes.append(f"Канал обновлений: {before.public_updates_channel.mention if before.public_updates_channel else 'Отсутствует'} → {after.public_updates_channel.mention if after.public_updates_channel else 'Отсутствует'}")
        
        # Настройки AFK
        if before.afk_channel != after.afk_channel:
            changes.append(f"AFK канал: {before.afk_channel.mention if before.afk_channel else 'Отсутствует'} → {after.afk_channel.mention if after.afk_channel else 'Отсутствует'}")
        if before.afk_timeout != after.afk_timeout:
            changes.append(f"Тайм-аут AFK: `{before.afk_timeout}с` → `{after.afk_timeout}с`")
        
        # Настройки бустов
        if before.premium_tier != after.premium_tier:
            changes.append(f"Уровень буста: `{before.premium_tier}` → `{after.premium_tier}`")
        if before.premium_subscription_count != after.premium_subscription_count:
            changes.append(f"Количество бустов: `{before.premium_subscription_count}` → `{after.premium_subscription_count}`")
        
        # Локализация
        if before.preferred_locale != after.preferred_locale:
            changes.append(f"Основной язык: `{before.preferred_locale}` → `{after.preferred_locale}`")
        
        # Функции сервера
        if before.features != after.features:
            added_features = set(after.features) - set(before.features)
            removed_features = set(before.features) - set(after.features)
            if added_features:
                changes.append(f"Добавлены функции: `{', '.join(added_features)}`")
            if removed_features:
                changes.append(f"Удалены функции: `{', '.join(removed_features)}`")

        if changes:
            try:
                async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
                    moderator = entry.user
                    reason = entry.reason
                    break
            except discord.Forbidden:
                moderator = None
                reason = None

            embed = create_embed(
                title="⚙️ Сервер обновлен",
                description=f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes)
            )
            
            # Добавляем статистику сервера
            stats = (
                f"{EMOJIS['DOT']} **Участников:** `{after.member_count}`\n"
                f"{EMOJIS['DOT']} **Каналов:** `{len(after.channels)}`\n"
                f"{EMOJIS['DOT']} **Ролей:** `{len(after.roles)}`\n"
                f"{EMOJIS['DOT']} **Эмодзи:** `{len(after.emojis)}`\n"
                f"{EMOJIS['DOT']} **Стикеров:** `{len(after.stickers)}`\n"
                f"{EMOJIS['DOT']} **Бустов:** `{after.premium_subscription_count}`\n"
                f"{EMOJIS['DOT']} **Создан:** <t:{int(after.created_at.timestamp())}:F>"
            )
            embed.add_field(name="📊 Статистика", value=stats, inline=False)

            if moderator:
                embed.add_field(
                    name="👮 Модератор",
                    value=f"{EMOJIS['DOT']} **Модератор:** {moderator.mention}\n"
                          f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
                    inline=False
                )

            if after.icon:
                embed.set_thumbnail(url=after.icon.url)
            if after.banner:
                embed.set_image(url=after.banner.url)

            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Логирование изменений эмодзи"""
        if not self.log_channel:
            return

        # Найти новые эмодзи
        new_emojis = [emoji for emoji in after if emoji not in before]
        # Найти удаленные эмодзи
        removed_emojis = [emoji for emoji in before if emoji not in after]

        if new_emojis:
            embed = create_embed(
                title="😀 Новые эмодзи добавлены",
                description="\n".join(f"{EMOJIS['DOT']} {emoji} `{emoji.name}`" for emoji in new_emojis),
                footer={"text": f"Всего эмодзи: {len(after)}"}
            )
            await self.log_event(embed)

        if removed_emojis:
            embed = create_embed(
                title="🗑️ Эмодзи удалены",
                description="\n".join(f"{EMOJIS['DOT']} `{emoji.name}`" for emoji in removed_emojis),
                footer={"text": f"Всего эмодзи: {len(after)}"}
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        """Логирование изменений стикеров"""
        if not self.log_channel:
            return

        new_stickers = [sticker for sticker in after if sticker not in before]
        removed_stickers = [sticker for sticker in before if sticker not in after]

        if new_stickers:
            embed = create_embed(
                title="🌟 Новые стикеры добавлены",
                description="\n".join(f"{EMOJIS['DOT']} `{sticker.name}`" for sticker in new_stickers),
                footer={"text": f"Всего стикеров: {len(after)}"}
            )
            await self.log_event(embed)

        if removed_stickers:
            embed = create_embed(
                title="🗑️ Стикеры удалены",
                description="\n".join(f"{EMOJIS['DOT']} `{sticker.name}`" for sticker in removed_stickers),
                footer={"text": f"Всего стикеров: {len(after)}"}
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Расширенное логирование изменений участника"""
        if not self.log_channel:
            return

        changes = []
        moderator = None
        reason = None
        
        # Изменение никнейма
        if before.nick != after.nick:
            changes.append(f"Никнейм: `{before.nick or 'Отсутствует'}` → `{after.nick or 'Отсутствует'}`")

        # Изменение ролей
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                try:
                    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                        if entry.target.id == after.id:
                            moderator = entry.user
                            reason = entry.reason
                            break
                except discord.Forbidden:
                    pass
            
            if added_roles:
                changes.append(f"Добавлены роли: {', '.join(role.mention for role in added_roles)}")
            if removed_roles:
                changes.append(f"Удалены роли: {', '.join(role.mention for role in removed_roles)}")

        # Изменение статуса буста
        if before.premium_since != after.premium_since:
            if after.premium_since:
                changes.append(f"Начал бустить сервер: <t:{int(after.premium_since.timestamp())}:F>")
            else:
                changes.append("Прекратил бустить сервер")

        # Изменение таймаута
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                changes.append(f"Выдан таймаут до: <t:{int(after.timed_out_until.timestamp())}:F>")
            else:
                changes.append("Таймаут снят")

        # Изменение флагов участника
        if before.flags != after.flags:
            changes.append("Изменены флаги участника")

        if changes:
            embed = create_embed(
                title="👤 Участник обновлен",
                description=f"{EMOJIS['DOT']} **Участник:** {after.mention} (`{after.id}`)\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes)
            )

            if moderator:
                embed.add_field(
                    name="👮 Модератор",
                    value=f"{EMOJIS['DOT']} **Модератор:** {moderator.mention}\n"
                          f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
                    inline=False
                )

            if after.avatar:
                embed.set_thumbnail(url=after.avatar.url)

            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Логирование изменений каналов"""
        if not self.log_channel:
            return

        moderator = None
        try:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                if entry.target.id == before.id:
                    moderator = entry.user
                    break
        except discord.Forbidden:
            pass

        embed = create_embed(
            title="📝 Канал изменен",
            description=f"Канал: {after.mention}"
        )

        changes = []

        if before.name != after.name:
            changes.append(f"**Название:** {before.name} ➜ {after.name}")

        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(f"**Тема:** {before.topic or 'Нет'} ➜ {after.topic or 'Нет'}")
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(f"**Медленный режим:** {before.slowmode_delay}с ➜ {after.slowmode_delay}с")
            if before.nsfw != after.nsfw:
                changes.append(f"**NSFW:** {before.nsfw} ➜ {after.nsfw}")

        if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                changes.append(f"**Битрейт:** {before.bitrate//1000}kbps ➜ {after.bitrate//1000}kbps")
            if before.user_limit != after.user_limit:
                changes.append(f"**Лимит пользователей:** {before.user_limit or 'Нет'} ➜ {after.user_limit or 'Нет'}")

        if before.category != after.category:
            changes.append(f"**Категория:** {before.category or 'Нет'} ➜ {after.category or 'Нет'}")

        if before.position != after.position:
            changes.append(f"**Позиция:** {before.position} ➜ {after.position}")

        if changes:
            embed.add_field(name="Изменения", value="\n".join(changes), inline=False)
            
            if moderator:
                embed.add_field(name="Модератор", value=f"{moderator.mention} ({moderator.id})", inline=False)
            
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
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

        embed = create_embed(
            title="🗑️ Сообщение удалено",
            description=f"**Автор:** {message.author.mention} ({message.author.id})\n"
                       f"**Канал:** {message.channel.mention}\n"
                       f"**Создано:** <t:{int(message.created_at.timestamp())}:R>"
        )

        if message.content:
            if len(message.content) > 1024:
                embed.add_field(name="Содержание", value=f"{message.content[:1021]}...", inline=False)
            else:
                embed.add_field(name="Содержание", value=message.content, inline=False)

        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.proxy_url})" for a in message.attachments])
            if len(attachments) > 1024:
                attachments = attachments[:1021] + "..."
            embed.add_field(name="Вложения", value=attachments, inline=False)

        if moderator and moderator != message.author:
            embed.add_field(name="Удалил", value=f"{moderator.mention} ({moderator.id})", inline=False)

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if not self.bot.is_ready():
            return

        moderator = None
        reason = None

        if before.name != after.name or before.color != after.color or before.permissions != after.permissions:
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    moderator = entry.user
                    reason = entry.reason
                    break
            except discord.Forbidden:
                pass

            embed = create_embed(title=f"{EMOJIS['DOT']} Роль изменена", color=after.color)
            
            if moderator:
                embed.set_author(name=f"{moderator.name}", icon_url=moderator.display_avatar.url)
            
            if before.name != after.name:
                embed.add_field(name="Название", value=f"**До:** {before.name}\n**После:** {after.name}", inline=False)
            
            if before.color != after.color:
                embed.add_field(name="Цвет", value=f"**До:** {before.color}\n**После:** {after.color}", inline=False)
            
            if before.permissions != after.permissions:
                added_perms = [perm[0] for perm in after.permissions if perm not in before.permissions and perm[1]]
                removed_perms = [perm[0] for perm in before.permissions if perm not in after.permissions and perm[1]]
                
                if added_perms:
                    embed.add_field(name="Добавленные права", value="\n".join(f"✅ {perm}" for perm in added_perms), inline=False)
                if removed_perms:
                    embed.add_field(name="Удаленные права", value="\n".join(f"❌ {perm}" for perm in removed_perms), inline=False)
            
            if reason:
                embed.add_field(name="Причина", value=reason, inline=False)
            
            embed.set_footer(text=f"ID: {after.id}")
            embed.timestamp = discord.utils.utcnow()
            
            await self.send_log(after.guild, embed, "role_logs")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """Логирование создания тредов"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🧵 Тред создан",
            description=f"{EMOJIS['DOT']} **Название:** {thread.mention}\n"
                      f"{EMOJIS['DOT']} **Владелец:** {thread.owner.mention if thread.owner else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Родительский канал:** {thread.parent.mention}\n"
                      f"{EMOJIS['DOT']} **Медленный режим:** `{thread.slowmode_delay}с`\n"
                      f"{EMOJIS['DOT']} **Автоархивация:** `{thread.auto_archive_duration} минут`",
            footer={"text": f"ID: {thread.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        """Логирование удаления тредов"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🗑️ Тред удален",
            description=f"{EMOJIS['DOT']} **Название:** `{thread.name}`\n"
                      f"{EMOJIS['DOT']} **Родительский канал:** {thread.parent.mention if thread.parent else 'Неизвестно'}",
            footer={"text": f"ID: {thread.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        """Расширенное логирование изменений тредов"""
        if not self.log_channel:
            return

        changes = []
        
        if before.name != after.name:
            changes.append(f"Название: `{before.name}` → `{after.name}`")
        if before.archived != after.archived:
            changes.append(f"Статус архивации: `{'Да' if after.archived else 'Нет'}`")
        if before.locked != after.locked:
            changes.append(f"Заблокирован: `{'Да' if after.locked else 'Нет'}`")
        if before.slowmode_delay != after.slowmode_delay:
            changes.append(f"Медленный режим: `{before.slowmode_delay}с` → `{after.slowmode_delay}с`")
        if before.auto_archive_duration != after.auto_archive_duration:
            changes.append(f"Время автоархивации: `{before.auto_archive_duration}` → `{after.auto_archive_duration}`")
        if before.pinned != after.pinned:
            changes.append(f"Закреплен: `{'Да' if after.pinned else 'Нет'}`")

        if changes:
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.thread_update):
                    if entry.target.id == after.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
            except discord.Forbidden:
                moderator = None
                reason = None

            embed = create_embed(
                title="🧵 Тред обновлен",
                description=f"{EMOJIS['DOT']} **Тред:** {after.mention}\n"
                          f"{EMOJIS['DOT']} **Родительский канал:** {after.parent.mention}\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes)
            )

            thread_info = (
                f"{EMOJIS['DOT']} **Участников:** `{len(after.members)}`\n"
                f"{EMOJIS['DOT']} **Сообщений:** `{after.message_count}`\n"
                f"{EMOJIS['DOT']} **Создан:** <t:{int(after.created_at.timestamp())}:F>"
            )
            embed.add_field(name="📊 Информация", value=thread_info, inline=False)

            if moderator:
                embed.add_field(
                    name="👮 Модератор",
                    value=f"{EMOJIS['DOT']} **Модератор:** {moderator.mention}\n"
                          f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`",
                    inline=False
                )

            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Расширенное логирование создания приглашений"""
        if not self.log_channel:
            return

        # Получаем информацию о создателе
        inviter_info = ""
        if invite.inviter:
            roles = [role.mention for role in invite.inviter.roles if not role.is_default()]
            roles_str = ", ".join(roles) if roles else "Нет"
            inviter_info = (
                f"{EMOJIS['DOT']} **Создатель:** {invite.inviter.mention} (`{invite.inviter.id}`)\n"
                f"{EMOJIS['DOT']} **Никнейм создателя:** `{invite.inviter.display_name}`\n"
                f"{EMOJIS['DOT']} **Роли создателя:** {roles_str}\n"
                f"{EMOJIS['DOT']} **Аккаунт создан:** <t:{int(invite.inviter.created_at.timestamp())}:F>\n"
                f"{EMOJIS['DOT']} **Присоединился к серверу:** <t:{int(invite.inviter.joined_at.timestamp())}:F>\n"
            )

        # Получаем информацию о канале
        channel_info = (
            f"{EMOJIS['DOT']} **Канал:** {invite.channel.mention} (`{invite.channel.id}`)\n"
            f"{EMOJIS['DOT']} **Тип канала:** `{str(invite.channel.type)}`\n"
            f"{EMOJIS['DOT']} **Категория:** `{invite.channel.category.name if invite.channel.category else 'Нет'}`\n"
        )
        
        if isinstance(invite.channel, discord.TextChannel):
            channel_info += (
                f"{EMOJIS['DOT']} **Тема канала:** `{invite.channel.topic or 'Отсутствует'}`\n"
                f"{EMOJIS['DOT']} **Медленный режим:** `{invite.channel.slowmode_delay}с`\n"
                f"{EMOJIS['DOT']} **NSFW:** `{'Да' if invite.channel.nsfw else 'Нет'}`\n"
            )
        elif isinstance(invite.channel, discord.VoiceChannel):
            channel_info += (
                f"{EMOJIS['DOT']} **Битрейт:** `{invite.channel.bitrate//1000}kbps`\n"
                f"{EMOJIS['DOT']} **Лимит пользователей:** `{invite.channel.user_limit or 'Без лимита'}`\n"
                f"{EMOJIS['DOT']} **Регион:** `{invite.channel.rtc_region or 'Авто'}`\n"
            )

        # Информация о приглашении
        invite_info = (
            f"{EMOJIS['DOT']} **Код:** `{invite.code}`\n"
            f"{EMOJIS['DOT']} **Ссылка:** `https://discord.gg/{invite.code}`\n"
            f"{EMOJIS['DOT']} **Временное:** `{'Да' if invite.temporary else 'Нет'}`\n"
            f"{EMOJIS['DOT']} **Максимум использований:** `{invite.max_uses if invite.max_uses else 'Неограничено'}`\n"
            f"{EMOJIS['DOT']} **Срок действия:** `{invite.max_age if invite.max_age else 'Неограничено'} секунд`\n"
            f"{EMOJIS['DOT']} **Создано:** <t:{int(datetime.datetime.now().timestamp())}:F>\n"
        )

        embed = create_embed(
            title="📨 Приглашение создано",
            description=f"**👤 Информация о создателе:**\n{inviter_info}\n"
                      f"**📝 Информация о канале:**\n{channel_info}\n"
                      f"**🔗 Информация о приглашении:**\n{invite_info}",
            footer={"text": f"ID приглашения: {invite.id if hasattr(invite, 'id') else 'Неизвестно'}"}
        )

        if invite.inviter and invite.inviter.avatar:
            embed.set_thumbnail(url=invite.inviter.avatar.url)

        await self.log_event(embed)

    async def track_invite_uses(self):
        """Отслеживание использования приглашений"""
        self.invite_uses = {}
        try:
            for guild in self.bot.guilds:
                self.invite_uses[guild.id] = {
                    invite.code: {
                        'uses': invite.uses,
                        'inviter': invite.inviter,
                        'channel': invite.channel,
                        'created_at': invite.created_at,
                        'max_uses': invite.max_uses,
                        'temporary': invite.temporary
                    } async for invite in guild.invites()
                }
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Логирование удаления приглашений"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🗑️ Приглашение удалено",
            description=f"{EMOJIS['DOT']} **Код:** `{invite.code}`\n"
                      f"{EMOJIS['DOT']} **Ссылка:** `https://discord.gg/{invite.code}`\n"
                      f"{EMOJIS['DOT']} **Канал:** {invite.channel.mention} (`{invite.channel.id}`)\n"
                      f"{EMOJIS['DOT']} **Удалено:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"Код приглашения: {invite.code}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance):
        """Логирование создания трибун"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🎭 Трибуна создана",
            description=f"{EMOJIS['DOT']} **Название:** `{stage_instance.topic}`\n"
                      f"{EMOJIS['DOT']} **Канал:** {stage_instance.channel.mention}\n"
                      f"{EMOJIS['DOT']} **Приватность:** `{'Публичная' if stage_instance.discoverable_disabled else 'Приватная'}`",
            footer={"text": f"ID: {stage_instance.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance):
        """Логирование удаления трибун"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🗑️ Трибуна удалена",
            description=f"{EMOJIS['DOT']} **Название:** `{stage_instance.topic}`\n"
                      f"{EMOJIS['DOT']} **Канал:** {stage_instance.channel.mention}",
            footer={"text": f"ID: {stage_instance.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_stage_instance_update(self, before, after):
        """Логирование изменений трибун"""
        if not self.log_channel:
            return

        changes = []
        if before.topic != after.topic:
            changes.append(f"Название: `{before.topic}` → `{after.topic}`")
        if before.discoverable_disabled != after.discoverable_disabled:
            changes.append(f"Приватность: `{'Публичная' if not after.discoverable_disabled else 'Приватная'}`")

        if changes:
            embed = create_embed(
                title="🎭 Трибуна обновлена",
                description=f"{EMOJIS['DOT']} **Канал:** {after.channel.mention}\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes),
                footer={"text": f"ID: {after.id}"}
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_create(self, event):
        """Расширенное логирование создания событий"""
        if not self.log_channel:
            return

        location = event.location if isinstance(event.location, str) else "Нет"
        if event.channel:
            location = event.channel.mention

        embed = create_embed(
            title="📅 Создано новое событие",
            description=f"{EMOJIS['DOT']} **Название:** `{event.name}`\n"
                      f"{EMOJIS['DOT']} **Описание:** `{event.description or 'Нет описания'}`\n"
                      f"{EMOJIS['DOT']} **Создатель:** {event.creator.mention if event.creator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Локация:** {location}\n"
                      f"{EMOJIS['DOT']} **Начало:** <t:{int(event.start_time.timestamp())}:F>\n"
                      f"{EMOJIS['DOT']} **Конец:** {f'<t:{int(event.end_time.timestamp())}:F>' if event.end_time else 'Не указано'}\n"
                      f"{EMOJIS['DOT']} **Тип:** `{event.entity_type}`\n"
                      f"{EMOJIS['DOT']} **Статус:** `{event.status}`\n"
                      f"{EMOJIS['DOT']} **Приватность:** `{'Публичное' if event.privacy_level == discord.GuildScheduledEventPrivacyLevel.guild_only else 'Приватное'}`",
            footer={"text": f"ID: {event.id}"}
        )

        if event.image:
            embed.set_thumbnail(url=event.image.url)

        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_delete(self, event):
        """Логирование удаления запланированных событий"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🗑️ Запланированное событие удалено",
            description=f"{EMOJIS['DOT']} **Название:** `{event.name}`\n"
                      f"{EMOJIS['DOT']} **Создатель:** {event.creator.mention if event.creator else 'Неизвестно'}",
            footer={"text": f"ID: {event.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_update(self, before, after):
        """Логирование изменений запланированных событий"""
        if not self.log_channel:
            return

        changes = []
        if before.name != after.name:
            changes.append(f"Название: `{before.name}` → `{after.name}`")
        if before.description != after.description:
            changes.append(f"Описание изменено")
        if before.start_time != after.start_time:
            changes.append(f"Время начала: <t:{int(before.start_time.timestamp())}:F> → <t:{int(after.start_time.timestamp())}:F>")
        if before.end_time != after.end_time:
            changes.append(f"Время окончания изменено")
        if before.location != after.location:
            changes.append(f"Локация: `{before.location}` → `{after.location}`")
        if before.status != after.status:
            changes.append(f"Статус: `{before.status}` → `{after.status}`")
        if before.channel != after.channel:
            changes.append(f"Канал: {before.channel.mention if before.channel else 'Не указан'} → {after.channel.mention if after.channel else 'Не указан'}")

        if changes:
            embed = create_embed(
                title="📝 Запланированное событие обновлено",
                description=f"{EMOJIS['DOT']} **Событие:** `{after.name}`\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes),
                footer={"text": f"ID: {after.id}"}
            )
            if after.image:
                embed.set_thumbnail(url=after.image.url)
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_user_add(self, event, user):
        """Логирование присоединения пользователей к запланированным событиям"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="👤 Пользователь присоединился к событию",
            description=f"{EMOJIS['DOT']} **Событие:** `{event.name}`\n"
                      f"{EMOJIS['DOT']} **Пользователь:** {user.mention} (`{user.id}`)\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID события: {event.id}"}
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_guild_scheduled_event_user_remove(self, event, user):
        """Логирование выхода пользователей из запланированных событий"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="👤 Пользователь покинул событие",
            description=f"{EMOJIS['DOT']} **Событие:** `{event.name}`\n"
                      f"{EMOJIS['DOT']} **Пользователь:** {user.mention} (`{user.id}`)\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID события: {event.id}"}
        )
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_integration_create(self, integration):
        """Логирование создания интеграций"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🔗 Новая интеграция добавлена",
            description=f"{EMOJIS['DOT']} **Название:** `{integration.name}`\n"
                      f"{EMOJIS['DOT']} **Тип:** `{integration.type}`\n"
                      f"{EMOJIS['DOT']} **Включена:** `{'Да' if integration.enabled else 'Нет'}`\n"
                      f"{EMOJIS['DOT']} **Синхронизируется:** `{'Да' if integration.syncing else 'Нет'}`\n"
                      f"{EMOJIS['DOT']} **Роль:** {integration.role.mention if integration.role else 'Не указана'}",
            footer={"text": f"ID: {integration.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_integration_update(self, integration):
        """Логирование обновления интеграций"""
        if not self.log_channel:
            return

        try:
            description = [
                f"{EMOJIS['DOT']} **Название:** `{integration.name}`",
                f"{EMOJIS['DOT']} **Тип:** `{integration.type}`",
                f"{EMOJIS['DOT']} **Включена:** `{'Да' if getattr(integration, 'enabled', False) else 'Нет'}`"
            ]

            # Добавляем дополнительные поля только если они существуют
            if hasattr(integration, 'syncing'):
                description.append(f"{EMOJIS['DOT']} **Синхронизируется:** `{'Да' if integration.syncing else 'Нет'}`")
            
            if hasattr(integration, 'role') and integration.role:
                description.append(f"{EMOJIS['DOT']} **Роль:** {integration.role.mention}")
            
            if hasattr(integration, 'synced_at') and integration.synced_at:
                description.append(f"{EMOJIS['DOT']} **Время последней синхронизации:** <t:{int(integration.synced_at.timestamp())}:F>")
            
            if hasattr(integration, 'expire_behavior'):
                description.append(f"{EMOJIS['DOT']} **Поведение при истечении:** `{integration.expire_behavior}`")
            
            if hasattr(integration, 'expire_grace_period'):
                description.append(f"{EMOJIS['DOT']} **Льготный период:** `{integration.expire_grace_period} дней`")
            
            if hasattr(integration, 'user') and integration.user:
                description.append(f"{EMOJIS['DOT']} **Пользователь:** {integration.user.mention}")
            
            if hasattr(integration, 'account') and integration.account:
                description.append(f"{EMOJIS['DOT']} **Аккаунт:** `{integration.account.name}`")

            embed = create_embed(
                title="🔄 Интеграция обновлена",
                description="\n".join(description),
                footer={"text": f"ID: {integration.id}"}
            )
            
            await self.log_event(embed)
            
        except Exception as e:
            print(f"❌ Ошибка при логировании обновления интеграции: {e}")
            if hasattr(e, '__traceback__'):
                print(''.join(traceback.format_tb(e.__traceback__)))

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        """Логирование изменений вебхуков"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🔧 Вебхуки обновлены",
            description=f"{EMOJIS['DOT']} **Канал:** {channel.mention}\n"
                      f"{EMOJIS['DOT']} **Категория:** `{channel.category}`\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID канала: {channel.id}"}
        )
        await self.log_event(embed)

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
            embed = create_embed(
                title="👤 Пользователь обновлен",
                description=f"{EMOJIS['DOT']} **Пользователь:** {after.mention} (`{after.id}`)\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes),
                footer={"text": f"ID: {after.id}"}
            )
            if after.avatar:
                embed.set_thumbnail(url=after.avatar.url)
            if after.banner:
                embed.set_image(url=after.banner.url)
            await self.log_event(embed)

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

    @commands.Cog.listener()
    async def on_thread_member_join(self, member):
        """Логирование присоединения участников к тредам"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🧵 Участник присоединился к треду",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Тред:** {member.thread.mention}\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID треда: {member.thread.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member):
        """Логирование выхода участников из тредов"""
        if not self.log_channel:
            return

        embed = create_embed(
            title="🧵 Участник покинул тред",
            description=f"{EMOJIS['DOT']} **Участник:** {member.mention} (`{member.id}`)\n"
                      f"{EMOJIS['DOT']} **Тред:** {member.thread.mention}\n"
                      f"{EMOJIS['DOT']} **Время:** <t:{int(datetime.datetime.now().timestamp())}:F>",
            footer={"text": f"ID треда: {member.thread.id}"}
        )
        await self.log_event(embed)

    @commands.Cog.listener()
    async def on_thread_member_update(self, before, after):
        """Логирование обновлений участников в тредах"""
        if not self.log_channel:
            return

        changes = []
        if before.join_timestamp != after.join_timestamp:
            changes.append(f"Время присоединения: <t:{int(before.join_timestamp.timestamp())}:F> → <t:{int(after.join_timestamp.timestamp())}:F>")

        if changes:
            embed = create_embed(
                title="🧵 Обновление участника в треде",
                description=f"{EMOJIS['DOT']} **Участник:** {after.mention} (`{after.id}`)\n"
                          f"{EMOJIS['DOT']} **Тред:** {after.thread.mention}\n"
                          f"{EMOJIS['DOT']} **Изменения:**\n" + 
                          "\n".join(f"{EMOJIS['DOT']} {change}" for change in changes),
                footer={"text": f"ID треда: {after.thread.id}"}
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Логирование ошибок slash-команд"""
        if self.log_channel:
            error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.log_channel.send(f"<@{self.owner_id}>, произошла ошибка!")
            embed = create_embed(
                title="⚠️ Ошибка slash-команды", 
                description=f"{EMOJIS['DOT']} **Команда:** `/{interaction.command.parent.name if interaction.command.parent else ''}{' ' if interaction.command.parent else ''}{interaction.command.name}`\n"
                          f"{EMOJIS['DOT']} **Автор:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                          f"{EMOJIS['DOT']} **Канал:** {interaction.channel.mention}\n"
                          f"{EMOJIS['DOT']} **Ошибка:**\n```py\n{error_trace[:1900]}```"
            )
            await self.log_event(embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Логирование массового удаления сообщений"""
        if not self.log_channel or len(messages) < 2:
            return

        # Фильтруем сообщения, исключая сообщения от других ботов
        filtered_messages = [msg for msg in messages if not msg.author.bot or msg.author == self.bot.user]
        
        if not filtered_messages:
            return

        # Создаем текстовое содержимое
        content = []
        content.append(f"Удаленные сообщения из канала: #{filtered_messages[0].channel.name}")
        content.append(f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("-" * 50 + "\n")
        
        for message in sorted(filtered_messages, key=lambda m: m.created_at):
            content.append(f"[{message.created_at.strftime('%d/%m/%Y - %H:%M:%S')}] {message.author} ({message.author.id}): {message.content}")
            if message.attachments:
                content.append(f"Вложения: {', '.join([a.url for a in message.attachments])}")
            if message.embeds:
                content.append(f"Количество эмбедов: {len(message.embeds)}")
            content.append("")

        # Создаем файл в памяти
        file_content = "\n".join(content)
        file = discord.File(
            io.BytesIO(file_content.encode('utf-8')),
            filename=f"DeletedMessages_{datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.txt"
        )

        # Получаем информацию о модераторе
        try:
            async for entry in filtered_messages[0].guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
                moderator = entry.user
                reason = entry.reason
                break
        except discord.Forbidden:
            moderator = None
            reason = None

        embed = create_embed(
            title="🗑️ Массовое удаление сообщений",
            description=f"{EMOJIS['DOT']} **Канал:** {filtered_messages[0].channel.mention}\n"
                      f"{EMOJIS['DOT']} **Количество сообщений:** `{len(filtered_messages)}`\n"
                      f"{EMOJIS['DOT']} **Модератор:** {moderator.mention if moderator else 'Неизвестно'}\n"
                      f"{EMOJIS['DOT']} **Причина:** `{reason or 'Не указана'}`\n\n"
                      f"📎 Полный список удаленных сообщений в файле.",
            footer={"text": f"ID канала: {filtered_messages[0].channel.id}"}
        )

        # Отправляем файл в канал логов
        await self.log_event(embed, file=file)

async def setup(bot):
    await bot.add_cog(Logs(bot)) 