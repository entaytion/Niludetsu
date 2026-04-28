import discord
from typing import Optional, Union

async def send(ctx, content=None, *, embed=None, view=None, ephemeral=False, **kwargs):
    """Универсальная отправка для префиксных и слэш команд."""
    if hasattr(ctx, "interaction") and ctx.interaction:
        if ctx.interaction.response.is_done():
            return await ctx.interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral, **kwargs)
        return await ctx.interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral, **kwargs)
    return await ctx.send(content=content, embed=embed, view=view, **kwargs)

async def defer(ctx, ephemeral=False):
    if hasattr(ctx, "interaction") and ctx.interaction:
        if not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(ephemeral=ephemeral)

async def send_moderation(ctx, embed):
    """Отправка лога модерации в канал и ответ юзеру."""
    await send(ctx, embed=embed)
