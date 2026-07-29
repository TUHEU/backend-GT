"""
Data Access Layer - Phase 1: plain JSON files, no database.

One read/write helper per file, all guarded by a lock so two requests
writing at once can't corrupt the file (the slide's "JSON files are not
designed for concurrent access" problem, mitigated but not solved -
solving it properly is what a real database gives you in a later phase).
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


# ---------- Users ----------
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


# ---------- Destinations ----------
def get_destinations():
    return _read(config.DESTINATIONS_FILE)


def find_destination(dest_id: str):
    return next((d for d in get_destinations() if d["id"] == dest_id), None)


def increment_popularity(dest_id: str):
    with _lock:
        dests = get_destinations()
        for d in dests:
            if d["id"] == dest_id:
                d["popularity"] = d.get("popularity", 0) + 1
        _write(config.DESTINATIONS_FILE, dests)


# ---------- Itineraries (called "Sorties" in this app) ----------
def get_itineraries():
    return _read(config.ITINERARIES_FILE)


def get_itineraries_for_user(user_id: str):
    return [
        i for i in get_itineraries()
        if i["owner_id"] == user_id or user_id in i.get("shared_with", [])
    ]


def create_itinerary(it: dict):
    with _lock:
        items = get_itineraries()
        items.append(it)
        _write(config.ITINERARIES_FILE, items)
    return it


def update_itinerary(it_id: str, patch: dict):
    with _lock:
        items = get_itineraries()
        for it in items:
            if it["id"] == it_id:
                it.update(patch)
                _write(config.ITINERARIES_FILE, items)
                return it
    return None


def delete_itinerary(it_id: str) -> bool:
    with _lock:
        items = get_itineraries()
        new_items = [i for i in items if i["id"] != it_id]
        if len(new_items) == len(items):
            return False
        _write(config.ITINERARIES_FILE, new_items)
        return True
