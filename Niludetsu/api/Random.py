"""
Модуль для генерации случайных чисел (API-версия)
"""

import random
from Niludetsu import Embed
from typing import Optional

class RandomAPI:
    """Класс-обёртка для логики генерации случайных чисел и создания эмбедов"""

    def __init__(self):
        # Здесь можно добавить конфиг/логирование, если понадобится
        pass

    def _create_result_embed(self, start: int, end: int, result: int) -> Embed:
        """Создаёт красивый эмбед с результатом"""
        embed = Embed(
            title="🎲 Случайное число",
            description=f"В диапазоне от **{start}** до **{end}**."
        ).add_field(
            name="Результат:",
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
        # Валидация входных данных (копия логики из вашего исходного rand.py)
        if max_value is None:
            await ctx.reply(embed=Embed.error(description="Укажите максимальное число!"))
            return

        if min_value is not None and min_value >= max_value:
            await ctx.reply(embed=Embed.error(description="Минимальное число должно быть меньше максимального!"))
            return

        if min_value is None and max_value <= 0:
            await ctx.reply(embed=Embed.error(description="Число должно быть больше 0!"))
            return

        start = min_value if min_value is not None else 0
        try:
            result = random.randint(start, max_value)
        except ValueError:
            await ctx.reply(embed=Embed.error(description="Неверный диапазон чисел."))
            return

        embed = self._create_result_embed(start, max_value, result)
        await ctx.reply(embed=embed)

# Глобальный экземпляр для использования как API
random_api = RandomAPI()

# Удобная обёртка-функция (чтобы сохранить совместимость с вызовом из Cog)
async def generate_random_number(ctx, max_value: int, min_value: Optional[int] = None):
    """
    Обёртка для совместимости — вызывает random_api.generate_random_number.
    """
    await random_api.generate_random_number(ctx, max_value, min_value)

