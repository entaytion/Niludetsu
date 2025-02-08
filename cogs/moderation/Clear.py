import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
import asyncio

def has_manage_messages():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("У вас недостаточно прав для использования этой команды! Требуется право: `Управление сообщениями`", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

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

            if not interaction.guild.me.guild_permissions.manage_messages:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка прав",
                        description="У меня нет прав на управление сообщениями!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            # Отправляем начальное сообщение о процессе
            progress_embed=Embed(
                title=f"{Emojis.LOADING} Очистка сообщений",
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
            result_embed=Embed(
                title=f"{Emojis.SUCCESS} Очистка завершена",
                color="GREEN"
            )
            
            result_embed.add_field(
                name=f"{Emojis.CHANNEL} Канал",
                value=target_channel.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            result_embed.add_field(
                name=f"{Emojis.STATS} Удалено сообщений",
                value=f"`{len(deleted)}`",
                inline=True
            )

            if user:
                result_embed.add_field(
                    name=f"{Emojis.USER} Фильтр по пользователю",
                    value=user.mention,
                    inline=True
                )
            if contains:
                result_embed.add_field(
                    name=f"{Emojis.SEARCH} Фильтр по содержимому",
                    value=f"```{contains}```",
                    inline=True
                )

            # Отправляем результат
            await interaction.edit_original_response(embed=result_embed)

            # Отправляем временное уведомление в канал
            notification = await target_channel.send(
                embed=Embed(
                    description=f"{Emojis.SUCCESS} Удалено `{len(deleted)}` сообщений",
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
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description=f"У меня недостаточно прав для очистки сообщений в {target_channel.mention}!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Clear(bot))