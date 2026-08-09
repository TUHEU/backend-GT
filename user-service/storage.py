"""Data Access Layer - user-service. Owns users.json exclusively.

No other service is allowed to read or write this file directly - that
is the whole point of service decomposition. Anyone else who needs user
data calls GET /internal/users/<id> over HTTP instead.
"""
import json
import threading
import uuid
from pathlib import Path

import config

_lock = threading.Lock()


def _read(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write(path: Path, data):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def get_users():
    return _read(config.USERS_FILE)


def find_user_by_email(email: str):
    email = email.lower().strip()
    return next((u for u in get_users() if u["email"] == email), None)


def find_user_by_id(user_id: str):
    return next((u for u in get_users() if u["id"] == user_id), None)


def create_user(user: dict):
    with _lock:
        users = get_users()
        users.append(user)
        _write(config.USERS_FILE, users)
    return user
