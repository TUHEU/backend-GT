"""
itinerary-service - Phase 2 (CS 4122 - Distributed Systems)

Owns the "sorties" (itineraries) data exclusively. Used to reach directly
into destinations.json to validate a stop and bump its popularity -
now it makes REST calls to recommendation-service instead, since that
service owns the Destinations DB.
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import requests

import config
import storage
from auth import login_required

app = Flask(__name__)
CORS(app)

REQUEST_TIMEOUT = 3


@app.post("/itineraries")
@login_required
def create_itinerary():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if len(title) < 2:
        return jsonify({"error": "title must be at least 2 characters"}), 400

    stops = body.get("stops", [])

    # Cross-service call: destinations live in recommendation-service now.
    for stop in stops:
        dest_id = stop.get("destination_id", "")
        try:
            r = requests.get(
                f"{config.RECOMMENDATION_SERVICE_URL}/internal/destinations/{dest_id}",
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException:
            return jsonify({"error": "recommendation-service unavailable, "
                                      "cannot validate destinations right now"}), 503
        if r.status_code == 404:
            return jsonify({"error": f"Unknown destination: {dest_id}"}), 400

    it = {
        "id": storage.new_id(),
        "owner_id": g.user_id,
        "owner_name": g.full_name,
        "title": title,
        "description": body.get("description"),
        "date": body.get("date"),
        "stops": stops,
        "shared_with": body.get("shared_with", []),
    }
    storage.create_itinerary(it)

    # Fire-and-forget-ish popularity bump: don't fail the whole request
    # if this particular call has trouble, the sortie itself is valid.
    for s in stops:
        try:
            requests.post(
                f"{config.RECOMMENDATION_SERVICE_URL}/internal/destinations/"
                f"{s['destination_id']}/popularity",
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException:
            pass

    return jsonify(it), 201


@app.get("/itineraries")
@login_required
def my_itineraries():
    items = storage.get_itineraries_for_user(g.user_id)
    return jsonify({"count": len(items), "results": items})


@app.get("/itineraries/<it_id>")
@login_required
def get_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    uid, email = g.user_id, g.email
    if it["owner_id"] != uid and uid not in it.get("shared_with", []) and email not in it.get("shared_with", []):
        return jsonify({"error": "Not allowed to view this sortie"}), 403
    return jsonify(it)


@app.put("/itineraries/<it_id>")
@login_required
def update_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    if it["owner_id"] != g.user_id:
        return jsonify({"error": "Only the owner can edit this sortie"}), 403

    body = request.get_json(silent=True) or {}
    patch = {k: v for k, v in body.items() if k in
             ("title", "description", "date", "stops", "shared_with") and v is not None}
    updated = storage.update_itinerary(it_id, patch)
    return jsonify(updated)


@app.delete("/itineraries/<it_id>")
@login_required
def delete_itinerary(it_id):
    it = next((i for i in storage.get_itineraries() if i["id"] == it_id), None)
    if not it:
        return jsonify({"error": "Sortie not found"}), 404
    if it["owner_id"] != g.user_id:
        return jsonify({"error": "Only the owner can delete this sortie"}), 403
    storage.delete_itinerary(it_id)
    return "", 204


# ---------- Internal, service-to-service only ----------
# recommendation-service calls this to see a user's past sorties when
# scoring recommendations for them.
@app.get("/internal/itineraries/user/<user_id>")
def internal_user_itineraries(user_id):
    items = storage.get_itineraries_for_user(user_id)
    return jsonify({"count": len(items), "results": items})


@app.get("/health")
def health():
    return {"service": "itinerary-service", "status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
