import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import json

# Загрузка конфигурации
CONFIG_FILE = 'config/config.json'
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

MOD_ROLE_ID = int(config.get('MOD_ROLE_ID', 0))

def has_mod_role():
    async def predicate(interaction: discord.Interaction):
        if MOD_ROLE_ID == 0:
            return False
        return interaction.user.guild_permissions.administrator or any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        )
    return app_commands.check(predicate)

class UnbanButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label="Разбанить", emoji="🔓")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and not any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        ):
            await interaction.response.send_message(
                embed=create_embed(
                    description="У вас недостаточно прав для выполнения этого действия!"
                )
            )
            return

        try:
            user = await interaction.client.fetch_user(self.user_id)
            await interaction.guild.unban(user, reason=f"Разбан от {interaction.user}")
            
            try:
                await user.send(
                    embed=create_embed(
                        title="🔓 Разбан",
                        description=f"Модератор {interaction.user.mention} **разбанил** вас на сервере {interaction.guild.name}"
                    )
                )
                dm_sent = True
            except:
                dm_sent = False

            await interaction.response.edit_message(
                embed=create_embed(
                    title="🔓 Разбан",
                    description=f"**Пользователь:** {user.name} (ID: {user.id})\n"
                              f"**Модератор:** {interaction.user.name} (ID: {interaction.user.id})\n"
                              f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}"
                ),
                view=None
            )
            
        except discord.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пользователь не найден!"
                )
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Недостаточно прав для разбана!"
                )
            )

class BanView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=1800)  # 30 минут
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
    @has_mod_role()
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана",
        delete_days: app_commands.Range[int, 0, 7] = 0
    ):
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="У бота недостаточно прав для выполнения этого действия!"
                )
            )

        if user.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете забанить участника с равной или более высокой ролью!"
                )
            )

        if user.bot:
            return await interaction.response.send_message(
                embed=create_embed(
                    description="Вы не можете забанить бота!"
                )
            )

        try:
            try:
                await user.send(
                    embed=create_embed(
                        title="🔨 Бан",
                        description=f"Вы были забанены на сервере {interaction.guild.name}\n"
                                  f"**Причина:** `{reason}`\n"
                                  f"**Модератор:** {interaction.user.mention}"
                    )
                )
                dm_sent = True
            except:
                dm_sent = False

            await user.ban(reason=f"{reason} | Забанил: {interaction.user}", delete_message_days=delete_days)

            await interaction.response.send_message(
                embed=create_embed(
                    title="🔨 Бан",
                    description=f"**Пользователь:** {user.name} | (ID: {user.id})\n"
                              f"**Модератор:** {interaction.user.name} | (ID: {interaction.user.id})\n"
                              f"**Причина:** `{reason}`\n"
                              f"**Удалено сообщений:** за {delete_days} дней\n"
                              f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
                    footer={'text': f"ID: {user.id}"}
                ),
                view=BanView(user.id)
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Невозможно забанить этого пользователя!"
                )
            )

async def setup(bot):
    await bot.add_cog(Ban(bot)) 