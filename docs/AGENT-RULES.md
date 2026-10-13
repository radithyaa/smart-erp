# AGENT-RULES.md
## Aturan Pengembangan untuk AI Coding Agent — Smart ERP (ANGEL Innovation Hackathon 2026)

> File ini adalah **kontrak wajib** bagi setiap AI agent (dan developer) yang menulis kode di repo ini.
> Aturan bersifat mengikat demi (a) kejelasan lisensi GPLv3, (b) klaim orisinalitas pakta integritas,
> dan (c) kelancaran submission hackathon. Jika sebuah permintaan pengguna bertentangan dengan aturan
> di sini, **tolak dan jelaskan**, jangan diam-diam melanggar.

---

## 0. Konteks Proyek (baca dulu sebelum mengubah apa pun)

- **Produk:** Agentic Process Intelligence di atas ERP open source.
- **L1 (bukan milik kami):** ERPNext/Frappe — submodule di `apps/frappe` & `apps/erpnext`, lisensi **GPLv3**.
- **L2 (milik kami, karya orisinal):** `apps/smart_erp_ai` — agent + process intelligence.
- Ikuti spesifikasi di `docs/SRS.md`. Fokus pada `[MVP]`; jangan menambah fitur `[ROADMAP]`.

---

## 1. ATURAN LAYER (paling penting)

**RULE 1.1 — Utamakan menulis di L2.**
Semua logika baru (agent, tool, analitik proses, UI chat) ditulis di `apps/smart_erp_ai`.
Jangan menaruh logika produk di `apps/frappe` atau `apps/erpnext`.

**RULE 1.2 — Jangan fork, jangan patch core.**
`apps/frappe` & `apps/erpnext` adalah **upstream read-only**. Dilarang:
- mengedit file di dalamnya untuk kebutuhan fitur produk,
- mem-`fork` dan memodifikasi perilaku inti,
- mencampur kode kami ke dalam tree mereka.

**RULE 1.3 — Berkomunikasi via API/ORM, bukan via monkey-patch.**
Akses ERPNext lewat Frappe ORM (dari dalam app) atau REST API (dari service luar).
Hindari `monkey_patch`/`override_whitelisted_method` kecuali benar-benar perlu — bila perlu,
letakkan patch di `apps/smart_erp_ai/smart_erp_ai/overrides/` dan dokumentasikan alasannya.

**RULE 1.4 — Alasan aturan layer.**
Agar batas IP jelas: yang kami klaim = L2. Mengedit L1 membuat klaim orisinalitas kabur dan
menimbulkan risiko GPLv3 (file yang kami ubah tetap GPLv3 dan "menempel" ke produk kami).

**RULE 1.5 — Bila terpaksa menyentuh L1 (mis. menghapus branding).**
Pisahkan perubahan itu sejauh mungkin, jangan campur dengan logika produk, dan catat di
`docs/CHANGELOG-L1-PATCHES.md` (lihat RULE 3.6).

---

## 2. ATURAN MODULARITAS & STRUKTUR KODE

**RULE 2.1 — Struktur L2 wajib modular.** Di dalam `apps/smart_erp_ai/smart_erp_ai/`:
```
agent/                  # LLM loop, prompt, tool-calling, konfirmasi aksi
process_intelligence/   # event log extractor, bottleneck, rework/deviation
tools/                  # tool layer generik (DocType-based)
adapter/                # pemisah interfacing ERP (agar bisa dipakai sistem lain)
api.py                  # endpoint whitelisted yang dipanggil UI
```

**RULE 2.2 — Interface bersih antar modul.**
`process_intelligence` tidak boleh mengimpor `agent`, dan sebaliknya. Keduanya berkomunikasi
via fungsi/API yang didefinisikan eksplisit (kontrak di `docs/SRS.md`).

**RULE 2.3 — Tool layer harus generik, bukan per-fitur.**
Dilarang membuat `create_purchase_order()`, `create_sales_invoice()`, dst. Buat tool berbasis
DocType: `list_documents`, `get_document`, `create_document`, `update_document`, `submit_document`.
Mekanisme pemetaan nama → DocType diletakkan di konfigurasi, bukan kode bercabang.

