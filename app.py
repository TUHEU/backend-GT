"""
Yaoundé Ensemble - Phase 1 Monolith (CS 4122 - Distributed Systems)

A single Flask process, JSON file storage, JWT auth - exactly the
Phase 1 brief: one API layer, one business-logic layer, one data-access
layer, no database yet. This is a SEPARATE student project from
GlobeTrotter: same course requirements, different concept, different
stack (Flask instead of FastAPI, vanilla HTML/CSS/JS instead of Flutter).

Concept: instead of a tourist-facing travel assistant, this is a
community outings board FOR Yaoundé residents - built by the community,
for the community: local markets, sports grounds, youth centers,
libraries, cultural spaces. Same 5 required endpoints, different heart.

Run: python app.py   (serves API + the static frontend on :5000)
"""
from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.auth import auth_bp
from routes.destinations import destinations_bp
from routes.recommendations import recommendations_bp
from routes.itineraries import itineraries_bp

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(destinations_bp)
app.register_blueprint(recommendations_bp)
app.register_blueprint(itineraries_bp)


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/<path:path>")
def static_pages(path):
    """Lets /explore.html, /login.html etc. resolve directly, and falls
    back to index.html for anything unknown (simple SPA-ish routing)."""
    try:
        return send_from_directory(app.static_folder, path)
    except Exception:
        return app.send_static_file("index.html")


@app.get("/health")
def health():
    return {"service": "yaounde-ensemble-monolith", "status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
