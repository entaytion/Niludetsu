import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

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
            
            embed=Embed(
                title=f"{cat_info['emoji']} {cat_info['title']}",
                description=description,
                footer={'text': f"{cat_info['footer']} • [] - обязательный параметр, <> - необязательный параметр",
                        'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"},
                color="DEFAULT"
            )
            await interaction.response.edit_message(embed=embed, view=self.view)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=Embed(
                    description="Это меню устарело. Используйте `/help` еще раз!",
                    color="RED"
                )
            )

class AllCommandsButton(discord.ui.Button):
    def __init__(self, categories):
        super().__init__(style=discord.ButtonStyle.secondary, label="Все команды", emoji="📚")
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        try:
            all_commands = []
            for cat_name, cat_info in sorted(self.categories.items(), key=lambda x: x[1]['title']):
                # Пропускаем отключенные категории
                if cat_name in interaction.client.get_cog('Settings').settings["disabled_groups"]:
                    continue
                
                all_commands.append(f"\n{cat_info['emoji']} **{cat_info['title']}**")
                
                # Получаем активные команды и сортируем их
                active_commands = sorted(cat_info['commands'])
                if active_commands:
                    commands_list = " ".join(f"`{cmd}`" for cmd in active_commands)
                    all_commands.append(commands_list)
                
                # Получаем отключенные команды для этой категории
                disabled_commands = sorted([cmd for cmd in cat_info["commands"] 
                                   if cmd not in active_commands])
                if disabled_commands:
                    all_commands.append(f"\n⚠️ *Отключенные команды:* {', '.join(f'`{cmd}`' for cmd in disabled_commands)}")
            
            embed=Embed(
                title="📚 Список всех команд",
                description="\n".join(all_commands) if all_commands else "Нет доступных команд",
                footer={'text': "Выберите категорию ниже для подробного описания команд • [] - обязательный параметр, <> - необязательный параметр",
                        'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"},
                color="DEFAULT"
            )
            await interaction.response.edit_message(embed=embed)
        except discord.errors.NotFound:
            await interaction.response.send_message(
                embed=Embed(
                    description="Это меню устарело. Используйте `/help` еще раз!",
                    color="RED"
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
            "economy": {
                "title": "Команды экономики",
                "emoji": "💰",
                "original_commands": ["/blackjack", "/casino", "/daily", "/deposit", "/duel", "/pay", "/rob", "/shop", "/slots", "/withdraw", "/work"],
                "commands": [cmd for cmd in ["/blackjack", "/casino", "/daily", "/deposit", "/duel", "/pay", "/rob", "/shop", "/slots", "/withdraw", "/work"]
                           if self.is_command_available(cmd.strip('/'), "economy")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/blackjack [bet]` — играть в блекджек.",
                    f"{Emojis.DOT} `/casino [bet] [amount]` — играть в казино.",
                    f"{Emojis.DOT} `/daily` — получить дневную награду (кулдаун: `24 часа`).",
                    f"{Emojis.DOT} `/deposit [amount]` — перевести деньги в банк.",
                    f"{Emojis.DOT} `/duel [user] [bet]` — позвать кого-то на дуэль.",
                    f"{Emojis.DOT} `/pay [user] [amount]` — перевести деньги.",
                    f"{Emojis.DOT} `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).",
                    f"{Emojis.DOT} `/shop [id_role]` — просмотреть магазин.",
                    f"{Emojis.DOT} `/slots [amount]` — играть в слот-машину.",
                    f"{Emojis.DOT} `/withdraw [amount]` — снять деньги из банка.",
                    f"{Emojis.DOT} `/work` — пойти на работу (кулдаун: `1 час`)."
                ]),
                "footer": "Справочник по командам из раздела \"Экономика\""
            },
            "fun": {
                "title": "Команды для развлечений",
                "emoji": "🎉",
                "original_commands": ["/8ball", "/bite", "/coin", "/cry", "/demotivator", "/divorce", "/hug", "/kiss", "/lgbt", "/marry", "/mcserver", "/pat", "/sex", "/slap"],
                "commands": [cmd for cmd in ["/8ball", "/bite", "/coin", "/cry", "/demotivator", "/divorce", "/hug", "/kiss", "/lgbt", "/marry", "/mcserver", "/pat", "/sex", "/slap"]
                           if self.is_command_available(cmd.strip('/'), "fun")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/8ball [question]` — магический шар ответит на твой вопрос.",
                    f"{Emojis.DOT} `/bite [user]` — укусить кого-то.",
                    f"{Emojis.DOT} `/coin [guess]` — орёл или решка.",
                    f"{Emojis.DOT} `/cry [user]` — заплакать.",
                    f"{Emojis.DOT} `/demotivator [title] <subtitle> <image>` — демотиватор.",
                    f"{Emojis.DOT} `/divorce` — развестись с кем-то.",
                    f"{Emojis.DOT} `/hug [user]` — обнять кого-то.",
                    f"{Emojis.DOT} `/kiss [user]` — поцеловать кого-то.",
                    f"{Emojis.DOT} `/lgbt [user]` — аватар пользователя в стиле ЛГБТ.",
                    f"{Emojis.DOT} `/marry [user]` — жениться на кого-то.",
                    f"{Emojis.DOT} `/mcserver [address]` — информация о сервере Minecraft.",
                    f"{Emojis.DOT} `/pat [user]` — погладить кого-то.",
                    f"{Emojis.DOT} `/sex [user]` — логично.",
                    f"{Emojis.DOT} `/slap [user]` — ударить кого-то."
                ]),
                "footer": "Справочник по командам для развлечений"
            },
            "games": {
                "title": "Команды для игр",
                "emoji": "🎮",
                "original_commands": ["/2048", "/akinator", "/capitals", "/country", "/minesweeper", "/rps", "/tictactoe", "/wordle"],
                "commands": [cmd for cmd in ["/2048", "/akinator", "/capitals", "/country", "/minesweeper", "/rps", "/tictactoe", "/wordle"]
                           if self.is_command_available(cmd.strip('/'), "games")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/2048` — играть в 2048.",
                    f"{Emojis.DOT} `/akinator` — играть в Акинатор.",
                    f"{Emojis.DOT} `/capitals` — играть в угадай столицу.",
                    f"{Emojis.DOT} `/country` — играть в угадай страну.",
                    f"{Emojis.DOT} `/minesweeper` — играть в сапёр.",
                    f"{Emojis.DOT} `/rps <user>` — играть в камень, ножницы, бумага.",
                    f"{Emojis.DOT} `/tictactoe <user>` — играть в крестики-нолики.",
                    f"{Emojis.DOT} `/wordle` — играть в слова."
                ]),
                "footer": "Справочник по командам из раздела \"Игры\""
            },
            "main": {
                "title": "Основные команды",
                "emoji": "⚙️",
                "original_commands": ["/analytics", "/backup", "/crash", "/help", "/invites", "/logs", "/roleinfo", "/serverinfo", "/userinfo"],
                "commands": [cmd for cmd in ["/analytics", "/backup", "/crash", "/help", "/invites", "/logs", "/roleinfo", "/serverinfo", "/userinfo"]
                           if self.is_command_available(cmd.strip('/'), "main")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/analytics [bot/channels/roles/server]` — аналитика сервера.",
                    f"{Emojis.DOT} `/backup [create/info/restore]` — бэкап сервера.",
                    f"{Emojis.DOT} `/crash` — выключить бота.",
                    f"{Emojis.DOT} `/help` — вызвать помощь.",
                    f"{Emojis.DOT} `/invites [channel/welcome/leave/test/info/list]` — инвайты сервера.",
                    f"{Emojis.DOT} `/logs` — логи сервера.",
                    f"{Emojis.DOT} `/roleinfo [role]` — роль сервера.",
                    f"{Emojis.DOT} `/serverinfo` — сервер информация.",
                    f"{Emojis.DOT} `/userinfo <user>` — участник сервера."
                ]),
                "footer": "Справочник по командам из раздела \"Основное\""
            },
            "moderation": {
                "title": "Команды для модерации",
                "emoji": "🛡️",
                "original_commands": ["/ban", "/clear", "/kick", "/lock", "/massrole", "/mute", "/mutes", "/reset", "/slowmode", "/unban", "/unlock", "/unmute", "/warn", "/warns"],
                "commands": [cmd for cmd in ["/ban", "/clear", "/kick", "/lock", "/massrole", "/mute", "/mutes", "/reset", "/slowmode", "/unban", "/unlock", "/unmute", "/warn", "/warns"]
                           if self.is_command_available(cmd.strip('/'), "moderation")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/ban [user] [reason] <delete_days>` — забанить кого-то.",
                    f"{Emojis.DOT} `/clear [amount]` — очистить сообщения.",
                    f"{Emojis.DOT} `/kick [user] [reason]` — кикнуть кого-то.",
                    f"{Emojis.DOT} `/lock [channel/all_channels]` — заблокировать канал/ы.",
                    f"{Emojis.DOT} `/massrole [add/remove] [role] [filter]` — массовая выдача/удаление роли.",
                    f"{Emojis.DOT} `/mute [user] <reason> <duration>` — замутить кого-то.",
                    f"{Emojis.DOT} `/mutes` — список мутов.",
                    f"{Emojis.DOT} `/reset [mutes/warns]` — сбросить муты/варны.",
                    f"{Emojis.DOT} `/slowmode [set/info/off] [channel/all_channels] [duration] <reason>` — установить задержку в чате.",
                    f"{Emojis.DOT} `/unban [user] <reason>` — разбанить кого-то.",
                    f"{Emojis.DOT} `/unlock [channel/all_channels]` — разблокировать канал/ы.",
                    f"{Emojis.DOT} `/unmute [user] <reason>` — размутить кого-то.",
                    f"{Emojis.DOT} `/warn [add/remove/clear] [user] <reason>` — предупредить кого-то.",
                    f"{Emojis.DOT} `/warns <user>` — посмотреть предупреждения."
                ]),
                "footer": "Справочник по командам для модерации"
            },
            "music": {
                "title": "Команды для управления музыкой",
                "emoji": "🎵",
                "original_commands": ["/leave", "/nightcore", "/np", "/pause", "/play", "/queue", "/repeat", "/resume", "/shuffle", "/skip", "/stop", "/volume"],
                "commands": [cmd for cmd in ["/leave", "/nightcore", "/np", "/pause", "/play", "/queue", "/repeat", "/resume", "/shuffle", "/skip", "/stop", "/volume"]
                           if self.is_command_available(cmd.strip('/'), "music")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/leave` — отключить бота от голосового канала.",
                    f"{Emojis.DOT} `/nightcore` — включить эффект Nightcore.",
                    f"{Emojis.DOT} `/np` — показать текущий трек и прогресс.",
                    f"{Emojis.DOT} `/pause` — приостановить воспроизведение.",
                    f"{Emojis.DOT} `/play [query]` — воспроизвести песню или добавить в очередь.",
                    f"{Emojis.DOT} `/queue` — показать текущую очередь воспроизведения.",
                    f"{Emojis.DOT} `/repeat` — повторить текущую песню.",
                    f"{Emojis.DOT} `/resume` — возобновить воспроизведение.",
                    f"{Emojis.DOT} `/shuffle` — перемешать песни.",
                    f"{Emojis.DOT} `/skip` — пропустить текущую песню.",
                    f"{Emojis.DOT} `/stop` — остановить воспроизведение и очистить очередь.",
                    f"{Emojis.DOT} `/volume [value]` — изменить громкость музыки."
                ]),
                "footer": "Справочник по командам управления музыкой"
            },
            "profile": {
                "title": "Команды профиля",
                "emoji": "👤", 
                "original_commands": ["/avatar", "/bio", "/leaderboard", "/profile"],
                "commands": [cmd for cmd in ["/avatar", "/bio", "/leaderboard", "/profile"]
                           if self.is_command_available(cmd.strip('/'), "profile")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/avatar <user>` — просмотреть аватар пользователя.",
                    f"{Emojis.DOT} `/bio [set/view/clear]` — просмотреть профиль.",
                    f"{Emojis.DOT} `/leaderboard [money/level/reputation]` — просмотреть лидеров.",
                    f"{Emojis.DOT} `/profile <user>` — проверить уровень.",
                ]),
                "footer": "Справочник по командам из раздела \"Профиль\""
            },
            "utilities": {
                "title": "Команды для утилит",
                "emoji": "🧷",
                "original_commands": ["/afk", "/ai", "/currency", "/exchange", "/emoji", "/k", "/math", "/poll", "/qr", "/quote", "/rand", "/reminder", "/t", "/translate", "/weather", "/whois"],
                "commands": [cmd for cmd in ["/afk", "/ai", "/currency", "/exchange", "/emoji", "/k", "/math", "/poll", "/qr", "/quote", "/rand", "/reminder", "/t", "/translate", "/weather", "/whois"]
                           if self.is_command_available(cmd.strip('/'), "utilities")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/afk <reason>` — установить статус AFK.",
                    f"{Emojis.DOT} `/ai [ask/info/providers]` — спросить что-то у ИИ.",
                    f"{Emojis.DOT} `/currency` — показать текущий курс валют.",
                    f"{Emojis.DOT} `/emoji [download/pack/all]` — скачать эмодзи.",
                    f"{Emojis.DOT} `/exchange [amount] [from_currency] [to_currency]` — конвертировать сумму из одной валюты в другую.",
                    f"{Emojis.DOT} `/k [text]` — исправление раскладки.",
                    f"{Emojis.DOT} `/math [expression]` — решить математическую задачу.",
                    f"{Emojis.DOT} `/poll [question] [options]` — создать опрос.",
                    f"{Emojis.DOT} `/qr [text]` — создать QR-код.",
                    f"{Emojis.DOT} `/quote [message_id]` — сделать цитату.",
                    f"{Emojis.DOT} `/rand [min] [max]` — рандомный выбор.",
                    f"{Emojis.DOT} `/reminder [create/list/delete]` — напоминания.",
                    f"{Emojis.DOT} `/t [text]` — транслитерация слов.",
                    f"{Emojis.DOT} `/translate [text] [lang]` — перевести текст.",
                    f"{Emojis.DOT} `/weather [city]` — узнать погоду.",
                    f"{Emojis.DOT} `/whois [domain]` — информация о домене."
                ]),
                "footer": "Справочник по командам для утилит"
            },
            "admin": {
                "title": "Команды администратора",
                "emoji": "🛡️",
                "original_commands": ["/form", "/giveaway", "/ideas", "/logs", "/reports", "/setup", "/tickets"],
                "commands": [cmd for cmd in ["/form", "/giveaway", "/ideas", "/logs", "/reports", "/setup", "/tickets"]
                           if self.is_command_available(cmd.strip('/'), "admin")],
                "description": "\n".join([
                    f"{Emojis.DOT} `/form [setup/edit]` — конфигурация заявок.",
                    f"{Emojis.DOT} `/giveaway [create/end/reroll]` — конфигурация розыгрышей.",
                    f"{Emojis.DOT} `/ideas [setup/edit]` — конфигурация идей.",
                    f"{Emojis.DOT} `/logs [enable/disable/set/status/test]` — конфигурация логирования.",
                    f"{Emojis.DOT} `/reports [setup/edit]` — конфигурация жалоб.",
                    f"{Emojis.DOT} `/setup` — конфигурация сервера.",
                    f"{Emojis.DOT} `/tickets [setup/stats]` — конфигурация тикетов."
                ]),
                "footer": "Справочник по командам из раздела \"Администратор\""
            },
        }

        # Подсчет отключенных команд
        disabled_count = len(self.settings_cog.settings["disabled_commands"])
        disabled_groups_count = len(self.settings_cog.settings["disabled_groups"])
        
        # Удаляем полностью отключенные категории
        categories = {k: v for k, v in categories.items() 
                     if k not in self.settings_cog.settings["disabled_groups"]}

        # Создаем начальное сообщение
        initial_embed=Embed(
            title="📚 Справочник по командам",
            description="Выберите категорию из списка ниже для просмотра команд.\n\n" +
                       (f"⚠️ Отключено команд: {disabled_count}\n" if disabled_count > 0 else "") +
                       (f"🚫 Отключено категорий: {disabled_groups_count}" if disabled_groups_count > 0 else ""),
            footer={
                'text': "Используйте меню ниже для навигации • [] - обязательный параметр, <> - необязательный параметр",
                'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
            }
        )

        view = HelpView(categories)
        message = await interaction.response.send_message(embed=initial_embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(Help(bot))
