import discord
from discord.ext import commands
from utils import create_embed, EMOJIS

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
            
            # Формируем описание с учетом отключенных команд
            description = cat_info["description"]
            
            # Получаем все возможные команды для этой категории
            all_commands = [cmd.strip('/') for cmd in cat_info["original_commands"]]
            
            # Получаем отключенные команды
            settings_cog = interaction.client.get_cog('Settings')
            disabled_commands = [cmd for cmd in all_commands 
                               if cmd in settings_cog.settings["disabled_commands"]]
            
            # Если есть отключенные команды в этой категории, добавляем информацию о них
            if disabled_commands:
                description += "\n\n⚠️ **Отключенные команды в этой категории:**\n"
                description += ", ".join(f"`/{cmd}`" for cmd in disabled_commands)
            
            embed = create_embed(
                title=f"{cat_info['emoji']} {cat_info['title']}",
                description=description,
                footer={
                    'text': cat_info["footer"],
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
            await interaction.response.edit_message(embed=embed, view=self.view)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Это меню устарело. Используйте `/help` еще раз!"
                )
            )

class AllCommandsButton(discord.ui.Button):
    def __init__(self, categories):
        super().__init__(style=discord.ButtonStyle.secondary, label="Все команды", emoji="📚")
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        try:
            all_commands = []
            for cat_name, cat_info in self.categories.items():
                # Пропускаем отключенные категории
                if cat_name in interaction.client.get_cog('Settings').settings["disabled_groups"]:
                    continue
                
                all_commands.append(f"\n{cat_info['emoji']} **{cat_info['title']}**")
                
                # Получаем активные команды
                active_commands = cat_info['commands']
                if active_commands:
                    commands_list = " ".join(f"`{cmd}`" for cmd in active_commands)
                    all_commands.append(commands_list)
                
                # Получаем отключенные команды для этой категории
                disabled_commands = [cmd for cmd in cat_info["commands"] 
                                   if cmd not in active_commands]
                if disabled_commands:
                    all_commands.append(f"\n⚠️ *Отключенные команды:* {', '.join(f'`{cmd}`' for cmd in disabled_commands)}")
            
            embed = create_embed(
                title="📚 Список всех команд",
                description="\n".join(all_commands) if all_commands else "Нет доступных команд",
                footer={
                    'text': "Выберите категорию ниже для подробного описания команд",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
            await interaction.response.edit_message(embed=embed)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Это меню устарело. Используйте `/help` еще раз!"
                )
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
        self.settings_cog = None

    async def get_settings_cog(self):
        if self.settings_cog is None:
            self.settings_cog = self.bot.get_cog('Settings')
        return self.settings_cog

    def is_command_available(self, command_name: str, category_name: str) -> bool:
        """Проверяет, доступна ли команда"""
        # Если категория отключена
        if category_name in self.settings_cog.settings["disabled_groups"]:
            return False
            
        # Если команда отключена
        if command_name in self.settings_cog.settings["disabled_commands"]:
            return False
            
        return True

    @discord.app_commands.command(name="help", description="Справочник по командам")
    async def help(self, interaction: discord.Interaction):
        await self.get_settings_cog()
        
        categories = {
            "main": {
                "title": "Основные команды",
                "emoji": "⚙️",
                "original_commands": ["/help", "/serverinfo", "/userinfo", "/roleinfo", "/analytics", "/crash"],
                "commands": [cmd for cmd in ["/help", "/serverinfo", "/userinfo", "/roleinfo", "/analytics", "/crash"] 
                           if self.is_command_available(cmd.strip('/'), "main")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/help` — помощь.",
                    f"{EMOJIS['DOT']} `/serverinfo` — информация о сервере.",
                    f"{EMOJIS['DOT']} `/userinfo` — информация о пользователе.",
                    f"{EMOJIS['DOT']} `/roleinfo` — информация о роли.",
                    f"{EMOJIS['DOT']} `/analytics` — статистика сервера.",
                    f"{EMOJIS['DOT']} `/crash` — завершить работу бота."
                ]),
                "footer": "Справочник по командам из раздела \"Основное\""
            },
            "admin": {
                "title": "Команды администратора",
                "emoji": "🛡️",
                "original_commands": ["/reports", "/form", "/ideas", "/backup"],
                "commands": [cmd for cmd in ["/reports", "/form", "/ideas", "/backup"]
                           if self.is_command_available(cmd.strip('/'), "admin")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/reports` — конфигурация жалоб.",
                    f"{EMOJIS['DOT']} `/form` — конфигурация заявок.",
                    f"{EMOJIS['DOT']} `/ideas` — конфигурация идей.",
                    f"{EMOJIS['DOT']} `/backup` — конфигурация бэкапов."
                ]),
                "footer": "Справочник по командам из раздела \"Администратор\""
            },
            "games": {
                "title": "Команды для игр",
                "emoji": "🎮",
                "original_commands": ["/rps", "/wordle", "/tictactoe", "/2048", "/country", "/capitals", "/minesweeper", "/coin"],
                "commands": [cmd for cmd in ["/rps", "/wordle", "/tictactoe", "/2048", "/country", "/capitals", "/minesweeper", "/coin"]
                           if self.is_command_available(cmd.strip('/'), "games")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/rps [user]` — играть в камень, ножницы, бумага.",
                    f"{EMOJIS['DOT']} `/wordle [user]` — играть в слова.",
                    f"{EMOJIS['DOT']} `/tictactoe [user]` — играть в крестики-нолики.",
                    f"{EMOJIS['DOT']} `/2048` — играть в 2048.",
                    f"{EMOJIS['DOT']} `/country` — играть в угадай страну.",
                    f"{EMOJIS['DOT']} `/capitals` — играть в угадай столицу.",
                    f"{EMOJIS['DOT']} `/minesweeper` — играть в сапёр.",
                    f"{EMOJIS['DOT']} `/coin` — орёл или решка."
                ]),
                "footer": "Справочник по командам из раздела \"Игры\""
            },
            "fun": {
                "title": "Команды для развлечений",
                "emoji": "🎉",
                "original_commands": ["/marry", "/divorce", "/hug", "/kiss", "/slap", "/pat", "/sex", "/bite", "/cry", "/lgbt", "/8ball", "/mcserver", "/coin", "/demotivator"],
                "commands": [cmd for cmd in ["/marry", "/divorce", "/hug", "/kiss", "/slap", "/pat", "/sex", "/bite", "/cry", "/lgbt", "/8ball", "/mcserver", "/coin", "/demotivator"]
                           if self.is_command_available(cmd.strip('/'), "fun")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/marry [user]` — жениться на кого-то.",
                    f"{EMOJIS['DOT']} `/divorce [user]` — развестись с кем-то.",
                    f"{EMOJIS['DOT']} `/hug [user]` — обнять кого-то.",
                    f"{EMOJIS['DOT']} `/kiss [user]` — поцеловать кого-то.",
                    f"{EMOJIS['DOT']} `/slap [user]` — ударить кого-то.",
                    f"{EMOJIS['DOT']} `/pat [user]` — погладить кого-то.",
                    f"{EMOJIS['DOT']} `/sex [user]` — логично.",
                    f"{EMOJIS['DOT']} `/bite [user]` — укусить кого-то.",
                    f"{EMOJIS['DOT']} `/cry [user]` — заплакать.",
                    f"{EMOJIS['DOT']} `/lgbt [user]` — аватар пользователя в стиле ЛГБТ.",
                    f"{EMOJIS['DOT']} `/8ball [question]` — магический шар ответит на твой вопрос.",
                    f"{EMOJIS['DOT']} `/mcserver` — информация о сервере Minecraft.",
                    f"{EMOJIS['DOT']} `/coin` — орёл или решка.",
                    f"{EMOJIS['DOT']} `/demotivator` — демотиватор."
                ]),
                "footer": "Справочник по командам для развлечений"
            },
            "music": {
                "title": "Команды для управления музыкой",
                "emoji": "🎵",
                "original_commands": ["/play", "/queue", "/skip", "/stop", "/pause", "/np", "/repeat", "/shuffle", "/nightcore", "/resume", "/volume"],
                "commands": [cmd for cmd in ["/play", "/queue", "/skip", "/stop", "/pause", "/np", "/repeat", "/shuffle", "/nightcore", "/resume", "/volume"]
                           if self.is_command_available(cmd.strip('/'), "music")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/play` — воспроизвести песню или добавить в очередь.",
                    f"{EMOJIS['DOT']} `/queue` — показать текущую очередь воспроизведения.",
                    f"{EMOJIS['DOT']} `/skip` — пропустить текущую песню.",
                    f"{EMOJIS['DOT']} `/stop` — остановить воспроизведение и очистить очередь.",
                    f"{EMOJIS['DOT']} `/pause` — приостановить воспроизведение.",
                    f"{EMOJIS['DOT']} `/np` — показать текущий трек и прогресс.",
                    f"{EMOJIS['DOT']} `/repeat` — повторить текущую песню.",
                    f"{EMOJIS['DOT']} `/shuffle` — перемешать песни.",
                    f"{EMOJIS['DOT']} `/nightcore` — включить эффект Nightcore.",
                    f"{EMOJIS['DOT']} `/resume` — возобновить воспроизведение.",
                    f"{EMOJIS['DOT']} `/volume` — изменить громкость музыки."
                ]),
                "footer": "Справочник по командам управления музыкой"
            },
            "economy": {
                "title": "Команды экономики",
                "emoji": "💰",
                "original_commands": ["/balance", "/shop", "/sell", "/slots", "/deposit", "/withdraw", "/daily", "/work", "/pay", "/leaderboard", "/casino", "/blackjack", "/rob", "/duel"],
                "commands": [cmd for cmd in ["/balance", "/shop", "/sell", "/slots", "/deposit", "/withdraw", "/daily", "/work", "/pay", "/leaderboard", "/casino", "/blackjack", "/rob", "/duel"]
                           if self.is_command_available(cmd.strip('/'), "economy")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/balance [user]` — проверить баланс.",
                    f"{EMOJIS['DOT']} `/shop` — просмотреть магазин.",
                    f"{EMOJIS['DOT']} `/sell` — продать роль.",
                    f"{EMOJIS['DOT']} `/slots [amount]` — играть в слот-машину.",
                    f"{EMOJIS['DOT']} `/deposit [amount]` — перевести деньги в банк.",
                    f"{EMOJIS['DOT']} `/withdraw [amount]` — снять деньги из банка.",
                    f"{EMOJIS['DOT']} `/daily` — получить дневную награду (кулдаун: `24 часа`).",
                    f"{EMOJIS['DOT']} `/work` — пойти на работу (кулдаун: `1 час`).",
                    f"{EMOJIS['DOT']} `/pay [user] [amount]` — перевести деньги.",
                    f"{EMOJIS['DOT']} `/leaderboard` — посмотреть топ юзеров по деньгам.",
                    f"{EMOJIS['DOT']} `/casino [bet] [amount]` — играть в казино.",
                    f"{EMOJIS['DOT']} `/blackjack [bet]` — играть в блекджек.",
                    f"{EMOJIS['DOT']} `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).",
                    f"{EMOJIS['DOT']} `/duel [user] [bet]` — позвать кого-то на дуэль."
                ]),
                "footer": "Справочник по командам из раздела \"Экономика\""
            },
            "profile": {
                "title": "Команды профиля",
                "emoji": "👤",
                "original_commands": ["/level", "/inventory", "/userinfo", "/avatar", "/bio", "/streak"],
                "commands": [cmd for cmd in ["/level", "/inventory", "/userinfo", "/avatar", "/bio", "/streak"]
                           if self.is_command_available(cmd.strip('/'), "profile")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/level <user>` — проверить уровень.",
                    f"{EMOJIS['DOT']} `/inventory` — просмотреть инвентарь.",
                    f"{EMOJIS['DOT']} `/userinfo <user>` — просмотреть информацию о пользователе.",
                    f"{EMOJIS['DOT']} `/avatar <user>` — просмотреть аватар пользователя.",
                    f"{EMOJIS['DOT']} `/bio [set/view/clear]` — просмотреть профиль.",
                    f"{EMOJIS['DOT']} `/streak` — просмотреть вашого питомца Огонька."
                ]),
                "footer": "Справочник по командам из раздела \"Профиль\""
            },
            "moderation": {
                "title": "Команды для модерации",
                "emoji": "🛡️",
                "original_commands": ["/lock", "/unlock", "/kick", "/ban", "/unban", "/warn", "/mute", "/unmute", "/clear", "/warns", "/massrole", "/mutes", "/reset"],
                "commands": [cmd for cmd in ["/lock", "/unlock", "/kick", "/ban", "/unban", "/warn", "/mute", "/unmute", "/clear", "/warns", "/massrole", "/mutes", "/reset"]
                           if self.is_command_available(cmd.strip('/'), "moderation")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/lock [channel] / [all_channels]` — заблокировать канал/ы.",
                    f"{EMOJIS['DOT']} `/unlock [channel] / [all_channels]` — разблокировать канал/ы.",
                    f"{EMOJIS['DOT']} `/kick [user] [reason]` — кикнуть кого-то.",
                    f"{EMOJIS['DOT']} `/ban [user] [reason] [delete_days]` — забанить кого-то.",
                    f"{EMOJIS['DOT']} `/unban [user]` — разбанить кого-то.",
                    f"{EMOJIS['DOT']} `/warn [add/remove/clear] [user] <reason>` — предупредить кого-то.",
                    f"{EMOJIS['DOT']} `/warns <user>` — посмотреть предупреждения.",
                    f"{EMOJIS['DOT']} `/mute [user] [reason]` — замутить кого-то.",
                    f"{EMOJIS['DOT']} `/unmute [user]` — размутить кого-то.",
                    f"{EMOJIS['DOT']} `/clear [amount]` — очистить сообщения.",
                    f"{EMOJIS['DOT']} `/massrole [add/remove] [role] [filter]` — массовая выдача/удаление роли.",
                    f"{EMOJIS['DOT']} `/mutes` — список мутов.",
                    f"{EMOJIS['DOT']} `/reset` — сбросить муты/варны."
                ]),
                "footer": "Справочник по командам для модерации"
            },
            "utils": {
                "title": "Команды для утилит",
                "emoji": "🧷",
                "original_commands": ["/reminder", "/quote", "/weather", "/translate", "/poll", "/qr", "/ai", "/afk", "/t", "/k", "/math", "/rand", "/whois"],
                "commands": [cmd for cmd in ["/reminder", "/quote", "/weather", "/translate", "/poll", "/qr", "/ai", "/afk", "/t", "/k", "/math", "/rand", "/whois"]
                           if self.is_command_available(cmd.strip('/'), "utils")],
                "description": "\n".join([
                    f"{EMOJIS['DOT']} `/reminder [create] / [list] / [delete]` — напоминания.",
                    f"{EMOJIS['DOT']} `/quote` — сделать цитату.",
                    f"{EMOJIS['DOT']} `/weather` — узнать погоду.",
                    f"{EMOJIS['DOT']} `/translate` — перевести текст.",
                    f"{EMOJIS['DOT']} `/poll` — создать опрос.",
                    f"{EMOJIS['DOT']} `/qr` — создать QR-код.",
                    f"{EMOJIS['DOT']} `/ai` — спросить что-то у ИИ.",
                    f"{EMOJIS['DOT']} `/afk` — установить статус AFK.",
                    f"{EMOJIS['DOT']} `/t` — транслитерация слов.",
                    f"{EMOJIS['DOT']} `/k` — исправление раскладки.",
                    f"{EMOJIS['DOT']} `/math` — решить математическую задачу.",
                    f"{EMOJIS['DOT']} `/rand` — рандомный выбор.",
                    f"{EMOJIS['DOT']} `/whois` — информация о пользователе."
                ]),
                "footer": "Справочник по командам для утилит"
            },
        }

        # Подсчет отключенных команд
        disabled_count = len(self.settings_cog.settings["disabled_commands"])
        disabled_groups_count = len(self.settings_cog.settings["disabled_groups"])
        
        # Удаляем полностью отключенные категории
        categories = {k: v for k, v in categories.items() 
                     if k not in self.settings_cog.settings["disabled_groups"]}

        # Создаем начальное сообщение
        initial_embed = create_embed(
            title="📚 Справочник по командам",
            description="Выберите категорию из списка ниже для просмотра команд.\n\n" +
                       (f"⚠️ Отключено команд: {disabled_count}\n" if disabled_count > 0 else "") +
                       (f"🚫 Отключено категорий: {disabled_groups_count}" if disabled_groups_count > 0 else ""),
            footer={
                'text': "Используйте меню ниже для навигации",
                'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
            }
        )

        view = HelpView(categories)
        message = await interaction.response.send_message(embed=initial_embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(Help(bot))
