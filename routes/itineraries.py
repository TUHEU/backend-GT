"""POST /itineraries, GET /itineraries, GET/PUT/DELETE /itineraries/<id>

Called "sorties" (outings) in the UI - a group of friends/neighbors
planning to go somewhere together, which is the community framing of
what the course calls an "itinerary".
"""
from flask import Blueprint, request, jsonify, g

import storage
from auth import login_required

itineraries_bp = Blueprint("itineraries", __name__)


@itineraries_bp.post("/itineraries")
@login_required
def create_itinerary():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if len(title) < 2:
        return jsonify({"error": "title must be at least 2 characters"}), 400

    stops = body.get("stops", [])
    for stop in stops:
        if not storage.find_destination(stop.get("destination_id", "")):
            return jsonify({"error": f"Unknown destination: {stop.get('destination_id')}"}), 400

    it = {
        "id": storage.new_id(),
        "owner_id": g.current_user["id"],
        "owner_name": g.current_user["full_name"],
        "title": title,
        "description": body.get("description"),
        "date": body.get("date"),
        "stops": stops,
        "shared_with": body.get("shared_with", []),
    }
    storage.create_itinerary(it)
    for s in stops:
        storage.increment_popularity(s["destination_id"])
    return jsonify(it), 201


@itineraries_bp.get("/itineraries")
@login_required
def my_itineraries():
    items = storage.get_itineraries_for_user(g.current_user["id"])
    return jsonify({"count": len(items), "results": items})


@itineraries_bp.get("/itineraries/<it_id>")
@login_required
def get_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    uid, email = g.current_user["id"], g.current_user["email"]
    if it["owner_id"] != uid and uid not in it.get("shared_with", []) and email not in it.get("shared_with", []):
        return jsonify({"error": "Not allowed to view this sortie"}), 403
    return jsonify(it)


@itineraries_bp.put("/itineraries/<it_id>")
@login_required
def update_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    if it["owner_id"] != g.current_user["id"]:
        return jsonify({"error": "Only the owner can edit this sortie"}), 403

    body = request.get_json(silent=True) or {}
    patch = {k: v for k, v in body.items() if k in
             ("title", "description", "date", "stops", "shared_with") and v is not None}
    updated = storage.update_itinerary(it_id, patch)
    return jsonify(updated)


@itineraries_bp.delete("/itineraries/<it_id>")
@login_required
def delete_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    if it["owner_id"] != g.current_user["id"]:
        return jsonify({"error": "Only the owner can delete this sortie"}), 403
    storage.delete_itinerary(it_id)
    return "", 204
