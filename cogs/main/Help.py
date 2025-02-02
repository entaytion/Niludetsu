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
                    f"{Emojis.Dot} `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).",
                    f"{Emojis.Dot} `/shop [id_role]` — просмотреть магазин.",
                    f"{Emojis.Dot} `/slots [amount]` — играть в слот-машину.",
                    f"{Emojis.Dot} `/withdraw [amount]` — снять деньги из банка.",
                    f"{Emojis.Dot} `/work` — пойти на работу (кулдаун: `1 час`)."
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
                    f"{Emojis.Dot} `/8ball [question]` — магический шар ответит на твой вопрос.",
                    f"{Emojis.Dot} `/bite [user]` — укусить кого-то.",
                    f"{Emojis.Dot} `/coin [guess]` — орёл или решка.",
                    f"{Emojis.Dot} `/cry [user]` — заплакать.",
                    f"{Emojis.Dot} `/demotivator [title] <subtitle> <image>` — демотиватор.",
                    f"{Emojis.Dot} `/divorce` — развестись с кем-то.",
                    f"{Emojis.Dot} `/hug [user]` — обнять кого-то.",
                    f"{Emojis.Dot} `/kiss [user]` — поцеловать кого-то.",
                    f"{Emojis.Dot} `/lgbt [user]` — аватар пользователя в стиле ЛГБТ.",
                    f"{Emojis.Dot} `/marry [user]` — жениться на кого-то.",
                    f"{Emojis.Dot} `/mcserver [address]` — информация о сервере Minecraft.",
                    f"{Emojis.Dot} `/pat [user]` — погладить кого-то.",
                    f"{Emojis.Dot} `/sex [user]` — логично.",
                    f"{Emojis.Dot} `/slap [user]` — ударить кого-то."
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
                    f"{Emojis.Dot} `/2048` — играть в 2048.",
                    f"{Emojis.Dot} `/akinator` — играть в Акинатор.",
                    f"{Emojis.Dot} `/capitals` — играть в угадай столицу.",
                    f"{Emojis.Dot} `/country` — играть в угадай страну.",
                    f"{Emojis.Dot} `/minesweeper` — играть в сапёр.",
                    f"{Emojis.Dot} `/rps <user>` — играть в камень, ножницы, бумага.",
                    f"{Emojis.Dot} `/tictactoe <user>` — играть в крестики-нолики.",
                    f"{Emojis.Dot} `/wordle` — играть в слова."
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
                    f"{Emojis.Dot} `/analytics [bot/channels/roles/server]` — аналитика сервера.",
                    f"{Emojis.Dot} `/backup [create/info/restore]` — бэкап сервера.",
                    f"{Emojis.Dot} `/crash` — выключить бота.",
                    f"{Emojis.Dot} `/help` — вызвать помощь.",
                    f"{Emojis.Dot} `/invites [channel/welcome/leave/test/info/list]` — инвайты сервера.",
                    f"{Emojis.Dot} `/logs` — логи сервера.",
                    f"{Emojis.Dot} `/roleinfo [role]` — роль сервера.",
                    f"{Emojis.Dot} `/serverinfo` — сервер информация.",
                    f"{Emojis.Dot} `/userinfo <user>` — участник сервера."
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
                    f"{Emojis.Dot} `/ban [user] [reason] <delete_days>` — забанить кого-то.",
                    f"{Emojis.Dot} `/clear [amount]` — очистить сообщения.",
                    f"{Emojis.Dot} `/kick [user] [reason]` — кикнуть кого-то.",
                    f"{Emojis.Dot} `/lock [channel/all_channels]` — заблокировать канал/ы.",
                    f"{Emojis.Dot} `/massrole [add/remove] [role] [filter]` — массовая выдача/удаление роли.",
                    f"{Emojis.Dot} `/mute [user] <reason> <duration>` — замутить кого-то.",
                    f"{Emojis.Dot} `/mutes` — список мутов.",
                    f"{Emojis.Dot} `/reset [mutes/warns]` — сбросить муты/варны.",
                    f"{Emojis.Dot} `/slowmode [set/info/off] [channel/all_channels] [duration] <reason>` — установить задержку в чате.",
                    f"{Emojis.Dot} `/unban [user] <reason>` — разбанить кого-то.",
                    f"{Emojis.Dot} `/unlock [channel/all_channels]` — разблокировать канал/ы.",
                    f"{Emojis.Dot} `/unmute [user] <reason>` — размутить кого-то.",
                    f"{Emojis.Dot} `/warn [add/remove/clear] [user] <reason>` — предупредить кого-то.",
                    f"{Emojis.Dot} `/warns <user>` — посмотреть предупреждения."
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
                    f"{Emojis.Dot} `/leave` — отключить бота от голосового канала.",
                    f"{Emojis.Dot} `/nightcore` — включить эффект Nightcore.",
                    f"{Emojis.Dot} `/np` — показать текущий трек и прогресс.",
                    f"{Emojis.Dot} `/pause` — приостановить воспроизведение.",
                    f"{Emojis.Dot} `/play [query]` — воспроизвести песню или добавить в очередь.",
                    f"{Emojis.Dot} `/queue` — показать текущую очередь воспроизведения.",
                    f"{Emojis.Dot} `/repeat` — повторить текущую песню.",
                    f"{Emojis.Dot} `/resume` — возобновить воспроизведение.",
                    f"{Emojis.Dot} `/shuffle` — перемешать песни.",
                    f"{Emojis.Dot} `/skip` — пропустить текущую песню.",
                    f"{Emojis.Dot} `/stop` — остановить воспроизведение и очистить очередь.",
                    f"{Emojis.Dot} `/volume [value]` — изменить громкость музыки."
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
                    f"{Emojis.Dot} `/avatar <user>` — просмотреть аватар пользователя.",
                    f"{Emojis.Dot} `/bio [set/view/clear]` — просмотреть профиль.",
                    f"{Emojis.Dot} `/leaderboard [money/level/reputation]` — просмотреть лидеров.",
                    f"{Emojis.Dot} `/profile <user>` — проверить уровень.",
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
                    f"{Emojis.Dot} `/afk <reason>` — установить статус AFK.",
                    f"{Emojis.Dot} `/ai [ask/info/providers]` — спросить что-то у ИИ.",
                    f"{Emojis.Dot} `/currency` — показать текущий курс валют.",
                    f"{Emojis.Dot} `/emoji [download/pack/all]` — скачать эмодзи.",
                    f"{Emojis.Dot} `/exchange [amount] [from_currency] [to_currency]` — конвертировать сумму из одной валюты в другую.",
                    f"{Emojis.Dot} `/k [text]` — исправление раскладки.",
                    f"{Emojis.Dot} `/math [expression]` — решить математическую задачу.",
                    f"{Emojis.Dot} `/poll [question] [options]` — создать опрос.",
                    f"{Emojis.Dot} `/qr [text]` — создать QR-код.",
                    f"{Emojis.Dot} `/quote [message_id]` — сделать цитату.",
                    f"{Emojis.Dot} `/rand [min] [max]` — рандомный выбор.",
                    f"{Emojis.Dot} `/reminder [create/list/delete]` — напоминания.",
                    f"{Emojis.Dot} `/t [text]` — транслитерация слов.",
                    f"{Emojis.Dot} `/translate [text] [lang]` — перевести текст.",
                    f"{Emojis.Dot} `/weather [city]` — узнать погоду.",
                    f"{Emojis.Dot} `/whois [domain]` — информация о домене."
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
                    f"{Emojis.Dot} `/form [setup/edit]` — конфигурация заявок.",
                    f"{Emojis.Dot} `/giveaway [create/end/reroll]` — конфигурация розыгрышей.",
                    f"{Emojis.Dot} `/ideas [setup/edit]` — конфигурация идей.",
                    f"{Emojis.Dot} `/logs [enable/disable/set/status/test]` — конфигурация логирования.",
                    f"{Emojis.Dot} `/reports [setup/edit]` — конфигурация жалоб.",
                    f"{Emojis.Dot} `/setup` — конфигурация сервера.",
                    f"{Emojis.Dot} `/tickets [setup/stats]` — конфигурация тикетов."
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
