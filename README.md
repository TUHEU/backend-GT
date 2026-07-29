# Yaoundé Ensemble — Phase 1 (Monolith)
CS 4122 · Distributed Systems · The ICT University

A separate Phase 1 capstone project: same course requirements as
GlobeTrotter, different stack and a different concept — a community
outings board for Yaoundé residents (marchés, terrains de sport,
bibliothèques, maisons des jeunes) instead of a tourist travel assistant.

## Stack
- **Backend:** Python + Flask, JSON file storage, JWT auth (PyJWT +
  Werkzeug password hashing) — no database yet, exactly per the Phase 1
  brief.
- **Frontend:** vanilla HTML/CSS/JavaScript (no framework), served
  directly by Flask as static files — one process, one server, per the
  monolith architecture diagram.

## Endpoints implemented
```
POST   /register            create an account
POST   /login                get a JWT
GET    /me                   current user profile
GET    /categories            list of place categories
GET    /destinations           search places (q, tag, category, quartier)
GET    /destinations/<id>       one place
GET    /recommendations         personalized, JWT-protected
POST   /itineraries            create a "sortie" (outing)
GET    /itineraries             your sorties (owned + shared with you)
GET    /itineraries/<id>         one sortie
PUT    /itineraries/<id>         edit (owner only)
DELETE /itineraries/<id>         delete (owner only)
```

## Design
The visual identity is built around Yaoundé's shared yellow taxis and
their hand-painted destination boards — the hero's scrolling "taxi
board" marquee is the signature element. Palette: warm charcoal
background, moto-taxi yellow accent, laterite red (the red clay soil of
the seven hills) as secondary, muted palm green used sparingly. This is
deliberately NOT the same look as GlobeTrotter (dark green/orange/gold) —
a different project should not look like a copy.

## Where to put an IP address

`frontend/js/config.js` is the one place for this — it works exactly like
`baseUrl` in the GlobeTrotter Flutter app's `constants.dart`:

```js
const ApiConfig = {
  BASE_URL: "",   // leave empty when Flask serves the frontend itself
};
```

- **Leave it empty** (the default) whenever you open the site through
  Flask itself — `http://localhost:5000` or `http://<your-LAN-IP>:5000`.
  An empty `BASE_URL` means every request automatically goes back to
  whatever address the page was loaded from, so there's nothing to type.
- **Only fill it in** if the frontend files end up served from somewhere
  different than the Flask backend - e.g. testing the HTML files from a
  different static host while the API stays on your PC or a VPS. Example:
  `BASE_URL: "http://192.168.1.20:5000"` or
  `BASE_URL: "https://tondomaine.duckdns.org"`.

## Running it

```bash
cd backend
pip install -r requirements.txt --break-system-packages
python app.py
```

Then open **http://localhost:5000** — Flask serves both the API and the
frontend pages (`index.html`, `explore.html`, `login.html`,
`register.html`, `itineraries.html`) from the same process, on the same
port, which is exactly what "monolith" means here.

To test from your phone on the same Wi-Fi: find your PC's LAN IP
(`ipconfig` / `ifconfig`), then open `http://<that-ip>:5000` on the
phone. `config.js` can stay empty for this too.

## Data
`backend/data/destinations.json` ships with 20 seed places across 8
categories (marché, sport, culture, parc, restaurant, bibliothèque,
salle-de-fête, artisanat) spread across real Yaoundé quartiers. This is
representative course-project content, not a verified real-time
business directory.

`backend/data/users.json` and `backend/data/itineraries.json` start
empty — they fill up as people register and create sorties.

## What's deliberately not here yet
Per the Phase 1 brief itself: no database (JSON only), no horizontal
scaling, no service decomposition, no automated tests. Those are later
phases.
