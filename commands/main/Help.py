import discord
from discord.ext import commands
from Niludetsu import Embed, config
from Niludetsu.tools.CommandRegistry import CommandType, get_command_registry

def build_help_notes(context_type: str) -> str:
    legend_lines = [
        "**Обозначения:**",
        "> `[]` — обязательный параметр",
        "> `<>` — необязательный параметр",
    ]

    if context_type == "prefix":
        prefixes = " ".join(sorted(config.PREFIX["MAIN_SERVER"]))
        legend_lines.append(f"> Префиксы: `{prefixes}`")

    legend_lines.extend(
        [
            "> 🔹 — только префикс",
            "> 🔸 — только slash",
            "> ◽ — гибридная команда (префикс + slash)",
        ]
    )

    return "\n".join(legend_lines)

def chunk_lines(lines: list[str], *, limit: int = 1024) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        entry_len = len(line) + 1

        if current and current_len + entry_len > limit:
            chunks.append(current)
            current = []
            current_len = 0

        if entry_len > limit:
            slice_start = 0
            while slice_start < len(line):
                slice_end = min(slice_start + limit, len(line))
                chunks.append([line[slice_start:slice_end]])
                slice_start = slice_end
            continue

        current.append(line)
        current_len += entry_len

    if current:
        chunks.append(current)

    return chunks

def format_command_name(cmd, prefix):
    cmd_type = cmd.get("type", CommandType.HYBRID)

    if cmd_type == CommandType.SLASH:
        return f"/{cmd['name']}"
    if cmd_type == CommandType.HYBRID:
        return f"{prefix}{cmd['name']}"
    return f"{prefix}{cmd['name']}"

def build_intro_embed(categories, prefix, context_type, guild):
    notes = build_help_notes(context_type)
    intro_lines = [
        "**Привет!** Это интерактивная справка по командам бота.",
        "Используйте выпадающее меню ниже, чтобы выбрать категорию и посмотреть доступные команды.",
    ]

    embed = Embed.default(description=f"{notes}\n\n" + "\n".join(intro_lines))

    category_lines = []
    total_commands = 0

    for _, cat_info in sorted(categories.items(), key=lambda x: x[1]['title']):
        command_count = len(cat_info["command_list"])
        total_commands += command_count
        category_lines.append(f"{cat_info['emoji']} **{cat_info['title']}** · `{command_count}`")

    if category_lines:
        for index, chunk in enumerate(chunk_lines(category_lines)):
            formatted = "\n".join(f"- {line}" for line in chunk)
            name = "> Категории команд:" if index == 0 else "\u200b"
            embed.add_field(name=name, value=formatted, inline=True)

    guild_name = guild.name if guild else "Неизвестный сервер"
    stats_lines = [
        f"- **Всего команд:** `{total_commands}`",
        f"- **Категорий:** `{len(categories)}`",
        f"- **Сервер:** {guild_name}",
    ]
    embed.add_field(name="> Краткая статистика:", value="\n".join(stats_lines), inline=True)

    if guild and guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name="Справка | Niludetsu")

    return embed

