import discord
from discord import app_commands
from discord.ext import commands
import yaml
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from utils import create_embed, EMOJIS

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
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            self.settings = self.config.get('invites', {})
        
    def save_settings(self):
        """Сохраняет настройки в файл"""
        self.config['invites'] = self.settings
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, indent=4, allow_unicode=True)

    async def cache_invites(self):
        """Кэширует все текущие инвайты для всех серверов"""
        for guild in self.bot.guilds:
            try:
                guild_invites = await guild.invites()
                self.invites[guild.id] = guild_invites
                self.invite_uses[guild.id] = {invite.code: invite.uses for invite in guild_invites}
            except discord.Forbidden:
                continue

    async def get_used_invite(self, guild: discord.Guild) -> Optional[discord.Invite]:
        """Определяет, какой инвайт был использован"""
        try:
            current_invites = await guild.invites()
            
            # Получаем старые использования инвайтов
            old_uses = self.invite_uses.get(guild.id, {})
            
            # Обновляем кэш текущих инвайтов
            self.invites[guild.id] = current_invites
            self.invite_uses[guild.id] = {invite.code: invite.uses for invite in current_invites}
            
            # Ищем инвайт, количество использований которого изменилось
            for invite in current_invites:
                old_uses_count = old_uses.get(invite.code, 0)
                if invite.uses > old_uses_count:
                    return invite
                    
        except discord.Forbidden:
            return None
            
        return None

    def get_log_channel(self, guild_id: int) -> Optional[int]:
        """Получает ID канала для логов"""
        return self.settings.get('log_channels', {}).get(str(guild_id))

    def set_log_channel(self, guild_id: int, channel_id: int):
        """Устанавливает канал для логов"""
        if 'log_channels' not in self.settings:
            self.settings['log_channels'] = {}
        self.settings['log_channels'][str(guild_id)] = channel_id
        self.save_settings()

    def set_welcome_message(self, guild_id: int, message: str):
        """Устанавливает приветственное сообщение"""
        if 'welcome_messages' not in self.settings:
            self.settings['welcome_messages'] = {}
        self.settings['welcome_messages'][str(guild_id)] = message
        self.save_settings()

    def set_leave_message(self, guild_id: int, message: str):
        """Устанавливает сообщение при выходе"""
        if 'leave_messages' not in self.settings:
            self.settings['leave_messages'] = {}
        self.settings['leave_messages'][str(guild_id)] = message
        self.save_settings()

    def get_welcome_message(self, guild_id: int) -> str:
        """Получает приветственное сообщение"""
        return self.settings.get('welcome_messages', {}).get(
            str(guild_id),
            "👋 {member.mention} присоединился к серверу!\n" +
            "📨 Приглашение от: {inviter.mention}\n" +
            "📊 Использований: {invite.uses}"
        )

    def get_leave_message(self, guild_id: int) -> str:
        """Получает сообщение при выходе"""
        return self.settings.get('leave_messages', {}).get(
            str(guild_id),
            "👋 {member} покинул сервер\n" +
            "⏱️ Пробыл на сервере: {time_on_server}"
        )

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
        embed = create_embed(
            title="Участник присоединился",
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Определяем тип аккаунта
        account_type, account_info = self.get_account_type(member)
        
        # Определяем источник приглашения
        invite_source, source_info = self.get_invite_source(invite)
        
        fields = [
            ("👤 Участник", f"{member.mention} ({member})", True),
            ("🏷️ ID", member.id, True),
            ("📅 Аккаунт создан", f"<t:{int(member.created_at.timestamp())}:R>", True),
            ("🔍 Тип аккаунта", account_info, True),
            ("📨 Источник", source_info, True)
        ]
        
        if invite:
            inviter = invite.inviter
            fields.extend([
                ("🔗 Приглашение", f"discord.gg/{invite.code}", True),
                ("👥 Пригласил", f"{inviter.mention} ({inviter})" if inviter else "Неизвестно", True),
                ("📊 Использований", invite.uses, True),
                ("⏱️ Создано", f"<t:{int(invite.created_at.timestamp())}:R>", True),
                ("♾️ Бесконечное", "Да" if invite.max_uses == 0 else "Нет", True),
                ("⌛ Истекает", f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Никогда", True)
            ])
            
            # Добавляем информацию о канале приглашения
            if invite.channel:
                fields.append(("📝 Канал", f"{invite.channel.mention} ({invite.channel.name})", True))
        
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        # Добавляем предупреждение для подозрительных аккаунтов
        if account_type == AccountType.SUSPICIOUS:
            embed.description = f"⚠️ **Внимание!** Аккаунт создан совсем недавно!"
            
        return embed

    async def format_leave_message(self, member: discord.Member) -> discord.Embed:
        """Форматирует сообщение о выходе участника"""
        embed = create_embed(
            title="Участник покинул сервер",
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        time_on_server = datetime.now(timezone.utc) - member.joined_at
        days = time_on_server.days
        hours, remainder = divmod(time_on_server.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        time_format = []
        if days > 0:
            time_format.append(f"{days} дн.")
        if hours > 0:
            time_format.append(f"{hours} ч.")
        if minutes > 0:
            time_format.append(f"{minutes} мин.")
        
        time_str = " ".join(time_format) if time_format else "менее минуты"
        
        fields = [
            ("👤 Участник", f"{member} ({member.id})", True),
            ("📅 Присоединился", f"<t:{int(member.joined_at.timestamp())}:R>", True),
            ("⏱️ Пробыл на сервере", time_str, True)
        ]
        
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
            
        return embed

    async def on_member_join(self, member: discord.Member):
        """Обработчик события входа участника"""
        if member.bot:
            return
            
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
        if member.bot:
            return
            
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
        
    invites = app_commands.Group(name="invites", description="Управление системой инвайтов")
    
    @invites.command(name="channel", description="Установить канал для логов инвайтов")
    @app_commands.describe(channel="Канал для логов")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.invite_tracker.set_log_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{EMOJIS['SUCCESS']} Канал для логов инвайтов установлен: {channel.mention}"
            ),
            ephemeral=True
        )
        
    @invites.command(name="welcome", description="Установить приветственное сообщение")
    @app_commands.describe(message="Текст сообщения")
    @commands.has_permissions(administrator=True)
    async def set_welcome_message(self, interaction: discord.Interaction, *, message: str):
        self.invite_tracker.set_welcome_message(interaction.guild_id, message)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{EMOJIS['SUCCESS']} Приветственное сообщение установлено!"
            ),
            ephemeral=True
        )
        
    @invites.command(name="leave", description="Установить сообщение при выходе")
    @app_commands.describe(message="Текст сообщения")
    @commands.has_permissions(administrator=True)
    async def set_leave_message(self, interaction: discord.Interaction, *, message: str):
        self.invite_tracker.set_leave_message(interaction.guild_id, message)
        await interaction.response.send_message(
            embed=create_embed(
                description=f"{EMOJIS['SUCCESS']} Сообщение при выходе установлено!"
            ),
            ephemeral=True
        )
        
    @invites.command(name="test", description="Протестировать сообщения")
    @app_commands.describe(type="Тип сообщения для теста")
    @app_commands.choices(type=[
        app_commands.Choice(name="Приветственное", value="welcome"),
        app_commands.Choice(name="При выходе", value="leave")
    ])
    @commands.has_permissions(administrator=True)
    async def test_messages(self, interaction: discord.Interaction, type: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        
        if type.value == "welcome":
            invite = None
            try:
                invites = await interaction.guild.invites()
                if invites:
                    invite = invites[0]
            except discord.Forbidden:
                pass
                
            embed = await self.invite_tracker.format_join_message(interaction.user, invite)
            await interaction.followup.send(
                content="Тест приветственного сообщения:",
                embed=embed
            )
        else:
            embed = await self.invite_tracker.format_leave_message(interaction.user)
            await interaction.followup.send(
                content="Тест сообщения при выходе:",
                embed=embed
            )
            
    @invites.command(name="info", description="Информация о приглашении")
    @app_commands.describe(code="Код приглашения (без discord.gg/)")
    @commands.has_permissions(administrator=True)
    async def invite_info(self, interaction: discord.Interaction, code: str):
        try:
            invite = await self.bot.fetch_invite(code)
            
            embed = create_embed(
                title=f"ℹ️ Информация о приглашении",
                description=f"Информация о приглашении с кодом `{code}`"
            )
            
            if invite.guild:
                embed.add_field(name="🏠 Сервер", value=invite.guild.name, inline=True)
            
            if invite.channel:
                embed.add_field(name="📝 Канал", value=invite.channel.mention, inline=True)
            
            if invite.inviter:
                embed.add_field(name="👤 Создатель", value=invite.inviter.mention, inline=True)
            
            if invite.created_at:
                embed.add_field(name="⏱️ Создано", value=f"<t:{int(invite.created_at.timestamp())}:R>", inline=True)
            
            if hasattr(invite, 'uses') and invite.uses is not None:
                embed.add_field(name="📊 Использований", value=str(invite.uses), inline=True)
            
            if hasattr(invite, 'max_uses') and invite.max_uses:
                embed.add_field(name="🔢 Макс. использований", value=str(invite.max_uses), inline=True)
            
            if hasattr(invite, 'expires_at') and invite.expires_at:
                embed.add_field(name="⌛ Истекает", value=f"<t:{int(invite.expires_at.timestamp())}:R>", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Приглашение не найдено!"
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при получении информации о приглашении: {str(e)}"
                ),
                ephemeral=True
            )

    @invites.command(name="list", description="Список активных приглашений")
    @commands.has_permissions(administrator=True)
    async def list_invites(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_invites = await interaction.guild.invites()
            
            if not guild_invites:
                await interaction.followup.send(
                    embed=create_embed(
                        description=f"{EMOJIS['INFO']} На сервере нет активных приглашений!",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return
                
            embeds = []
            current_embed = create_embed(
                title="Активные приглашения",
                timestamp=datetime.utcnow()
            )
            
            for i, invite in enumerate(guild_invites):
                # Каждые 25 полей создаем новый эмбед
                if i > 0 and i % 25 == 0:
                    embeds.append(current_embed)
                    current_embed = create_embed(
                        title="Активные приглашения (продолжение)",
                        timestamp=datetime.utcnow()
                    )
                
                inviter = invite.inviter
                channel = invite.channel
                value = (
                    f"👥 {inviter.mention if inviter else 'Неизвестно'}\n"
                    f"📝 {channel.mention if channel else 'Неизвестно'}\n"
                    f"📊 {invite.uses}/{invite.max_uses if invite.max_uses else '∞'}\n"
                    f"⏱️ Создано: <t:{int(invite.created_at.timestamp())}:R>"
                )
                
                if invite.expires_at:
                    value += f"\n⌛ Истекает: <t:{int(invite.expires_at.timestamp())}:R>"
                    
                current_embed.add_field(
                    name=f"🔗 discord.gg/{invite.code}",
                    value=value,
                    inline=True
                )
            
            embeds.append(current_embed)
            
            for embed in embeds:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except discord.Forbidden:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} У меня нет прав для просмотра приглашений!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            
async def setup(bot):
    await bot.add_cog(InvitesCog(bot)) 