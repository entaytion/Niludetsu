import discord
from discord.ext import commands
from discord import app_commands
import yaml
from datetime import datetime, timedelta
from Niludetsu import (
    Embed,
    Emojis,
    helper_only,
    cooldown,
    Database
)
import asyncio

# Загрузка конфигурации
with open('data/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

MOD_ROLE_ID = int(config.get('moderation', {}).get('mod_role', 0))
MAX_WARNINGS = int(config.get('moderation', {}).get('max_warnings', 3))

def has_mod_role():
    async def predicate(interaction: discord.Interaction):
        if MOD_ROLE_ID == 0:
            return False
        return interaction.user.guild_permissions.administrator or any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        )
    return app_commands.check(predicate)

def has_helper_role():
    async def predicate(interaction: discord.Interaction):
        if MOD_ROLE_ID == 0:
            return False
        return interaction.user.guild_permissions.administrator or any(
            role.id == MOD_ROLE_ID for role in interaction.user.roles
        )
    return app_commands.check(predicate)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        asyncio.create_task(self.db.init())  # Асинхронная инициализация базы данных

    async def get_user_active_warnings(self, user_id: int, guild_id: int) -> int:
        result = await self.db.execute(
            "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ? AND active = TRUE",
            (str(user_id), str(guild_id))
        )
        return result[0][0] if result else 0

    @app_commands.command(name="warn", description="Выдать предупреждение участнику")
    @app_commands.describe(
        member="Участник для предупреждения",
        reason="Причина предупреждения"
    )
    @has_helper_role()
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        await self._warn_member(interaction, member, reason)
        
    async def _warn_member(self, ctx, member: discord.Member, reason: str):
        """Общая логика выдачи предупреждения"""
        # Проверяем права
        if member.top_role >= ctx.guild.me.top_role:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Я не могу выдать предупреждение участнику с ролью выше моей",
                color="RED"
            )
            if isinstance(ctx, discord.Interaction):
                return await ctx.response.send_message(embed=embed, ephemeral=True)
            return await ctx.send(embed=embed)
            
        # Применяем предупреждение
        success = await self.punishment_handler.apply_punishment(
            member,
            "warn",
            reason,
            moderator_id=ctx.user.id if isinstance(ctx, discord.Interaction) else ctx.author.id
        )
        
        if success:
            embed = Embed(
                title=f"{Emojis.SUCCESS} Предупреждение выдано",
                description=f"{Emojis.DOT} **Участник:** {member.mention}\n"
                          f"{Emojis.DOT} **Причина:** {reason}",
                color="GREEN"
            )
        else:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Не удалось выдать предупреждение",
                color="RED"
            )
            
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    @app_commands.command(name="remove", description="Удалить предупреждение у пользователя")
    @app_commands.describe(
        user="Пользователь",
        warning_id="ID предупреждения для удаления"
    )
    @has_helper_role()
    @cooldown(seconds=3)
    async def warn_remove(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        warning_id: int
    ):
        # Отправляем сообщение о начале процесса
        progress_embed=Embed(
            title=f"{Emojis.LOADING} Удаление предупреждения",
            description=f"Удаляю предупреждение у {user.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)
        
        # Проверяем, существует ли предупреждение
        result = await self.db.fetch_all(
            """
            SELECT * FROM moderation 
            WHERE id = ? AND user_id = ? AND guild_id = ? AND type = 'warn' AND active = TRUE
            """,
            warning_id, str(user.id), str(interaction.guild.id)
        )
        warning = result[0] if result else None
        
        if not warning:
            return await interaction.edit_original_response(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Предупреждение не найдено!",
                    color="RED"
                )
            )

        # Деактивируем предупреждение
        await self.db.execute(
            """
            UPDATE moderation 
            SET active = FALSE 
            WHERE id = ? AND type = 'warn'
            """,
            warning_id
        )

        warning_count = await self.get_user_active_warnings(user.id, interaction.guild.id)

        # Пытаемся отправить личное сообщение
        dm_sent = False
        try:
            await user.send(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Предупреждение снято",
                    description=(
                        f"**Сервер:** {interaction.guild.name}\n"
                        f"**Модератор:** {interaction.user.mention}\n"
                        f"**Предупреждения:** `{warning_count}/{MAX_WARNINGS}`"
                    ),
                    color="GREEN"
                )
            )
            dm_sent = True
        except:
            pass

        # Создаем эмбед для канала
        remove_embed=Embed(
            title=f"{Emojis.SUCCESS} Предупреждение удалено",
            color="GREEN"
        )

        remove_embed.add_field(
            name=f"{Emojis.USER} Пользователь",
            value=f"{user.mention} (`{user.id}`)",
            inline=True
        )
        remove_embed.add_field(
            name=f"{Emojis.SHIELD} Модератор",
            value=interaction.user.mention,
            inline=True
        )
        remove_embed.add_field(
            name=f"{Emojis.WARNING} Предупреждения",
            value=f"`{warning_count}/{MAX_WARNINGS}`",
            inline=True
        )
        remove_embed.add_field(
            name=f"{Emojis.MESSAGE} Личное сообщение",
            value=f"{'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
            inline=False
        )

        await interaction.edit_original_response(embed=remove_embed)

    @app_commands.command(name="warnclear", description="Удалить все предупреждения у пользователя")
    @app_commands.describe(user="Пользователь для очистки предупреждений")
    @has_helper_role()
    @cooldown(seconds=3)
    async def warn_clear(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        # Отправляем сообщение о начале процесса
        progress_embed=Embed(
            title=f"{Emojis.LOADING} Очистка предупреждений",
            description=f"Удаляю все предупреждения у {user.mention}...",
            color="YELLOW"
        )
        await interaction.response.send_message(embed=progress_embed)

        # Деактивируем все предупреждения
        await self.db.execute(
            """
            UPDATE moderation 
            SET active = FALSE 
            WHERE user_id = ? AND guild_id = ? AND type = 'warn' AND active = TRUE
            """,
            str(user.id), str(interaction.guild.id)
        )

        # Пытаемся отправить личное сообщение
        dm_sent = False
        try:
            await user.send(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Предупреждения сняты",
                    description=(
                        f"**Сервер:** {interaction.guild.name}\n"
                        f"**Модератор:** {interaction.user.mention}\n"
                        f"**Предупреждения:** `0/{MAX_WARNINGS}`"
                    ),
                    color="GREEN"
                )
            )
            dm_sent = True
        except:
            pass

        # Создаем эмбед для канала
        clear_embed=Embed(
            title=f"{Emojis.SUCCESS} Предупреждения очищены",
            color="GREEN"
        )

        clear_embed.add_field(
            name=f"{Emojis.USER} Пользователь",
            value=f"{user.mention} (`{user.id}`)",
            inline=True
        )
        clear_embed.add_field(
            name=f"{Emojis.SHIELD} Модератор",
            value=interaction.user.mention,
            inline=True
        )
        clear_embed.add_field(
            name=f"{Emojis.WARNING} Предупреждения",
            value=f"`0/{MAX_WARNINGS}`",
            inline=True
        )
        clear_embed.add_field(
            name=f"{Emojis.MESSAGE} Личное сообщение",
            value=f"{'✅ Отправлено' if dm_sent else '❌ Не удалось отправить'}",
            inline=False
        )

        await interaction.edit_original_response(embed=clear_embed)

async def setup(bot):
    await bot.add_cog(Warn(bot))