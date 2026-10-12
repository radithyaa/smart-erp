#!/usr/bin/env bash
# Convenience wrapper around the Smart ERP docker stack.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker/docker-compose.yml"
SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"

case "${1:-help}" in
  up)       $COMPOSE up -d ;;
  down)     $COMPOSE down ;;
  stop)     $COMPOSE stop ;;
  restart)  $COMPOSE restart ;;
  ps)       $COMPOSE ps ;;
  logs)     $COMPOSE logs -f "${2:-backend}" ;;
  build)    $COMPOSE build ;;
  bench)    shift; $COMPOSE exec backend bench --site "$SITE" "$@" ;;
  shell)    $COMPOSE exec backend bash ;;
  db)       $COMPOSE exec mariadb mariadb -uroot -p"${DB_ROOT_PASSWORD:-admin}" ;;
  migrate)  $COMPOSE exec backend bench --site "$SITE" migrate ;;
  backup)   $COMPOSE exec backend bench --site "$SITE" backup ;;
  *)
    cat <<EOF
Smart ERP helper

  ./scripts/smart-erp.sh up            Start all services
  ./scripts/smart-erp.sh down          Stop and remove containers
  ./scripts/smart-erp.sh ps            Show service status
  ./scripts/smart-erp.sh logs [svc]    Tail logs (default: backend)
  ./scripts/smart-erp.sh build         Rebuild app image from submodules
  ./scripts/smart-erp.sh shell         Bash inside backend container
  ./scripts/smart-erp.sh bench <args>  Run bench command for the site
  ./scripts/smart-erp.sh migrate       Migrate the site
  ./scripts/smart-erp.sh backup        Backup the site
  ./scripts/smart-erp.sh db            MariaDB root shell
EOF
    ;;
esac
