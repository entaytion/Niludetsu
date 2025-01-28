import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Mutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mutes", description="Показать список замученных участников")
    @has_mod_role()
    @command_cooldown()
    async def mutes(self, interaction: discord.Interaction):
        try:
            if not interaction.user.guild_permissions.moderate_members:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас нет прав на просмотр списка мутов!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение
            progress_embed = create_embed(
                title=f"{EMOJIS['LOADING']} Загрузка списка мутов",
                description="Собираю информацию о замученных участниках...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed)

            muted_members = []
            now = datetime.utcnow()

            for member in interaction.guild.members:
                if member.timed_out_until:
                    if member.timed_out_until > now:
                        muted_members.append({
                            'member': member,
                            'until': member.timed_out_until
                        })

            if not muted_members:
                no_mutes_embed = create_embed(
                    title=f"{EMOJIS['INFO']} Список мутов",
                    description="На сервере нет замученных участников",
                    color="GREEN"
                )
                return await interaction.edit_original_response(embed=no_mutes_embed)

            # Сортируем по времени окончания мута
            muted_members.sort(key=lambda x: x['until'])

            # Создаем эмбед со списком
            mutes_embed = create_embed(
                title=f"{EMOJIS['MUTE']} Список замученных участников",
                description=f"Всего замучено: `{len(muted_members)}` участников",
                color="BLUE"
            )

            # Добавляем информацию о каждом замученном участнике
            for i, mute_info in enumerate(muted_members, 1):
                member = mute_info['member']
                until = mute_info['until']
                time_left = until - now
                hours = time_left.total_seconds() // 3600
                minutes = (time_left.total_seconds() % 3600) // 60

                mutes_embed.add_field(
                    name=f"{i}. {member.name}",
                    value=(
                        f"**ID:** `{member.id}`\n"
                        f"**Осталось:** {int(hours)}ч {int(minutes)}м\n"
                        f"**До:** {until.strftime('%d.%m.%Y %H:%M')} UTC"
                    ),
                    inline=True
                )

                # Добавляем разделитель каждые 3 поля
                if i % 3 == 0:
                    mutes_embed.add_field(name="\u200b", value="\u200b", inline=False)

            mutes_embed.set_footer(text=f"Запросил: {interaction.user}")
            await interaction.edit_original_response(embed=mutes_embed)

        except Exception as e:
            error_embed = create_embed(
                title=f"{EMOJIS['ERROR']} Ошибка",
                description=f"Произошла непредвиденная ошибка: {str(e)}",
                color="RED"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed)
            else:
                await interaction.edit_original_response(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Mutes(bot)) 