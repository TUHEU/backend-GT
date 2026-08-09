"""
recommendation-service - Phase 2 (CS 4122 - Distributed Systems)

Owns the "destinations" data (the slide's Destinations DB) and computes
personalized recommendations by calling OUT to user-service (for
preferences) and itinerary-service (for past sorties) over REST - this
is the "Recommendation Service reads data from User and Itinerary
services" bullet from the slide, made real.
"""
from datetime import datetime, timezone

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import requests

import config
import storage
from auth import login_required

app = Flask(__name__)
CORS(app)

CATEGORIES = [
    "marche", "sport", "culture", "parc", "restaurant", "bibliotheque",
    "salle-de-fete", "artisanat",
]

REQUEST_TIMEOUT = 3  # seconds - a slow/dead peer shouldn't hang this service forever


@app.get("/categories")
def categories():
    return jsonify({"results": CATEGORIES})


@app.get("/destinations")
def search_destinations():
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    quartier = request.args.get("quartier", "").strip().lower()
    limit = min(max(int(request.args.get("limit", 50)), 1), 100)

    dests = storage.get_destinations()
    if q:
        dests = [
            d for d in dests
            if q in d["name"].lower()
            or q in d.get("quartier", "").lower()
            or q in d.get("description", "").lower()
            or any(q in t for t in d.get("tags", []))
        ]
    if tag:
        dests = [d for d in dests if tag in d.get("tags", [])]
    if category:
        dests = [d for d in dests if d.get("category") == category]
    if quartier:
        dests = [d for d in dests if quartier in d.get("quartier", "").lower()]

    dests = sorted(dests, key=lambda d: d.get("popularity", 0), reverse=True)[:limit]
    dests = [{**d, **storage.rating_summary(d["id"])} for d in dests]
    return jsonify({"count": len(dests), "results": dests})


@app.get("/destinations/<dest_id>")
def get_destination(dest_id):
    d = storage.find_destination(dest_id)
    if not d:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify({**d, **storage.rating_summary(dest_id)})


@app.get("/destinations/<dest_id>/reviews")
def list_reviews(dest_id):
    if not storage.find_destination(dest_id):
        return jsonify({"error": "Destination not found"}), 404
    reviews = sorted(storage.get_reviews_for_destination(dest_id),
                      key=lambda r: r["created_at"], reverse=True)
    return jsonify({"count": len(reviews), "results": reviews,
                     **storage.rating_summary(dest_id)})


@app.post("/destinations/<dest_id>/reviews")
@login_required
def create_review(dest_id):
    if not storage.find_destination(dest_id):
        return jsonify({"error": "Destination not found"}), 404

    body = request.get_json(silent=True) or {}
    try:
        rating = int(body.get("rating"))
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be an integer from 1 to 5"}), 400
    if rating < 1 or rating > 5:
        return jsonify({"error": "rating must be an integer from 1 to 5"}), 400

    comment = (body.get("comment") or "").strip()[:500]

    review = {
        "id": storage.new_id(),
        "destination_id": dest_id,
        "user_id": g.user_id,
        "user_name": g.full_name or "Anonyme",
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    storage.add_review(review)
    return jsonify(review), 201


@app.get("/recommendations")
@login_required
def recommendations():
    limit = min(max(int(request.args.get("limit", 10)), 1), 50)
    user_id = g.user_id

    # Cross-service call #1: preferences live in user-service, not here.
    prefs = set()
    try:
        r = requests.get(f"{config.USER_SERVICE_URL}/internal/users/{user_id}",
                          timeout=REQUEST_TIMEOUT)
        if r.ok:
            prefs = set(r.json().get("preferences", []))
    except requests.RequestException:
        pass  # user-service unreachable - degrade gracefully, still return popularity-based picks

    # Cross-service call #2: past sorties live in itinerary-service, not here.
    visited_ids, trip_tags = set(), set()
    try:
        r = requests.get(f"{config.ITINERARY_SERVICE_URL}/internal/itineraries/user/{user_id}",
                          timeout=REQUEST_TIMEOUT)
        if r.ok:
            for it in r.json().get("results", []):
                for stop in it.get("stops", []):
                    visited_ids.add(stop["destination_id"])
    except requests.RequestException:
        pass  # itinerary-service unreachable - same graceful degradation

    for dest_id in visited_ids:
        d = storage.find_destination(dest_id)
        if d:
            trip_tags.update(d.get("tags", []))

    all_dests = storage.get_destinations()
    max_pop = max((d.get("popularity", 0) for d in all_dests), default=1) or 1

    scored = []
    for d in all_dests:
        if d["id"] in visited_ids:
            continue
        tags = set(d.get("tags", []))
        score = (
            3.0 * len(tags & prefs)
            + 1.5 * len(tags & trip_tags)
            + 1.0 * d.get("popularity", 0) / max_pop
        )
        reasons = []
        if tags & prefs:
            reasons.append("Correspond a tes centres d'interet : " + ", ".join(sorted(tags & prefs)))
        if tags & trip_tags:
            reasons.append("Similaire a tes sorties precedentes")
        if d.get("popularity", 0) >= 0.6 * max_pop:
            reasons.append("Populaire dans le quartier")
        scored.append({**d, "score": round(score, 2), "reasons": reasons or ["A decouvrir"]})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"count": len(scored[:limit]), "results": scored[:limit]})


# ---------- Internal, service-to-service only ----------
# itinerary-service calls these when creating a sortie: confirm the
# destination_id is real, then bump its popularity counter.
@app.get("/internal/destinations/<dest_id>")
def internal_get_destination(dest_id):
    d = storage.find_destination(dest_id)
    if not d:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify(d)


@app.post("/internal/destinations/<dest_id>/popularity")
def internal_bump_popularity(dest_id):
    ok = storage.increment_popularity(dest_id)
    if not ok:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify({"ok": True})


@app.get("/health")
def health():
    return {"service": "recommendation-service", "status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
