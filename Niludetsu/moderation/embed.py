import discord
from typing import Optional, Union

class ModerationEmbedConstructor:
    """
    Универсальный конструктор для создания эмбедов модерационных действий
    """

    # Константы для эмбедов
    SYSTEM_NAME = "Æther! System"
    SYSTEM_ICON = "https://cdn.discordapp.com/emojis/1355956973006225490.webp?size=160"
    EMBED_COLOR = 0x000001  # Цвет 1

    # Типы наказаний и их названия
    PUNISHMENT_NAMES = {
        "mute": "Мут",
        "ban": "Бан",
        "warn": "Предупреждение",
        "timeout": "Тайм-аут"
    }

    @staticmethod
    def format_duration(minutes: int) -> str:
        """
        Конвертирует минуты в читаемый формат времени

        Parameters
        ----------
        minutes : int
            Количество минут

        Returns
        -------
        str
            Отформатированная строка времени
        """
        if minutes == 0:
            return "Навсегда"

        if minutes < 60:
            return f"{minutes} мин."

        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours < 24:
            if remaining_minutes == 0:
                return f"{hours} ч."
            else:
                return f"{hours} ч. {remaining_minutes} мин."

        days = hours // 24
        remaining_hours = hours % 24

        if days < 30:
            if remaining_hours == 0:
                return f"{days} д."
            else:
                return f"{days} д. {remaining_hours} ч."

        months = days // 30
        remaining_days = days % 30

        if remaining_days == 0:
            return f"{months} мес."
        else:
            return f"{months} мес. {remaining_days} д."

    @classmethod
    def moderationembed(
        cls,
        punishment_type: str,
        target_user: Union[discord.Member, discord.User],
        moderator: Union[discord.Member, discord.User],
        punishment_id: int,
        reason: str,
        duration_minutes: Optional[int] = None,
        mode: str = 'channel',
        is_removal: bool = False
    ) -> discord.Embed:
        """
        Универсальный метод для создания эмбедов модерации
        """
        # Определяем, это личное сообщение или канал
        is_dm = (mode == 'dm')

        base_punishment_type = punishment_type
        if punishment_type.lower().startswith("un"):
            base_punishment_type = punishment_type[2:]  # "unwarn" -> "warn"

        # Получаем название наказания
        punishment_name = cls.PUNISHMENT_NAMES.get(base_punishment_type.lower(), base_punishment_type.capitalize())

        # Формируем описание в зависимости от типа и контекста
        if is_removal:
            if is_dm:
                description = f"С вас было **снято** наказание: **``{punishment_name}``**."
                description += "\n-# - Наказание больше не действует."
            else:
                description = f"С <@{target_user.id}> было **снято** наказание **``{punishment_name}``**."
        else:
            if is_dm:
                description = f"Вы получили за нарушение правил сервера: **``{punishment_name}``**."
                description += "\n-# - Если вы не согласны с наказанием, обжалуйте его, прикрепивши его айди."
            else:
                description = f"<@{target_user.id}> получает за нарушение правил сервера: **``{punishment_name}``**."

        # Создаём эмбед
        embed = discord.Embed(
            description=description,
            color=cls.EMBED_COLOR
        )

        # Устанавливаем автора
        embed.set_author(
            name=cls.SYSTEM_NAME,
            icon_url=cls.SYSTEM_ICON
        )

        # Добавляем поля
        punishment_id_name = "> ID снятого наказания:" if is_removal else "> ID наказания:"
        embed.add_field(
            name=punishment_id_name,
            value=f"```{punishment_id}```",
            inline=True
        )

        # Поле причины (меняется в зависимости от типа)
        reason_field_name = "> Причина снятия:" if is_removal else "> Причина:"
        embed.add_field(
            name=reason_field_name,
            value=f"```{reason}```",
            inline=True
        )

        # Добавляем длительность (только для выдачи и если указана)
        if not is_removal and duration_minutes is not None:
            formatted_duration = cls.format_duration(duration_minutes)
            embed.add_field(
                name="> Длительность:",
                value=f"```{formatted_duration}```",
                inline=True
            )

        # Устанавливаем футер с информацией о модераторе
        moderator_name = f"{moderator.name}#{moderator.discriminator}" if moderator.discriminator != "0" else moderator.name
        embed.set_footer(
            text=f"Модератор: {moderator_name} | {moderator.id}",
            icon_url=moderator.display_avatar.url
        )

        return embed

# Функция для быстрого доступа
def moderationembed(punishment_type, target_user, moderator, punishment_id, reason, 
                   duration_minutes=None, mode='channel', is_removal=False) -> discord.Embed:
    """
    Быстрый доступ к универсальному конструктору эмбедов модерации

    Примеры использования:
    # Выдача мута на 3 часа для основного чата
    embed = moderationembed("mute", user, moderator, 1488, "1.1", 180)

    # Тот же мут для DM
    dm_embed = moderationembed("mute", user, moderator, 1488, "1.1", 180, mode='dm')

    # Снятие мута для основного чата
    unmute_embed = moderationembed("mute", user, moderator, 1488, "Истёк срок", is_removal=True)

    # Снятие мута для DM
    unmute_dm = moderationembed("mute", user, moderator, 1488, "Истёк срок", mode='dm', is_removal=True)
    """
    return ModerationEmbedConstructor.moderationembed(
        punishment_type, target_user, moderator, punishment_id, reason, 
        duration_minutes, mode, is_removal
    )

