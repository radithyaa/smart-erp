# DEV-B-STATUS.md — Status Jalur Analitik (Dev B)

> Ringkasan pekerjaan **Dev B** (jalur analitik: *membaca & menganalisis ERP*).
> Merujuk `docs/SRS.md` (F1–F4, NFR4, NFR5, §8) dan `docs/DEV-TASKS.md` (§3, §6).
>
> Aturan yang dipatuhi: seluruh kode ada di **L2** (`apps/smart_erp_ai`), tidak
> menyentuh L1 (`RULE 1.1–1.2`); analitik bicara lewat **adapter** (`RULE 2.4`);
> kontrak antar-modul eksplisit (`RULE 2.2`); tanpa dependensi baru.

## ✅ Status: SEMUA TUGAS DEV B SELESAI & TERVERIFIKASI DI SITE HIDUP

Diverifikasi pada stack Docker (`erpnext.localhost`, ERPNext 16.50.0 / Frappe 16.51.1):
300 kasus P2P di-seed, **seluruh analitik F1–F4/F7 berjalan dengan angka nyata**.

| Hasil verifikasi | Angka nyata |
|---|---|
| F1 event log | **1875 baris** event kanonik (syarat ≥200) |
| F2 bottleneck | Purchase Invoice avg 37.0j; Purchase Receipt avg 29.43j / **median 2.16j** (tanda bottleneck disuntik) |
| F3 rework/deviasi | **17 rework** (persis sesuai sunutkan) + 3 deviasi (data demo ERPNext) |
| F7 pending | 6 PO tertahan (menunggu langkah berikutnya) |
| Uji unit | **7/7 LULUS** (`bench run-tests`) |

## Ringkasan tugas

| Task | Req | Status | Lokasi |
|---|---|---|---|
| **B6** Adapter layer | NFR5 | ✅ | `adapter/base.py`, `adapter/erpnext_source.py` |
| **B1** Event log extractor | F1 | ✅ | `process_intelligence/event_log.py` |
| **B2** Bottleneck analysis | F2 | ✅ | `process_intelligence/bottleneck.py` |
| **B3** Rework & deviation | F3 | ✅ | `process_intelligence/rework.py` |
| **Kontrak** AnalysisQueryAPI v1 | F7/§1 | ✅ | `process_intelligence/api.py` |
| **B4** Generator data dummy | §8 | ✅ | `scripts/seed_demo_data.py` |
| **B5** Visualisasi (data siap-render) | F4 | ✅ | `process_intelligence/api.py` (`flow_diagram`, `process_overview`) |
| **B7** Script reproducible | NFR4 | ✅ | `scripts/seed-demo-data.sh`, `scripts/run-demo.sh` |

## Peta ke SRS

- **F1** — `event_log.extract_events()` menghasilkan tabel kanonik
  `case_id | activity | timestamp | actor | doctype | reference`. Sumber: `Version`
  (transisi `docstatus`/`workflow_state`) + timestamp dokumen. Mencakup
  `Purchase Order → Purchase Receipt → Purchase Invoice`.
- **F2** — `bottleneck.compute_bottlenecks()`: `avg`/`median`/`count` per tahap,
  tahap di atas threshold ditandai `is_bottleneck`.
- **F3** — `rework.detect_rework()` (dokumen di-cancel setelah submit) +
  `rework.detect_deviations()` (Invoice tanpa Receipt, dst.).
- **F4** — `api.flow_diagram()` & `api.process_overview()` mengembalikan JSON
  siap-render untuk UI (grafik batang durasi + diagram alur beranotasi).
- **NFR5** — analitik (`bottleneck.py`, `rework.py`) **tidak** mengimpor
  `frappe`/ORM; hanya bergantung pada `adapter.base.ProcessEvent`.
- **NFR4** — skrip idempoten `seed-demo-data.sh` + `run-demo.sh`.
- **§8** — `seed_demo_data.run()`: 200–500 kasus P2P dengan bottleneck &
  rework yang disuntik, dapat di-reset (`reset()`).

## Cara verifikasi (di dalam `bench`)

```sh
# 1. Seed (idempoten) — prasyarat semua analisis
bench --site erpnext.localhost execute smart_erp_ai.scripts.seed_demo_data.run

# 2. F1: event log (harus >= 200 kasus → ribuan baris event)
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.event_log.extract_p2p_events

# 3. F2: bottleneck
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.api.bottlenecks

# 4. F3: rework & deviasi
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.api.rework_cases

# 5. F7: dokumen tertahan (menunggu langkah berikutnya / approval)
bench --site erpnext.localhost execute smart_erp_ai.process_intelligence.api.pending_at_stage
```

Atau lewat helper shell (dari root repo):

```sh
./scripts/seed-demo-data.sh 300      # buat 300 kasus
./scripts/run-demo.sh                # verifikasi F1+F2+F3+F7
./scripts/seed-demo-data.sh reset    # bersihkan batch seed
```

## Uji unit

Logika murni B2/B3 diuji dengan event sintetis, **tanpa butuh ERP hidup**:

```sh
# di site hidup (Frappe test runner)
bench --site erpnext.localhost set-config allow_tests true   # sekali
bench --site erpnext.localhost run-tests --module smart_erp_ai.tests.test_process_intelligence
```

Cakupan: 7 test (transisi bottleneck, peringkat, summary, rework, deviasi, alur
normal). **Status: 7/7 LULUS** — diverifikasi di site hidup.

## Titik integrasi yang diharapkan dari Dev A (A6 — jembatan F7)

Daftarkan fungsi berikut sebagai **tool baru** di `tools/registry.py` (bentuk
return sesuai kontrak §1, tanpa tabel tambahan):

