#!/usr/bin/env bash
# Runs automatically after the Codespace / devcontainer is created.
# Brings up the ERPNext (develop) stack and creates the site on first run.
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker/docker-compose.yml"

SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-admin}"

echo "==> Waiting for Docker daemon..."
for i in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then break; fi
  sleep 2
done
docker info >/dev/null 2>&1 || { echo "Docker daemon not available"; exit 1; }

echo "==> Building app image from submodules (first run can take a while)..."
$COMPOSE build

echo "==> Starting infra (mariadb + redis)..."
$COMPOSE up -d mariadb redis-cache redis-queue

echo "==> Waiting for MariaDB to be healthy..."
for i in $(seq 1 60); do
  status=$(docker inspect --format '{{.State.Health.Status}}' smart-erp-mariadb-1 2>/dev/null || echo unknown)
  if [ "$status" = "healthy" ]; then break; fi
  sleep 3
done

echo "==> Running configurator..."
$COMPOSE run --rm configurator

echo "==> Ensuring site exists..."
if $COMPOSE run --rm --no-deps --entrypoint test backend -f "sites/$SITE/site_config.json"; then
  echo "    Site $SITE already exists, skipping creation."
else
  echo "    Creating site $SITE and installing ERPNext..."
  $COMPOSE run --rm backend \
    bench new-site "$SITE" \
      --db-root-password "$DB_ROOT_PASSWORD" \
      --admin-password "$ADMIN_PASSWORD" \
      --install-app erpnext \
      --set-default
fi

echo "==> Starting application services..."
$COMPOSE up -d backend websocket queue-short queue-long scheduler frontend

echo ""
echo "=========================================================="
echo " ERPNext is starting."
echo " Web UI : http://$SITE:8080  (Codespaces will forward port 8080)"
echo " User   : Administrator"
echo " Pass   : $ADMIN_PASSWORD"
echo "=========================================================="
echo "Note: nginx may need ~15s and a restart to pick up the backend."
echo "      If you get 502:  $COMPOSE restart frontend"
