"""
api-gateway - Phase 2 (CS 4122 - Distributed Systems)

The single entry point for every API request (the slide's "API Gateway:
single entry point ... routes requests to the appropriate service").

Pure API gateway - it does NOT serve the frontend. Frontend and backend
are two separate deployable units now (two separate repos): the
frontend is a static site that can go on Netlify/Vercel/GitHub Pages/
Nginx, and this gateway (plus the 3 services behind it) is a Docker
Compose stack that can go on any VPS or container host. They talk to
each other over plain HTTPS - see frontend/js/config.js for where the
frontend is told this gateway's URL.
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests

import config

app = Flask(__name__)
CORS(app)  # allows the separately-hosted frontend's origin to call this API

# path prefix -> upstream service base URL
ROUTES = {
    "register": config.USER_SERVICE_URL,
    "login": config.USER_SERVICE_URL,
    "me": config.USER_SERVICE_URL,
    "categories": config.RECOMMENDATION_SERVICE_URL,
    "destinations": config.RECOMMENDATION_SERVICE_URL,
    "recommendations": config.RECOMMENDATION_SERVICE_URL,
    "itineraries": config.ITINERARY_SERVICE_URL,
}

HOP_BY_HOP = {"content-encoding", "content-length", "transfer-encoding", "connection"}


def _proxy(upstream_base: str, path: str):
    url = f"{upstream_base}/{path}"
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            params=request.args,
            data=request.get_data(),
            timeout=config.REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return jsonify({"error": f"Upstream service unavailable: {upstream_base}"}), 503

    headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP]
    return Response(resp.content, status=resp.status_code, headers=headers)


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def route_request(path):
    top_segment = path.split("/", 1)[0]
    if top_segment in ROUTES:
        return _proxy(ROUTES[top_segment], path)
    return jsonify({"error": f"No such API route: /{path}"}), 404


@app.get("/")
def index():
    return jsonify({
        "service": "api-gateway",
        "message": "This is the Yaounde Ensemble API gateway. "
                    "The frontend is a separate deployment - see its own repo.",
        "routes": sorted(set(ROUTES.keys())),
    })


@app.get("/health")
def health():
    """Aggregate health check - pings every downstream service."""
    results = {"service": "api-gateway", "status": "ok", "downstream": {}}
    for name, base in (
        ("user-service", config.USER_SERVICE_URL),
        ("itinerary-service", config.ITINERARY_SERVICE_URL),
        ("recommendation-service", config.RECOMMENDATION_SERVICE_URL),
    ):
        try:
            r = requests.get(f"{base}/health", timeout=2)
            results["downstream"][name] = "ok" if r.ok else f"http {r.status_code}"
        except requests.RequestException as e:
            results["downstream"][name] = f"unreachable ({e.__class__.__name__})"
            results["status"] = "degraded"
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
