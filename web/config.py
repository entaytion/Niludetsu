import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Discord OAuth2
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "niludetsu-web-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Bot owner
OWNER_ID = int(os.getenv("OWNER_ID", "636570363605680139"))

# Server
HOST = os.getenv("WEB_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT") or os.getenv("WEB_PORT") or "8000")
