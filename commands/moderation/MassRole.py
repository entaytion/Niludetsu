import asyncio, discord
from discord.ext import commands
from Niludetsu.moderation.checks import moderationcommand
from Niludetsu import send, Embed
from Niludetsu.moderation.system.massrole import MassRoleSystem
from Niludetsu.locale import _

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
        try:
            role = await commands.RoleConverter().convert(ctx, role_input)
            return role
        except commands.RoleNotFound:
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
    @moderationcommand(required_level=5, cooldown=300)
    async def massrole(
        self,
        ctx: commands.Context,
        role_input: str = None,
        action: str = "add"
    ):
        t = _(ctx=ctx)
        action_label_add = t("moderation", "massrole_action_add")
        action_label_remove = t("moderation", "massrole_action_remove")

        if not role_input:
            embed = Embed.error(description=t("moderation", "massrole_no_role"))
            await send(ctx, embed=embed, ephemeral=True)
            return

        action = action.lower()
        if action not in ["add", "remove"]:
            embed = Embed.error(description=t("moderation", "massrole_invalid_action"))
            await send(ctx, embed=embed, ephemeral=True)
            return

        role = await self._get_role_from_input(ctx, role_input)
        if not role:
            embed = Embed.error(description=t("moderation", "massrole_not_found", role=role_input))
            await send(ctx, embed=embed, ephemeral=True)
            return

        is_valid, error_msg = self.massrole_system.validate_role(ctx.guild, role)
        if not is_valid:
            embed = Embed.error(description=error_msg)
            await send(ctx, embed=embed, ephemeral=True)
            return

        is_valid, error_msg = self.massrole_system.validate_role_hierarchy(
            ctx.guild, ctx.author, role
        )
        if not is_valid:
            embed = Embed.error(description=error_msg)
            await send(ctx, embed=embed, ephemeral=True)
            return

        has_dangerous, dangerous_perms = self.massrole_system.has_dangerous_permissions(role)
        if has_dangerous:
            embed = Embed.error(description=t("moderation", "massrole_dangerous", role=role.mention))
            from Niludetsu.locale import DEFAULT_LOCALE
            issues_text = DEFAULT_LOCALE.get("moderation", {}).get("massrole_result_issues", "").format(count=error_count)
            embed.add_field(
                name=t("moderation", "massrole_result_issues_header"),
                value=issues_text,
                inline=False
            )
            embed.add_field(
                name=t("moderation", "massrole_dangerous_recommendation").split("\n", 1)[0] + ":",
                value=t("moderation", "massrole_dangerous_recommendation").split("\n", 1)[1] if "\n" in t("moderation", "massrole_dangerous_recommendation") else t("moderation", "massrole_dangerous_recommendation"),
                inline=False
            )
            await send(ctx, embed=embed, ephemeral=True)
            return

        action_text = action_label_add if action == "add" else action_label_remove
        members_count = len([m for m in ctx.guild.members if not m.bot])
        estimated_time = max(1, members_count // 10)

        confirm_embed = Embed.warning(
            title=t("moderation", "massrole_confirm_title"),
            description=t("moderation", "massrole_confirm_desc", action=action_text, role=role.mention, count=members_count)
        )
        confirm_embed.add_field(
            name=t("moderation", "massrole_details_header"),
            value=t("moderation", "massrole_details", name=role.name, action=action_text.capitalize(), count=members_count, time=estimated_time),
            inline=False
        )
        confirm_message = await ctx.send(embed=confirm_embed)

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
                cancel_embed = Embed.info(description=t("moderation", "massrole_cancelled"))
                await confirm_message.edit(embed=cancel_embed)
                await confirm_message.clear_reactions()
                return

            await confirm_message.clear_reactions()

            action_label = action_label_add if action == "add" else action_label_remove
            progress_embed = Embed.loading(
                title=t("moderation", "massrole_progress_title"),
                description=t("moderation", "massrole_progress", role=role.mention, action=action_label, total=members_count, processed="0")
            )
            await confirm_message.edit(embed=progress_embed)

            async def update_progress(processed, total):
                progress_embed.description = t("moderation", "massrole_progress", role=role.mention, action=action_label, total=total, processed=processed)
                try:
                    await confirm_message.edit(embed=progress_embed)
                except:
                    pass

            success_count, error_count, processed_members = await self.massrole_system.process_mass_role(
                guild=ctx.guild,
                moderator=ctx.author,
                role=role,
                action=action,
                progress_callback=update_progress
            )

            await self.massrole_system.log_mass_role_action(
                guild=ctx.guild,
                moderator=ctx.author,
                role=role,
                action=action,
                success_count=success_count,
                error_count=error_count
            )

            action_verb = t("moderation", "massrole_verb_given") if action == "add" else t("moderation", "massrole_verb_removed")
            result_embed = Embed.success(
                title=t("moderation", "massrole_result_title"),
                description=t("moderation", "massrole_result", role=role.mention, action=action_label, success=success_count, errors=error_count, verb=action_verb)
            )

            if error_count > 0:
                result_embed.add_field(
                    name=t("moderation", "massrole_result_issues_header"),
                    value=t("moderation", "massrole_result_issues", count=error_count),
                    inline=False
                )

            await confirm_message.edit(embed=result_embed)

        except asyncio.TimeoutError:
            timeout_embed = Embed.warning(
                title=t("moderation", "massrole_timeout"),
                description=t("moderation", "massrole_timeout_desc")
            )
            await confirm_message.edit(embed=timeout_embed)
            await confirm_message.clear_reactions()

async def setup(bot):
    """Загрузка расширения."""
    await bot.add_cog(MassRole(bot))

