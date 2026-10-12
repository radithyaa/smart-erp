#!/bin/bash
# Dev-overlay entrypoint.
#
# In the default (image-baked) stack, the base image's entrypoint.sh points
# sites/assets at the in-image /home/frappe/frappe-bench/assets directory. That
# does not work when app sources are bind-mounted for hot reload, because the
# watch/build output lands under the bind-mounted apps/ tree instead.
#
# Here we point sites/assets at a named volume (shared read-write between the
# backend and the frontend/nginx container) and link each app's public dir into
# it, so anything the watcher rebuilds is immediately visible to nginx.
#
# This runs instead of the base entrypoint (entrypoint override in the dev
# overlay), so it must exec the passed command itself.
set -euo pipefail

umask 0002

BENCH_DIR="/home/frappe/frappe-bench"
ASSETS_PATH="$BENCH_DIR/sites/assets"
SHARED_ASSETS="$BENCH_DIR/assets"

echo "[dev-entrypoint] Preparing shared assets dir at $SHARED_ASSETS"
mkdir -p "$SHARED_ASSETS"

# Point sites/assets at the shared, writable assets dir.
rm -rf "$ASSETS_PATH"
mkdir -p "$(dirname "$ASSETS_PATH")"
ln -s "$SHARED_ASSETS" "$ASSETS_PATH"

# Link each app's public dir into the shared assets dir, mirroring what the
# base image does at build time: assets/<app> -> apps/<app>/<app>/public
for app_dir in "$BENCH_DIR"/apps/*/; do
    app_name="$(basename "$app_dir")"
    public_dir="$app_dir$app_name/public"
    if [ -d "$public_dir" ]; then
        link="$SHARED_ASSETS/$app_name"
        # Only (re)create if missing or pointing elsewhere.
        if [ ! -e "$link" ] || [ "$(readlink -f "$link" 2>/dev/null)" != "$(readlink -f "$public_dir" 2>/dev/null)" ]; then
            rm -rf "$link"
            ln -s "$public_dir" "$link"
        fi
    fi
done

# Site-level dirs under assets (css/, js/, locale/, *.json) are produced by
# `bench build`; ensure the directory exists so nginx never 404s the manifest.
touch "$SHARED_ASSETS/.keep"

echo "[dev-entrypoint] Executing: $*"
exec "$@"
