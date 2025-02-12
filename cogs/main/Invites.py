import discord
from discord import app_commands
from discord.ext import commands
import yaml
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class AccountType:
    NORMAL = "Обычный"
    NEW = "Новый"
    SUSPICIOUS = "Подозрительный"

class InviteSource:
    UNKNOWN = "Неизвестно"
    DISCORD = "Discord"
    SERVER = "Сервер"
    VANITY = "Персональная ссылка"
    INTEGRATION = "Интеграция"
    TWITTER = "Twitter"
    FACEBOOK = "Facebook"
    INSTAGRAM = "Instagram"
    REDDIT = "Reddit"
    YOUTUBE = "YouTube"
    TWITCH = "Twitch"
    STEAM = "Steam"
    XBOX = "Xbox"
    PLAYSTATION = "PlayStation"
    MOBILE = "Мобильное приложение"
    DESKTOP = "Компьютер"
    WEB = "Веб-браузер"

    @staticmethod
    def get_platform_emoji(source: str) -> str:
        emoji_map = {
            "TWITTER": "🐦",
            "FACEBOOK": "👥",
            "INSTAGRAM": "📸",
            "REDDIT": "🤖",
            "YOUTUBE": "🎥",
            "TWITCH": "📺",
            "STEAM": "🎮",
            "XBOX": "🟩",
            "PLAYSTATION": "🎯",
            "MOBILE": "📱",
            "DESKTOP": "💻",
            "WEB": "🌐",
            "UNKNOWN": "❓"
        }
        return emoji_map.get(source, "❓")

    @staticmethod
    def from_invite_source(source: Optional[str]) -> Tuple[str, str]:
        """Преобразует источник приглашения в читаемый формат"""
        if not source:
            return "UNKNOWN", f"❓ Источник не определен"
            
        source = source.upper()
        platform = source.split('_')[0] if '_' in source else source
        
        if platform in ["TWITTER", "FACEBOOK", "INSTAGRAM", "REDDIT", "YOUTUBE", "TWITCH"]:
            emoji = InviteSource.get_platform_emoji(platform)
            return platform, f"{emoji} {platform.capitalize()}"
        elif platform in ["DESKTOP", "MOBILE", "WEB"]:
            emoji = InviteSource.get_platform_emoji(platform)
            return platform, f"{emoji} {platform.capitalize()}"
        elif platform in ["XBOX", "PLAYSTATION", "STEAM"]:
            emoji = InviteSource.get_platform_emoji(platform)
            return platform, f"{emoji} {platform}"
        else:
            return "UNKNOWN", f"❓ Неизвестный источник ({source})"

