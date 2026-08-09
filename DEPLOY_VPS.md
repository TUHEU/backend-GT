# Yaoundé Ensemble — actual VPS deployment (Phase 2 update)

This documents what's genuinely live, not a hypothetical plan. Updates
the Phase 1 version of this file: the single Flask process is now 4.

VPS: Contabo, `root@38.242.246.126`, Ubuntu 24.04, no domain name.
Shared with several other students' projects (checked via `ss -tulpn`
before picking ports, same discipline as Phase 1).

## Architecture

```
Browser
  │
  ├──► http://38.242.246.126:8081  (Nginx, static files - UNCHANGED)
  │      serves /var/www/frontend  (separate git repo: frontend)
  │      index.html, explore.html, destination.html, login.html,
  │      register.html, itineraries.html, css/, js/
  │
  └──► http://38.242.246.126:5003  (api-gateway, PM2/gunicorn)
         │  same port the Phase 1 monolith used - no firewall/DNS
         │  change needed, frontend/js/config.js didn't need to change
         │
         ├──► 127.0.0.1:5011  user-service          (users.json)
         ├──► 127.0.0.1:5012  itinerary-service      (itineraries.json)
         └──► 127.0.0.1:5013  recommendation-service (destinations.json,
                                                        reviews.json)
```

Frontend and backend are still two **separate git repos**, on two
separate ports, exactly as before. The only thing that changed behind
`:5003` is that it's now 4 processes instead of 1 - the browser and
`frontend/js/config.js` can't tell the difference.

**Only `:5003` (api-gateway) is exposed.** The three services behind it
bind to `127.0.0.1`, not `0.0.0.0` - they're unreachable from outside
the VPS entirely, reachable only by api-gateway and each other over
localhost. No `ufw` rule needed for 5011/5012/5013.

## Backend — `/root/backend-GT`

- Same repo as Phase 1, restructured: now `api-gateway/`,
  `user-service/`, `itinerary-service/`, `recommendation-service/`
  subfolders, each its own Python venv + `gunicorn`.
- All 4 managed by **PM2** via `ecosystem.config.js` (process names
  `yaounde-api-gateway`, `yaounde-user-service`,
  `yaounde-itinerary-service`, `yaounde-recommendation-service`).
- Ports: api-gateway `5003` (public, `ufw allow 5003/tcp` - already
  open from Phase 1, no change needed); the other three on
  `127.0.0.1:5011/5012/5013` (internal only, picked because
  5000/5001/5002 were already taken by other apps on this shared VPS -
  same reasoning that put the Phase 1 backend on 5003 in the first
  place; re-verify with `ss -tulpn` before reusing these blindly on a
  different VPS).
- `pm2 save` run after starting all 4, so they survive a reboot.
- Every process needs the SAME `SECRET_KEY` env var - only
  user-service issues JWTs (on register/login), but all four verify
  them independently, so a mismatch breaks auth everywhere at once.
  Set it once in `ecosystem.config.js`.

### First-time setup (per service)
Each service needs its own venv (they're independent deployable units,
so independent dependency sets - itinerary-service and
recommendation-service need `requests` for their inter-service calls,
user-service doesn't):
```bash
cd /root/backend-GT
for svc in api-gateway user-service itinerary-service recommendation-service; do
  cd $svc
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt
  cd ..
done
pm2 start ecosystem.config.js
pm2 save
```

### Redeploying after a code change
```bash
cd /root/backend-GT
git pull
for svc in api-gateway user-service itinerary-service recommendation-service; do
  ./$svc/venv/bin/pip install -r $svc/requirements.txt
done
pm2 restart ecosystem.config.js
curl http://localhost:5003/health   # confirm all 4 report "ok" before walking away
```
(`update.sh` on the VPS should be updated to run this loop instead of
the old single-service restart - not bundled in this zip, same as
Phase 1's note.)

## Frontend — `/var/www/frontend`

**Unchanged from Phase 1** - pure static files, served directly by
**Nginx** (config at `/etc/nginx/sites-available/yaounde-ensemble`,
port `8081`). No redeploy steps changed; just `git pull` and Nginx
picks up the new files immediately (no process to restart).

New pages this round: `destination.html` (place detail + map +
reviews). Nginx serves it automatically once it lands via `git pull` -
no config change needed, it's just another static file.

## No domain, no HTTPS (for now)

Same as Phase 1 - both ports serve plain `http://`. Revisit once a
domain gets added: point DNS at the VPS, add an Nginx server block per
domain, `certbot --nginx -d yourdomain`, and switch api-gateway's PM2
bind from `0.0.0.0:5003` to `127.0.0.1:5003` so Nginx becomes the only
public door to it too (proxied via a second Nginx server block) - same
pattern already used for GlobeTrotter's deployments.

## Rollback

If Phase 2 has a bad night: `pm2 stop ecosystem.config.js`, then
temporarily bring back a single-process Phase 1 checkout on `:5003`
(git has the old commit) until the microservices version is fixed.
Data files (`users.json`, `itineraries.json`, `destinations.json`) are
compatible either way - Phase 2 didn't change their shape, only which
process owns each one.
