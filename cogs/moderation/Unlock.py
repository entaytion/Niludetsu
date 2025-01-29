import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role

class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unlock", description="Разблокировать канал")
    @app_commands.describe(
        channel="Канал для разблокировки (по умолчанию - текущий)",
        reason="Причина разблокировки",
        all_channels="Разблокировать все каналы"
    )
    @has_mod_role()
    @command_cooldown()
    async def unlock(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None,
        all_channels: Optional[bool] = False
    ):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У вас нет прав на управление каналами!",
                    color="RED"
                )
            )

        if all_channels:
            success_count = 0
            failed_count = 0
            failed_channels = []
            
            progress_embed = create_embed(
                title=f"{EMOJIS['LOADING']} Разблокировка каналов",
                description="Идет процесс разблокировки всех каналов...",
                color="YELLOW"
            )
            await interaction.response.send_message(embed=progress_embed)
            
            for ch in interaction.guild.channels:
                try:
                    overwrites = ch.overwrites_for(interaction.guild.default_role)
                    overwrites.connect = None
                    overwrites.send_messages = None
                    await ch.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                    success_count += 1
                except:
                    failed_count += 1
                    failed_channels.append(ch.mention)
            
            result_embed = create_embed(
                title=f"{EMOJIS['UNLOCK']} Массовая разблокировка завершена",
                color="GREEN"
            )
            
            result_embed.add_field(
                name=f"{EMOJIS['SUCCESS']} Успешно разблокировано",
                value=f"`{success_count}` каналов",
                inline=True
            )
            
            if failed_count > 0:
                result_embed.add_field(
                    name=f"{EMOJIS['ERROR']} Не удалось разблокировать",
                    value=f"`{failed_count}` каналов",
                    inline=True
                )
                if failed_channels:
                    result_embed.add_field(
                        name="Проблемные каналы",
                        value=", ".join(failed_channels[:5]) + ("..." if len(failed_channels) > 5 else ""),
                        inline=False
                    )
            
            result_embed.set_footer(text=f"Модератор: {interaction.user}")
            await interaction.edit_original_response(embed=result_embed)
        else:
            target_channel = channel or interaction.channel
            overwrites = target_channel.overwrites_for(interaction.guild.default_role)
            overwrites.connect = None
            overwrites.send_messages = None
            await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
            
            unlock_embed = create_embed(
                title=f"{EMOJIS['UNLOCK']} Канал разблокирован",
                color="GREEN"
            )
            
            unlock_embed.add_field(
                name=f"{EMOJIS['CHANNEL']} Канал",
                value=target_channel.mention,
                inline=True
            )
            unlock_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            
            if reason:
                unlock_embed.add_field(
                    name=f"{EMOJIS['REASON']} Причина",
                    value=f"```{reason}```",
                    inline=False
                )
            
            unlock_embed.set_footer(text=f"ID канала: {target_channel.id}")
            await interaction.response.send_message(embed=unlock_embed)

async def setup(bot):
    await bot.add_cog(Unlock(bot))