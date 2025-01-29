import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown, has_mod_role
import yaml

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
    
    @app_commands.command(name="unmute", description="Размутить участника")
    @app_commands.describe(
        member="Участник для размута",
        reason="Причина размута"
    )
    @has_mod_role()
    @command_cooldown()
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Причина не указана"):
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description="У меня нет прав на размут участников!",
                    color="RED"
                )
            )

        mute_role_id = self.config.get('moderation', {}).get('mute_role')
        if not mute_role_id:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка конфигурации",
                    description="Роль мута не настроена в конфигурации!",
                    color="RED"
                )
            )

        mute_role = interaction.guild.get_role(int(mute_role_id))
        if not mute_role:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description="Роль мута не найдена на сервере!",
                    color="RED"
                )
            )

        has_mute_role = mute_role in member.roles
        is_timed_out = member.is_timed_out()

        if not has_mute_role and not is_timed_out:
            return await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description=f"{member.mention} не находится в муте!",
                    color="RED"
                )
            )

        try:
            if has_mute_role:
                await member.remove_roles(mute_role, reason=reason)

            if is_timed_out:
                await member.timeout(None, reason=reason)
            
            unmute_embed = create_embed(
                title=f"{EMOJIS['UNMUTE']} Размут участника",
                color="GREEN"
            )
            
            unmute_embed.set_thumbnail(url=member.display_avatar.url)
            unmute_embed.add_field(
                name=f"{EMOJIS['USER']} Участник",
                value=member.mention,
                inline=True
            )
            unmute_embed.add_field(
                name=f"{EMOJIS['SHIELD']} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            unmute_embed.add_field(
                name=f"{EMOJIS['REASON']} Причина",
                value=f"```{reason}```",
                inline=False
            )
            unmute_embed.set_footer(text=f"ID: {member.id}")
            
            await interaction.response.send_message(embed=unmute_embed)
            
            try:
                dm_embed = create_embed(
                    title=f"{EMOJIS['UNMUTE']} Вы были размучены",
                    color="GREEN"
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['SERVER']} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['SHIELD']} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{EMOJIS['REASON']} Причина",
                    value=f"```{reason}```",
                    inline=False
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка прав",
                    description=f"У меня недостаточно прав для размута {member.mention}!",
                    color="RED"
                )
            )

async def setup(bot):
    await bot.add_cog(Unmute(bot))