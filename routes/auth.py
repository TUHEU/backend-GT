"""POST /register, POST /login, GET /me"""
import re
from flask import Blueprint, request, jsonify, g

import storage
from auth import hash_password, verify_password, create_token, login_required

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _public(user: dict) -> dict:
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "quartier": user.get("quartier", ""),
        "preferences": user.get("preferences", []),
    }


@auth_bp.post("/register")
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


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    user = storage.find_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["id"], user["full_name"], user["email"])
    return jsonify({"access_token": token, "token_type": "bearer", "user": _public(user)})


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(_public(g.current_user))
