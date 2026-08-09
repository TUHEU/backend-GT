/**
 * PM2 process definitions for the Yaoundé Ensemble Phase 2 backend -
 * now 4 processes instead of the old single "backend-gt" one.
 *
 * Run from inside `backend GT/`:   pm2 start ecosystem.config.js
 *
 * Same pattern as the old Phase 1 config: PM2 runs gunicorn (inside
 * each service's own venv) rather than Python directly, with
 * interpreter set to "none" so PM2 executes it via its shebang.
 *
 * Ports carried over from the live deployment where possible:
 * - api-gateway stays on 5003 - that's the port already open in ufw
 *   and already hardcoded in frontend/js/config.js, so nothing on the
 *   frontend or firewall side needs to change.
 * - user-service/itinerary-service/recommendation-service could NOT
 *   reuse 5000/5001/5002 - those were already taken by other students'
 *   apps on this shared VPS (per the original DEPLOY_VPS.md note).
 *   Moved to 5011/5012/5013 instead - double check these are still
 *   free on your VPS with `ss -tulpn` before deploying, same as the
 *   original setup did.
 * - Only api-gateway needs `ufw allow <port>/tcp` and a public bind
 *   (0.0.0.0). The other three are internal-only: bind them to
 *   127.0.0.1 so they're unreachable from outside the VPS entirely -
 *   only api-gateway (and each other, over localhost) can reach them.
 */
const SECRET_KEY = "change-this-to-something-random-and-long";
// Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"
// Use the SAME value for all four apps below - JWTs signed by
// user-service must verify identically in the other three.

module.exports = {
  apps: [
    {
      name: "yaounde-user-service",
      script: "user-service/venv/bin/gunicorn",
      args: "--workers 2 --bind 127.0.0.1:5011 app:app",
      cwd: __dirname + "/user-service",
      interpreter: "none",
      env: { SECRET_KEY },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
    {
      name: "yaounde-itinerary-service",
      script: "itinerary-service/venv/bin/gunicorn",
      args: "--workers 2 --bind 127.0.0.1:5012 app:app",
      cwd: __dirname + "/itinerary-service",
      interpreter: "none",
      env: {
        SECRET_KEY,
        RECOMMENDATION_SERVICE_URL: "http://127.0.0.1:5013",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
    {
      name: "yaounde-recommendation-service",
      script: "recommendation-service/venv/bin/gunicorn",
      args: "--workers 2 --bind 127.0.0.1:5013 app:app",
      cwd: __dirname + "/recommendation-service",
      interpreter: "none",
      env: {
        SECRET_KEY,
        USER_SERVICE_URL: "http://127.0.0.1:5011",
        ITINERARY_SERVICE_URL: "http://127.0.0.1:5012",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
    {
      name: "yaounde-api-gateway",
      script: "api-gateway/venv/bin/gunicorn",
      args: "--workers 2 --bind 0.0.0.0:5003 app:app",
      cwd: __dirname + "/api-gateway",
      interpreter: "none",
      env: {
        USER_SERVICE_URL: "http://127.0.0.1:5011",
        ITINERARY_SERVICE_URL: "http://127.0.0.1:5012",
        RECOMMENDATION_SERVICE_URL: "http://127.0.0.1:5013",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
