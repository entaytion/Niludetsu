import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown, has_admin_role
import yaml

# Загрузка конфигурации
CONFIG_FILE = 'data/config.yaml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

class UnbanButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label="Разбанить", emoji="🔓")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if not await has_admin_role()(interaction):
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="У вас недостаточно прав для разбана пользователей!",
                    color="RED"
                ),
                ephemeral=True
            )

        try:
            user = await interaction.client.fetch_user(self.user_id)
            await interaction.guild.unban(user, reason=f"Разбан от {interaction.user}")
            
            unban_embed=Embed(
                title=f"{Emojis.UNBAN} Пользователь разбанен",
                color="GREEN"
            )
            
            unban_embed.set_thumbnail(url=user.display_avatar.url)
            unban_embed.add_field(
                name=f"{Emojis.USER} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            unban_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            unban_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            await interaction.response.send_message(embed=unban_embed)
            
            try:
                dm_embed=Embed(
                    title=f"{Emojis.UNBAN} Вы были разбанены",
                    color="GREEN"
                )
                dm_embed.add_field(
                    name=f"{Emojis.SERVER} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.SHIELD} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
                
        except discord.NotFound:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Пользователь не найден!",
                    color="RED"
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="У меня недостаточно прав для разбана пользователей!",
                    color="RED"
                ),
                ephemeral=True
            )

class BanView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.add_item(UnbanButton(user_id))

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Забанить пользователя на сервере")
    @app_commands.describe(
        user="Пользователь для бана",
        reason="Причина бана",
        delete_days="Удалить сообщения пользователя за последние X дней (0-7)"
    )
    @has_admin_role()
    @command_cooldown()
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана",
        delete_days: app_commands.Range[int, 0, 7] = 0
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Вы не можете забанить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.id == self.bot.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Я не могу забанить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Вы не можете забанить участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        try:
            ban_embed=Embed(
                title=f"{Emojis.BAN} Бан пользователя",
                color="RED"
            )
            
            ban_embed.set_thumbnail(url=user.display_avatar.url)
            ban_embed.add_field(
                name=f"{Emojis.USER} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            ban_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            ban_embed.add_field(
                name=f"{Emojis.REASON} Причина",
                value=f"```{reason}```",
                inline=False
            )
            if delete_days > 0:
                ban_embed.add_field(
                    name=f"{Emojis.TIME} Удаление сообщений",
                    value=f"За последние `{delete_days}` дней",
                    inline=False
                )
            ban_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            try:
                dm_embed=Embed(
                    title=f"{Emojis.BAN} Вы были забанены",
                    color="RED"
                )
                dm_embed.add_field(
                    name=f"{Emojis.SERVER} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.SHIELD} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.REASON} Причина",
                    value=f"```{reason}```",
                    inline=False
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            await user.ban(reason=reason, delete_message_days=delete_days)
            await interaction.response.send_message(embed=ban_embed, view=BanView(user.id))
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description=f"У меня недостаточно прав для бана {user.mention}!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Ban(bot)) 