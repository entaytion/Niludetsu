import discord
from discord.ext import commands
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS, EMOJIS

class CategorySelect(discord.ui.Select):
    def __init__(self, categories):
        self.categories = categories
        options = [
            discord.SelectOption(
                label=cat_info["title"],
                value=cat_name,
                description=f"Показать команды из категории {cat_info['title'].lower()}",
                emoji=cat_info["emoji"]
            ) for cat_name, cat_info in categories.items()
        ]
        super().__init__(placeholder="Выберите категорию", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            cat_info = self.categories[self.values[0]]
            embed = create_embed(
                title=f"{cat_info['emoji']} {cat_info['title']}",
                description=cat_info["description"],
                footer={
                    'text': cat_info["footer"],
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
            await interaction.response.edit_message(embed=embed, view=self.view)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Это меню устарело. Используйте `/help` еще раз!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )

class AllCommandsButton(discord.ui.Button):
    def __init__(self, categories):
        super().__init__(style=discord.ButtonStyle.secondary, label="Все команды", emoji="📚")
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        try:
            all_commands = []
            for cat_name, cat_info in self.categories.items():
                all_commands.append(f"\n{cat_info['emoji']} **{cat_info['title']}**")
                commands_list = " ".join(f"`{cmd}`" for cmd in cat_info['commands'])
                all_commands.append(commands_list)
            
            embed = create_embed(
                title="📚 Список всех команд",
                description="\n".join(all_commands),
                footer={
                    'text': "Выберите категорию ниже для подробного описания команд",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
            await interaction.response.edit_message(embed=embed)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Это меню устарело. Используйте `/help` еще раз!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )

class HelpView(discord.ui.View):
    def __init__(self, categories):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.add_item(CategorySelect(categories))
        self.add_item(AllCommandsButton(categories))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @discord.app_commands.command(name="help", description="Справочник по командам")
    async def help(self, interaction: discord.Interaction):
        categories = {
            "main": {
                "title": "Основные команды",
                "emoji": "⚙️",
                "commands": ["/help", "/reload"],
                "description": f"{EMOJIS['DOT']} `/help` — помощь.\n"
                              f"{EMOJIS['DOT']} `/reload` — перезагрузка бота.\n",
                "footer": "Справочник по командам из раздела \"Основное\""
            },
            "fun": {
                "title": "Команды для развлечений",
                "emoji": "🎮",
                "commands": ["/marry", "/divorce", "/hug", "/kiss", "/slap", "/pat", "/sex", "/bite", "/cry"],
                "description": f"{EMOJIS['DOT']} `/marry` — жениться на кого-то.\n"
                              f"{EMOJIS['DOT']} `/divorce` — развестись с кем-то.\n"
                              f"{EMOJIS['DOT']} `/hug` — обнять кого-то.\n"
                              f"{EMOJIS['DOT']} `/kiss` — поцеловать кого-то.\n"
                              f"{EMOJIS['DOT']} `/slap` — ударить кого-то.\n"
                              f"{EMOJIS['DOT']} `/pat` — погладить кого-то.\n"
                              f"{EMOJIS['DOT']} `/sex` — логично.\n"
                              f"{EMOJIS['DOT']} `/bite` — укусить кого-то.\n"
                              f"{EMOJIS['DOT']} `/cry` — заплакать.",
                "footer": "Справочник по командам для развлечений"
            },
            "music": {
                "title": "Команды для управления музыкой",
                "emoji": "🎵",
                "commands": ["/play", "/queue", "/skip", "/stop", "/pause", "/np", "/repeat", "/shuffle", "/nightcore", "/resume"],
                "description": f"{EMOJIS['DOT']} `/play` — воспроизвести песню или добавить в очередь.\n"
                              f"{EMOJIS['DOT']} `/queue` — показать текущую очередь воспроизведения.\n"
                              f"{EMOJIS['DOT']} `/skip` — пропустить текущую песню.\n"
                              f"{EMOJIS['DOT']} `/stop` — остановить воспроизведение и очистить очередь.\n"
                              f"{EMOJIS['DOT']} `/pause` — приостановить воспроизведение.\n"
                              f"{EMOJIS['DOT']} `/np` — показать текущий трек и прогресс.\n"
                              f"{EMOJIS['DOT']} `/repeat` — повторить текущую песню.\n"
                              f"{EMOJIS['DOT']} `/shuffle` — перемешать песни.\n"
                              f"{EMOJIS['DOT']} `/nightcore` — включить эффект Nightcore.\n"
                              f"{EMOJIS['DOT']} `/resume` — возобновить воспроизведение.",
                "footer": "Справочник по командам управления музыкой"
            },
            "economy": {
                "title": "Команды экономики",
                "emoji": "💰",
                "commands": ["/balance", "/shop", "/sell", "/slots", "/deposit", "/withdraw", "/daily", "/work", "/pay", "/leaderboard", "/casino", "/blackjack", "/rob"],
                "description": f"{EMOJIS['DOT']} `/balance <user>` — проверить баланс.\n"
                              f"{EMOJIS['DOT']} `/shop` — просмотреть магазин.\n"
                              f"{EMOJIS['DOT']} `/sell` — продать роль.\n"
                              f"{EMOJIS['DOT']} `/slots` — играть в слот-машину.\n"
                              f"{EMOJIS['DOT']} `/deposit [amount]` — перевести деньги в банк.\n"
                              f"{EMOJIS['DOT']} `/withdraw [amount]` — снять деньги из банка.\n"
                              f"{EMOJIS['DOT']} `/daily` — получить дневную награду (кулдаун: `24 часа`).\n"
                              f"{EMOJIS['DOT']} `/work` — пойти на работу (кулдаун: `1 час`).\n"
                              f"{EMOJIS['DOT']} `/pay [user] [amount]` — перевести деньги.\n"
                              f"{EMOJIS['DOT']} `/leaderboard` — посмотреть топ юзеров по деньгам.\n"
                              f"{EMOJIS['DOT']} `/casino [bet] [amount]` — играть в казино.\n"
                              f"{EMOJIS['DOT']} `/blackjack [bet]` — играть в блекджек.\n"
                              f"{EMOJIS['DOT']} `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).\n",
                "footer": "Справочник по командам из раздела \"Экономика\""
            },
            "profile": {
                "title": "Команды профиля",
                "emoji": "👤",
                "commands": ["/level", "/inventory"],
                "description": f"{EMOJIS['DOT']} `/level <user>` — проверить уровень.\n"
                              f"{EMOJIS['DOT']} `/inventory` — просмотреть инвентарь.\n",
                "footer": "Справочник по командам из раздела \"Профиль\""
            },
            "moderation": {
                "title": "Команды для модерации // unreleased",
                "emoji": "🛡️",
                "commands": ["/lock", "/unlock"],
                "description": f"{EMOJIS['DOT']} `/lock` — заблокировать канал/ы.\n"
                              f"{EMOJIS['DOT']} `/unlock` — разблокировать канал/ы.",
                "footer": "Справочник по командам для модерации"
            },
            "utils": {
                "title": "Команды для утилит",
                "emoji": "🧷",
                "commands": ["/reminder create", "/reminder list", "/reminder delete", "/quote"],
                "description": f"{EMOJIS['DOT']} `/reminder create` — создать напоминание.\n"
                              f"{EMOJIS['DOT']} `/reminder list` — посмотреть список напоминаний.\n"
                              f"{EMOJIS['DOT']} `/reminder delete` — удалить напоминание.",
                              f"{EMOJIS['DOT']} `/quote` — сделать цитату."
                "footer": "Справочник по командам для утилит"
            },
        }

        all_commands = []
        for cat_name, cat_info in categories.items():
            all_commands.append(f"\n{cat_info['emoji']} **{cat_info['title']}**")
            commands_list = " ".join(f"`{cmd}`" for cmd in cat_info['commands'])
            all_commands.append(commands_list)
        
        embed = create_embed(
            title="📚 Список всех команд",
            description="\n".join(all_commands),
            footer={
                'text': "Выберите категорию ниже для подробного описания команд",
                'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
            }
        )

        view = HelpView(categories)
        response = await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(Help(bot))