class InviteTracker:
    def __init__(self, bot):
        self.bot = bot
        self.invites: Dict[int, List[discord.Invite]] = {}
        self.invite_uses: Dict[int, Dict[str, int]] = {}
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            self.settings = self.config.get('invites', {})
        
    def save_settings(self):
        """Сохраняет настройки в файл"""
        self.config['invites'] = self.settings
        with open('data/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, indent=4, allow_unicode=True)

    async def cache_invites(self):
        """Кэширует все текущие инвайты для всех серверов"""
        print("[Invites] Начало кэширования инвайтов...")
        for guild in self.bot.guilds:
            try:
                guild_invites = await guild.invites()
                self.invites[guild.id] = guild_invites
                print(f"[Invites] Кэшировано {len(guild_invites)} инвайтов для {guild.name}")
            except discord.Forbidden:
                print(f"[Invites] Нет прав для просмотра инвайтов на сервере {guild.name}")
                continue
            except Exception as e:
                print(f"[Invites] Ошибка при кэшировании инвайтов для {guild.name}: {e}")
                continue
        print("[Invites] Кэширование инвайтов завершено")

    async def get_used_invite(self, guild: discord.Guild) -> Optional[discord.Invite]:
        """Определяет, какой инвайт был использован"""
        try:
            current_invites = await guild.invites()
            
            # Получаем старые инвайты
            old_invites = self.invites.get(guild.id, [])
            
            # Ищем инвайт, количество использований которого изменилось
            for invite in current_invites:
                # Ищем соответствующий старый инвайт
                old_invite = discord.utils.get(old_invites, code=invite.code)
                
                if old_invite is None:
                    # Если это новый инвайт и он уже был использован
                    if invite.uses > 0:
                        # Обновляем кэш и возвращаем этот инвайт
                        self.invites[guild.id] = current_invites
                        return invite
                elif invite.uses > old_invite.uses:
                    # Если количество использований увеличилось
                    self.invites[guild.id] = current_invites
                    return invite
            
            # Проверяем, не был ли использован временный инвайт, который уже удален
            for old_invite in old_invites:
                if not discord.utils.get(current_invites, code=old_invite.code):
                    # Если старый инвайт больше не существует, возможно он был использован
                    return old_invite
                    
            # Обновляем кэш в любом случае
            self.invites[guild.id] = current_invites
                    
        except discord.Forbidden:
            print(f"[Invites] Нет прав для просмотра инвайтов на сервере {guild.name}")
            return None
        except Exception as e:
            print(f"[Invites] Ошибка при получении инвайтов: {e}")
            return None
            
        return None

    def get_log_channel(self, guild_id: int) -> Optional[int]:
        """Получает ID канала для логов"""
        return self.settings.get('channel')

    def get_account_type(self, member: discord.Member) -> Tuple[str, str]:
        """Определяет тип аккаунта участника"""
        account_age = datetime.now(timezone.utc) - member.created_at
        
        if account_age < timedelta(days=3):
            return AccountType.SUSPICIOUS, f"⚠️ Аккаунт создан менее 3 дней назад ({account_age.days} дн.)"
        elif account_age < timedelta(days=7):
            return AccountType.NEW, f"ℹ️ Новый аккаунт ({account_age.days} дн.)"
        else:
            return AccountType.NORMAL, f"✅ Обычный аккаунт ({account_age.days} дн.)"

    def get_invite_source(self, invite: Optional[discord.Invite]) -> Tuple[str, str]:
        """Определяет источник приглашения"""
        if not invite:
            return InviteSource.UNKNOWN, "🔍 Источник не определен"
            
        # Проверяем источник приглашения
        if hasattr(invite, 'source'):
            platform, source_text = InviteSource.from_invite_source(invite.source)
            return platform, source_text
            
        # Если источник не определен, используем стандартную логику
        if invite.guild and invite.guild.vanity_url_code and invite.code == invite.guild.vanity_url_code:
            return InviteSource.VANITY, "🌟 Персональная ссылка сервера"
        elif invite.inviter and invite.inviter.bot:
            return InviteSource.INTEGRATION, f"🤖 Интеграция ({invite.inviter.name})"
        elif "discord.gg/" in (invite.code or ""):
            return InviteSource.DISCORD, "🔗 Ссылка Discord"
        else:
            return InviteSource.SERVER, "🏠 Серверное приглашение"

    async def format_join_message(self, member: discord.Member, invite: Optional[discord.Invite]) -> discord.Embed:
        """Форматирует сообщение о входе участника"""
        embed=Embed(
            title=f"👋 Новый {'бот' if member.bot else 'участник'} #{len(member.guild.members)}",
            color=0x2ecc71 if not member.bot else 0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Определяем тип аккаунта
        account_type, account_info = self.get_account_type(member)
        
        # Определяем источник приглашения
        invite_source, source_info = self.get_invite_source(invite)
        
        # Основная информация об участнике
        embed.add_field(
            name=f"{'🤖' if member.bot else '👤'} {'Бот' if member.bot else 'Участник'}",
            value=f"{member.mention}\n`{member.name}`\nID: `{member.id}`",
            inline=False
        )
        
        # Информация об аккаунте
        created_timestamp = int(member.created_at.timestamp())
        embed.add_field(
            name="📅 Информация об аккаунте",
            value=f"Создан: <t:{created_timestamp}:D> (<t:{created_timestamp}:R>)\n{account_info if not member.bot else '🤖 Бот'}",
            inline=False
        )
        
        # Информация о приглашении
        if invite:
            inviter = invite.inviter
            invite_info = [
                f"🔗 Код: `{invite.code}`",
                f"👥 Добавил: {inviter.mention if inviter else 'Неизвестно'}",
                f"📊 Использований: `{invite.uses}`",
                f"📨 Источник: {source_info}"
            ]
            
            if invite.channel:
                invite_info.append(f"📝 Канал: {invite.channel.mention}")
                
            if invite.expires_at:
                expires_timestamp = int(invite.expires_at.timestamp())
                invite_info.append(f"⌛ Истекает: <t:{expires_timestamp}:R>")
            else:
                invite_info.append("⌛ Истекает: Никогда")
                
            embed.add_field(
                name="📨 Информация о приглашении",
                value="\n".join(invite_info),
                inline=False
            )
        else:
            embed.add_field(
                name="📨 Информация о приглашении",
                value="❓ Не удалось определить источник приглашения",
                inline=False
            )
            
        # Добавляем предупреждение для подозрительных аккаунтов (только для обычных пользователей)
        if not member.bot:
            if account_type == AccountType.SUSPICIOUS:
                embed.description = "⚠️ **Внимание!** Этот аккаунт был создан совсем недавно и может быть подозрительным!"
                embed.color = 0xe74c3c
            elif account_type == AccountType.NEW:
                embed.description = "ℹ️ Это новый аккаунт Discord"
                embed.color = 0xf1c40f
            
        return embed

    async def format_leave_message(self, member: discord.Member) -> discord.Embed:
        """Форматирует сообщение о выходе участника"""
        embed=Embed(
            title=f"👋 {'Бот' if member.bot else 'Участник'} покинул сервер",
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Основная информация об участнике
        embed.add_field(
            name=f"{'🤖' if member.bot else '👤'} {'Бот' if member.bot else 'Участник'}",
            value=f"`{member.name}`\nID: `{member.id}`",
            inline=False
        )
        
        # Информация о ролях
        if member.roles[1:]:  # Исключаем @everyone
            roles = [role.mention for role in reversed(member.roles[1:])]
            roles_str = " ".join(roles[:10])
            if len(member.roles) > 11:
                roles_str += f"\n*...и еще {len(member.roles) - 11} ролей*"
            embed.add_field(
                name=f"👑 Роли ({len(member.roles) - 1})",
                value=roles_str,
                inline=False
            )
            
        # Информация о времени на сервере
        joined_at = member.joined_at
        if joined_at:
            joined_timestamp = int(joined_at.timestamp())
            time_on_server = datetime.now(timezone.utc) - joined_at
            days = time_on_server.days
            hours = time_on_server.seconds // 3600
            minutes = (time_on_server.seconds % 3600) // 60
            
            time_parts = []
            if days > 0:
                time_parts.append(f"{days} {'дней' if days % 10 != 1 or days == 11 else 'день'}")
            if hours > 0:
                time_parts.append(f"{hours} {'часов' if hours % 10 != 1 or hours == 11 else 'час'}")
            if minutes > 0:
                time_parts.append(f"{minutes} {'минут' if minutes % 10 != 1 or minutes == 11 else 'минуту'}")
                
            time_str = ", ".join(time_parts) if time_parts else "менее минуты"
            
            embed.add_field(
                name="⏱️ Информация о пребывании",
                value=f"Присоединился: <t:{joined_timestamp}:D> (<t:{joined_timestamp}:R>)\nПробыл на сервере: {time_str}",
                inline=False
            )
            
        # Информация об аккаунте
        created_timestamp = int(member.created_at.timestamp())
        account_age = datetime.now(timezone.utc) - member.created_at
        account_age_days = account_age.days
        
        embed.add_field(
            name="📅 Информация об аккаунте",
            value=f"Создан: <t:{created_timestamp}:D> (<t:{created_timestamp}:R>)\nВозраст аккаунта: {account_age_days} {'дней' if account_age_days % 10 != 1 or account_age_days == 11 else 'день'}",
            inline=False
        )
        
        return embed

    async def on_member_join(self, member: discord.Member):
        """Обработчик события входа участника"""
        guild = member.guild
        log_channel_id = self.get_log_channel(guild.id)
        if not log_channel_id:
            return
            
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        invite = await self.get_used_invite(guild)
        embed = await self.format_join_message(member, invite)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def on_member_remove(self, member: discord.Member):
        """Обработчик события выхода участника"""
        guild = member.guild
        log_channel_id = self.get_log_channel(guild.id)
        if not log_channel_id:
            return
            
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = await self.format_leave_message(member)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def setup(self):
        """Инициализация трекера"""
        # Проверяем и кэшируем канал для логов
        if not self.settings.get('channel'):
            print("❌ Канал для логов инвайтов не настроен")
            return
            
        # Кэшируем текущие инвайты
        await self.cache_invites()

class InvitesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_tracker = InviteTracker(bot)
        
    async def cog_load(self):
        await self.invite_tracker.setup()
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.invite_tracker.on_member_join(member)
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.invite_tracker.on_member_remove(member)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Обработчик создания нового инвайта"""
        if invite.guild.id in self.invite_tracker.invites:
            self.invite_tracker.invites[invite.guild.id].append(invite)
            print(f"[Invites] Новый инвайт {invite.code} добавлен в кэш для {invite.guild.name}")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Обработчик удаления инвайта"""
        if invite.guild.id in self.invite_tracker.invites:
            guild_invites = self.invite_tracker.invites[invite.guild.id]
            self.invite_tracker.invites[invite.guild.id] = [i for i in guild_invites if i.code != invite.code]
            print(f"[Invites] Инвайт {invite.code} удален из кэша для {invite.guild.name}")

async def setup(bot):
    await bot.add_cog(InvitesCog(bot)) 