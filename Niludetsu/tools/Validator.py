import functools
import inspect
from Niludetsu.tools.Embed import Embed
from Niludetsu.Exceptions import NiludetsuException

class Check:

    async def run(self, ctx, data: dict) -> dict:
        return data


class ValidationPipeline:

    def __init__(self, *checks: Check):
        self.checks = checks

    async def execute(self, ctx, **initial) -> dict:
        data = dict(initial)
        for check in self.checks:
            data = await check.run(ctx, data)
        return data


def economy(*checks: Check):

    def decorator(func):
        sig = inspect.signature(func)
        param_names = [
            name for name in sig.parameters
            if name not in ("self", "ctx")
        ]

        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.defer()

            for i, value in enumerate(args):
                if i < len(param_names):
                    kwargs[param_names[i]] = value

            pipeline = ValidationPipeline(*checks)
            try:
                data = await pipeline.execute(ctx, cog=self, **kwargs)
            except Exception as e:
                error_embed = Embed.exception(error=e, user=ctx.author)
                await ctx.reply(embed=error_embed, ephemeral=True)
                return
            
            ctx.eco = data
            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator
