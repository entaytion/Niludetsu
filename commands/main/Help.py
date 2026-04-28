import discord
from discord.ext import commands
from Niludetsu import Embed, config

CAT_INFO = {
    "economy":     ("Экономика",   "💰"),
    "profile":     ("Профиль",     "👤"),
    "fun":         ("Развлечения", "🎮"),
    "moderation":  ("Модерация",   "🛡️"),
    "system":      ("Система",     "⚙️"),
    "main":        ("Основное",    "🏠"),
    "utilities":   ("Утилиты",     "🛠️"),
    "tools":       ("Инструменты", "🔧"),
    "partnership": ("Партнерство", "🤝"),
    "marriage":    ("Семья",       "💍"),
}

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    def build_categories(self):
        """Динамически собирает команды из бота и группирует по папкам."""
        categories = {}
        for cmd in self.bot.commands:
            if cmd.hidden: continue

            module = cmd.module.split(".")
            folder = module[1] if len(module) > 1 else "main"

            if folder not in categories:
                title, emoji = CAT_INFO.get(folder, (folder.capitalize(), "❓"))
                categories[folder] = {"title": title, "emoji": emoji, "command_list": []}

            raw_desc = cmd.description or cmd.help or "Нет описания"
            categories[folder]["command_list"].append({
                "name": cmd.name,
                "aliases": list(cmd.aliases),
                "description": raw_desc,
                "type": "hybrid" if isinstance(cmd, commands.HybridCommand) else "prefix"
            })
        return categories

    @commands.hybrid_command(name="help", description="Список всех команд бота")
    async def help(self, ctx):
        categories = self.build_categories()
        prefix = "/" if ctx.interaction else (ctx.prefix or "!")
        
        embed = Embed.default(title="Справка по командам", description="Выберите категорию из списка ниже.")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        for k, v in categories.items():
            embed.add_field(name=f"{v['emoji']} {v['title']}", value=f"`{len(v['command_list'])}` команд", inline=True)
            
        view = HelpView(categories, prefix, ctx.author.id)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

class HelpView(discord.ui.View):
    def __init__(self, categories, prefix, owner_id):
        super().__init__(timeout=180)
        self.categories, self.prefix, self.owner_id = categories, prefix, owner_id
        self.add_item(CategorySelect(categories, prefix))

    async def interaction_check(self, i):
        if i.user.id != self.owner_id:
            await i.response.send_message("Это не ваше меню!", ephemeral=True)
            return False
        return True

class CategorySelect(discord.ui.Select):
    def __init__(self, categories, prefix):
        self.categories, self.prefix = categories, prefix
        options = [discord.SelectOption(label=v["title"], value=k, emoji=v["emoji"]) for k, v in categories.items()]
        super().__init__(placeholder="Выберите категорию...", options=options)

    async def callback(self, i: discord.Interaction):
        cat = self.categories[self.values[0]]
        embed = Embed.default(title=f"{cat['emoji']} {cat['title']}")
        
        lines = []
        for c in sorted(cat["command_list"], key=lambda x: x["name"]):
            type_icon = "◽" if c["type"] == "hybrid" else "🔹"
            lines.append(f"{type_icon} `{self.prefix}{c['name']}` — {c['description']}")
        
        embed.description = "\n".join(lines)
        await i.response.edit_message(embed=embed)

async def setup(bot): await bot.add_cog(Help(bot))
