# Yaoundé Ensemble — Backend (Phase 2, Microservices)
CS 4122 · Distributed Systems · The ICT University

This is the **backend repo only** (`backend-GT` on the VPS) — separate
from the `frontend` repo. Phase 1's single Flask process is now 5
independent services behind an API gateway. **This is a live
deployment update, not a from-scratch rebuild** — see `DEPLOY_VPS.md`
for exactly what's running on the actual VPS right now and how to
redeploy it.

## Architecture

```
                    ┌──────────────┐      ┌──────────────┐
   Frontend ──────► │ api-gateway  │─────►│ user-service │───► users.json
  (separate         │   :5003      │      │    :5011     │
   deployment)      │  (unchanged  │      └──────────────┘
                     │   port from  │      ┌──────────────────┐
                     │   Phase 1)   │─────►│ itinerary-service │──► itineraries.json
                     │              │      │      :5012        │
                     │              │      └────────┬───────────┘
                     │              │               │ validates/bumps
                     │              │               ▼ destinations
                     │              │      ┌──────────────────────┐
                     │              │─────►│ recommendation-service │──► destinations.json
                     └──────────────┘      │        :5013           │──► reviews.json
                                            └───────────┬─────────────┘
                                                         │ pulls preferences
                                                         │ + past sorties
                                            (calls user-service and
                                             itinerary-service back)

                    api-gateway ──────────► chat-service :5014 ──► rooms.json
                                                                 ──► messages.json
```

- **user-service** — owns `users.json`. `/register`, `/login`, `/me`.
- **itinerary-service** — owns `itineraries.json` (called "sorties" in
  the UI). Full CRUD. On create, it calls recommendation-service to
  confirm each `destination_id` is real and to bump its popularity.
- **recommendation-service** — owns `destinations.json` and
  `reviews.json`. `/categories`, `/destinations`, `/recommendations`,
  `/destinations/<id>/reviews`. Scoring pulls a user's preferences from
  user-service and past sorties from itinerary-service — both over the
  network, not shared code.
- **chat-service** — owns `rooms.json` and `messages.json`.
  `GET/POST /rooms`, `GET /rooms/<id>`, `GET/POST /rooms/<id>/messages`.
  No WebSocket — the frontend polls `GET .../messages?since=<ts>` every
  few seconds, since api-gateway's `_proxy()` is a synchronous
  `requests` call and can't forward a socket upgrade anyway.
- **api-gateway** — the only address the frontend ever talks to.
  Stayed on **port 5003**, the same port Phase 1's single process used
  — so the live frontend's `js/config.js` and the VPS's `ufw` rule both
  needed zero changes for this upgrade. Pure API now, no static files.

Auth is **decentralized**: only user-service issues JWTs (on
register/login), but every service verifies them independently off the
same `SECRET_KEY` — no service has to call user-service just to
authenticate an incoming request.

## Why the ports look like this
`user-service`/`itinerary-service`/`recommendation-service` are on
5011/5012/5013, not the more obvious 5001/5002/5003 — because
5000/5001/5002 were already taken by other students' apps on the
shared VPS (this was true back in Phase 1 too, which is why the
original single backend ended up on 5003 instead of 5000). Since
`api-gateway` needed to keep 5003 for continuity with the live
frontend, the three internal services moved to the next free block.
`chat-service` took the next free port after that, **5014**. All four
internal services are bound to `127.0.0.1` only — never reachable from
outside the VPS, only from api-gateway and each other.

## Running it locally (for development, not the VPS)

```bash
docker compose up --build
```
Then:
```bash
curl http://localhost:5003/health
```
Point a locally-served frontend's `js/config.js` `BASE_URL` at
`http://localhost:5003`.

**Without Docker**, run each service in its own terminal (set
`PORT`/`*_SERVICE_URL` env vars per service, see each `config.py`):
```bash
cd user-service && pip install -r requirements.txt --break-system-packages && python app.py
cd itinerary-service && pip install -r requirements.txt --break-system-packages && python app.py
cd recommendation-service && pip install -r requirements.txt --break-system-packages && python app.py
cd chat-service && pip install -r requirements.txt --break-system-packages && python app.py
cd api-gateway && pip install -r requirements.txt --break-system-packages && python app.py
```

## Deploying / redeploying to the actual VPS
See `DEPLOY_VPS.md` — it documents the real PM2 + gunicorn setup this
project runs on (`ecosystem.config.js`), not just a generic Docker
option. Docker Compose above is for local development; the VPS itself
uses PM2, matching the convention already established there for
Phase 1 and ~10 other student projects sharing that box.

## What changed vs. Phase 1, concretely
- `destinations.py`'s search/lookup logic moved into
  recommendation-service unchanged — it was never anyone else's data.
- `itineraries.py` lost its direct `storage.find_destination()` calls;
  those became two REST calls to recommendation-service
  (`GET /internal/destinations/<id>` and
  `POST /internal/destinations/<id>/popularity`).
- `recommendations.py` lost its direct access to `g.current_user` and
  `storage.get_itineraries_for_user()`; those became REST calls to
  user-service and itinerary-service respectively, with a graceful
  fallback to popularity-only scoring if a peer is unreachable.
- New this round: **ratings & reviews** — `reviews.json` +
  `GET/POST /destinations/<id>/reviews`, owned by
  recommendation-service; every destination response now also carries
  `avg_rating` and `review_count`.
- New this round: every seed destination now carries `lat`/`lng` for
  the frontend's map view.
- api-gateway didn't exist before Phase 2 — it's the only thing the
  frontend talks to now, and (as of this round) it no longer serves any
  HTML/CSS/JS itself either — that's 100% the frontend repo's job.
- New this round: **chat-service** — a 5th service, `rooms.json` +
  `messages.json`, same decentralized-JWT verification as every other
  service. `api-gateway`'s `ROUTES` table and `/health` aggregator both
  updated to include it.

## Known Phase-2-appropriate limitations
Per the course's own "Challenges of Microservices" slide: no
distributed tracing, no message queue (all inter-service calls are
synchronous REST), no service registry (URLs are hardcoded via env
vars / PM2 env / Compose service names), and each service still writes
to a local JSON file rather than a real per-service database. Those are
natural next steps for Phase 3/4, not oversights here.
