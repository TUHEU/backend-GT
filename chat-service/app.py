"""
chat-service - Phase 2 (CS 4122 - Distributed Systems)

Owns the "chat" data exclusively (rooms + messages), same one-service-
one-database rule as every other service here. Real-time-ish rather
than truly real-time: the API is plain REST, polled by the frontend
every few seconds with ?since=<timestamp> - not a WebSocket/socket.io
server. That's a deliberate fit for this stack, not a shortcut: the
api-gateway is a synchronous `requests`-based HTTP proxy (see its
_proxy() in app.py), which cannot forward a WebSocket upgrade, and
adding one would mean either bypassing the gateway for chat alone or
rebuilding it around an async server. Short-interval polling keeps
chat behind the same single entry point as every other route, with no
change to api-gateway's request/response model.
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS

import config
import storage
from auth import login_required

app = Flask(__name__)
CORS(app)


def _public_room(room: dict) -> dict:
    return {
        "id": room["id"],
        "name": room["name"],
        "description": room.get("description", ""),
        "created_by_name": room.get("created_by_name"),
        "created_at": room.get("created_at"),
    }


@app.get("/rooms")
@login_required
def list_rooms():
    rooms = [_public_room(r) for r in storage.get_rooms()]
    return jsonify({"count": len(rooms), "results": rooms})


@app.post("/rooms")
@login_required
def create_room():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if len(name) < 2:
        return jsonify({"error": "name must be at least 2 characters"}), 400
    if len(name) > 60:
        return jsonify({"error": "name must be 60 characters or fewer"}), 400

    room = {
        "id": storage.new_id(),
        "name": name,
        "description": (body.get("description") or "").strip()[:200],
        "created_by": g.user_id,
        "created_by_name": g.full_name,
        "created_at": storage.now_iso(),
    }
    storage.create_room(room)
    return jsonify(_public_room(room)), 201


@app.get("/rooms/<room_id>")
@login_required
def get_room(room_id):
    room = storage.find_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    return jsonify(_public_room(room))


@app.get("/rooms/<room_id>/messages")
@login_required
def list_messages(room_id):
    room = storage.find_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    since = request.args.get("since")
    msgs = storage.get_messages(room_id, since=since, limit=config.MESSAGES_PAGE_SIZE)
    return jsonify({"count": len(msgs), "results": msgs})


@app.post("/rooms/<room_id>/messages")
@login_required
def send_message(room_id):
    room = storage.find_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content cannot be empty"}), 400
    if len(content) > config.MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"content must be {config.MAX_MESSAGE_LENGTH} characters or fewer"}), 400

    msg = {
        "id": storage.new_id(),
        "room_id": room_id,
        "user_id": g.user_id,
        "user_name": g.full_name,
        "content": content,
        "created_at": storage.now_iso(),
    }
    storage.create_message(msg)
    return jsonify(msg), 201


@app.get("/health")
def health():
    return {"service": "chat-service", "status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
