import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
import asyncio

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Очистить сообщения в канале")
    @app_commands.describe(
        amount="Количество сообщений для удаления (1-1000)",
        user="Удалить сообщения только от конкретного пользователя",
        contains="Удалить сообщения, содержащие определенный текст",
        channel="Канал для очистки (по умолчанию - текущий)"
    )
    @has_mod_role()
    @command_cooldown()
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 1000],
        user: discord.Member = None,
        contains: str = None,
        channel: discord.TextChannel = None
    ):
        try:
            target_channel = channel or interaction.channel
            
            if not interaction.user.guild_permissions.manage_messages:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас нет прав на управление сообщениями!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if not interaction.guild.me.guild_permissions.manage_messages:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У меня нет прав на управление сообщениями!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение о процессе
            progress_embed = create_embed(
                title=f"{EMOJIS['LOADING']} Очистка сообщений",
                description="Идет процесс удаления сообщений...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed, ephemeral=True)

            def check_message(message):
                if user and message.author.id != user.id:
                    return False
                if contains and contains.lower() not in message.content.lower():
                    return False
                return True

            deleted = await target_channel.purge(
                limit=amount,
                check=check_message,
                reason=f"Очистка от {interaction.user}"
            )

            # Создаем эмбед с результатами
            result_embed = create_embed(
                title=f"{EMOJIS['SUCCESS']} Очистка завершена",
                color="GREEN"
            )
            
            result_embed.add_field(
                name=f"{EMOJIS['CHANNEL']} Канал",
                value=target_channel.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{EMOJIS['STATS']} Удалено сообщений",
                value=f"`{len(deleted)}`",
                inline=True
            )

            if user:
                result_embed.add_field(
                    name=f"{EMOJIS['USER']} Фильтр по пользователю",
                    value=user.mention,
                    inline=True
                )
            if contains:
                result_embed.add_field(
                    name=f"{EMOJIS['SEARCH']} Фильтр по содержимому",
                    value=f"```{contains}```",
                    inline=True
                )

            # Отправляем результат
            await interaction.edit_original_response(embed=result_embed)

            # Отправляем временное уведомление в канал
            notification = await target_channel.send(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} Удалено `{len(deleted)}` сообщений",
                    color="GREEN"
                )
            )
            await asyncio.sleep(5)
            try:
                await notification.delete()
            except discord.NotFound:
                pass

        except discord.Forbidden:
            await interaction.edit_original_response(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description=f"У меня недостаточно прав для очистки сообщений в {target_channel.mention}!",
                    color="RED"
                )
            )
        except Exception as e:
            await interaction.edit_original_response(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description=f"Произошла непредвиденная ошибка: {str(e)}",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Clear(bot))