from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для генерации случайных чисел (API-версия)
"""

import random

from typing import Optional

class RandomAPI:

    def __init__(self):
        pass

    def _create_result_embed(self, start: int, end: int, result: int, t) -> Embed:
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
        t = _(ctx=ctx)
        
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

random_api = RandomAPI()

async def generate_random_number(ctx, max_value: int, min_value: Optional[int] = None):
    await random_api.generate_random_number(ctx, max_value, min_value)

