# Smart ERP

ERPNext pada branch **`version-16`** (rilis stabil, Frappe Framework 16) dengan UI
Vue/frappe-ui, untuk pengembangan kolaboratif dengan **preview web** dan **SSH** di
GitHub Codespaces.

> Pin versi saat ini: **Frappe 16.51.1** + **ERPNext 16.50.0**, cocok dengan base
> image `frappe/erpnext:v16` di `docker/Dockerfile`. Submodule **sengaja** tidak
> memakai `develop` (17-dev/unstable) agar build stabil. Lihat catatan pinning di
> `docker/Dockerfile`.

## Cara pakai (GitHub Codespaces)

1. Push repo ini ke GitHub.
2. Di halaman repo → tombol **Code** → tab **Codespaces** → **Create codespace on main**.
3. Codespace akan otomatis:
   - build image dari source di `apps/frappe` + `apps/erpnext`
   - menyalakan MariaDB + Redis
   - membuat site `erpnext.localhost` dan meng-install ERPNext (hanya saat pertama kali)
4. Setelah selesai, port **8080** akan otomatis terbuka sebagai preview.

**Login default:** `Administrator` / `admin`

> Site & database disimpan di **Docker volume** di dalam Codespace. Karena
> Codespace gratis dihapus setelah idle, data bisa hilang — pakai
> `./scripts/smart-erp.sh backup` bila perlu menyimpan.

## Struktur repo

```
smart-erp/
├── apps/
│   ├── frappe/          # submodule → github.com/frappe/frappe   (branch version-16)
│   ├── erpnext/         # submodule → github.com/frappe/erpnext  (branch version-16)
│   └── smart_erp_ai/    # L2 app MILIK TIM (bukan submodule) — agent + process intelligence
│
├── docker/
│   ├── Dockerfile          # build bench image dari source submodule + apps/smart_erp_ai
│   └── docker-compose.yml  # mariadb, redis, backend, websocket, workers, scheduler, nginx
├── scripts/
│   ├── devcontainer-setup.sh   # dijalankan otomatis oleh Codespaces
│   ├── smart-erp.sh            # helper perintah sehari-hari
│   ├── seed-demo-data.sh       # [L2] seed data dummy P2P
│   └── run-demo.sh             # [L2] jalankan demo analisis F1–F3/F7
└── .devcontainer/devcontainer.json
```

### Layer: L1 vs L2 (penting — baca `docs/AGENT-RULES.md`)

| Layer | Isi | Lisensi | Boleh diedit? |
|---|---|---|---|
| **L1** | `apps/frappe`, `apps/erpnext` (submodule) | GPLv3 | **Tidak** — upstream read-only (RULE 1.2) |
| **L2** | `apps/smart_erp_ai` (kode kami) | milik tim | Ya — di sini semua logika produk |

Karena `frappe` dan `erpnext` adalah **submodule**, kode aplikasi bisa diedit
langsung, dan perubahan tercatat di git. App L2 `smart_erp_ai` adalah direktori
biasa di repo ini (bukan submodule), sehingga perubahan ikut ter-commit biasa. 👥

> Setup otomatis: `apps/smart_erp_ai` **ter-bake ke image** (lihat `docker/Dockerfile`)
> dan otomatis di-`install-app` ke site saat setup / `up` via `scripts/post-up-fix.sh`.
> Tidak ada langkah manual tambahan.

## Setelah clone di luar Codespaces (mesin sendiri)

```sh
git clone --recurse-submodules <repo-url> smart-erp
cd smart-erp
./scripts/devcontainer-setup.sh     # atau: bash scripts/devcontainer-setup.sh
```

Bila sudah terlanjur clone tanpa submodule:

```sh
git submodule update --init --recursive
```

## Perintah sehari-hari

```sh
./scripts/smart-erp.sh up            # nyalakan semua service
./scripts/smart-erp.sh ps            # status service
./scripts/smart-erp.sh logs backend  # lihat log
./scripts/smart-erp.sh down          # matikan (data tetap)
./scripts/smart-erp.sh build         # rebuild image setelah ubah source
./scripts/smart-erp.sh fix           # re-apply grant DB + asset manifest + daftar app L2
./scripts/smart-erp.sh dev           # hot reload (bind-mount source + watcher)
./scripts/smart-erp.sh shell         # masuk bash ke container backend
./scripts/smart-erp.sh bench <args>  # jalankan bench untuk site
./scripts/smart-erp.sh migrate       # migrasi site
./scripts/smart-erp.sh backup        # backup site
```

## Demo analitik L2 (Smart ERP AI)

Setelah stack hidup, siapkan data & jalankan demo dalam dua perintah:

```sh
./scripts/smart-erp.sh seed          # 300 kasus P2P dummy (bottleneck + rework disuntik)
./scripts/smart-erp.sh demo          # F1 event log → F2 bottleneck → F3 rework → F7 pending
```

Perintah lain: `./scripts/smart-erp.sh seed 400`, `./scripts/smart-erp.sh reseed`
(hapus batch seed saja). Detail di `docs/DEV-TASKS.md` & `docs/DEV-B-STATUS.md`.

## Alur kolaborasi

- Setiap orang membuka **Codespace sendiri** dari repo ini (atau berbagi satu
  Codespace untuk pairing).
