"""
user-service - Phase 2 (CS 4122 - Distributed Systems)

Owns the "users" data exclusively. Handles registration, login, and
profile lookups - including an /internal endpoint that the other
services call over the network instead of touching users.json directly.
"""
import re

from flask import Flask, request, jsonify, g
from flask_cors import CORS

import config
import storage
from auth import hash_password, verify_password, create_token, login_required

app = Flask(__name__)
CORS(app)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _public(user: dict) -> dict:
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "quartier": user.get("quartier", ""),
        "preferences": user.get("preferences", []),
    }


@app.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    full_name = (body.get("full_name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    quartier = (body.get("quartier") or "").strip()
    preferences = [p.lower() for p in body.get("preferences", [])]

    if len(full_name) < 2:
        return jsonify({"error": "full_name must be at least 2 characters"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400
    if storage.find_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    user = {
        "id": storage.new_id(),
        "full_name": full_name,
        "email": email,
        "password_hash": hash_password(password),
        "quartier": quartier,
        "preferences": preferences,
    }
    storage.create_user(user)
    token = create_token(user["id"], user["full_name"], user["email"])
    return jsonify({"access_token": token, "token_type": "bearer", "user": _public(user)}), 201


@app.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    user = storage.find_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["id"], user["full_name"], user["email"])
    return jsonify({"access_token": token, "token_type": "bearer", "user": _public(user)})


@app.get("/me")
@login_required
def me():
    return jsonify(_public(g.current_user))


# ---------- Internal, service-to-service only ----------
# Not exposed through the API Gateway's public routes. Lets
# recommendation-service pull a user's preferences without ever
# touching users.json itself.
@app.get("/internal/users/<user_id>")
def internal_get_user(user_id):
    user = storage.find_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_public(user))


@app.get("/health")
def health():
    return {"service": "user-service", "status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
