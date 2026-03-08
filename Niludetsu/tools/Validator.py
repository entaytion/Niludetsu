import functools
import inspect
from Niludetsu.tools.Embed import Embed


class ValidationError(Exception):
    """Прерывает пайплайн и отдаёт embed пользователю."""

    def __init__(self, embed: Embed):
        self.embed = embed


class Check:
    """Один шаг валидации. Подклассы переопределяют run()."""

    async def run(self, ctx, data: dict) -> dict:
        return data


class ValidationPipeline:
    """Прогоняет список Check-ов по порядку."""

    def __init__(self, *checks: Check):
        self.checks = checks

    async def execute(self, ctx, **initial) -> dict:
        data = dict(initial)
        for check in self.checks:
            data = await check.run(ctx, data)
        return data


def economy(*checks: Check):
    """
    Декоратор для команд экономики. При ошибке автоматически шлёт embed.

    Все аргументы команды передаются в pipeline как начальные данные.
    Результат pipeline сохраняется в ctx.eco — dict с проверенными данными.

    Пример:
        @commands.hybrid_command(...)
        @economy(ParseAmount("bet"), EnsureBalance())
        async def coinflip(self, ctx, *, bet: Optional[str] = None):
            bet_value = ctx.eco["amount"]
    """

    def decorator(func):
        # Вытаскиваем имена параметров (кроме self и ctx), чтобы маппить
        # позиционные аргументы в именованные для pipeline
        sig = inspect.signature(func)
        param_names = [
            name for name in sig.parameters
            if name not in ("self", "ctx")
        ]

        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Defer сразу, чтобы interaction не истёк за 3 секунды
            if ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.defer()

            # Конвертируем позиционные аргументы в kwargs
            for i, value in enumerate(args):
                if i < len(param_names):
                    kwargs[param_names[i]] = value

            pipeline = ValidationPipeline(*checks)
            try:
                data = await pipeline.execute(ctx, cog=self, **kwargs)
            except ValidationError as e:
                await ctx.reply(embed=e.embed, ephemeral=True)
                return
            ctx.eco = data
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator
