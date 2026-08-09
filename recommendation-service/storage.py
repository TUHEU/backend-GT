"""Data Access Layer - recommendation-service. Owns destinations.json
exclusively (the slide's "Destinations DB")."""
import json
import threading
import uuid
from pathlib import Path

import config

_lock = threading.Lock()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


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


def get_destinations():
    return _read(config.DESTINATIONS_FILE)


def find_destination(dest_id: str):
    return next((d for d in get_destinations() if d["id"] == dest_id), None)


def increment_popularity(dest_id: str):
    with _lock:
        dests = get_destinations()
        found = False
        for d in dests:
            if d["id"] == dest_id:
                d["popularity"] = d.get("popularity", 0) + 1
                found = True
        if found:
            _write(config.DESTINATIONS_FILE, dests)
        return found


# ---------- Reviews ----------
def get_reviews_for_destination(dest_id: str):
    return [r for r in _read(config.REVIEWS_FILE) if r["destination_id"] == dest_id]


def add_review(review: dict):
    with _lock:
        reviews = _read(config.REVIEWS_FILE)
        reviews.append(review)
        _write(config.REVIEWS_FILE, reviews)
    return review


def rating_summary(dest_id: str):
    ratings = [r["rating"] for r in get_reviews_for_destination(dest_id)]
    if not ratings:
        return {"avg_rating": None, "review_count": 0}
    return {"avg_rating": round(sum(ratings) / len(ratings), 1), "review_count": len(ratings)}
