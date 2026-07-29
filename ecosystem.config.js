/**
 * PM2 process definition for the Yaoundé Ensemble Flask backend.
 * Run from inside backend/:   pm2 start ecosystem.config.js
 *
 * PM2 doesn't run Python directly - it runs an executable and manages
 * its process (restarts, logs, boot persistence). Here that executable
 * is gunicorn, sitting inside the venv, with interpreter set to "none"
 * so PM2 executes it directly (via its shebang) instead of trying to
 * hand it to Node.
 *
 * Port 5003: not a default choice - on the actual deployment VPS,
 * 5000/5001/5002 were all already taken by other apps (`ss -tulpn`
 * showed the full picture). Check what's free on YOUR VPS before
 * reusing this port blindly.
 */
module.exports = {
  apps: [
    {
      name: "backend-gt",
      script: "venv/bin/gunicorn",
      args: "--workers 2 --bind 0.0.0.0:5003 app:app",
      interpreter: "none",
      cwd: __dirname,
      env: {
        // Change this to a long random string before going live.
        // Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"
        SECRET_KEY: "change-this-to-something-random-and-long",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
