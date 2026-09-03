import Niludetsu.config as config

class AccessGuard:
    def __init__(self, bot):
        self.bot = bot

    @property
    def allowed_guilds(self) -> list[int]:
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
        return sorted(list(self.bot.cogs.keys()))

    def set_category_enabled(self, guild_id: int, category: str, enabled: bool):
        pass

    def is_command_allowed(self, guild_id: int, command_name: str):
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return True
        cog = cmd.cog
        if not cog:
            return True
        cog_name = cog.qualified_name

        if cog_name == "Owner":
            return True

        cm = getattr(self.bot, "config_manager", None)
        if cm:
            status = cm.get_custom_text(guild_id, "cogs", cog_name, "enabled")
            if status == "disabled":
                return False
        return True
