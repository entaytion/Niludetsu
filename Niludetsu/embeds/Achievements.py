"""Унифицированные эмбеды для системы достижений.

Формат соответствует стилю EconomyEmbed:
    Title:       "Действие — username"
    Description: "@user, текст..."
    Thumbnail:   аватар пользователя
    Color:       Colors.PRIMARY
"""

from typing import List, Dict, Union
import discord
from Niludetsu.tools.Embed import Colors, Embed
from Niludetsu.tools.Emojis import Emojis

class AchievementEmbed:
    """Фабрика embed'ов для достижений."""

    @staticmethod
    def unlocked(
        user: Union[discord.Member, discord.User],
        achievements: List[Dict],
    ) -> Embed:
        """Embed для одного или нескольких полученных достижений."""
        count = len(achievements)
        action = "Новое достижение" if count == 1 else "Новые достижения"
        
        lines = []
        if count == 1:
            ach = achievements[0]
            desc = (
                f"вы получили достижение **{ach.get('icon', '')} {ach['name']}**\n"
                f"Награда: **{ach['reward']:,}** {Emojis.MONEY}"
            )
            lines.append(f"{user.mention}, {desc}")
        else:
            lines.append(f"{user.mention}, вы получили новые достижения!\n")
            for ach in achievements:
                lines.append(
                    f"**{ach.get('icon', '')} {ach['name']}** — "
                    f"награда: **{ach['reward']:,}** {Emojis.MONEY}"
                )

        return Embed.user(
            user=user,
            title_prefix=action,
            description="\n".join(lines).strip(),
            color=Colors.PRIMARY,
        )
