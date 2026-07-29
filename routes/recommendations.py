"""GET /recommendations - personalized, based on preferences + past sorties."""
from flask import Blueprint, request, jsonify, g

import storage
from auth import login_required

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.get("/recommendations")
@login_required
def recommendations():
    limit = min(max(int(request.args.get("limit", 10)), 1), 50)
    prefs = set(g.current_user.get("preferences", []))

    visited_ids = set()
    trip_tags = set()
    for it in storage.get_itineraries_for_user(g.current_user["id"]):
        for stop in it.get("stops", []):
            visited_ids.add(stop["destination_id"])
            d = storage.find_destination(stop["destination_id"])
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
