"""Launch:  cd Niludetsu && uv run --project web web/run.py"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir=str(Path(__file__).resolve().parent),
    )
