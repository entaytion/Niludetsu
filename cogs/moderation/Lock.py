import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lock", description="Заблокировать канал")
    @app_commands.describe(
        channel="Канал для блокировки (по умолчанию - текущий)",
        reason="Причина блокировки",
        all_channels="Заблокировать все каналы"
    )
    @has_mod_role()
    @command_cooldown()
    async def lock(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None,
        all_channels: Optional[bool] = False
    ):
        try:
            if not interaction.user.guild_permissions.manage_channels:
                return await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['ERROR']} Ошибка прав",
                        description="У вас нет прав на управление каналами!",
                        color="RED"
                    ),
                    ephemeral=True
                )

            if all_channels:
                success_count = 0
                failed_count = 0
                failed_channels = []
                
                progress_embed = create_embed(
                    title=f"{EMOJIS['LOADING']} Блокировка каналов",
                    description="Идет процесс блокировки всех каналов...",
                    color="YELLOW"
                )
                await interaction.response.send_message(embed=progress_embed)
                
                for ch in interaction.guild.channels:
                    try:
                        overwrites = ch.overwrites_for(interaction.guild.default_role)
                        overwrites.send_messages = False
                        overwrites.connect = False
                        await ch.set_permissions(
                            interaction.guild.default_role,
                            overwrite=overwrites,
                            reason=f"Массовая блокировка от {interaction.user}"
                        )
                        success_count += 1
                    except:
                        failed_count += 1
                        failed_channels.append(ch.mention)
                
                result_embed = create_embed(
                    title=f"{EMOJIS['LOCK']} Массовая блокировка завершена",
                    color="RED"
                )
                
                result_embed.add_field(
                    name=f"{EMOJIS['SUCCESS']} Успешно заблокировано",
                    value=f"`{success_count}` каналов",
                    inline=True
                )
                
                if failed_count > 0:
                    result_embed.add_field(
                        name=f"{EMOJIS['ERROR']} Не удалось заблокировать",
                        value=f"`{failed_count}` каналов",
                        inline=True
                    )
                    if failed_channels:
                        result_embed.add_field(
                            name="Проблемные каналы",
                            value=", ".join(failed_channels[:5]) + ("..." if len(failed_channels) > 5 else ""),
                            inline=False
                        )
                
                if reason:
                    result_embed.add_field(
                        name=f"{EMOJIS['REASON']} Причина",
                        value=f"```{reason}```",
                        inline=False
                    )
                
                result_embed.set_footer(text=f"Модератор: {interaction.user}")
                await interaction.edit_original_response(embed=result_embed)
            else:
                target_channel = channel or interaction.channel
                overwrites = target_channel.overwrites_for(interaction.guild.default_role)
                overwrites.send_messages = False
                
                if isinstance(target_channel, discord.VoiceChannel):
                    overwrites.connect = False
                
                await target_channel.set_permissions(
                    interaction.guild.default_role,
                    overwrite=overwrites,
                    reason=f"Блокировка от {interaction.user}"
                )
                
                lock_embed = create_embed(
                    title=f"{EMOJIS['LOCK']} Канал заблокирован",
                    color="RED"
                )
                
                lock_embed.add_field(
                    name=f"{EMOJIS['CHANNEL']} Канал",
                    value=target_channel.mention,
                    inline=True
                )
                lock_embed.add_field(
                    name=f"{EMOJIS['SHIELD']} Модератор",
                    value=interaction.user.mention,
                    inline=True
                )
                
                if reason:
                    lock_embed.add_field(
                        name=f"{EMOJIS['REASON']} Причина",
                        value=f"```{reason}```",
                        inline=False
                    )
                
                lock_embed.set_footer(text=f"ID канала: {target_channel.id}")
                await interaction.response.send_message(embed=lock_embed)

                # Отправляем уведомление в заблокированный канал
                try:
                    await target_channel.send(
                        embed=create_embed(
                            title=f"{EMOJIS['LOCK']} Канал заблокирован",
                            description=f"Модератор: {interaction.user.mention}\n"
                                      f"Причина: {f'```{reason}```' if reason else '`Не указана`'}",
                            color="RED"
                        )
                    )
                except discord.Forbidden:
                    pass

        except discord.Forbidden:
            error_embed = create_embed(
                title=f"{EMOJIS['ERROR']} Ошибка прав",
                description=f"У меня недостаточно прав для блокировки {'каналов' if all_channels else target_channel.mention}!",
                color="RED"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed)
            else:
                await interaction.edit_original_response(embed=error_embed)
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
    await bot.add_cog(Lock(bot))