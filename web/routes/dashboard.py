from __future__ import annotations

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..auth import get_current_user, fetch_user_guilds
from ..database import db
from ..bot import get_bot

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="web/templates")


class SettingsIn(BaseModel):
    bump_color: str
    bump_title: str
    bump_description: str

    welcome_channel_id: str | None = None
    welcome_title: str | None = None
    welcome_description: str | None = None

    goodbye_channel_id: str | None = None
    goodbye_title: str | None = None
    goodbye_description: str | None = None

    level_title: str | None = None
    level_description: str | None = None
    level_message: str | None = None

    boost_channel_id: str | None = None
    boost_title: str | None = None
    boost_description: str | None = None

    cogs: dict[str, bool] | None = None


async def _ensure_admin_guilds(user: dict) -> list:
    guilds = await fetch_user_guilds(user["access_token"])
    admin = []
    for g in guilds:
        perms = int(g.get("permissions", "0"))
        if (perms & 0x8) or g.get("owner", False):
            admin.append(g)
    return admin


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request, user=Depends(get_current_user)):
    try:
        guilds = await _ensure_admin_guilds(user)
    except Exception:
        return RedirectResponse(url="/auth/logout", status_code=303)

    for g in guilds:
        g["is_premium"] = await db.is_premium(g["id"])

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "guilds": guilds},
    )


@router.get("/dashboard/guild/{guild_id}", response_class=HTMLResponse)
async def guild_settings(guild_id: str, request: Request, user=Depends(get_current_user)):
    try:
        guilds = await _ensure_admin_guilds(user)
    except Exception:
        return RedirectResponse(url="/auth/logout", status_code=303)

    guild = next((g for g in guilds if g["id"] == guild_id), None)
    if not guild:
        raise HTTPException(status_code=403, detail="Forbidden")

    bot = get_bot()
    channels = []
    cogs_states = {}
    
    is_premium = await db.is_premium(guild_id)
    settings = await db.get_guild_settings(guild_id)

    if bot:
        g = bot.get_guild(int(guild_id))
        if g:
            channels = [
                {"id": str(c.id), "name": c.name, "type": 0}
                for c in g.text_channels
            ]
        cogs_list = sorted([name for name in bot.cogs.keys() if name != "Owner"])
        for name in cogs_list:
            cogs_states[name] = settings.get("cogs", {}).get(name, "enabled") != "disabled"

    return templates.TemplateResponse(
        "guild.html",
        {
            "request": request,
            "user": user,
            "guild": guild,
            "is_premium": is_premium,
            "settings": settings,
            "channels": channels,
            "cogs_states": cogs_states,
        },
    )


@router.post("/api/guilds/{guild_id}/settings")
async def save_guild_settings_api(
    guild_id: str,
    body: SettingsIn,
    user=Depends(get_current_user),
):
    try:
        guilds = await _ensure_admin_guilds(user)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    guild = next((g for g in guilds if g["id"] == guild_id), None)
    if not guild:
        raise HTTPException(status_code=403, detail="Forbidden")

    is_premium = await db.is_premium(guild_id)
    if not is_premium:
        raise HTTPException(status_code=403, detail="Premium required")

    try:
        color_hex = body.bump_color.lstrip("#")
        color_int = int(color_hex, 16)
    except ValueError:
        color_int = 6514417

    gid = str(guild_id)

    await db.set_guild_setting(gid, "bump_reminder", "notification_embed", {
        "title": body.bump_title,
        "description": body.bump_description,
        "color": color_int,
    })

    if body.welcome_channel_id is not None:
        await db.set_guild_setting(gid, "welcome", "channel_id", body.welcome_channel_id)
    if body.welcome_title is not None or body.welcome_description is not None:
        await db.set_guild_setting(gid, "welcome", "join_embed", {
            "title": body.welcome_title or "",
            "description": body.welcome_description or "",
            "color": color_int,
        })

    if body.goodbye_channel_id is not None:
        await db.set_guild_setting(gid, "goodbye", "channel_id", body.goodbye_channel_id)
    if body.goodbye_title is not None or body.goodbye_description is not None:
        await db.set_guild_setting(gid, "goodbye", "leave_embed", {
            "title": body.goodbye_title or "",
            "description": body.goodbye_description or "",
            "color": color_int,
        })

    if body.level_title is not None or body.level_description is not None:
        await db.set_guild_setting(gid, "levels", "level_up_embed", {
            "title": body.level_title or "",
            "description": body.level_description or "",
            "color": color_int,
        })
    if body.level_message is not None:
        await db.set_guild_setting(gid, "levels", "level_up_message", body.level_message)

    if body.boost_channel_id is not None:
        await db.set_guild_setting(gid, "boost", "channel_id", body.boost_channel_id)
    if body.boost_title is not None or body.boost_description is not None:
        await db.set_guild_setting(gid, "boost", "boost_embed", {
            "title": body.boost_title or "",
            "description": body.boost_description or "",
            "color": color_int,
        })

    if body.cogs is not None:
        for name, enabled in body.cogs.items():
            status = "enabled" if enabled else "disabled"
            await db.set_guild_setting(gid, "cogs", name, status)

    return {"ok": True}
