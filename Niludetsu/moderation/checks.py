"""
Декоратор для модераторских команд с проверкой прав и кулдауном.
"""
import functools
from Niludetsu.config import OWNER_ID, ROLE_PRIORITY
from Niludetsu.tools.Embed import Embed
from Niludetsu.tools.Time import TimeService
from typing import Callable

_time = TimeService()

def moderationcommand(required_level: int = 1, cooldown: int = 0):
    """
    Декоратор для модераторских команд с проверкой прав и кулдауном.
    Кулдаун индивидуальный для пользователя. Для уровня 4+ кулдаун не применяется.

    Parameters
    ----------
    required_level : int
        Минимальный уровень разрешений (1-5):
        1 - Младший модератор
        2 - Модератор
        3 - Старший модератор
        4 - Админ-модератор (без кулдауна)
        5 - Администратор (без кулдауна)
    cooldown : int
        Кулдаун в секундах
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            member = ctx.author if hasattr(ctx, 'author') else ctx.user
            guild = ctx.guild

            # Правильно определяем тип взаимодействия
            is_interaction = getattr(ctx, 'interaction', None) is not None

            # Функция для отправки ошибок с правильным типом ответа
            async def send_error(embed):
                if is_interaction:
                    if ctx.interaction.response.is_done():
                        await ctx.followup.send(embed=embed)
                    else:
                        await ctx.interaction.response.send_message(embed=embed)
                else:
                    await ctx.send(embed=embed)

            # Проверяем владельца бота (максимальный приоритет)
            if member.id == OWNER_ID:
                user_level = 5
            # Проверяем владельца сервера
            elif guild.owner_id == member.id:
                user_level = 5
            # Проверяем права администратора Discord
            elif getattr(member, 'guild_permissions', None) and member.guild_permissions.administrator:
                user_level = 5
            else:
                # Получаем уровень из ROLE_PRIORITY в конфиге
                user_role_ids = [role.id for role in member.roles]
                user_level = max(
                    (ROLE_PRIORITY.get(role_id, 0) for role_id in user_role_ids),
                    default=0
                )

            # Проверка строгой иерархии
            if user_level < required_level:
                role_names = {
                    1: "Младший модератор",
                    2: "Модератор", 
                    3: "Старший модератор",
                    4: "Админ-модератор",
                    5: "Администратор"
                }
                required_role = role_names.get(required_level, f"Уровень {required_level}")
                await send_error(Embed.error(
                    description=f"Недостаточно прав для использования команды. Требуется: **{required_role}**"
                ))
                return

            # ПРОВЕРКА КУЛДАУНА (встроенный в TimeService)

            # Уровень 4+ не имеет кулдауна
            has_no_cooldown = user_level >= 4

            if cooldown > 0 and not has_no_cooldown:
                # Генерируем ключ для кулдауна: user_id:guild_id:command_name
                cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"

                # Проверяем кулдаун через TimeService
                can_use, remaining = _time.check_cooldown(cooldown_key, cooldown)

                if not can_use:
                    # Форматируем оставшееся время
                    remaining_formatted = _time.format_duration(remaining)
                    await send_error(Embed.error(
                        description=f"Команда на кулдауне. Повторите через: **{remaining_formatted}**"
                    ))
                    return

            try:
                result = await func(self, ctx, *args, **kwargs)
                return result

            except Exception as e:
                # Проверяем, является ли это ModerationError (ошибка иерархии/прав)
                try:
                    from Niludetsu.moderation.exceptions import ModerationError
                    if isinstance(e, ModerationError):
                        # Отправляем ошибку пользователю
                        error_embed = Embed.error(description=str(e))
                        await send_error(error_embed)
                        
                        # При ModerationError сбрасываем кулдаун
                        if cooldown > 0 and not has_no_cooldown:
                            cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"
                            _time.clear_cooldown(cooldown_key)
                        return
                except ImportError:
                    pass

                # При любых других ошибках сбрасываем кулдаун
                if cooldown > 0 and not has_no_cooldown:
                    cooldown_key = f"{member.id}:{guild.id}:{func.__name__}"
                    _time.clear_cooldown(cooldown_key)

                # Пробрасываем исключение дальше
                raise e

        return wrapper
    return decorator

def check_moderation_target(moderator, target, allow_bots_for_admin: bool = False):
    """
    Проверяет валидность цели модерации.

    Parameters
    ----------
    moderator : discord.Member
        Модератор
    target : discord.Member
        Цель модерации
    allow_bots_for_admin : bool
        Разрешить ботов для администраторов (уровень 5)

    Returns
    -------
    Tuple[bool, Optional[str]]
        (можно_модерировать, сообщение_об_ошибке)
    """
    # Проверка: нельзя модерировать себя
    if moderator.id == target.id:
        return False, "Нельзя выполнить это действие над собой!"

    # Проверка: нельзя модерировать владельца сервера
    if target.guild.owner_id == target.id:
        return False, "Нельзя выполнить это действие над владельцем сервера!"

    # Проверка: нельзя модерировать администратора Discord
    if target.guild_permissions.administrator:
        return False, "Нельзя выполнить это действие над администратором!"

    # Проверка: ботов можно банить только администраторам (уровень 5)
    if target.bot:
        if not allow_bots_for_admin:
            return False, "Нельзя выполнить это действие над ботом!"

        # Проверяем, есть ли у модератора уровень 5
        moderator_level = 0

        # Владелец бота
        if moderator.id == OWNER_ID:
            moderator_level = 5
        # Владелец сервера
        elif moderator.guild.owner_id == moderator.id:
            moderator_level = 5
        # Администратор Discord
        elif moderator.guild_permissions.administrator:
            moderator_level = 5
        else:
            # Получаем уровень из ролей
            moderator_role_ids = [role.id for role in moderator.roles]
            moderator_level = max(
                (ROLE_PRIORITY.get(role_id, 0) for role_id in moderator_role_ids),
                default=0
            )

        if moderator_level < 5:
            return False, "Только администраторы (уровень 5) могут модерировать ботов!"

    # Проверка иерархии ролей
    if target.top_role >= moderator.top_role:
        return False, "Вы не можете применять модерацию к пользователю с равной или более высокой ролью!"

    return True, None

