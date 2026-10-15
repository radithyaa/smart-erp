#!/usr/bin/env bash
# Idempotent post-start repairs for the Smart ERP stack.
#
# Run this after the stack is up (devcontainer-setup.sh calls it automatically,
# and ./scripts/smart-erp.sh up calls it too). It fixes the two things that
# otherwise break on a fresh device or after a rebuild:
#
#   1. DB user grant bound to a stale container IP.
#      Frappe creates the site DB user for the *specific* host IP of the
#      container that ran `bench new-site`. Docker assigns a new IP on every
#      `up`, so the backend later gets "Access denied for user ...@<new-ip>".
#      We re-create the same user with host '%' so any container can connect.
#
#   2. Stale asset manifest (sites/assets/assets.json).
#      After the image is rebuilt the hashed bundle filenames change, but the
#      manifest baked into the image can point at the old names -> CSS/JS 404
#      and the layout breaks. We regenerate the manifest from the already-built
#      bundles without recompiling (bench build --using-cached).
#
# Both steps are safe to run repeatedly.
set -euo pipefail
cd "$(dirname "$0")/.."
# Respect an externally-provided compose file set (e.g. the dev overlay exports
# COMPOSE_FILE), otherwise use the default stack.
if [ -n "${COMPOSE_FILE:-}" ]; then
  COMPOSE="docker compose"
else
  COMPOSE="docker compose -f docker/docker-compose.yml"
fi
SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-admin}"

# L2 app (ours). Registered in the image (Dockerfile) and re-ensured here so a
# site volume created before the app existed still picks it up.
L2_APP="smart_erp_ai"

running() { $COMPOSE ps --status running --services 2>/dev/null | grep -qx "$1"; }

echo "==> [post-up-fix] Ensuring DB grant for site '$SITE' uses host '%'"
if running mariadb && running backend; then
  # Read credentials from the site config (created by `bench new-site`).
  site_cfg=$($COMPOSE exec -T backend cat "sites/$SITE/site_config.json" 2>/dev/null || true)
  if [ -n "$site_cfg" ]; then
    db_name=$(printf '%s' "$site_cfg" | sed -n 's/.*"db_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    db_user=$(printf '%s' "$site_cfg" | sed -n 's/.*"db_user"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    db_password=$(printf '%s' "$site_cfg" | sed -n 's/.*"db_password"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

    if [ -n "$db_user" ] && [ -n "$db_password" ]; then
      $COMPOSE exec -T mariadb mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "
        CREATE USER IF NOT EXISTS '$db_user'@'%' IDENTIFIED BY '$db_password';
        ALTER USER '$db_user'@'%' IDENTIFIED BY '$db_password';
        GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '$db_user'@'%';
        FLUSH PRIVILEGES;" \
        && echo "    OK: '$db_user'@'%' granted on \`$db_name\`" \
        || echo "    WARN: could not (re)grant DB user; continuing"
    else
      echo "    Skipped: could not read db_user/db_password from $SITE config"
    fi
  else
    echo "    Skipped: site '$SITE' not created yet"
  fi
else
  echo "    Skipped: mariadb/backend not running"
fi

echo "==> [post-up-fix] Ensuring localhost site resolution and default_site"
if running backend; then
  $COMPOSE exec -T backend bash -c \
    "cd /home/frappe/frappe-bench && \
     [ -d sites/$SITE ] && [ ! -e sites/localhost ] && ln -s $SITE sites/localhost || true; \
     echo '$SITE' > sites/currentsite.txt; \
     bench set-config -g default_site $SITE >/dev/null 2>&1 || true" \
    && echo "    OK: localhost mapped to $SITE" \
    || echo "    WARN: could not configure localhost resolution"
else
  echo "    Skipped: backend not running"
fi

echo "==> [post-up-fix] Regenerating asset manifest from built bundles"
if running backend; then
  # Repair the common fresh-volume case as well as stale hashed filenames.
  # A new named `sites` volume can hide the manifest generated in the image;
  # --using-cached cannot create bundles that are absent from that volume.
  if $COMPOSE exec -T backend bash -c \
    'test -s sites/assets/assets.json && compgen -G "sites/assets/frappe/dist/css/desk.bundle.*.css" >/dev/null'; then
    $COMPOSE exec -T backend bash -c \
      'cd /home/frappe/frappe-bench && bench build --apps frappe,erpnext --using-cached'
  else
    $COMPOSE exec -T backend bash -c \
      'cd /home/frappe/frappe-bench && bench build --apps frappe,erpnext'
  fi \
    && echo "    OK: asset manifest regenerated" \
    || echo "    WARN: asset build failed; inspect backend logs and run 'bench build --apps frappe,erpnext'"
else
  echo "    Skipped: backend not running"
fi

# --- L2 app registration (idempotent) -------------------------------------
# Makes `bench execute smart_erp_ai...` work and installs the app on the site
# the first time. Needed because a site volume created before the app existed
# will not have it, and because sites/apps.txt lives in the shared volume while
# the editable-install .pth lives in the image.
echo "==> [post-up-fix] Ensuring L2 app '$L2_APP' is registered and installed"
if running backend; then
  # 1) apps.txt (volume) must list the app.
  $COMPOSE exec -T backend bash -lc "grep -qx '$L2_APP' sites/apps.txt 2>/dev/null || echo '$L2_APP' >> sites/apps.txt" \
    && echo "    OK: sites/apps.txt lists $L2_APP" \
    || echo "    WARN: could not update sites/apps.txt"

  # 2) editable install (.pth) so the module is importable. The image already
  #    did this at build; re-run cheaply/idempotently (pip -e is a no-op if ok).
  $COMPOSE exec -T backend bash -lc \
    "cd /home/frappe/frappe-bench && env/bin/pip install -e apps/$L2_APP -q" \
    && echo "    OK: $L2_APP importable (editable install)" \
    || echo "    WARN: editable install failed"

  # 3) install on the site if not already installed.
  if $COMPOSE exec -T backend test -f "sites/$SITE/site_config.json"; then
    if $COMPOSE exec -T backend bench --site "$SITE" list-apps 2>/dev/null | grep -q "$L2_APP"; then
      echo "    OK: already installed on $SITE"
    else
      $COMPOSE exec -T backend bench --site "$SITE" install-app "$L2_APP" \
        && echo "    OK: installed on $SITE" \
        || echo "    WARN: install-app failed; run manually"
    fi
  else
    echo "    Skipped: site $SITE not created yet"
  fi
else
  echo "    Skipped: backend not running"
fi

echo "==> [post-up-fix] Done"
