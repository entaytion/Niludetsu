from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..auth import get_oauth_url, exchange_code, fetch_user, create_token
from ..config import OWNER_ID

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="web/templates")


@router.get("/login")
async def login():
    return RedirectResponse(get_oauth_url())


@router.get("/callback")
async def callback(code: str):
    token_data = await exchange_code(code)
    access_token = token_data["access_token"]
    user = await fetch_user(access_token)

    session_token = create_token(user, access_token)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response