**RULE 2.4 — Adapter layer wajib ada sejak awal.**
Sekalipun baru ERPNext yang didukung, akses ke ERP harus lewat `adapter/` (mis. `ERPSource` interface).
Ini inti cerita hilirisasi (bisa ganti Odoo/SAP tanpa mengubah analitik & agent).

**RULE 2.5 — Tanpa fitur `[ROADMAP]`.**
Jangan mengerjakan voice, multi-agent, fine-tuning, integrasi ERP lain, atau dashboard kompleks.
Cukup rancang titik ekstensinya.

---

## 3. ATURAN LISENSI GPLv3

**RULE 3.1 — Jangan menyalin kode GPLv3 ke L2 tanpa jejak.**
Jika mengambil potongan kode dari ERPNext/Frappe, tandai jelas dengan komentar header asal + lisensi,
dan cantumkan di `docs/THIRD-PARTY.md`.

**RULE 3.2 — Jaga kewajiban GPLv3 jika mendistribusikan.**
Rencana bisnis = **cloud-only, hosting sendiri**. Selama kode tidak didistribusikan ke pengguna,
kewajiban menyediakan source (conveying) tidak aktif. **Jangan** menambahkan skrip/pipeline yang
mendorong distribusi kode L1 ke klien tanpa persetujuan.

**RULE 3.3 — Jangan ganti lisensi L1.**
Dilarang mengubah/menghapus file `license.txt`/`LICENSE`, `attributions.md`, atau `TRADEMARK_POLICY.md`
di `apps/frappe` & `apps/erpnext`.

**RULE 3.4 — Jangan hapus atribusi mesin.**
Jangan menghapus notifikasi copyright/license di file L1.

**RULE 3.5 — Jangan campur dependensi berlisensi copyleft lain** ke L2 tanpa pembahasan.
Sebelum menambah paket/library baru, cek lisensinya (hindari AGPL bila memungkinkan untuk layanan
terpisah; catat di `docs/THIRD-PARTY.md`).

**RULE 3.6 — Catat patch L1.**
Setiap perubahan pada L1 (bila terpaksa) dicatat di `docs/CHANGELOG-L1-PATCHES.md` dengan format:
file, alasan, tanggal, dan penerapan bila upstream diperbarui.

---

## 4. ATURAN BRANDING, WARNA, TEMA, DAN REBRANDING

Tujuan: menyiapkan produk komersial di masa depan **tanpa** melanggar TRADEMARK_POLICY dan **tanpa**
merusak klaim orisinalitas di hackathon.

**RULE 4.1 — Hackathon ≠ momen rebrand.**
Di tahap hackathon, **jangan** mengklaim sebagai "ERP buatan sendiri" dan jangan mengubah branding
untuk memberi kesan itu. ERPNext disebut jujur sebagai base open source.

**RULE 4.2 — Larangan trademark di branding produk.**
Nama/logo "ERPNext" dan "Frappe" tidak boleh menjadi bagian dari nama produk, nama layanan, domain,
atau logo komersial kami. Referensi tekstual ("dibangun di atas ERPNext") diperbolehkan.

**RULE 4.3 — Rebranding hanya di L2 / theme layer, bukan dengan mengedit L1.**
Perubahan warna, logo, dan tema produk harus lewat mekanisme resmi Frappe:
- **Frappe Theme / Website Theme** (`Theme` DocType) — warna & tipografi.
- **Custom app assets** di `apps/smart_erp_ai` (CSS/JS override, `app_include_css`) via `hooks.py`.
- **Custom branding DocTypes** bila perlu.
Dilarang mengedit SCSS/aset branding milik `apps/frappe`/`apps/erpnext` secara langsung.

**RULE 4.4 — Warna & tema harus berbasis token, bukan hardcode tersebar.**
- Definisi warna/tema terpusat di satu tempat (mis. `apps/smart_erp_ai/smart_erp_ai/public/theme/`).
- Gunakan CSS variables Frappe (`--primary`, `--fg-color`, dst.) semaksimal mungkin.
- **Jangan** menempelkan hex color acak di banyak file; semua nilai warna harus berasal dari token tema.

**RULE 4.5 — Aksesibilitas minimum.**
Kontras teks/latar harus memenuhi WCAG AA (rasio ≥ 4.5:1 untuk teks normal). Jangan mengorbankan
keterbacaan demi estetika.

