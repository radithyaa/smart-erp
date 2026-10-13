#!/usr/bin/env bash
# B7 — Seed data dummy P2P untuk demo (SRS §8, NFR4).
#
# Idempoten: aman dijalankan berulang; batch lama dihapus lebih dulu oleh
# generator (lihat smart_erp_ai/scripts/seed_demo_data.py).
#
# Pakai:
#   ./scripts/seed-demo-data.sh            # 300 kasus (default)
#   ./scripts/seed-demo-data.sh 400        # 400 kasus
#   ./scripts/seed-demo-data.sh reset      # hapus batch seed saja
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker/docker-compose.yml"
SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"
CASES="${1:-300}"

run_bench() { $COMPOSE exec -T backend bench --site "$SITE" "$@"; }

if [ "$CASES" = "reset" ]; then
  echo "==> Menghapus batch seed dari site '$SITE'..."
  run_bench execute smart_erp_ai.scripts.seed_demo_data.reset
  exit 0
fi

echo "==> Membuat $CASES kasus P2P (bottleneck + rework disuntik) di site '$SITE'..."
run_bench execute smart_erp_ai.scripts.seed_demo_data.run --kwargs "{'cases': $CASES}"

echo ""
echo "==> Verifikasi cepat (jumlah event log yang dihasilkan):"
run_bench execute smart_erp_ai.process_intelligence.event_log.count_p2p_events 2>/dev/null || true
echo "Selesai. Jalankan './scripts/run-demo.sh' untuk menyiapkan dan menguji alur demo."
