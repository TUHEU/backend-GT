# Yaoundé Ensemble — actual VPS deployment (as of now)

This documents what's genuinely live, not a hypothetical plan.

VPS: Contabo, `root@38.242.246.126`, Ubuntu 24.04, no domain name.
Shared with several other students' projects (checked via `ss -tulpn`
before picking ports, to avoid collisions).

## Architecture

```
Browser
  │
  ├──► http://38.242.246.126:8081  (Nginx, static files)
  │      serves /var/www/frontend  (separate git repo: frontend)
  │      index.html, explore.html, login.html, register.html,
  │      itineraries.html, css/, js/
  │
  └──► http://38.242.246.126:5003  (Gunicorn, via PM2)
         /root/backend-GT           (separate git repo: backend-GT)
         Flask app, JSON storage in data/, JWT auth
```

Frontend and backend are two **separate git repos**, deployed as two
separate services, on two separate ports. `frontend/js/config.js` is
what bridges them — it hardcodes `BASE_URL: "http://38.242.246.126:5003"`
so every `fetch()` call from the :8081 pages reaches the :5003 API.
CORS is open on the Flask side (`flask-cors`) to allow this.

## Backend — `/root/backend-GT`

- Python venv + `gunicorn`, managed by **PM2** (not systemd - this VPS
  already runs ~10 other apps via PM2, so it matches convention here)
- PM2 process name: `backend-gt`, config in `ecosystem.config.js`
- Bound to `0.0.0.0:5003` (no Nginx in front of the API - direct)
- `ufw allow 5003/tcp` opened
- `pm2 save` run, so it survives a VPS reboot
- `update.sh` / `restore.sh` live directly on the VPS in
  `/root/backend-GT` (not bundled in this zip - see chat history for
  their contents if you need to recreate them elsewhere)
  - `update.sh`: backs up `data/` first, `git pull`, reinstalls deps,
    `pm2 restart`, health-checks `/health` before declaring success
  - `restore.sh`: lists backups, or `./restore.sh <file>` to roll back

## Frontend — `/var/www/frontend`

- Pure static files, served directly by **Nginx** (config at
  `/etc/nginx/sites-available/yaounde-ensemble`, port `8081`)
- `ufw allow 8081/tcp` opened
- No process to manage - Nginx just reads files off disk
- `update.sh` lives directly on the VPS in `/var/www/frontend` (same
  note as above - not bundled here)

## No domain, no HTTPS (for now)

Both ports serve plain `http://`. Let's Encrypt needs a domain name to
issue a certificate against - can't do it for a bare IP. Fine for a
course project; revisit if a real domain gets added later (at that
point: point DNS at the VPS, add an Nginx server block per domain,
`certbot --nginx -d yourdomain`, and switch the backend's PM2 bind back
to `127.0.0.1:5003` so Nginx becomes the only public door to it - same
pattern already used for GlobeTrotter's Phase 1/2 deployments).

## Known gotcha: config.js vs. update.sh

`frontend/js/config.js`'s `BASE_URL` is hardcoded to the VPS IP in this
repo now - correct for production. If you ever run this project
**locally** through a single `python app.py` process instead (see
README.md), you'd need to blank `BASE_URL` back to `""` locally, but
NOT commit that change - keep the VPS-pointed version in git, since
that's what `frontend/update.sh`'s `git pull` will always restore on
the server regardless of local edits.

## Redeploying after a code change (either repo)

The `update.sh` scripts live on the VPS itself in each repo's folder
(`/root/backend-GT/update.sh` and `/var/www/frontend/update.sh`) —
not in this zip. On the VPS:

```bash
# backend
cd /root/backend-GT && ./update.sh

# frontend
cd /var/www/frontend && ./update.sh
```
