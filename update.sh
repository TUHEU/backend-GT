#!/usr/bin/env bash
# Mise a jour Yaounde Ensemble (backend-GT) - Phase 2, 4 services
#
# Reconstruit a partir du script Phase 1 (meme structure de messages,
# meme sauvegarde avant modification, meme verification de sante a la
# fin) - adapte pour installer/redemarrer les 4 services au lieu d'un
# seul processus PM2 "backend-gt".

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "=== Mise a jour Yaounde Ensemble (backend-GT) - $(date '+%Y-%m-%d %H:%M:%S') ==="

# ---- 1) Sauvegarde des donnees avant toute modification ----
mkdir -p backups
tar -czf "backups/data_${TIMESTAMP}.tar.gz" \
  user-service/data itinerary-service/data recommendation-service/data 2>/dev/null || true
echo "[OK] Donnees sauvegardees -> /root/backend-GT/backups/data_${TIMESTAMP}.tar.gz"

# ---- 2) Recuperation des changements ----
if [ -d .git ]; then
  echo "[OK] Depot git detecte - recuperation des changements..."
  git pull
else
  echo "[!] Pas de depot git ici - etape ignoree."
fi

# ---- 3) Installation des dependances, par service ----
echo "[OK] Installation des dependances (par service)..."
for svc in api-gateway user-service itinerary-service recommendation-service; do
  if [ ! -d "$svc/venv" ]; then
    echo "    -> $svc : premiere fois, creation du venv"
    python3 -m venv "$svc/venv"
  fi
  "./$svc/venv/bin/pip" install --quiet -r "$svc/requirements.txt"
done

# ---- 4) Redemarrage via PM2 ----
echo "[OK] Redemarrage des 4 services (PM2)..."
# Si l'ancien process unique "backend-gt" existe encore (avant la
# premiere migration Phase 2), on le retire - sinon cette ligne ne
# fait rien.
pm2 delete backend-gt 2>/dev/null || true
if pm2 describe yaounde-api-gateway > /dev/null 2>&1; then
  pm2 restart ecosystem.config.js
else
  pm2 start ecosystem.config.js
fi
pm2 save
pm2 list

# ---- 5) Verification du demarrage ----
echo "[OK] Verification du demarrage..."
OK=0
for i in 1 2 3 4 5; do
  if curl -sf http://127.0.0.1:5003/health > /dev/null; then
    OK=1
    break
  fi
  sleep 2
done

if [ "$OK" = "1" ]; then
  echo "[OK] L'API repond sur http://127.0.0.1:5003/health"
  curl -s http://127.0.0.1:5003/health
  echo
else
  echo "[!] L'API ne repond pas sur http://127.0.0.1:5003/health apres plusieurs essais."
  echo
  echo "Dernieres lignes du journal :"
  pm2 logs --lines 30 --nostream
  echo
  echo "[ERREUR] Verifie les logs ci-dessus. Restauration possible depuis : /root/backend-GT/backups"
  exit 1
fi
