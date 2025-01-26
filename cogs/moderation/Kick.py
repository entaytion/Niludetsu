import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
import yaml

# Загрузка конфигурации
CONFIG_FILE = 'config/config.yaml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

MOD_ROLE_ID = int(config.get('moderation', {}).get('mod_role', 0)) # Преобразование строки в целое число

# Проверка роли модератора
def has_mod_role():
    async def predicate(interaction: discord.Interaction):
        try:
            if MOD_ROLE_ID == 0:
                return interaction.user.guild_permissions.administrator
            return interaction.user.guild_permissions.administrator or any(
                role.id == MOD_ROLE_ID for role in interaction.user.roles
            )
        except Exception as e:
            print(f"Error in mod role check: {e}")
            return False
    return app_commands.check(predicate)

# Класс кнопки для отмены кика
class UndoKickButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(style=discord.ButtonStyle.success, label="Отменить кик", emoji="🔄")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        try:
            # Проверка прав с более надежной логикой
            if not (interaction.user.guild_permissions.administrator or 
                    any(role.id == MOD_ROLE_ID for role in interaction.user.roles)):
                await interaction.response.send_message(
                    embed=create_embed(
                        description="У вас недостаточно прав для выполнения этого действия!"
                    )
                )
                return

            user = await interaction.client.fetch_user(self.user_id)
            
            # Создаем приглашение с обработкой ошибок
            try:
                invite = await interaction.channel.create_invite(max_age=1800, max_uses=1)
            except discord.HTTPException:
                # Если не удалось создать приглашение, используем альтернативный канал
                invite = await interaction.guild.system_channel.create_invite(max_age=1800, max_uses=1) \
                    if interaction.guild.system_channel else None

            # Отправка личного сообщения с обработкой ошибок
            dm_sent = False
            try:
                await user.send(
                    embed=create_embed(
                        title="🔄 Отмена кика",
                        description=f"Модератор {interaction.user.name} отменил ваш кик.\n" 
                                    f"Вернуться на сервер: {invite.url if invite else 'Приглашение недоступно'}"
                    )
                )
                dm_sent = True
            except discord.HTTPException:
                pass

            # Обновление сообщения с кнопкой
            await interaction.response.edit_message(
                embed=create_embed(
                    title="🔄 Отмена кика",
                    description=f"Пользователь: {user.name} (ID: {user.id})\n"
                                f"Приглашение: {invite.url if invite else 'Недоступно'}\n"
                                f"Личное сообщение: {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}"
                ),
                view=None
            )

        except discord.NotFound:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Пользователь не найден!"
                )
            )
        except Exception as e:
            print(f"Unexpected error in UndoKickButton: {e}")
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Произошла непредвиденная ошибка: {str(e)}"
                )
            )

# Класс представления с кнопкой
class KickView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=1800)  # 30 минут
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
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана",
    ):
        try:
            # Расширенная проверка прав
            if not interaction.guild.me.guild_permissions.kick_members:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="У бота недостаточно прав для выполнения этого действия!"
                    )
                )

            if user.top_role >= interaction.user.top_role:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Вы не можете кикнуть участника с равной или более высокой ролью!"
                    )
                )

            if user.bot:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Вы не можете кикнуть бота!"
                    )
                )

            # Отправка личного сообщения с обработкой ошибок
            dm_sent = False
            try:
                await user.send(
                    embed=create_embed(
                        title="🦶 Кик",
                        description=f"Вы были **кикнуты с сервера** {interaction.guild.name}\n"
                                    f"**Причина:** `{reason}`\n"
                                    f"**Модератор:** {interaction.user.name}"
                    )
                )
                dm_sent = True
            except discord.HTTPException:
                pass

            # Кик пользователя
            await user.kick(reason=f"{reason} | Кикнул: {interaction.user}")

            # Отправка подтверждающего сообщения
            await interaction.response.send_message(
                embed=create_embed(
                    title="🦶 Кик",
                    description=f"Пользователь: {user.name} (ID: {user.id})\n"
                                f"**Модератор:** {interaction.user.name} (ID: {interaction.user.id})\n"
                                f"**Причина:** `{reason}`\n"
                                f"**Личное сообщение:** {'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
                    footer={'text': f"ID: {user.id}"}
                ),
                view=KickView(user.id)  # Добавляем кнопки
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Невозможно кикнуть этого пользователя!"
                )
            )
        except Exception as e:
            print(f"Unexpected error in kick command: {e}")
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Произошла непредвиденная ошибка: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(Kick(bot))