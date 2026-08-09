"""JWT issuing/verification + password hashing - user-service.

user-service is the only place that ISSUES tokens (login/register). Every
service independently VERIFIES them with the same SECRET_KEY - that's
the decentralized-auth pattern: a service never has to call user-service
just to authenticate a request.
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

import config
import storage


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_token(user_id: str, full_name: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "full_name": full_name, "email": email, "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def login_required(f):
    """Decorator: validates the Bearer token and injects g.current_user."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = storage.find_user_by_id(payload.get("sub"))
        if not user:
            return jsonify({"error": "User no longer exists"}), 401
        g.current_user = user
        g.token_claims = payload
        return f(*args, **kwargs)
    return wrapper
