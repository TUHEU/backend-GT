"""GET /categories, GET /destinations, GET /destinations/<id>

Called "destinations" to match the course's required endpoint name, but
in this app's own language these are "lieux" (places) - community spots,
not tourist attractions.
"""
from flask import Blueprint, request, jsonify

import storage

destinations_bp = Blueprint("destinations", __name__)

CATEGORIES = [
    "marche", "sport", "culture", "parc", "restaurant", "bibliotheque",
    "salle-de-fete", "artisanat",
]


@destinations_bp.get("/categories")
def categories():
    return jsonify({"results": CATEGORIES})


@destinations_bp.get("/destinations")
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
    return jsonify({"count": len(dests), "results": dests})


@destinations_bp.get("/destinations/<dest_id>")
def get_destination(dest_id):
    d = storage.find_destination(dest_id)
    if not d:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify(d)
