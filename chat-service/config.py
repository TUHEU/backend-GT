"""Configuration - chat-service (Phase 2)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("SECRET_KEY", "yaounde-ensemble-phase2-secret-change-me")
ALGORITHM = "HS256"

ROOMS_FILE = DATA_DIR / "rooms.json"
MESSAGES_FILE = DATA_DIR / "messages.json"

PORT = int(os.getenv("PORT", 5014))

# Longest message a user can send, and how many messages a single
# GET /rooms/<id>/messages call returns at most (oldest-first window,
# same idea as the other services' list endpoints).
MAX_MESSAGE_LENGTH = 2000
MESSAGES_PAGE_SIZE = 200
