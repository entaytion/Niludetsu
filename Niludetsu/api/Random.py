from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для генерации случайных чисел (API-версия)
"""

import random

from typing import Optional

class RandomAPI:
    """Класс-обёртка для логики генерации случайных чисел и создания эмбедов"""

    def __init__(self):
        # Здесь можно добавить конфиг/логирование, если понадобится
        pass

    def _create_result_embed(self, start: int, end: int, result: int, t) -> Embed:
        """Создаёт красивый эмбед с результатом"""
        embed = Embed(
            title=t("api_random", "title"),
            description=t("api_random", "range", start=start, end=end)
        ).add_field(
            name=t("api_random", "result"),
            value=f"```{result}```",
            inline=False
        )
        return embed

    async def generate_random_number(self, ctx, max_value: int, min_value: Optional[int] = None):
        """
        Генерирует случайное число в указанном диапазоне и отправляет ответ в контекст.

        Parameters
        ----------
        ctx : Union[discord.Interaction, commands.Context]
            Объект взаимодействия Discord или контекст команды
        max_value : int
            Максимальное число (или единственное число для диапазона 0-max)
        min_value : Optional[int]
            Минимальное число (необязательно)
        """
        t = _(ctx=ctx)
        
        # Валидация входных данных (копия логики из вашего исходного rand.py)
        if max_value is None:
            await ctx.reply(embed=Embed.error(description=t("api_random", "specify_max")))
            return

        if min_value is not None and min_value >= max_value:
            await ctx.reply(embed=Embed.error(description=t("api_random", "min_vs_max")))
            return

        if min_value is None and max_value <= 0:
            await ctx.reply(embed=Embed.error(description=t("api_random", "positive_only")))
            return

        start = min_value if min_value is not None else 0
        try:
            result = random.randint(start, max_value)
        except ValueError:
            await ctx.reply(embed=Embed.error(description=t("api_random", "invalid_range")))
            return

        embed = self._create_result_embed(start, max_value, result, t)
        await ctx.reply(embed=embed)

# Глобальный экземпляр для использования как API
random_api = RandomAPI()

# Удобная обёртка-функция (чтобы сохранить совместимость с вызовом из Cog)
async def generate_random_number(ctx, max_value: int, min_value: Optional[int] = None):
    """
    Обёртка для совместимости — вызывает random_api.generate_random_number.
    """
    await random_api.generate_random_number(ctx, max_value, min_value)

