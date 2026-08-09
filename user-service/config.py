"""Configuration - user-service (Phase 2)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("SECRET_KEY", "yaounde-ensemble-phase2-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

USERS_FILE = DATA_DIR / "users.json"

PORT = int(os.getenv("PORT", 5011))
