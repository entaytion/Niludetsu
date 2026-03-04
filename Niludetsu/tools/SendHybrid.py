from __future__ import annotations

from typing import Any, Optional

import discord


def _resolve_interaction(ctx: Any) -> Optional[discord.Interaction]:
    if isinstance(ctx, discord.Interaction):
        return ctx
    return getattr(ctx, "interaction", None)


def ensure_embed(result: Any) -> discord.Embed:
    from Niludetsu.tools.Embed import Embed  # local import to avoid import cycles

    if isinstance(result, discord.Embed):
        return result

    if isinstance(result, dict):
        if not result.get("success", False):
            error_msg = result.get("error", "Неизвестная ошибка")
            return Embed.error(description=error_msg)

        embed = result.get("embed")
        if isinstance(embed, discord.Embed):
            return embed
        return Embed.success(description=f"✅ Действие выполнено успешно! **ID:** {result.get('punishment_id', 'N/A')}")

    return Embed.error(description="Неверный формат ответа")


async def defer(ctx: Any, *, ephemeral: bool = False, thinking: bool = True) -> bool:
    interaction = _resolve_interaction(ctx)
    if interaction is None:
        return False
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=ephemeral, thinking=thinking)
            return True
    except discord.HTTPException:
        return False
    return False


def _embed_kwargs(
    embed: Optional[discord.Embed] = None,
    embeds: Optional[list[discord.Embed]] = None,
) -> dict[str, Any]:
    """Return either ``embed`` or ``embeds`` — never both — to avoid
    ``TypeError: Cannot mix embed and embeds keyword arguments``."""
    if embed is not None and embeds is not None:
        # embed takes priority; drop embeds
        return {"embed": embed}
    if embed is not None:
        return {"embed": embed}
    if embeds is not None:
        return {"embeds": embeds}
    return {}


async def send(
    ctx: Any,
    content: Optional[str] = None,
    *,
    embed: Optional[discord.Embed] = None,
    embeds: Optional[list[discord.Embed]] = None,
    view: Optional[discord.ui.View] = None,
    ephemeral: bool = False,
    mention_author: bool = False,
    reply: bool = False,
    **kwargs: Any,
) -> Optional[discord.Message]:
    """Unified sender for prefix/hybrid/slash contexts.

    - For interactions: uses response.send_message or followup.send.
    - For prefix contexts: uses ctx.reply (optional) or ctx.send.
    - Falls back to ctx.channel.send if interaction is already dead.
    """

    embed_kw = _embed_kwargs(embed, embeds)
    interaction = _resolve_interaction(ctx)

    if interaction is not None:
        try:
            if interaction.response.is_done():
                return await interaction.followup.send(
                    content,
                    **embed_kw,
                    view=view,
                    ephemeral=ephemeral,
                    **kwargs,
                )

            await interaction.response.send_message(
                content,
                **embed_kw,
                view=view,
                ephemeral=ephemeral,
                **kwargs,
            )
            try:
                return await interaction.original_response()
            except Exception:
                return None
        except discord.NotFound:
            # 10062 Unknown interaction
            pass
        except discord.HTTPException:
            pass

        channel = getattr(ctx, "channel", None)
        if channel is not None:
            try:
                return await channel.send(content, **embed_kw, view=view, **kwargs)
            except Exception:
                return None
        return None

    if reply and hasattr(ctx, "reply"):
        return await ctx.reply(
            content,
            **embed_kw,
            view=view,
            mention_author=mention_author,
            **kwargs,
        )

    if hasattr(ctx, "send"):
        return await ctx.send(content, **embed_kw, view=view, **kwargs)

    channel = getattr(ctx, "channel", None)
    if channel is not None:
        return await channel.send(content, **embed_kw, view=view, **kwargs)
    return None


async def send_moderation(ctx: Any, *, embed: discord.Embed) -> None:
    """Send moderation result with different UX for prefix vs slash:

    - Prefix: delete user's command message, send embed as public message
    - Slash: ephemeral confirmation to moderator, send embed as public message
    """
    is_slash = getattr(ctx, "interaction", None) is not None

    if is_slash:
        interaction = ctx.interaction
        if interaction.response.is_done():
            await interaction.followup.send("Команда выполнена.", ephemeral=True)
        else:
            await interaction.response.send_message("Команда выполнена.", ephemeral=True)
        await ctx.channel.send(embed=embed)
    else:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.channel.send(embed=embed)
