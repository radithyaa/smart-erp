#!/usr/bin/env bash
# B7 — Menyiapkan & memverifikasi demo dari nol (NFR4).
#
# Urutan: seed data → ekstrak event log → analisis bottleneck → rework.
# Cocok dijalankan setelah stack hidup (./scripts/smart-erp.sh up).
#
# Pakai:
#   ./scripts/run-demo.sh          # seed (bila perlu) + jalankan analisis
#   ./scripts/run-demo.sh --reseed # paksa seed ulang lebih dulu
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker/docker-compose.yml"
SITE="${FRAPPE_SITE_NAME:-erpnext.localhost}"
KW_P2P="{'process': 'purchase-to-pay'}"

run_bench() { $COMPOSE exec -T backend bench --site "$SITE" "$@"; }

if [ "${1:-}" = "--reseed" ]; then
  bash scripts/seed-demo-data.sh
fi

echo "==> [F1] Ekstraksi event log P2P..."
EVENTS=$(run_bench execute smart_erp_ai.process_intelligence.event_log.extract_p2p_events || true)
echo "    (contoh output di atas; jumlah baris bisa besar)"

echo ""
echo "==> [F2] Analisis bottleneck P2P:"
run_bench execute smart_erp_ai.process_intelligence.api.bottlenecks --kwargs "$KW_P2P"

echo ""
echo "==> [F3] Rework / deviasi P2P:"
run_bench execute smart_erp_ai.process_intelligence.api.rework_cases --kwargs "$KW_P2P"

echo ""
echo "==> [F7] Dokumen tertahan di tahap Purchase Order:"
run_bench execute smart_erp_ai.process_intelligence.api.pending_at_stage \
  --kwargs "{'process': 'purchase-to-pay', 'stage': 'purchase_order'}"

echo ""
echo "Demo siap. Buka UI chat di http://$SITE:8080 dan jalankan 4 pertanyaan tetap (SRS §9)."
