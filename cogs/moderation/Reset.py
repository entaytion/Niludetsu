import discord
from discord.ext import commands
from discord import app_commands
import yaml
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown, has_admin_role
from Niludetsu.database import Database

class Reset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @app_commands.command(name="reset", description="Сбросить муты и/или предупреждения участника")
    @app_commands.describe(
        member="Участник для сброса",
        mutes="Сбросить муты",
        warns="Сбросить предупреждения",
        reason="Причина сброса"
    )
    @has_admin_role()
    @command_cooldown()
    async def reset(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        mutes: Optional[bool] = False,
        warns: Optional[bool] = False,
        reason: Optional[str] = None
    ):
        if not (mutes or warns):
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка параметров",
                    description="Выберите хотя бы одно действие: сброс мутов или предупреждений!",
                    color="RED"
                ),
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="Вы не можете сбросить данные участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        # Отправляем начальное сообщение
        progress_embed = Embed(
            title=f"{Emojis.LOADING} Сброс данных",
            description=f"Сбрасываю данные участника {member.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        success_actions = []
        failed_actions = []

        # Сброс мутов
        if mutes:
            try:
                # Удаляем все активные муты из базы данных
                await self.db.execute(
                    "DELETE FROM mutes WHERE user_id = ? AND guild_id = ?",
                    (member.id, interaction.guild_id)
                )
                # Снимаем роль мута, если она есть
                mute_role_id = self.config['roles'].get('muted')
                if mute_role_id:
                    mute_role = interaction.guild.get_role(int(mute_role_id))
                    if mute_role and mute_role in member.roles:
                        await member.remove_roles(mute_role, reason=f"Сброс мутов от {interaction.user}: {reason if reason else 'Причина не указана'}")
                success_actions.append("муты")
            except Exception as e:
                print(f"Ошибка при сбросе мутов: {e}")
                failed_actions.append("муты")

        # Сброс предупреждений
        if warns:
            try:
                # Удаляем все предупреждения из базы данных
                await self.db.execute(
                    "DELETE FROM warns WHERE user_id = ? AND guild_id = ?",
                    (member.id, interaction.guild_id)
                )
                success_actions.append("предупреждения")
            except Exception as e:
                print(f"Ошибка при сбросе предупреждений: {e}")
                failed_actions.append("предупреждения")

        # Создаем эмбед с результатами
        if success_actions:
            description = f"Успешно сброшены: {', '.join(success_actions)}"
            if failed_actions:
                description += f"\nНе удалось сбросить: {', '.join(failed_actions)}"
        else:
            description = f"Не удалось сбросить: {', '.join(failed_actions)}"

        result_embed = Embed(
            title=f"{Emojis.SUCCESS if success_actions else Emojis.ERROR} Результат сброса данных",
            description=description,
            color="GREEN" if success_actions else "RED"
        )
        result_embed.add_field(
            name="Информация",
            value=f"**Участник:** {member.mention}\n"
                  f"**Модератор:** {interaction.user.mention}\n"
                  f"**Причина:** {reason or 'Не указана'}"
        )

        await interaction.edit_original_response(embed=result_embed)

async def setup(bot):
    await bot.add_cog(Reset(bot))