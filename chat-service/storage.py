"""Data Access Layer - chat-service. Owns rooms.json and messages.json
exclusively, same JSON-file-plus-lock pattern as the other services
(itinerary-service, recommendation-service) - keeps the whole Phase 2
stack dependency-free (no DB server to stand up for a course project).
"""
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import config

# One lock guards both files - message volume is low enough (a course
# chat, not a production app) that a single global lock is simpler
# than per-file locks and never becomes a real bottleneck.
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_default_room():
    """Seeds a "Général" room on first run so the room list is never
    empty for a brand-new deployment - mirrors how recommendation-
    service ships with seeded destinations.json."""
    rooms = _read(config.ROOMS_FILE)
    if rooms:
        return
    rooms = [{
        "id": "general",
        "name": "Général",
        "description": "Le salon principal - discute avec toute la communauté.",
        "created_by": None,
        "created_by_name": "Yaoundé Ensemble",
        "created_at": now_iso(),
    }]
    _write(config.ROOMS_FILE, rooms)


_ensure_default_room()


# ---------- Rooms ----------

def get_rooms():
    return _read(config.ROOMS_FILE)


def find_room_by_id(room_id: str):
    return next((r for r in get_rooms() if r["id"] == room_id), None)


def create_room(room: dict):
    with _lock:
        rooms = get_rooms()
        rooms.append(room)
        _write(config.ROOMS_FILE, rooms)
    return room


# ---------- Messages ----------

def get_messages(room_id: str, since: str = None, limit: int = None):
    msgs = [m for m in _read(config.MESSAGES_FILE) if m["room_id"] == room_id]
    msgs.sort(key=lambda m: m["created_at"])
    if since:
        msgs = [m for m in msgs if m["created_at"] > since]
    if limit and not since:
        msgs = msgs[-limit:]
    return msgs


def create_message(msg: dict):
    with _lock:
        msgs = _read(config.MESSAGES_FILE)
        msgs.append(msg)
        _write(config.MESSAGES_FILE, msgs)
    return msg
