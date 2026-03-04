import discord
from discord import app_commands
from discord.ext import commands
from Niludetsu import config
from typing import Optional

def _owner_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user and interaction.user.id == config.OWNER_ID
    return app_commands.check(predicate)

def _parse_color(color_str: Optional[str]) -> Optional[int]:
    if not color_str:
        return None
    s = color_str.strip().lower()
    try:
        if s.startswith("#"):
            return int(s[1:], 16)
        if s.startswith("0x"):
            return int(s, 16)
        # allow plain int or decimal string
        return int(s, 10)
    except Exception:
        return None

class Say(commands.Cog):
    """Developer-only say command to send messages/embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="🛡️ Отправить сообщение или эмбед от имени бота (только владелец)")
    @app_commands.guilds(config.SERVERS["MAIN_ID"])  # ускоряет обновление структуры команды
    @_owner_only()
    @app_commands.describe(
        title="Заголовок эмбеда (обязательно)",
        description="Описание эмбеда (обязательно)",
        color="Цвет эмбеда (обязательно: hex, 0xRRGGBB или число)",
        content="Текстовое содержимое сообщения (необязательно)",
        url="URL для заголовка эмбеда",
        image_url="URL изображения для эмбеда",
        thumbnail_url="URL миниатюры для эмбеда",
        footer="Текст футера эмбеда",
        author_name="Имя автора эмбеда",
        author_icon="URL иконки автора",
        timestamp="Добавить текущий timestamp в эмбед",
        channel="Канал, в который отправить (по умолчанию текущий)"
    )
    async def say(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str,
        content: Optional[str] = None,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        footer: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon: Optional[str] = None,
        timestamp: Optional[bool] = False,
        channel: Optional[discord.TextChannel] = None,
    ):
        """Send an embed (required title, description, color) as the bot. Only OWNER_ID can use it."""
        target = channel or interaction.channel
        if not isinstance(target, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            return await interaction.response.send_message("Эту команду можно использовать только в текстовых каналах/ветках.", ephemeral=True)

        # Build embed with required fields
        color_value = _parse_color(color)
        if color_value is None:
            return await interaction.response.send_message("Некорректный цвет. Используйте #RRGGBB, 0xRRGGBB или число.", ephemeral=True)

        embed = discord.Embed(title=title, description=description, color=color_value)
        if url:
            embed.url = url
        if image_url:
            embed.set_image(url=image_url)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if footer:
            embed.set_footer(text=footer)
        if author_name or author_icon:
            embed.set_author(name=author_name or "", icon_url=author_icon or discord.Embed.Empty)
        if timestamp:
            embed.timestamp = discord.utils.utcnow()

        try:
            await target.send(content=content or None, embed=embed)
        except discord.Forbidden:
            return await interaction.response.send_message("Нет прав отправлять сообщения в указанный канал.", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"Ошибка при отправке сообщения: {e}", ephemeral=True)

        await interaction.response.send_message("Отправлено.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))

