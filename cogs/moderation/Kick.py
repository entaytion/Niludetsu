import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
import yaml

# Загрузка конфигурации
CONFIG_FILE = 'data/config.yaml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

MOD_ROLE_ID = int(config.get('moderation', {}).get('mod_role', 0)) # Преобразование строки в целое число

# Класс кнопки для отмены кика
class UndoKickButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label="Отменить кик", emoji="🔄")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        try:
            if not await has_mod_role()(interaction):
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас недостаточно прав для отмены кика!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            user = await interaction.client.fetch_user(self.user_id)
            invite = await interaction.channel.create_invite(
                max_age=1800,
                max_uses=1,
                reason=f"Отмена кика от {interaction.user}"
            )
            
            try:
                dm_embed=Embed(
                    title=f"{EMOJIS['INVITE']} Приглашение на сервер",
                    description=f"Модератор {interaction.user.mention} отменил ваш кик.\nВы можете вернуться на сервер по этой ссылке: {invite.url}",
                    color="GREEN"
                )
                await user.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False

            undo_embed=Embed(
                title=f"{EMOJIS['SUCCESS']} Кик отменён",
                color="GREEN"
            )
            
            undo_embed.add_field(
                name=f"{EMOJIS['USER']} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            undo_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            undo_embed.add_field(
                name=f"{EMOJIS['MESSAGE']} Статус",
                value=f"Приглашение {'отправлено' if dm_sent else 'не удалось отправить'} в ЛС",
                inline=False
            )
            undo_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            await interaction.response.send_message(embed=undo_embed)
            
        except discord.NotFound:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Пользователь не найден!",
                    color="RED"
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У меня недостаточно прав для создания приглашения!",
                    color="RED"
                ),
                ephemeral=True
            )

# Класс представления с кнопкой
class KickView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.add_item(UndoKickButton(user_id))

# Команда для кика
class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Выгнать пользователя с сервера")
    @app_commands.describe(
        user="Пользователь для кика",
        reason="Причина кика",
    )
    @has_mod_role()
    @command_cooldown()
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана",
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Вы не можете кикнуть самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.id == self.bot.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Я не могу кикнуть самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Вы не можете кикнуть участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        try:
            kick_embed=Embed(
                title=f"{EMOJIS['KICK']} Кик пользователя",
                color="YELLOW"
            )
            
            kick_embed.set_thumbnail(url=user.display_avatar.url)
            kick_embed.add_field(
                name=f"{EMOJIS['USER']} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            kick_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            kick_embed.add_field(
                name=f"{EMOJIS['REASON']} Причина",
                value=f"```{reason}```",
                inline=False
            )
            kick_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            try:
                dm_embed=Embed(
                    title=f"{EMOJIS['KICK']} Вы были кикнуты",
                    color="YELLOW"
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['SERVER']} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['SHIELD']} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['REASON']} Причина",
                    value=f"```{reason}```",
                    inline=False
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            await user.kick(reason=reason)
            await interaction.response.send_message(embed=kick_embed, view=KickView(user.id))
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description=f"У меня недостаточно прав для кика {user.mention}!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Kick(bot))