- Port 8080 di-forward jadi URL publik `https://<codespace>-8080.app.github.dev`
  yang bisa dibuka siapa saja dengan link itu.
- Untuk **SSH** ke Codespace: `gh cs ssh` atau langsung dari terminal VS Code.
- Setelah mengubah kode di `apps/frappe` / `apps/erpnext`:

  ```sh
  ./scripts/smart-erp.sh build
  ./scripts/smart-erp.sh up -d
  ```

  Untuk perubahan Python saja, cukup restart service terkait:
  `docker compose -f docker/docker-compose.yml restart backend`

- Setelah mengubah kode **L2** (`apps/smart_erp_ai`): pakai mode dev
  (`./scripts/smart-erp.sh dev`) yang me-bind-mount `apps/smart_erp_ai/smart_erp_ai`,
  sehingga perubahan Python langsung ter-reload oleh gunicorn tanpa rebuild.

## Hot reload (mode dev)

Default stack **tidak** hot reload karena source di-bake ke image (lihat catatan
di `docker/docker-compose.yml`). Untuk pengembangan yang butuh live edit,
ada overlay terpisah `docker/docker-compose.dev.yml` yang **tidak mengubah**
alur default:

```sh
./scripts/smart-erp.sh dev        # nyalakan dengan hot reload
./scripts/smart-erp.sh dev-logs   # lihat log watcher esbuild
./scripts/smart-erp.sh dev-down   # matikan
```

Apa yang aktif:

- **L2 `apps/smart_erp_ai`** (kode produk kami): source Python di-bind-mount;
  edit `apps/smart_erp_ai/smart_erp_ai/**/*.py`, gunicorn (`--reload`) langsung
  memuat ulang. Tidak perlu rebuild.

- **Frontend (JS/CSS):** source `apps/*/public/**` di-bind-mount. Edit file
  `.bundle.js` / `.bundle.scss`, service `watch` (esbuild) otomatis
  meng-compile ulang, lalu **refresh browser**. `developer_mode` membuat Frappe
  membaca `assets.json` segar tanpa cache.
- **Backend (Python):** edit `apps/**/*.py`, gunicorn (`--reload`) otomatis
  me-restart worker. Tidak perlu perintah apa pun.

Catatan penting:

- Frappe **tidak** punya HMR seperti Vite; perubahan frontend butuh refresh
  browser (opsi `LIVE_RELOAD=1` sudah aktif untuk auto-reload Desk).
- Bind-mount hanya subpath sumber (`frappe/frappe`, `erpnext/erpnext`, tooling
  esbuild). `node_modules` tetap dari image agar tidak ter-shadow.
- Hasil build `public/dist` ditulis ke checkout Anda, tapi sudah ada di
  `.gitignore` upstream sehingga tidak mengotori git.
- Kembali ke mode default: `./scripts/smart-erp.sh dev-down` lalu
  `./scripts/smart-erp.sh up`.

## Troubleshooting

| Gejala | Sebab | Solusi |
|--------|-------|--------|
| **502 Bad Gateway** | nginx menyimpan cache DNS upstream setelah backend restart | `docker compose -f docker/docker-compose.yml restart frontend` |
| **500 Access denied for user** | user DB ter-grant ke IP container lama | `./scripts/smart-erp.sh fix` |
| **CSS/layout rusak (asset 404)** | `sites/assets/assets.json` stale vs bundle hasil rebuild | `./scripts/smart-erp.sh fix` |
| Build lama / kehabisan disk | image ERPNext besar | `docker system prune -a` |

### Dua masalah yang umum: 500 & asset 404

Keduanya otomatis diperbaiki oleh **`scripts/post-up-fix.sh`**, dipanggil oleh
`devcontainer-setup.sh` saat setup device baru dan oleh `./scripts/smart-erp.sh up`.
Bila perlu menjalankan manual: `./scripts/smart-erp.sh fix`.

Skrip itu idempoten dan melakukan:

1. **Grant ulang DB user dengan host `%`** — Frappe membuat user DB terikat ke
   IP container saat `bench new-site`. Docker memberi IP baru setiap `up`,
   sehingga muncul `Access denied for user '<db_user>'@'<ip-baru>'`. Skrip
   membuat ulang user `<db_user>'@'%'` dengan password dari
   `sites/<site>/site_config.json`.
2. **Regenerate manifest asset** (`bench build --using-cached`) — setelah image
   di-rebuild, nama bundle ber-hash berubah tetapi `assets.json` bisa masih
   menunjuk nama lama → CSS/JS 404 sehingga layout rusak.

Setelah kode di `apps/frappe` / `apps/erpnext` diubah dan di-rebuild
(`./scripts/smart-erp.sh build && ./scripts/smart-erp.sh up -d`), langkah 2
sudah otomatis tercakup.

## Catatan penting

- **Kuota Codespaces gratis**: 120 core-hour/bulan. Codespace 4-core akan
  menghabiskan kuota dalam ~30 jam aktif. Matikan saat tidak dipakai.
- **Data hilang saat Codespace dihapus** (free tier). Backup jika perlu.
- Untuk server **staging permanen gratis**, kombinasi terbaik adalah
  Oracle Cloud "Always Free" (VM ARM 4 CPU/24 GB). Codespaces untuk dev
  kolaboratif, Oracle untuk yang online terus.
