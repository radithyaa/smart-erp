# Smart ERP

ERPNext pada branch **`develop`** (Frappe Framework develop) dengan UI Vue/frappe-ui,
untuk pengembangan kolaboratif dengan **preview web** dan **SSH** di GitHub Codespaces.

> Versi branch `develop` saat ini terbaca sebagai **17.0.0-dev** (unstable).
> Bila ingin yang stabil, pin submodule ke branch `version-16`/`version-15`.

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
│   ├── frappe/      # submodule → github.com/frappe/frappe   (branch develop)
│   └── erpnext/     # submodule → github.com/frappe/erpnext  (branch develop)
├── docker/
│   ├── Dockerfile          # build bench image dari source submodule
│   └── docker-compose.yml  # mariadb, redis, backend, websocket, workers, scheduler, nginx
├── scripts/
│   ├── devcontainer-setup.sh   # dijalankan otomatis oleh Codespaces
│   └── smart-erp.sh            # helper perintah sehari-hari
└── .devcontainer/devcontainer.json
```

Karena `frappe` dan `erpnext` adalah **submodule**, kode aplikasi bisa diedit
langsung, dan perubahan tercatat di git. 👥

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
./scripts/smart-erp.sh shell         # masuk bash ke container backend
./scripts/smart-erp.sh bench <args>  # jalankan bench untuk site
./scripts/smart-erp.sh migrate       # migrasi site
./scripts/smart-erp.sh backup        # backup site
```

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

## Troubleshooting

| Gejala | Sebab | Solusi |
|--------|-------|--------|
| **502 Bad Gateway** | nginx menyimpan cache DNS upstream setelah backend restart | `docker compose -f docker/docker-compose.yml restart frontend` |
| **500 Access denied for user** | user DB ter-grant ke IP container lama | lihat bagian bawah |
| Build lama / kehabisan disk | image ERPNext besar | `docker system prune -a` |

Perbaikan *Access denied*: user database dibuat dengan host IP tertentu. Buat
ulang dengan host `%` dan password yang sama seperti di
`sites/erpnext.localhost/site_config.json`:

```sh
docker compose -f docker/docker-compose.yml exec mariadb \
  mariadb -uroot -padmin -e "
    CREATE USER IF NOT EXISTS '<db_user>'@'%' IDENTIFIED BY '<db_password>';
    GRANT ALL PRIVILEGES ON \`<db_name>\`.* TO '<db_user>'@'%';
    FLUSH PRIVILEGES;"
```

## Catatan penting

- **Kuota Codespaces gratis**: 120 core-hour/bulan. Codespace 4-core akan
  menghabiskan kuota dalam ~30 jam aktif. Matikan saat tidak dipakai.
- **Data hilang saat Codespace dihapus** (free tier). Backup jika perlu.
- Untuk server **staging permanen gratis**, kombinasi terbaik adalah
  Oracle Cloud "Always Free" (VM ARM 4 CPU/24 GB). Codespaces untuk dev
  kolaboratif, Oracle untuk yang online terus.
