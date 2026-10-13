#!/usr/bin/env bash
# Convenience wrapper around the Smart ERP docker stack.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker/docker-compose.yml"
DEV_COMPOSE="docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml"
SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"

# Enable developer_mode on the site so Frappe serves fresh assets (no cache) and
# cache-busts with a timestamp. Required for the hot-reload dev overlay.
enable_developer_mode() {
  $COMPOSE exec -T backend bench --site "$SITE" set-config developer_mode 1 >/dev/null 2>&1 &&
    $COMPOSE exec -T backend bench --site "$SITE" clear-cache >/dev/null 2>&1 || true
}

# True if any container of the given compose invocation is running.
has_running_services() {
  local compose="$1"
  [ -n "$($compose ps --status running -q 2>/dev/null)" ]
}

# Tail logs for a service, with a friendly message when nothing is running.
tail_logs() {
  local compose="$1" svc="$2" hint="$3"
  if ! has_running_services "$compose"; then
    echo "No running containers for this stack."
    echo "Start it first, then retry. $hint"
    return 1
  fi
  $compose logs -f "$svc"
}

case "${1:-help}" in
  up)       $COMPOSE up -d && bash scripts/post-up-fix.sh ;;
  down)     $COMPOSE down ;;
  stop)     $COMPOSE stop ;;
  restart)  $COMPOSE restart && bash scripts/post-up-fix.sh ;;
  ps)       $COMPOSE ps ;;
  logs)     tail_logs "$COMPOSE" "${2:-backend}" "Try: ./scripts/smart-erp.sh up" ;;
  build)    $COMPOSE build ;;
  bench)    shift; $COMPOSE exec backend bench --site "$SITE" "$@" ;;
  shell)    $COMPOSE exec backend bash ;;
  db)       $COMPOSE exec mariadb mariadb -uroot -p"${DB_ROOT_PASSWORD:-admin}" ;;
  migrate)  $COMPOSE exec backend bench --site "$SITE" migrate ;;
  backup)   $COMPOSE exec backend bench --site "$SITE" backup ;;
  fix)      bash scripts/post-up-fix.sh ;;

  # --- L2 analytics demo (Dev B): seed data dummy + analisis proses ---
  seed)     bash scripts/seed-demo-data.sh "${2:-300}" ;;
  reseed)   bash scripts/seed-demo-data.sh reset ;;
  demo)     bash scripts/run-demo.sh ;;

  # --- Hot-reload dev mode (source bind-mounted, watcher + gunicorn --reload) ---
  dev)
    # If the *default* stack is up (no dev overlay), tear it down first so the
    # dev overlay can recreate services. If we're already in dev mode, do
    # nothing destructive — just re-run the idempotent steps below.
    if has_running_services "$COMPOSE" && ! $DEV_COMPOSE ps --status running -q watch 2>/dev/null | grep -q .; then
      echo "==> Stack is running in DEFAULT mode; switching to hot-reload dev mode..."
      $COMPOSE down
    fi
    echo "==> Starting stack in hot-reload dev mode..."
    $DEV_COMPOSE up -d
    echo "==> Waiting for backend..."
    for i in $(seq 1 30); do
      if $DEV_COMPOSE exec -T backend bash -c 'true' >/dev/null 2>&1; then break; fi
      sleep 2
    done
    echo "==> Enabling developer_mode for '$SITE'..."
    enable_developer_mode
    COMPOSE_FILE="docker/docker-compose.yml:docker/docker-compose.dev.yml" bash scripts/post-up-fix.sh
    echo ""
    echo "Hot reload is ON:"
    echo "  - Frontend: edit apps/*/public/**  -> esbuild rebuilds on save, refresh the browser"
    echo "  - Backend : edit apps/*/**/*.py    -> gunicorn reloads workers automatically"
    echo "  - Watcher logs: ./scripts/smart-erp.sh dev-logs"
    echo "  - Web UI      : http://$SITE:8080"
    ;;
  dev-down)
    $DEV_COMPOSE down
    ;;
  dev-logs)
    tail_logs "$DEV_COMPOSE" "${2:-watch}" "Try: ./scripts/smart-erp.sh dev" ;;
  dev-fix)
    # Re-apply the developer_mode flag if it got lost (e.g. fresh site volume).
    enable_developer_mode && echo "developer_mode enabled for '$SITE'"
    ;;

  *)
    cat <<EOF
Smart ERP helper

  ./scripts/smart-erp.sh up            Start all services
  ./scripts/smart-erp.sh down          Stop and remove containers
  ./scripts/smart-erp.sh ps            Show service status
  ./scripts/smart-erp.sh logs [svc]    Tail logs (default: backend)
  ./scripts/smart-erp.sh build         Rebuild app image from submodules
  ./scripts/smart-erp.sh fix           Re-apply DB grant + assets manifest
  ./scripts/smart-erp.sh shell         Bash inside backend container
  ./scripts/smart-erp.sh bench <args>  Run bench command for the site
  ./scripts/smart-erp.sh migrate       Migrate the site
  ./scripts/smart-erp.sh backup        Back up the site
  ./scripts/smart-erp.sh db            MariaDB root shell

L2 analytics demo (Smart ERP AI):
  ./scripts/smart-erp.sh seed [N]      Seed N dummy P2P cases (default 300)
  ./scripts/smart-erp.sh reseed        Delete the seed batch only
  ./scripts/smart-erp.sh demo          Run the F1/F2/F3/F7 analytics demo

Hot-reload dev mode:
  ./scripts/smart-erp.sh dev           Start stack with live reload (bind-mounted sources)
  ./scripts/smart-erp.sh dev-down      Stop the dev-mode stack
  ./scripts/smart-erp.sh dev-logs [svc] Tail watcher logs (default: watch)
  ./scripts/smart-erp.sh dev-fix       (Re)enable developer_mode on the site
EOF
    ;;
esac
