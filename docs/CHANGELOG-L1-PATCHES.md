# CHANGELOG-L1-PATCHES.md — Catatan Perubahan pada Layer L1 (ERPNext/Frappe)

> Dirujuk oleh `docs/AGENT-RULES.md` (RULE 1.5, RULE 3.6).
>
> **Prinsip:** perubahan pada L1 (`apps/frappe`, `apps/erpnext`) harus **seminimal mungkin**.
> Setiap patch wajib dicatat di sini agar:
> - batas IP tetap jelas (file yang dipatch tetap GPLv3 dan tidak boleh diklaim sebagai karya kami),
> - patch dapat di-apply ulang saat upstream diperbarui / submodule di-bump,
> - tidak ada patch yang hilang diam-diam.

## Format pencatatan

| Tanggal | File L1 | Alasan | Cara apply ulang | Terkait |
|---|---|---|---|---|
| _(belum ada patch — idealnya tetap kosong)_ | | | | |

## Alternatif yang wajib dipertimbangkan sebelum patch L1

Sebelum menambahkan patch di sini, pastikan tidak ada jalur L2 yang lebih bersih:

1. **Warna/tema** → gunakan `Theme` DocType / `app_include_css` dari `apps/smart_erp_ai` (RULE 4.3).
2. **Override perilaku** → gunakan `overrides/` di app kami via `hooks.py` (RULE 1.3).
3. **Branding user-facing** → gunakan konfigurasi/theme, bukan mengedit template L1.
4. **Ekstensi DocType** → gunakan Custom Field / Customize Form, bukan mengedit JSON L1.

Jika patch L1 tetap diperlukan, catat di tabel dan jelaskan mengapa opsi 1–4 tidak memadai.
