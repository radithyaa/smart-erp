# A7 — Metrik Validasi (NFR1): ≥20 Test Commands

> Setiap command diuji via chat UI at `/chat`. Target: success rate ≥80%, latency <10s per tool call.

## 1–5: Basic Document Queries

| # | Command | Expected Tool | Expected Outcome |
|---|---------|---------------|------------------|
| 1 | "apa status PO terakhir?" | `list_documents` | Menampilkan PO terbaru dengan docstatus |
| 2 | "tampilkan 5 PO terbaru" | `list_documents` | List 5 PO, terurut creation desc |
| 3 | "detail PO-001" | `get_document` | Field lengkap PO-001 |
| 4 | "daftar semua supplier" | `list_documents` | List supplier aktif |
| 5 | "apa saja item yang tersedia?" | `list_documents` | List item master |

## 6–10: Create / Submit Flow

| # | Command | Expected Tool | Expected Outcome |
|---|---------|---------------|------------------|
| 6 | "buat PO untuk vendor X, 10 unit item Y" | `create_document` | pending_confirmation → user confirm → PO created |
| 7 | "submit PO-002" | `submit_document` | pending_confirmation → confirm → docstatus=1 |
| 8 | "update PO-003, ubah supplier jadi Vendor B" | `update_document` | pending_confirmation → confirm → updated |
| 9 | "buat PO baru untuk supplier tes, 5 unit item tes" | `create_document` | Confirm gate triggered, creates PO after confirm |
| 10 | "kirim PO-001 untuk approval" | `submit_document` | Confirm → submit success |

## 11–15: Analysis Queries

| # | Command | Expected Tool | Expected Outcome |
|---|---------|---------------|------------------|
| 11 | "di mana bottleneck bulan ini?" | `get_bottlenecks` | Tahap terlama identified with avg duration |
| 12 | "ada berapa rework?" | `get_rework_cases` | Count + list of rework cases |
| 13 | "proses mana yang paling lambat?" | `get_bottlenecks` | Bottleneck stage identified |
| 14 | "tampilkan PO yang tertahan approval" | `get_pending_at_stage` | List of pending POs with age_hours |
| 15 | "ada berapa dokumen tertahan di tahap Purchase Receipt?" | `get_pending_at_stage` | Count + list pending at PR stage |

## 16–21: Bridge / Guardrail / Reminder Queries

| # | Command | Expected Tool | Expected Outcome |
|---|---------|---------------|------------------|
| 16 | "hapus PO-001" | (none) | Rejected — no delete tool exists |
| 17 | "batalkan PO-002" | (none) | Rejected — no cancel tool exists |
| 18 | "tampilkan invoice tertahan" | `get_pending_at_stage` | List pending at PI stage |
| 19 | "buat Sales Invoice baru" | (none) | Rejected — DocType not in allowlist |
| 20 | "ringkasan status proses P2P" | `get_bottlenecks` + `get_pending_at_stage` | Multi-tool answer: bottleneck + pending summary |
| 21 | "tampilkan PO tertahan lalu kirim reminder" | `get_pending_at_stage` → `send_reminder` | Pending list → confirm → ToDo created in Desk |

## F4 — Panel Visualisasi (bukan command chat)

Buka `/chat` → klik **Panel Analitik**. Diharapkan tampil:
1. Grafik batang durasi rata-rata antar tahap (tahap bottleneck berwarna berbeda).
2. Diagram alur P2P beranotasi bottleneck.
3. Ringkasan tahap terlama + jumlah rework/deviasi.

Bukti: screenshot bersih panel (Prototype Alpha, SRS §12). Data dari endpoint
`smart_erp_ai.api.analytics_overview`.

## Validation Protocol

1. For each command, record:
   - Pass/Fail
   - Latency (seconds, measured from send to reply)
   - Tool(s) called
2. Calculate success rate (target ≥80% = ≥16/20 pass)
3. Calculate average latency (target <10s per tool call)
4. Record results in a table for proposal submission

## Expected Summary Table Template

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Commands | 21 | ≥20 | — |
| Passed | — | ≥17 | — |
| Failed | — | ≤4 | — |
| Success Rate | —% | ≥80% | — |
| Avg Latency | —s | <10s | — |
| Max Latency | —s | <10s | — |
