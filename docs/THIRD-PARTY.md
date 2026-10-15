# THIRD-PARTY.md — Daftar Komponen & Lisensi Pihak Ketiga

> Dirujuk oleh `docs/AGENT-RULES.md` (RULE 3.1, RULE 3.5, RULE 4.6).
> Setiap penambahan library/aset pihak ketiga ke layer **L2 (`apps/smart_erp_ai`) wajib dicatat di sini**.

## Komponen inti (L1 — reference implementation)

| Komponen | Versi/Branch | Lisensi | Sumber | Catatan |
|---|---|---|---|---|
| Frappe Framework | `version-16` (16.51.1) | GPLv3 | github.com/frappe/frappe | Dipakai sebagai framework, **bukan** didistribusikan |
| ERPNext | `version-16` (16.50.0) | GPLv3 | github.com/frappe/erpnext | Reference implementation & sumber data |

## Dependensi L2 (kode kami)

| Paket | Versi | Lisensi | Kegunaan | Ditambahkan |
|---|---|---|---|---|
| `langchain` | `>=0.3,<0.4` | MIT | Orkestrasi agent + tool calling (`agent/loop.py`) | 2026-10 (Dev A) |
| `langchain-openai` | `>=0.2,<0.3` | MIT | Klien LLM OpenAI-compatible via API eksternal (NFR6) | 2026-10 (Dev A) |

> Keduanya berlisensi **MIT** (bukan AGPL) — aman untuk layanan terpisah sesuai
> RULE 3.5. Dideklarasikan di `apps/smart_erp_ai/pyproject.toml`.

## Aset desain (tema/ikon/font) untuk rebranding

| Aset | Lisensi | Sumber | Catatan |
|---|---|---|---|
| _(belum ada — isi saat menambah aset)_ | | | |

## Aturan pencatatan

1. Sebelum menambahkan dependensi/aset, cek lisensi dan catat di tabel yang sesuai.
2. Hindari lisensi **AGPL** untuk layanan terpisah (dapat memicu kewajiban source).
3. Untuk analitik proses, preferensi paket: MIT/BSD/Apache-2.0.
4. Cantumkan alasan ringkas pada kolom "Kegunaan".

> Riwayat: submodule sebelumnya menunjuk branch `develop` (17-dev, unstable) sementara
> `docker/Dockerfile` memakai base image `frappe/erpnext:v16` — ketidaksesuaian versi yang
> berisiko pada build. **Sudah diselaraskan** ke branch `version-16` (Frappe 16.51.1 + ERPNext
> 16.50.0). Bila ingin naik versi, bump **keduanya bersama-sama**: branch di `.gitmodules`
> dan tag base image di `docker/Dockerfile`.
