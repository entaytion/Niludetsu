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
        if category is None:
            embed = create_embed(
                title="<:aeOutlineDot:1266066158029770833> Категории:",
                description="Чтобы выбрать категорию, используйте команду `/help <категория>`.\n\n"
                            "**Доступные категории:**\n"
                            "<:aeOutlineDot:1266066158029770833> `main` — базовые команды.\n"
                            "<:aeOutlineDot:1266066158029770833> `music` — команды, связанные с музыкой.\n"
                            "<:aeOutlineDot:1266066158029770833> `economy` — команды, связанные с экономикой.",
                footer={
                    'text': "<> - необязательные параметры.\n[] - обязательные параметры.",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
        elif category == "main":
            embed = create_embed(
                title="Основные команды",
                description="<:aeOutlineDot:1266066158029770833> `/help` — помощь.\n"
                            "<:aeOutlineDot:1266066158029770833> `/reload` — перезагрузка бота.\n",
                footer={
                    'text': "Справочник по командам из раздела \"Основное\"",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
        elif category == "music":
            embed = create_embed(
                title="Команды для управления музыкой",
                description="<:aeOutlineDot:1266066158029770833> `/play` — воспроизвести песню или добавить в очередь.\n"
                            "<:aeOutlineDot:1266066158029770833> `/queue` — показать текущую очередь воспроизведения.\n"
                            "<:aeOutlineDot:1266066158029770833> `/skip` — пропустить текущую песню.\n"
                            "<:aeOutlineDot:1266066158029770833> `/stop` — остановить воспроизведение и очистить очередь.\n"
                            "<:aeOutlineDot:1266066158029770833> `/pause` — приостановить воспроизведение.\n"
                            "<:aeOutlineDot:1266066158029770833> `/np` — показать текущий трек и прогресс.\n"
                            "<:aeOutlineDot:1266066158029770833> `/repeat` — повторить текущую песню.\n"
                            "<:aeOutlineDot:1266066158029770833> `/shuffle` — перемешать песни.\n"
                            "<:aeOutlineDot:1266066158029770833> `/nightcore` — включить эффект Nightcore.\n"
                            "<:aeOutlineDot:1266066158029770833> `/resume` — возобновить воспроизведение.",
                footer={
                    'text': "Справочник по командам управления музыкой",
                    'icon_url': "https://cdn.discordapp.com/emojis/1265334981266374783.webp?size=160&quality=lossless"
                }
            )
        elif category == "economy":
            embed = create_embed(
                title="Команды экономики",
                description="<:aeOutlineDot:1266066158029770833> `/balance <user>` — проверить баланс.\n"
                            "<:aeOutlineDot:1266066158029770833> `/deposit [amount]` — перевести деньги в банк.\n"
                            "<:aeOutlineDot:1266066158029770833> `/withdraw [amount]` — снять деньги из банка.\n"
                            "<:aeOutlineDot:1266066158029770833> `/daily` — получить дневную награду (кулдаун: `24 часа`).\n"
                            "<:aeOutlineDot:1266066158029770833> `/work` — пойти на работу (кулдаун: `1 час`).\n"
                            "<:aeOutlineDot:1266066158029770833> `/pay [user] [amount]` — перевести деньги.\n"
                            "<:aeOutlineDot:1266066158029770833> `/leaderboard` — посмотреть топ юзеров по деньгам.\n"
                            "<:aeOutlineDot:1266066158029770833> `/casino [bet] [amount]` — играть в казино.\n"
                            "<:aeOutlineDot:1266066158029770833> `/rob [user]` — украсть деньги с кошелька (кулдаун: `5 минут`).\n",
                footer={
                    'text': "Справочник по командам из раздела \"Экономика\"",
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
