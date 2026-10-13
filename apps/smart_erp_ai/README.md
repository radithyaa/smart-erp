# smart_erp_ai (L2)

**Agentic Process Intelligence** di atas ERPNext — layer orisinal tim (L2).

> ERPNext/Frappe (L1) = GPLv3, submodule read-only. Semua kode di app ini milik tim.
> Baca `docs/AGENT-RULES.md` dan `docs/SRS.md` sebelum mengubah apa pun.

## Struktur

```
smart_erp_ai/
├── agent/                  # [Dev A] LLM loop, prompt, tool-calling, konfirmasi
├── process_intelligence/   # [Dev B] event log extractor, bottleneck, rework, api analitik
├── tools/                  # [Dev A] tool layer generik berbasis DocType
├── adapter/                # [Dev B] pemisah interfacing ERP (ERPSource)
├── api.py                  # [Dev A] endpoint whitelisted yang dipanggil UI
```

Kontrak antar-modul (`AnalysisQueryAPI`) ada di
`smart_erp_ai/process_intelligence/api.py` — **Dev B menyediakan, Dev A mengonsumsi**.

## Menjalankan (dari dalam `bench`)

```sh
# 1. Seed data dummy P2P (Dev B / B4)
bench --site erpnext.localhost execute smart_erp_ai.scripts.seed_demo_data.run

# 2. Event log extractor (Dev B / B1)
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.event_log.extract_events

# 3. Analisis bottleneck (Dev B / B2)
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.api.get_bottlenecks --kwargs "{'process':'purchase-to-pay'}"
```

Lihat `docs/DEV-TASKS.md` untuk pembagian tugas lengkap.
