from __future__ import annotations

import importlib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..auth import get_current_user, fetch_user_guilds
from ..database import db
from ..bot import get_bot

router = APIRouter(tags=["locale"])
templates = Jinja2Templates(directory="web/templates")

_DEFAULT_LOCALE: dict[str, dict[str, str]] = {}


def _load_default_locale() -> dict[str, dict[str, str]]:
    global _DEFAULT_LOCALE
    if _DEFAULT_LOCALE:
        return _DEFAULT_LOCALE
    try:
        mod = importlib.import_module("Niludetsu.locale")
        raw = getattr(mod, "DEFAULT_LOCALE", {})
        norm: dict[str, dict[str, str]] = {}
        for cat, phrases in raw.items():
            if isinstance(phrases, dict):
                norm[str(cat)] = {str(k): str(v) for k, v in phrases.items()}
            elif isinstance(phrases, str):
                norm.setdefault("_misc", {})[str(cat)] = phrases
        _DEFAULT_LOCALE = norm
    except Exception:
        _DEFAULT_LOCALE = {}
    return _DEFAULT_LOCALE


async def _get_guild_translations(guild_id: str) -> dict[str, str]:
    try:
        bot = get_bot()
        rows = await bot.db._neon.fetch(
            "SELECT key, value FROM public.custom_messages "
            "WHERE guild_id = $1 AND module = 'locale'",
            str(guild_id),
        )
        return {r["key"]: r["value"] if isinstance(r["value"], str) else str(r["value"]) for r in rows}
    except Exception:
        return {}


async def _save_guild_translations(guild_id: str, translations: dict[str, str]) -> None:
    bot = get_bot()
    if not bot:
        return
    for key, value in translations.items():
        if value is None:
            continue
        await bot.db._neon.execute(
            "INSERT INTO public.custom_messages (guild_id, module, key, value, updated_at) "
            "VALUES ($1, 'locale', $2, $3, now()) "
            "ON CONFLICT (guild_id, module, key) DO UPDATE SET value = $3, updated_at = now()",
            str(guild_id), key, value,
        )


class LocaleIn(BaseModel):
    translations: dict[str, str | None]


@router.get("/dashboard/guild/{guild_id}/locale", response_class=HTMLResponse)
async def locale_page(
    guild_id: str, request: Request, user=Depends(get_current_user)
):
    try:
        guilds = await fetch_user_guilds(user["access_token"])
    except Exception:
        return RedirectResponse(url="/auth/logout", status_code=303)

    guild = next((g for g in guilds if g["id"] == guild_id), None)
    if not guild:
        raise HTTPException(status_code=403, detail="Forbidden")

    perms = int(guild.get("permissions", "0"))
    if not ((perms & 0x8) or guild.get("owner", False)):
        raise HTTPException(status_code=403, detail="Forbidden")

    default_locale = _load_default_locale()
    overrides = await _get_guild_translations(guild_id)

    categories: dict[str, list[dict[str, Any]]] = {}
    for cat, phrases in sorted(default_locale.items()):
        items = []
        for key, default_text in sorted(phrases.items()):
            full_key = f"{cat}.{key}"
            items.append({
                "key": full_key,
                "short_key": key,
                "default": default_text,
                "custom": overrides.get(full_key, ""),
            })
        categories[cat] = items

    known_keys = {
        f"{cat}.{k}" for cat, phrases in default_locale.items() for k in phrases
    }
    orphans = []
    for k, v in sorted(overrides.items()):
        if k not in known_keys:
            orphans.append({"key": k, "short_key": k.split(".")[-1], "default": "", "custom": v})
    if orphans:
        categories["_custom"] = orphans

    is_premium = await db.is_premium(guild_id)

    return templates.TemplateResponse(
        "locale.html",
        {
            "request": request,
            "user": user,
            "guild": guild,
            "is_premium": is_premium,
            "categories": categories,
            "total_phrases": sum(len(v) for v in categories.values()),
        },
    )


@router.post("/api/guilds/{guild_id}/locale")
async def save_locale_api(
    guild_id: str, body: LocaleIn, user=Depends(get_current_user)
):
    try:
        guilds = await fetch_user_guilds(user["access_token"])
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    guild = next((g for g in guilds if g["id"] == guild_id), None)
    if not guild:
        raise HTTPException(status_code=403, detail="Forbidden")

    perms = int(guild.get("permissions", "0"))
    if not ((perms & 0x8) or guild.get("owner", False)):
        raise HTTPException(status_code=403, detail="Forbidden")

    is_premium = await db.is_premium(guild_id)
    if not is_premium:
        raise HTTPException(status_code=403, detail="Premium required")

    to_save = {k: v for k, v in body.translations.items() if v is not None}
    await _save_guild_translations(guild_id, to_save)

    bot = get_bot()
    if bot:
        for k, v in body.translations.items():
            if v is not None and v == "":
                await bot.db._neon.execute(
                    "DELETE FROM public.custom_messages "
                    "WHERE guild_id = $1 AND module = 'locale' AND key = $2",
                    str(guild_id), k,
                )

    cm = getattr(get_bot(), "config_manager", None) if get_bot() else None
    if cm and hasattr(cm, "_invalidate_locale"):
        cm._invalidate_locale(int(guild_id))

    return {"ok": True, "saved": len(to_save)}
