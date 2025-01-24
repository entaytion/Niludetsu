import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from utils import create_embed

class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unlock", description="Разблокировать канал или все каналы")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(
        channel="Канал для разблокировки (оставьте пустым для текущего канала)",
        all_channels="Разблокировать все каналы"
    )
    async def unlock(
        self, 
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        all_channels: bool = False
    ):
        try:
            if not interaction.user.guild_permissions.manage_channels:
                if not interaction.response.is_done():
                    return await interaction.response.send_message(
                        embed=create_embed(
                            description="У вас нет прав на управление каналами!"
                        )
                    )

            if all_channels:
                success_count = 0
                failed_count = 0
                for ch in interaction.guild.channels:
                    try:
                        overwrites = ch.overwrites_for(interaction.guild.default_role)
                        overwrites.connect = None
                        overwrites.send_messages = None
                        await ch.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                        success_count += 1
                    except:
                        failed_count += 1
                
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        embed=create_embed(
                            description=f"Разблокировано {success_count} каналов\nНе удалось разблокировать {failed_count} каналов"
                        )
                    )
            else:
                target_channel = channel or interaction.channel
                overwrites = target_channel.overwrites_for(interaction.guild.default_role)
                overwrites.connect = None
                overwrites.send_messages = None
                await target_channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        embed=create_embed(
                            description=f"Канал {target_channel.mention} разблокирован"
                        )
                    )

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Произошла ошибка при выполнении команды!"
                    )
                )
            print(f"Ошибка в команде unlock: {e}")

async def setup(bot):
    await bot.add_cog(Unlock(bot))