from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .config import HOST, PORT
from .auth import get_current_user, decode_token
from .routes import auth, dashboard, locale

web_dir = Path(__file__).resolve().parent
os.makedirs(str(web_dir / "static"), exist_ok=True)

app = FastAPI(title="Niludetsu Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(web_dir / "templates"))

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(locale.router)


def get_template_user(request: Request):
    token = request.cookies.get("session")
    if token:
        try:
            return decode_token(token)
        except Exception:
            pass
    return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_template_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/me", response_class=HTMLResponse)
async def my_profile(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("me.html", {"request": request, "user": user})
