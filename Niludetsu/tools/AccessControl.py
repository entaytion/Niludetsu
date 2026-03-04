
import discord, re
from ..tools.CommandRegistry import get_command_registry
from ..tools.Embed import Embed
from discord.ext import commands
from Niludetsu import config
from typing import Dict, List, Optional, Set

class AccessGuard:
    """
    Объединяет управление доступами к серверам и префиксным командам.
    Содержит логику старых CommandManager, ServerManager и CheckServer.
    """

    DEFAULT_CATEGORIES = ("fun", "reactions", "tools", "main")
    DISCORD_INVITE = "https://discord.gg/HxwZ6ceKKj"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.main_server_id: int = config.SERVERS["MAIN_ID"]
        self.allowed_servers: Set[int] = set(config.SERVERS.get("ALLOWED_ID", []))

        registry = get_command_registry()
        command_categories: Dict[str, Set[str]] = {}
        for category, data in registry.items():
            entries = set()
            for item in data.get("command_list", []):
                name = item.get("name")
                if name:
                    entries.add(str(name).lower())
                for alias in item.get("aliases", []) or []:
                    entries.add(str(alias).lower())
            command_categories[category] = entries

        self._command_categories = command_categories
        self._server_settings: Dict[int, Dict[str, bool]] = {}

        # Подписываемся на события
        bot.add_listener(self._on_ready, "on_ready")
        bot.add_listener(self._on_guild_join, "on_guild_join")

    def set_category_enabled(self, guild_id: int, category: str, enabled: bool) -> None:
        if guild_id not in self._server_settings:
            self._server_settings[guild_id] = {}
        self._server_settings[guild_id][category] = enabled

    def is_command_allowed(self, guild_id: int, command_name: str) -> bool:
        command_name = command_name.lower()
        default_categories = self.DEFAULT_CATEGORIES

        if guild_id not in self._server_settings:
            return any(
                command_name in self._command_categories.get(category, set())
                for category in default_categories
            )

        for category, commands in self._command_categories.items():
            if command_name in commands:
                if (
                    category in default_categories
                    and category not in self._server_settings[guild_id]
                ):
                    return True
                return self._server_settings[guild_id].get(category, False)

        return True

    def get_categories(self) -> List[str]:
        return list(self._command_categories.keys())

    def setup_default_categories(self, guild_id: int) -> None:
        for category in self.DEFAULT_CATEGORIES:
            self.set_category_enabled(guild_id, category, True)

    def can_use_prefix_command(self, guild_id: Optional[int]) -> bool:
        if guild_id is None:
            return True
        return guild_id == self.main_server_id or guild_id in self.allowed_servers

    def prefixes_for(self, guild_id: Optional[int]) -> List[str]:
        if guild_id == self.main_server_id:
            return config.PREFIX["MAIN_SERVER"]
        return config.PREFIX["OTHER_SERVER"]

    def create_restriction_embed(self) -> discord.Embed:
        return Embed.error(
            title="Ограниченный доступ",
            description="Приветствую! Бот доступен только на некоторых серверах.\nЕсли вы хотите попасть на бета-тест (шутка!), свяжитесь с <@636570363605680139>."
        )

    async def bootstrap(self) -> None:
        await self._audit_current_guilds()
        for guild in self.bot.guilds:
            if self.can_use_prefix_command(guild.id):
                self.setup_default_categories(guild.id)

    async def _audit_current_guilds(self) -> None:
        for guild in list(self.bot.guilds):
            if not self.can_use_prefix_command(guild.id):
                channel = await self._find_suitable_channel(guild)
                await self.handle_unauthorized_guild(guild, channel)

    async def _on_guild_join(self, guild: discord.Guild) -> None:
        if not self.can_use_prefix_command(guild.id):
            channel = await self._find_suitable_channel(guild)
            await self.handle_unauthorized_guild(guild, channel)
            return

        self.setup_default_categories(guild.id)
        print(f"✅ Бот добавлен на разрешённый сервер: {guild.name} (ID: {guild.id})")

    async def _on_ready(self) -> None:
        await self._audit_current_guilds()

    async def _find_suitable_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel

        keywords = ("general", "основной", "общий", "main", "чат", "channel")
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if any(re.search(rf"(?i){re.escape(word)}", channel.name) for word in keywords):
                    return channel

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None

    async def handle_unauthorized_guild(
        self,
        guild: discord.Guild,
        channel: Optional[discord.abc.Messageable],
    ) -> None:
        if channel:
            embed = self.create_restriction_embed()
            owner_mention = f"<@{guild.owner_id}>\n{self.DISCORD_INVITE}"
            await channel.send(content=owner_mention, embed=embed)
            print(f"✅ Сообщение отправлено в канал {channel.name} на сервере {guild.name}")
        else:
            print(f"❌ Не найден канал для уведомления на сервере {guild.name}")

        await guild.leave()
        print(f"🚫 Бот покинул неразрешённый сервер: {guild.name} (ID: {guild.id})")

