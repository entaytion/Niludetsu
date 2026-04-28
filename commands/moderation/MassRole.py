import asyncio, discord
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, Embed
from Niludetsu.moderation.system.massrole import MassRoleSystem

from typing import Optional

class MassRole(commands.Cog):
    """Команды массовой выдачи/снятия ролей."""

    def __init__(self, bot):
        self.bot = bot
        self.massrole_system = MassRoleSystem(bot)

    async def _get_role_from_input(
        self,
        ctx: commands.Context,
        role_input: str
    ) -> Optional[discord.Role]:
        """
        Получает роль по упоминанию, ID или имени.

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды
        role_input : str
            Строка с ролью

        Returns
        -------
        Optional[discord.Role]
            Найденная роль или None
        """
        try:
            # Попытка через конвертер Discord.py
            role = await commands.RoleConverter().convert(ctx, role_input)
            return role
        except commands.RoleNotFound:
            # Поиск по имени (регистронезависимый)
            role = discord.utils.find(
                lambda r: r.name.lower() == role_input.lower(),
                ctx.guild.roles
            )
            return role

    @commands.command(
        name="massrole",
        aliases=["mr"],
        description="Массовая выдача или снятие роли"
    )
    @commands.guild_only()
    @moderationcommand(required_level=5, cooldown=300)  # Только администраторы
    async def massrole(
        self,
        ctx: commands.Context,
        role_input: str = None,
        action: str = "add"
    ):
        """
        Массовая выдача или снятие роли всем участникам сервера.

        ⚠️ **ВНИМАНИЕ:** Эта команда доступна только администраторам (уровень 5)!

        Примеры:
        • !massrole @Участник add - выдать роль всем
        • !massrole "Новичок" remove - снять роль у всех
        • !massrole 123456789012345678 add - выдать роль по ID

        Аргументы:
        • role_input - Роль (упоминание, имя или ID)
        • action - Действие (add - выдать, remove - снять)
        """

        if not role_input:
            error_description = (
                "Укажите роль для массовой операции!\n"
                "**Использование:**\n"
                "`!massrole <роль> [add/remove]`\n"
                "**Примеры:**\n"
                "• `!massrole @Участник add`\n"
                "• `!massrole \"Новичок\" remove`"
            )
            embed = Embed.error(description=error_description)
            await send(ctx, embed=embed, ephemeral=True)
            return

        action = action.lower()
        if action not in ["add", "remove"]:
            error_description = (
                "Действие должно быть `add` (выдать) или `remove` (снять)!\n"
                "**Примеры:**\n"
                "• `!massrole @Участник add`\n"
                "• `!massrole @Участник remove`"
            )
            embed = Embed.error(description=error_description)
            await send(ctx, embed=embed, ephemeral=True)
            return

        role = await self._get_role_from_input(ctx, role_input)
        if not role:
            error_description = (
                f"Не удалось найти роль **{role_input}**!\n"
                "Убедитесь, что роль существует и вы правильно указали её имя, ID или упоминание."
            )
            embed = Embed.error(description=error_description)
            await send(ctx, embed=embed, ephemeral=True)
            return

        # Базовая валидация роли
        is_valid, error_msg = self.massrole_system.validate_role(ctx.guild, role)
        if not is_valid:
            embed = Embed.error(description=error_msg)
            await send(ctx, embed=embed, ephemeral=True)
            return

        # Проверка иерархии ролей
        is_valid, error_msg = self.massrole_system.validate_role_hierarchy(
            ctx.guild, ctx.author, role
        )
        if not is_valid:
            embed = Embed.error(description=error_msg)
            await send(ctx, embed=embed, ephemeral=True)
            return

        # Проверка на опасные права
        has_dangerous, dangerous_perms = self.massrole_system.has_dangerous_permissions(role)
        if has_dangerous:
            error_description = (
                f"Роль {role.mention} содержит **опасные права доступа**!\n"
                "Массовая выдача такой роли может быть **небезопасной**.\n"
                "**Для безопасности сервера эта операция заблокирована.**"
            )
            embed = Embed.error(description=error_description)
            embed.add_field(
                name="🚨 Обнаруженные опасные права:",
                value="\n".join(dangerous_perms[:15]),  # Первые 15
                inline=False
            )
            embed.add_field(
                name="💡 Рекомендация:",
                value=(
                    "Удалите опасные права из роли перед массовой выдачей "
                    "или назначайте её вручную только проверенным участникам."
                ),
                inline=False
            )
            await send(ctx, embed=embed, ephemeral=True)
            return
            

        action_text = "выдать" if action == "add" else "снять"
        members_count = len([m for m in ctx.guild.members if not m.bot])
        estimated_time = max(1, members_count // 10)  # ~10 участников в секунду

        confirm_description = (
            f"Вы собираетесь **{action_text}** роль {role.mention} "
            f"**{members_count}** участникам сервера.\n"
            f"**⚠️ Это действие может занять некоторое время!**\n"
            f"**⚠️ Отменить операцию после запуска будет невозможно!**\n"
            f"Продолжить?"
        )

        confirm_embed = Embed.error(
            title="Подтверждение массовой операции",
            description=confirm_description
        )

        confirm_embed.add_field(
            name="📋 Детали операции:",
            value=(
                f"**Роль:** {role.name}\n"
                f"**Действие:** {action_text.capitalize()}\n"
                f"**Участников:** {members_count}\n"
                f"**Примерное время:** ~{estimated_time} секунд"
            ),
            inline=False
        )

        confirm_message = await ctx.send(embed=confirm_embed)

        # Добавляем реакции
        await confirm_message.add_reaction("✅")
        await confirm_message.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == confirm_message.id
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "❌":
                cancel_embed = Embed.info(
                    description="Массовая операция с ролями была отменена."
                )
                await confirm_message.edit(embed=cancel_embed)
                await confirm_message.clear_reactions()
                return

            await confirm_message.clear_reactions()

            # Embed с прогрессом
            progress_description = (
                f"**Роль:** {role.mention}\n"
                f"**Действие:** {'Выдача' if action == 'add' else 'Снятие'}\n"
                f"**Участников:** {members_count}\n"
                f"**Прогресс:** 0/{members_count}"
            )
            progress_embed = Embed.info(
                title="Обработка массовой операции...",
                description=progress_description
            )
            await confirm_message.edit(embed=progress_embed)

            # Callback для обновления прогресса
            async def update_progress(processed, total):
                progress_embed.description = (
                    f"**Роль:** {role.mention}\n"
                    f"**Действие:** {'Выдача' if action == 'add' else 'Снятие'}\n"
                    f"**Участников:** {total}\n"
                    f"**Прогресс:** {processed}/{total}"
                )
                try:
                    await confirm_message.edit(embed=progress_embed)
                except:
                    pass

            # Выполняем операцию
            success_count, error_count, processed_members = await self.massrole_system.process_mass_role(
                guild=ctx.guild,
                moderator=ctx.author,
                role=role,
                action=action,
                progress_callback=update_progress
            )

            # Логируем операцию
            await self.massrole_system.log_mass_role_action(
                guild=ctx.guild,
                moderator=ctx.author,
                role=role,
                action=action,
                success_count=success_count,
                error_count=error_count
            )

            # Финальный embed с результатами
            action_verb = "выдана" if action == "add" else "снята"
            result_description = (
                f"**Роль:** {role.mention}\n"
                f"**Действие:** {'Выдача' if action == 'add' else 'Снятие'}\n"
                f"**Успешно обработано:** {success_count}\n"
                f"**Ошибок:** {error_count}\n"
                f"**Итого:** Роль {action_verb} {success_count} участникам"
            )
            result_embed = Embed.success(
                title="Массовая операция завершена!",
                description=result_description
            )

            if error_count > 0:
                result_embed.add_field(
                    name="⚠️ Детали обработки",
                    value=(
                        f"Некоторые участники ({error_count}) не были обработаны "
                        "из-за ошибок прав доступа или API."
                    ),
                    inline=False
                )

            await confirm_message.edit(embed=result_embed)

        except asyncio.TimeoutError:
            timeout_embed = Embed.warning(
                title="Время ожидания истекло",
                description="Операция была отменена из-за отсутствия подтверждения."
            )
            await confirm_message.edit(embed=timeout_embed)
            await confirm_message.clear_reactions()

async def setup(bot):
    """Загрузка расширения."""
    await bot.add_cog(MassRole(bot))

