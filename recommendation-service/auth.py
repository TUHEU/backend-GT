"""JWT verification only - recommendation-service never issues tokens,
only user-service does. Same SECRET_KEY, verified independently."""
from functools import wraps

import jwt
from flask import request, jsonify, g

import config


def login_required(f):
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
        g.user_id = payload.get("sub")
        g.full_name = payload.get("full_name")
        g.email = payload.get("email")
        g.token_claims = payload
        return f(*args, **kwargs)
    return wrapper
