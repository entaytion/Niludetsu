import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, has_admin_role, command_cooldown
import yaml

class Reset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @app_commands.command(name="reset", description="Сбросить различные настройки сервера")
    @app_commands.describe(
        type="Что нужно сбросить",
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="mutes", value="mutes"),
        app_commands.Choice(name="warns", value="warns")
    ])
    @has_admin_role()
    @command_cooldown()
    async def reset(self, interaction: discord.Interaction, type: str):
        await interaction.response.defer()

        if type == "mutes":
            # Получаем роль мута из конфига
            mute_role_id = self.config.get('moderation', {}).get('mute_role')
            if not mute_role_id:
                return await interaction.followup.send(
                    embed=create_embed(description="❌ Роль мута не настроена в конфигурации!")
                )

            mute_role = interaction.guild.get_role(int(mute_role_id))
            if not mute_role:
                return await interaction.followup.send(
                    embed=create_embed(description="❌ Роль мута не найдена на сервере!")
                )

            # Подсчитываем количество замученных участников
            muted_members = len(mute_role.members)

            # Снимаем роль мута у всех участников
            for member in mute_role.members:
                try:
                    await member.remove_roles(mute_role, reason="Массовый сброс мутов")
                    # Если у участника есть таймаут, тоже снимаем его
                    if member.is_timed_out():
                        await member.timeout(None, reason="Массовый сброс мутов")
                except discord.Forbidden:
                    continue

            await interaction.followup.send(
                embed=create_embed(
                    title="🔄 Сброс мутов",
                    description=f"✅ Успешно снят мут с **{muted_members}** участников"
                )
            )

        elif type == "warns":
            import sqlite3
            from utils import DB_PATH

            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    # Получаем количество активных предупреждений перед удалением
                    cursor.execute(
                        "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND active = TRUE",
                        (str(interaction.guild.id),)
                    )
                    warns_count = cursor.fetchone()[0]
                    
                    # Деактивируем все предупреждения для этого сервера
                    cursor.execute(
                        "UPDATE warnings SET active = FALSE WHERE guild_id = ? AND active = TRUE",
                        (str(interaction.guild.id),)
                    )
                    conn.commit()

                await interaction.followup.send(
                    embed=create_embed(
                        title="🔄 Сброс предупреждений",
                        description=f"✅ Успешно деактивировано **{warns_count}** предупреждений"
                    )
                )
            except Exception as e:
                await interaction.followup.send(
                    embed=create_embed(description=f"❌ Произошла ошибка при сбросе предупреждений: {str(e)}")
                )

async def setup(bot):
    await bot.add_cog(Reset(bot)) 