def build_category_embed(cat_info, prefix, context_type):
    """Строит embed для конкретной категории"""
    commands = sorted(cat_info["command_list"], key=lambda x: x["name"])

    notes = build_help_notes(context_type)
    description = [notes, ""]

    for cmd in commands:
        cmd_type = cmd.get("type", CommandType.HYBRID)

        # Формируем строку с алиасами
        aliases_str = ""
        if cmd.get("aliases") and cmd_type != CommandType.SLASH:
            aliases_str = f" | {', '.join(sorted(cmd['aliases']))}"

        # Формируем строку с аргументами
        args_str = ""
        required_args = [f"[{arg}]" for arg in cmd.get("required_args", [])]
        optional_args = [f"<{arg}>" for arg in cmd.get("optional_args", [])]
        if required_args or optional_args:
            args_str = f" {' '.join(required_args)} {' '.join(optional_args)}".strip()

        # Формируем имя команды
        cmd_name = format_command_name(cmd, prefix)

        # Добавляем индикатор типа команды
        type_indicator = ""
        if cmd_type == CommandType.PREFIX:
            type_indicator = "🔹 "
        elif cmd_type == CommandType.SLASH:
            type_indicator = "🔸 "
        elif cmd_type == CommandType.HYBRID:
            type_indicator = "◽ "

        cmd_str = f"- {type_indicator}`{cmd_name}{aliases_str}`"
        if args_str:
            cmd_str = f"- {type_indicator}`{cmd_name}{aliases_str} {args_str}`"
        cmd_str += f" — {cmd['description']}"
        description.append(cmd_str)

    if len(description) == 2:
        description.append("Нет доступных команд в этой категории")

    body_lines = description[2:]
    body = "\n".join(description).strip()

    embed = Embed.default(
        title=f"{cat_info['emoji']} {cat_info['title']}",
        description=body if len(body) <= 4096 else None
    )

    if embed.description is None:
        embed.description = notes
        for index, chunk in enumerate(chunk_lines(body_lines)):
            name = "Команды" if index == 0 else "\u200b"
            embed.add_field(name=name, value="\n".join(chunk), inline=False)

    return embed

class CategorySelect(discord.ui.Select):
    def __init__(self, categories, prefix, context_type, guild):
        self.categories = categories
        self.prefix = prefix
        self.context_type = context_type
        self.guild = guild

        options = []

        for cat_name, cat_info in sorted(categories.items(), key=lambda x: x[1]['title']):
            count = len(cat_info["command_list"])
            description = f"{count} команд" if count else "Нет доступных команд"
            options.append(
                discord.SelectOption(
                    label=cat_info["title"],
                    value=cat_name,
                    emoji=cat_info["emoji"],
                    description=description
                )
            )

        super().__init__(
            placeholder="📜 Посмотреть список команд",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]

        for option in self.options:
            option.default = option.value == value

        cat_info = self.categories.get(value)
        if not cat_info:
            await interaction.response.defer()
            return

        embed = build_category_embed(cat_info, self.prefix, self.context_type)

        try:
            await interaction.response.edit_message(embed=embed, view=self.view)
        except discord.errors.NotFound:
            await interaction.followup.send(
                embed=Embed.error(description="Это меню устарело. Используйте команду help еще раз!"),
                ephemeral=True
            )

class HelpView(discord.ui.View):
    def __init__(self, categories, prefix, context_type, guild):
        super().__init__(timeout=180)
        self.message = None
        self.select = CategorySelect(categories, prefix, context_type, guild)
        self.add_item(self.select)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    def get_context_type(self, ctx):
        """Определяет тип контекста вызова команды"""
        if ctx.interaction:
            return "slash"
        return "prefix"

    async def get_prefix(self, ctx):
        """Получает префикс из контекста"""
        if ctx.interaction:
            return "/"

        message_content = ctx.message.content
        for prefix in config.PREFIX["MAIN_SERVER"]:
            if message_content.startswith(prefix):
                return prefix
        return config.PREFIX["MAIN_SERVER"][0]

    @commands.hybrid_command(
        name="help",
        description="📖 Показать список команд",
        aliases=["помощь", "команды", "хелп"]
    )
    async def help(self, ctx):
        prefix = await self.get_prefix(ctx)
        context_type = self.get_context_type(ctx)
        categories = self.build_categories()

        embed = build_intro_embed(categories, prefix, context_type, ctx.guild)
        view = HelpView(categories, prefix, context_type, ctx.guild)

        message = await ctx.send(embed=embed, view=view)
        view.message = message

    def _is_command_available(self, cmd, context_type):
        """Проверяет доступна ли команда в данном контексте"""
        cmd_type = cmd.get("type", CommandType.HYBRID)

        if context_type == "prefix":
            return cmd_type in [CommandType.PREFIX, CommandType.HYBRID]
        elif context_type == "slash":
            return cmd_type in [CommandType.SLASH, CommandType.HYBRID]

        return True

    def build_categories(self):
        return get_command_registry()

async def setup(bot):
    await bot.add_cog(Help(bot))

