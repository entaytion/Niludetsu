import time
import httpx
import jwt
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from .config import (
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRY_HOURS,
)

DISCORD_API = "https://discord.com/api/v10"
OAUTH_SCOPE = "identify guilds"

# ─── Discord OAuth2 URLs ────────────────────────────────────────────


def get_oauth_url() -> str:
    params = urlencode(
        {
            "client_id": DISCORD_CLIENT_ID,
            "redirect_uri": DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": OAUTH_SCOPE,
        }
    )
    return f"{DISCORD_API}/oauth2/authorize?{params}"


# ─── Token exchange ─────────────────────────────────────────────────


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


# ─── Fetch Discord resources ────────────────────────────────────────


async def fetch_user(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_user_guilds(token: str) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


# ─── JWT helpers ─────────────────────────────────────────────────────


def create_token(user: dict, access_token: str = None) -> str:
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar"),
        "discriminator": user.get("discriminator", "0"),
        "global_name": user.get("global_name"),
        "access_token": access_token,
        "exp": int(time.time()) + JWT_EXPIRY_HOURS * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── Dependency ──────────────────────────────────────────────────────


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_token(token)
