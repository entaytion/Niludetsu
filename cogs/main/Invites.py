import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

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
    """Класс для отслеживания входов на сервер"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.guild_invites = {}
        
    async def load_invite_cache(self, guild_id: str):
        """Загрузка кеша инвайтов из базы данных"""
        try:
            results = await self.db.fetch_all(
                """
                SELECT invite_code, uses, inviter_id
                FROM invite_cache
                WHERE guild_id = ?
                """,
                guild_id
            )
            
            self.guild_invites[guild_id] = {
                row['invite_code']: row['uses'] for row in results
            }
        except Exception as e:
            print(f"❌ Ошибка при загрузке кеша инвайтов: {e}")
            
    async def save_invite_cache(self, guild_id: str, invites: dict):
        """Сохранение кеша инвайтов в базу данных"""
        try:
            # Удаляем старые записи
            await self.db.execute(
                "DELETE FROM invite_cache WHERE guild_id = ?",
                guild_id
            )
            
            # Добавляем новые записи
            for invite_code, uses in invites.items():
                await self.db.execute(
                    """
                    INSERT INTO invite_cache (guild_id, invite_code, uses)
                    VALUES (?, ?, ?)
                    """,
                    guild_id, invite_code, uses
                )
        except Exception as e:
            print(f"❌ Ошибка при сохранении кеша инвайтов: {e}")
            
    async def cache_invites(self, guild: discord.Guild):
        """Кэширование текущих приглашений сервера"""
        try:
            invites = await guild.invites()
            current_invites = {invite.code: invite.uses for invite in invites}
            
            # Добавляем vanity url если есть
            if guild.vanity_url:
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        current_invites[vanity.code] = vanity.uses
                except:
                    pass
                    
            # Сохраняем в память и базу данных
            self.guild_invites[guild.id] = current_invites
            await self.save_invite_cache(str(guild.id), current_invites)
            
        except Exception as e:
            print(f"❌ Ошибка при кэшировании инвайтов: {e}")
            
    async def get_used_invite(self, guild: discord.Guild) -> Tuple[str, discord.Member]:
        """Определяет использованное приглашение"""
        try:
            # Получаем текущие приглашения
            current_invites = await guild.invites()
            current_uses = {invite.code: invite.uses for invite in current_invites}
            
            # Проверяем vanity url
            if guild.vanity_url:
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        current_uses[vanity.code] = vanity.uses
                except:
                    pass
            
            # Загружаем сохраненные данные
            await self.load_invite_cache(str(guild.id))
            
            # Сравниваем с сохраненными
            if guild.id in self.guild_invites:
                old_uses = self.guild_invites[guild.id]
                
                # Ищем приглашение с увеличенным счетчиком использований
                for invite in current_invites:
                    old_count = old_uses.get(invite.code, 0)
                    new_count = current_uses.get(invite.code, 0)
                    
                    if new_count > old_count:
                        return invite.code, invite.inviter
                        
                # Проверяем vanity url
                if guild.vanity_url:
                    vanity_code = guild.vanity_url.code
                    old_count = old_uses.get(vanity_code, 0)
                    new_count = current_uses.get(vanity_code, 0)
                    
                    if new_count > old_count:
                        return vanity_code, None
                        
            # Обновляем кэш
            await self.cache_invites(guild)
            
        except Exception as e:
            print(f"❌ Ошибка при определении использованного приглашения: {e}")
            
        return None, None
            
    async def get_invite_source(self, member: discord.Member) -> Tuple[str, str]:
        """Определяет источник входа участника"""
        if member.bot:
            return InviteSource.INTEGRATION, "🤖 Бот добавлен через OAuth2"
            
        invite_code, inviter = await self.get_used_invite(member.guild)
        
        if invite_code:
            if member.guild.vanity_url and invite_code == member.guild.vanity_url.code:
                return InviteSource.VANITY, f"🌟 Персональная ссылка сервера ({invite_code})"
            elif inviter:
                if inviter.id == self.bot.user.id:
                    return InviteSource.SERVER, f"🤖 Приглашение от бота ({invite_code})"
                else:
                    return InviteSource.SERVER, f"👤 Приглашение от {inviter.mention} ({invite_code})"
                    
        return InviteSource.UNKNOWN, "🔍 Источник не определен"
            
    async def format_join_message(self, member: discord.Member) -> discord.Embed:
        """Форматирует сообщение о входе участника"""
        embed = Embed(
            title=f"👋 Новый {'бот' if member.bot else 'участник'} #{len(member.guild.members)}",
            color=0x2ecc71 if not member.bot else 0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Определяем тип аккаунта
        account_type, account_info = self.get_account_type(member)
        
        # Определяем источник входа
        invite_source, source_info = await self.get_invite_source(member)
        
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
        
        # Информация об источнике
        embed.add_field(
            name="📨 Источник входа",
            value=source_info,
            inline=False
        )
            
        # Добавляем предупреждение для подозрительных аккаунтов
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
        embed = Embed(
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
        """Обработка входа участника"""
        try:
            channel_id = await self.get_log_channel(member.guild.id)
            if not channel_id:
                return
                
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = await self.format_join_message(member)
                await channel.send(embed=embed)
                
        except Exception as e:
            print(f"❌ Ошибка при логировании входа: {e}")
            
    async def on_member_remove(self, member: discord.Member):
        """Обработка выхода участника"""
        try:
            channel_id = await self.get_log_channel(member.guild.id)
            if not channel_id:
                return
                
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = await self.format_leave_message(member)
                await channel.send(embed=embed)
                
        except Exception as e:
            print(f"❌ Ошибка при логировании выхода: {e}")

class InvitesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker = InviteTracker(bot)
        self._last_member = None
        
    async def cog_load(self):
        """Инициализация при загрузке кога"""
        for guild in self.bot.guilds:
            await self.tracker.cache_invites(guild)
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Проверяем, не был ли этот участник уже обработан
        if self._last_member and self._last_member.id == member.id:
            return
        self._last_member = member
        await self.tracker.on_member_join(member)
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.tracker.on_member_remove(member)
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """При входе на новый сервер"""
        await self.tracker.cache_invites(guild)
        
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """При создании нового приглашения"""
        await self.tracker.cache_invites(invite.guild)
        
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """При удалении приглашения"""
        await self.tracker.cache_invites(invite.guild)

async def setup(bot):
    await bot.add_cog(InvitesCog(bot)) 