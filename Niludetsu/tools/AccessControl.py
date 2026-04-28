import Niludetsu.config as config

class AccessGuard:
    def __init__(self, bot):
        self.bot = bot

    @property
    def allowed_guilds(self) -> list[int]:
        """Читає актуальні SERVERS з кешу settings при кожному зверненні."""
        return [int(config.SERVERS["MAIN_ID"])] + [int(g) for g in config.SERVERS.get("ALLOWED_ID", [])]

    async def bootstrap(self):
        for guild in self.bot.guilds:
            if guild.id not in self.allowed_guilds:
                try: await guild.leave()
                except: pass

    def prefixes_for(self, guild_id: int | None):
        if guild_id == config.SERVERS["MAIN_ID"]: return config.PREFIX["MAIN_SERVER"]
        return config.PREFIX["OTHER_SERVER"]

    def can_use_prefix_command(self, guild_id: int):
        return True

    def get_categories(self):
        return ["main", "economy", "fun", "moderation", "system", "utilities", "partnership", "profile"]

    def set_category_enabled(self, guild_id: int, category: str, enabled: bool):
        pass

    def is_command_allowed(self, guild_id: int, command_name: str):
        return True