| Tool | Fungsi | Kegunaan |
|---|---|---|
| `get_bottlenecks` | `process_intelligence.api.get_bottlenecks(process, period=None)` | "Di mana bottleneck…?" |
| `get_rework_cases` | `process_intelligence.api.get_rework_cases(process, limit=20)` | "Kasus apa yang menyimpang…?" |
| `get_pending_at_stage` | `process_intelligence.api.get_pending_at_stage(process, stage)` | "Ada N PO tertahan…" (tawaran aksi) |

## Asumsi & catatan

- **Backdating**: Frappe menimpa `creation`/`modified` saat save/submit; generator
  me-backdate pasca-submit via SQL langsung (aman, hanya untuk data seed).
- **Reset seed** memakai `frappe.db.delete` langsung agar tidak memicu efek
  stok/GL — aman karena hanya menyentuh dokumen bertanda seed.
- **Batas kepemilikan file** (`DEV-TASKS` §6) dipatuhi: Dev B hanya menulis di
  `process_intelligence/`, `adapter/`, `scripts/`, plus scaffold app minimal
  yang diperlukan agar modul bisa diimpor di `bench`.
- **Tidak ada patch L1** → `docs/CHANGELOG-L1-PATCHES.md` tetap kosong (ideal).
- **Tidak ada dependensi baru** → `docs/THIRD-PARTY.md` tidak berubah.

## 🐞 Temuan penting (hasil uji di site hidup)

Beberapa temuan yang **wajib diketahui** bila mengembangkan lanjut:

1. **Purchase Order TIDAK punya field `remarks` di ERPNext v16.** Penanda batch
   seed untuk PO memakai field `title` (Data, `allow_on_submit`); PR/PI memakai
   `remarks`. Lihat `_SEED_MARKER_FIELD` di `scripts/seed_demo_data.py`.
   *Pelajaran:* selalu cek field ada sebelum memakai untuk penanda.
2. **Model bottleneck = transisi antar-tahap, bukan durasi dalam satu dokumen.**
   Durasi "dalam dokumen" (created→submitted) ~0 karena backdating; yang bermakna
   adalah **jarak antar tahap** (PO→PR menangkap *approval delay*). Lihat
   `_durations_from_events()` di `process_intelligence/bottleneck.py`.
3. **Frappe menolak *posting date* di masa depan.** Generator menyisakan margin
   (`_random_start`) agar rantai delay maksimum (bottleneck 168j + billing 72j)
   selalu jatuh di masa lalu.
4. **Nama kasus (case_id) P2P di-resolusi lewat baris item, bukan field parent.**
   PI → (item) PR → (item) PO. `_child_link_target()` memindai **semua** baris
   item untuk tautan non-kosong (mencegah salah deteksi deviasi).
5. **Rework butuh urutan submit < cancel yang jelas.** Bila timestamp seri,
   pengurutan bisa menempatkan cancel sebelum submit → rework tidak terdeteksi.
   `_inject_rework()` memberi selisih waktu eksplisit (submit +1j, cancel +3j).

## ⚠️ Catatan lingkungan (bukan kode Dev B)

Saat menjalankan demo pertama kali, ditemukan masalah environment:

- **Submodule `apps/erpnext`/`apps/frappe` pada checkout lokal tidak lengkap**
  (sebagian direktori doctype hanya berisi `__pycache__`), dan **DB site
  tidak sinkron dengan kode** (ada DocType yatim seperti `Company Restriction`).
- **Solusi yang dipakai (satu kali):** `bench --site erpnext.localhost migrate`
  menghapus DocType yatim dan menyelaraskan DB dengan kode 16.50.0.
- **App L2 belum terdaftar di container** (image di-build dari submodule saja).
  **Sudah diperbaiki permanen** — lihat bagian berikut.

## 🐳 Integrasi Docker (sudah dikerjakan)

Agar anggota tim lain bisa setup tanpa langkah manual, `apps/smart_erp_ai`
sekarang **ter-bake ke image** dan **otomatis di-`install-app`** ke site:

| File | Perubahan |
|---|---|
| `docker/Dockerfile` | `COPY apps/smart_erp_ai` + `pip install -e` (buat `.pth`) + daftarkan di `sites/apps.txt` |
| `docker/docker-compose.dev.yml` | Bind-mount `apps/smart_erp_ai/smart_erp_ai` di semua service (backend/workers/watch/frontend) → hot reload L2 |
| `scripts/devcontainer-setup.sh` | `bench new-site … --install-app smart_erp_ai` untuk site baru |
| `scripts/post-up-fix.sh` | Langkah idempoten: pastikan `apps.txt`, `.pth`, dan `install-app` |
| `scripts/smart-erp.sh` | Perintah baru: `seed [N]`, `reseed`, `demo` |
| `README.md` | Dokumentasi layer L1/L2 + alur demo L2 |

Verifikasi: `docker build` sukses; di dalam image, `sites/apps.txt` berisi
`frappe/erpnext/smart_erp_ai` dan `import smart_erp_ai` berhasil. `post-up-fix.sh`
melaporkan ketiga langkah L2 OK saat dijalankan di stack hidup.

> **Cara pakai anggota tim (dari nol):**
> ```sh
> git clone --recurse-submodules <repo> smart-erp && cd smart-erp
> ./scripts/devcontainer-setup.sh     # build image, buat site, install ERPNext + L2
> ./scripts/smart-erp.sh seed         # seed 300 kasus P2P
> ./scripts/smart-erp.sh demo         # F1/F2/F3/F7
> ```
