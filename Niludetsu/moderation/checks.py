from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService as Time
from Niludetsu.locale import _
import Niludetsu.config as config

"""
Декоратор для модераторских команд с проверкой прав и кулдауном.
"""
import functools

from typing import Callable

_time = Time()

def moderationcommand(required_level: int = 1, cooldown: int = 0):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            t = _(ctx=ctx)
            member = ctx.author if hasattr(ctx, 'author') else ctx.user
            guild = ctx.guild

            is_interaction = getattr(ctx, 'interaction', None) is not None

            async def send_error(embed):
                if is_interaction:
                    if ctx.interaction.response.is_done():
                        await ctx.followup.send(embed=embed)
                    else:
                        await ctx.interaction.response.send_message(embed=embed)
                else:
                    await ctx.send(embed=embed)

            if member.id == config.OWNER_ID:
                user_level = 5
            elif guild.owner_id == member.id:
                user_level = 5
            elif getattr(member, 'guild_permissions', None) and member.guild_permissions.administrator:
                user_level = 5
            else:
                user_role_ids = [role.id for role in member.roles]
                user_level = max(
                    (config.ROLE_PRIORITY.get(role_id, 0) for role_id in user_role_ids),
                    default=0
                )

            if user_level < required_level:
                role_names = {
                    1: t("moderation_checks", "role_junior"),
                    2: t("moderation_checks", "role_moderator"),
                    3: t("moderation_checks", "role_senior"),
                    4: t("moderation_checks", "role_admin_mod"),
                    5: t("moderation_checks", "role_admin"),
                }
                required_role = role_names.get(required_level, f"Уровень {required_level}")
                await send_error(Embed.error(
                    description=t("moderation_checks", "insufficient_perms", role=required_role)
                ))
                return


            has_no_cooldown = user_level >= 4

            if cooldown > 0 and not has_no_cooldown:
                cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"

                can_use, remaining = _time.check_cooldown(cooldown_key, cooldown)

                if not can_use:
                    remaining_formatted = _time.format_duration(remaining)
                    await send_error(Embed.error(
                        description=t("moderation_checks", "on_cooldown", time=remaining_formatted)
                    ))
                    return

            try:
                result = await func(self, ctx, *args, **kwargs)
                return result

            except Exception as e:
                try:
                    from Niludetsu.moderation.exceptions import ModerationError
                    if isinstance(e, ModerationError):
                        error_embed = Embed.error(description=str(e))
                        await send_error(error_embed)
                        
                        if cooldown > 0 and not has_no_cooldown:
                            cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"
                            _time.clear_cooldown(cooldown_key)
                        return
                except ImportError:
                    pass

                if cooldown > 0 and not has_no_cooldown:
                    cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"
                    _time.clear_cooldown(cooldown_key)

                raise e

        return wrapper
    return decorator

def check_moderation_target(moderator, target, allow_bots_for_admin: bool = False):
    if moderator.id == target.id:
        return False, "Нельзя выполнить это действие над собой!"

    if target.guild.owner_id == target.id:
        return False, "Нельзя выполнить это действие над владельцем сервера!"

    if target.guild_permissions.administrator:
        return False, "Нельзя выполнить это действие над администратором!"

    if target.bot:
        if not allow_bots_for_admin:
            return False, "Нельзя выполнить это действие над ботом!"

        moderator_level = 0

        if moderator.id == config.OWNER_ID:
            moderator_level = 5
        elif moderator.guild.owner_id == moderator.id:
            moderator_level = 5
        elif moderator.guild_permissions.administrator:
            moderator_level = 5
        else:
            moderator_role_ids = [role.id for role in moderator.roles]
            moderator_level = max(
                (config.ROLE_PRIORITY.get(role_id, 0) for role_id in moderator_role_ids),
                default=0
            )

        if moderator_level < 5:
            return False, "Только администраторы (уровень 5) могут модерировать ботов!"

    if target.top_role >= moderator.top_role:
        return False, "Вы не можете применять модерацию к пользователю с равной или более высокой ролью!"

    return True, None

