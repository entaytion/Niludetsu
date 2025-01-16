import discord
from discord.ext import commands
from utils import create_embed, FOOTER_ERROR, FOOTER_SUCCESS

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @discord.app_commands.command(name="help", description="Справочник по командам")
    @discord.app_commands.describe(category="Категория для отображения команд (опционально)")
    async def help(self, interaction: discord.Interaction, category: str = None):
        categories = {
            "main": {
                "title": "Основные команды",
                "description": "<:aeOutlineDot:1266066158029770833> `/help` — помощь.\n"
                              "<:aeOutlineDot:1266066158029770833> `/reload` — перезагрузка бота.\n",
                "footer": "Справочник по командам из раздела \"Основное\""
            },
            "fun": {
                "title": "Команды для развлечений",
                "description": "<:aeOutlineDot:1266066158029770833> `/marry` — жениться на кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/divorce` — развестись с кем-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/hug` — обнять кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/kiss` — поцеловать кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/slap` — ударить кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/pat` — погладить кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/sex` — логично.\n"
                              "<:aeOutlineDot:1266066158029770833> `/bite` — укусить кого-то.\n"
                              "<:aeOutlineDot:1266066158029770833> `/cry` — заплакать.",
                "footer": "Справочник по командам для развлечений"
            },
            "music": {
                "title": "Команды для управления музыкой",
                "description": "<:aeOutlineDot:1266066158029770833> `/play` — воспроизвести песню или добавить в очередь.\n"
                              "<:aeOutlineDot:1266066158029770833> `/queue` — показать текущую очередь воспроизведения.\n"
                              "<:aeOutlineDot:1266066158029770833> `/skip` — пропустить текущую песню.\n"
                              "<:aeOutlineDot:1266066158029770833> `/stop` — остановить воспроизведение и очистить очередь.\n"
                              "<:aeOutlineDot:1266066158029770833> `/pause` — приостановить воспроизведение.\n"
                              "<:aeOutlineDot:1266066158029770833> `/np` — показать текущий трек и прогресс.\n"
                              "<:aeOutlineDot:1266066158029770833> `/repeat` — повторить текущую песню.\n"
                              "<:aeOutlineDot:1266066158029770833> `/shuffle` — перемешать песни.\n"
                              "<:aeOutlineDot:1266066158029770833> `/nightcore` — включить эффект Nightcore.\n"
                              "<:aeOutlineDot:1266066158029770833> `/resume` — возобновить воспроизведение.",
                "footer": "Справочник по командам управления музыкой"
            },
            "economy": {
                "title": "Команды экономики",
                "description": "<:aeOutlineDot:1266066158029770833> `/balance <user>` — проверить баланс.\n"
                              "<:aeOutlineDot:1266066158029770833> `/deposit [amount]` — перевести деньги в банк.\n"
                              "<:aeOutlineDot:1266066158029770833> `/withdraw [amount]` — снять деньги из банка.\n"
                              "<:aeOutlineDot:1266066158029770833> `/daily` — получить дневную награду (кулдаун: `24 часа`).\n"
                              "<:aeOutlineDot:1266066158029770833> `/work` — пойти на работу (кулдаун: `1 час`).\n"
                              "<:aeOutlineDot:1266066158029770833> `/pay [user] [amount]` — перевести деньги.\n"
                              "<:aeOutlineDot:1266066158029770833> `/leaderboard` — посмотреть топ юзеров по деньгам.\n"
                              "<:aeOutlineDot:1266066158029770833> `/casino [bet] [amount]` — играть в казино.\n"
                              "<:aeOutlineDot:1266066158029770833> `/blackjack [bet]` — играть в блекджек.\n"
                              "<:aeOutlineDot:1266066158029770833> `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).\n",
                "footer": "Справочник по командам из раздела \"Экономика\""
            },
            "moderation": {
                "title": "Команды для модерации // unreleased",
                "description": "<:aeOutlineDot:1266066158029770833> `/lock` — заблокировать канал/ы.\n"
                              "<:aeOutlineDot:1266066158029770833> `/unlock` — разблокировать канал/ы.",
                "footer": "Справочник по командам для модерации"
            }   
        }

        if category is None:
            categories_list = "\n".join([f"<:aeOutlineDot:1266066158029770833> `{cat}` — {categories[cat]['title'].lower()}." for cat in categories])
            embed = create_embed(
                title="<:aeOutlineDot:1266066158029770833> Категории:",
                description=f"Чтобы выбрать категорию, используйте команду `/help <категория>`.\n\n"
                           f"**Доступные категории:**\n{categories_list}",
                footer={
                    'text': "<> - необязательные параметры.\n[] - обязательные параметры.",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
        elif category in categories:
            cat_info = categories[category]
            embed = create_embed(
                title=cat_info["title"],
                description=cat_info["description"],
                footer={
                    'text': cat_info["footer"],
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
        else:
            embed = create_embed(
                description="Категория не найдена.",
                footer=FOOTER_ERROR
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