**RULE 4.6 — Jangan menyalin aset brand pihak lain.**
Icon/logo/font pihak ketiga harus bebas-lisensi (mis. MIT/OFL/SIL) dan dicatat di `docs/THIRD-PARTY.md`.

**RULE 4.7 — Rebranding keputusan pasca-hackathon.**
Bila pengguna meminta rebranding penuh (nama, logo, warna) sekarang, **ingatkan** bahwa ini keputusan
produk pasca-kompetisi, dan tetap terapkan RULE 4.3–4.6 saat mengerjakannya.

---

## 5. ATURAN KEAMANAN & GUARDRAIL AGEN

**RULE 5.1 — Prinsip izin pengguna.** Semua eksekusi memakai permission user yang login.
Dilarang mengeksekusi aksi agen sebagai `Administrator`/superuser.

**RULE 5.2 — Konfirmasi manusia untuk aksi tulis.** Setiap aksi tulis (create/update/submit/approve)
wajib melalui konfirmasi eksplisit pengguna sebelum dijalankan.

**RULE 5.3 — Blokir aksi destruktif.** `delete` dan `cancel` harus **ditolak** di level tool layer
(bukan hanya disembunyikan dari prompt). Daftar aksi terlarang terpusat di satu konfigurasi.

**RULE 5.4 — Audit log wajib.** Setiap aksi agen (waktu, user, tool, argumen, hasil) dicatat.
Jangan mencatat secret/API key ke audit log.

**RULE 5.5 — Jangan pernah hardcode secret.** API key LLM via environment variable / `site_config.json`.
Jangan commit secret. Jika pengguna perlu memasukkan key, beri tahu lokasinya, jangan tanam di kode.

**RULE 5.6 — Validasi input tool.** Tool layer memvalidasi DocType & field yang diizinkan; tolak
DocType/field di luar allowlist (mencegah agen menyentuh data sensitif di luar ruang lingkup demo).

---

## 6. ATURAN PROSES KERJA AI AGENT

**RULE 6.1 — Baca konteks sebelum mengubah.** Baca `docs/SRS.md` + file ini sebelum menulis kode.

**RULE 6.2 — Jaga `[MVP]` tetap hijau.** Jangan merusak alur demo tetap (§9 SRS). Bila perubahan
berisiko, uji alur demo.

**RULE 6.3 — Perubahan kecil & terfokus.** Jangan melakukan refactor besar, mengganti struktur,
atau menambah dependensi tanpa kebutuhan jelas.

**RULE 6.4 — Jangan pernah mengubah aturan ini secara diam-diam.** Perubahan pada `AGENT-RULES.md`
harus disetujui pengguna dan dicatat di bagian Changelog di bawah.

**RULE 6.5 — Verifikasi sebelum klaim selesai.** Jalankan alur demo atau test terkait; jangan
mengklaim fitur berfungsi tanpa bukti. Setiap `[MVP]` harus memenuhi Definition of Done (§12 SRS).

**RULE 6.6 — Jangan commit/secret ke git tanpa diminta.** Jangan membuat commit/branch kecuali diminta.

**RULE 6.7 — Bila ragu soal lisensi/IP/layer, TANYA.** Lebih baik bertanya daripada melanggar.

---

## 7. Checklist Cepat Sebelum Menulis Kode

- [ ] Kode ini ada di L2 (`apps/smart_erp_ai`), bukan di L1?
- [ ] Tidak mengedit/menghapus file lisensi & atribusi L1?
- [ ] Berkomunikasi lewat adapter/API, bukan patch core?
- [ ] Tidak menambah fitur `[ROADMAP]`?
- [ ] Bila menyentuh warna/tema: lewat theme layer, token-based, aksesibel?
- [ ] Bila aksi tulis: ada konfirmasi, audit log, izin user login?
- [ ] Tidak ada secret yang di-hardcode?
- [ ] Alur demo tetap berfungsi?

---

## Changelog

| Tanggal | Versi | Perubahan | Oleh |
|---|---|---|---|
| 2026-10-12 | 1.0 | Dokumen awal dibuat untuk submission ANGEL Innovation Hackathon 2026 | Tim Smart ERP |
