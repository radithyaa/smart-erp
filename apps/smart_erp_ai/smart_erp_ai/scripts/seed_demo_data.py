"""B4 — Generator Data Dummy P2P (SRS §8) — **kerjakan paling dulu**.

Membuat 200–500 kasus Purchase-to-Pay realistis di ERPNext dengan:

  * variasi **delay terkontrol** antar tahap, sebagian sengaja **tertahan di
    approval** → memunculkan *bottleneck* yang bisa dideteksi F2;
  * beberapa kasus **rework** (PO di-cancel setelah submit lalu dibuat ulang)
    → bahan F3;
  * **backdating** timestamp agar sebaran waktu terlihat seperti berbulan-bulan
    riwayat (lihat riset: creation/modified harus di-backdate pasca-submit via
    SQL langsung).

Sifat:
  * **Idempoten** — diberi ``tag`` khusus pada ``remarks``; menjalankan ulang
    akan **menghapus** batch lama lalu membuat baru (NFR4). ``reset()`` untuk
    membersihkan tanpa membuat.
  * Aman diulang pra-demo.

Pemakaian (dalam ``bench``)::

    bench --site erpnext.localhost execute smart_erp_ai.scripts.seed_demo_data.run
    bench --site erpnext.localhost execute smart_erp_ai.scripts.seed_demo_data.reset

Modul ini menulis dokumen lewat **ORM ERPNext (L1) sebagai service** — bukan
menyalin kode L1 ke L2. Tidak ada perubahan file L1 (RULE 1.2).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import frappe
from frappe.utils import get_datetime, now_datetime

#: Penanda batch agar mudah di-reset (idempoten).
SEED_TAG = "[SMART_ERP_SEED]"

#: Rentang jumlah kasus sesuai SRS §8.
DEFAULT_CASES = 300
MIN_CASES = 200
MAX_CASES = 500

#: Jumlah hari ke belakang sebagai rentang riwayat data.
HISTORY_DAYS = 120

#: Nama-nama item & supplier dummy yang dibuat bila belum ada.
DUMMY_ITEMS = [f"SEED-ITEM-{i:03d}" for i in range(1, 11)]
DUMMY_SUPPLIERS = [f"SEED-VENDOR-{i:02d}" for i in range(1, 9)]


# ---------------------------------------------------------------------------
# Master data helpers
# ---------------------------------------------------------------------------


def _default_company() -> str:
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if not company:
		companies = frappe.get_all("Company", pluck="name", limit=1)
		company = companies[0] if companies else None
	if not company:
		frappe.throw("Tidak ada Company. Jalankan setup site/ERPNext dulu.")
	return company


def _default_warehouse(company: str) -> str:
	warehouse = frappe.db.get_value("Company", company, "default_warehouse")
	if not warehouse:
		warehouses = frappe.get_all(
			"Warehouse", filters={"company": company, "is_group": 0}, pluck="name", limit=1
		)
		warehouse = warehouses[0] if warehouses else None
	if not warehouse:
		frappe.throw(f"Tidak ada Warehouse untuk company {company}.")
	return warehouse


def _ensure_suppliers() -> list[str]:
	group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"
	made: list[str] = []
	for name in DUMMY_SUPPLIERS:
		if frappe.db.exists("Supplier", name):
			made.append(name)
			continue
		supplier = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": name,
				"supplier_group": group,
			}
		)
		supplier.insert(ignore_permissions=True)
		made.append(supplier.name)
	return made


def _ensure_items(default_company: str) -> list[str]:
	uom = frappe.db.get_value("UOM", {"name": "Nos"}, "name") or frappe.db.get_value(
		"UOM", {}, "name"
	)
	made: list[str] = []
	for code in DUMMY_ITEMS:
		if frappe.db.exists("Item", code):
			made.append(code)
			continue
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code.replace("-", " ").title(),
				"item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name")
				or "All Item Groups",
				"stock_uom": uom,
				"is_stock_item": 1,
				"is_purchase_item": 1,
			}
		)
		item.insert(ignore_permissions=True)
		made.append(item.name)
	return made


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def _random_start(rng: random.Random) -> datetime:
	"""Waktu mulai acak dalam rentang HISTORY_DAYS terakhir.

	Disisakan margin ``SAFETY_MARGIN_DAYS`` dari sekarang agar rantai delay
	maksimum (bottleneck 168 jam + billing 72 jam) tidak pernah menghasilkan
	tanggal di masa depan (ERPNext menolak posting date > hari ini).
	"""
	latest_offset_days = 168 / 24 + 72 / 24 + 2  # bottleneck + billing + margin
	days_ago = rng.uniform(latest_offset_days, HISTORY_DAYS)
	return now_datetime() - timedelta(days=days_ago)


def _ts(value: datetime) -> str:
	return value.strftime("%Y-%m-%d %H:%M:%S")


def _posting_date(value: datetime) -> str:
	return value.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Backdating (pasca-submit) — lihat riset: creation/modified di-overwrite Frappe
# ---------------------------------------------------------------------------


def _backdate(doctype: str, name: str, when: datetime, owner: str) -> None:
	"""Backdate ``creation``/``modified``/owner sebuah dokumen + baris child.

	Harus dipanggil **setelah** submit, karena Frappe menimpa timestamp audit
	saat setiap save/submit (frappe/model/document.py:594).
	"""
	stamp = _ts(when)
	frappe.db.sql(
		f"UPDATE `tab{doctype}` SET creation=%s, modified=%s, owner=%s, modified_by=%s WHERE name=%s",
		(stamp, stamp, owner, owner, name),
	)
	child = f"{doctype} Item"
	if frappe.db.exists("DocType", child):
		frappe.db.sql(
			f"UPDATE `tab{child}` SET creation=%s, modified=%s, owner=%s, modified_by=%s WHERE parent=%s",
			(stamp, stamp, owner, owner, name),
		)


def _backdate_versions(doctype: str, name: str, when: datetime, owner: str) -> None:
	"""Selaraskan timestamp ``Version`` dengan waktu dokumen (untuk event log).

	Version diberi timestamp menaik (berdasarkan urutan ``creation`` aslinya)
	mulai dari ``when``, supaya urutan transisi (draft→submit→cancel) tetap
	konsisten dan tidak sekaligus sama (yang akan mengacaukan deteksi rework).
	"""
	rows = frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": name},
		fields=["name"],
		order_by="creation asc",
		limit_page_length=0,
	)
	for idx, row in enumerate(rows):
		stamp = _ts(when + timedelta(minutes=idx))
		frappe.db.sql(
			"UPDATE `tabVersion` SET creation=%s, modified=%s, owner=%s, modified_by=%s WHERE name=%s",
			(stamp, stamp, owner, owner, row["name"]),
		)


# ---------------------------------------------------------------------------
# Pembuatan satu kasus P2P
# ---------------------------------------------------------------------------


def _create_purchase_order(company, warehouse, supplier, item_code, qty, rate, when, owner):
	"""Buat + submit Purchase Order pada waktu tertentu, lalu backdate."""
	po = frappe.new_doc("Purchase Order")
	po.update(
		{
			"supplier": supplier,
			"company": company,
			"transaction_date": _posting_date(when),
			"schedule_date": _posting_date(when + timedelta(days=7)),
			# Catatan: Purchase Order TIDAK punya field `remarks` di ERPNext v16,
			# jadi penanda batch dipakai field `title` (Data, allow_on_submit).
			"title": SEED_TAG,
		}
	)
	po.append(
		"items",
		{
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"schedule_date": _posting_date(when + timedelta(days=7)),
			"warehouse": warehouse,
		},
	)
	po.flags.ignore_permissions = True
	po.insert(ignore_permissions=True)
	po.submit()
	_backdate("Purchase Order", po.name, when, owner)
	_backdate_versions("Purchase Order", po.name, when, owner)
	return po


def _create_purchase_receipt(company, warehouse, supplier, po, item_code, qty, rate, when, owner):
	"""Buat + submit Purchase Receipt yang tertaut ke PO, lalu backdate."""
	po_item = frappe.db.get_value(
		"Purchase Order Item", {"parent": po.name, "item_code": item_code}, "name"
	)
	pr = frappe.new_doc("Purchase Receipt")
	pr.update(
		{
			"supplier": supplier,
			"company": company,
			"posting_date": _posting_date(when),
			"posting_time": when.strftime("%H:%M:%S"),
			"set_posting_time": 1,
			"remarks": SEED_TAG,
		}
	)
	pr.append(
		"items",
		{
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"warehouse": warehouse,
			"purchase_order": po.name,
			"purchase_order_item": po_item,
		},
	)
	pr.flags.ignore_permissions = True
	pr.insert(ignore_permissions=True)
	pr.submit()
	_backdate("Purchase Receipt", pr.name, when, owner)
	_backdate_versions("Purchase Receipt", pr.name, when, owner)
	return pr


def _create_purchase_invoice(company, supplier, pr, po, item_code, qty, rate, when, owner):
	"""Buat + submit Purchase Invoice yang tertaut ke PR/PO, lalu backdate."""
	pr_item = frappe.db.get_value(
		"Purchase Receipt Item", {"parent": pr.name, "item_code": item_code}, "name"
	)
	pi = frappe.new_doc("Purchase Invoice")
	pi.update(
		{
			"supplier": supplier,
			"company": company,
			"posting_date": _posting_date(when),
			"set_posting_time": 1,
			"bill_no": f"SEED-BILL-{when.strftime('%Y%m%d%H%M%S')}",
			"bill_date": _posting_date(when),
			"remarks": SEED_TAG,
		}
	)
	pi.append(
		"items",
		{
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"purchase_receipt": pr.name,
			"purchase_receipt_item": pr_item,
			"purchase_order": po.name,
		},
	)
	pi.flags.ignore_permissions = True
	pi.insert(ignore_permissions=True)
	pi.submit()
	_backdate("Purchase Invoice", pi.name, when, owner)
	_backdate_versions("Purchase Invoice", pi.name, when, owner)
	return pi


def _inject_rework(po, item_code, qty, rate, when, owner):
	"""Rework: batalkan PO lama setelah di-submit (bahan F3).

	Ini data seed (milik Dev B), sehingga `cancel()` di sini sah — bukan aksi
	agen/F8. Garis waktu dibuat berbeda dari submit agar `purchase_order_cancelled`
	muncul **setelah** `purchase_order_submitted` (syarat deteksi rework):

	  * ``creation`` = ketika
	  * ``modified`` (submit/cancel) = ketika + 3 jam
	"""
	try:
		po.reload()
		po.cancel()
		cancel_when = when + timedelta(hours=3)
		stamp = _ts(cancel_when)
		frappe.db.sql(
			"UPDATE `tabPurchase Order` SET creation=%s, modified=%s, owner=%s, modified_by=%s "
			"WHERE name=%s",
			(_ts(when), stamp, owner, owner, po.name),
		)
		# Version: submit lebih dulu (when + 1 jam), cancel kemudian (when + 3 jam),
		# agar urutan submit < cancel jelas dan tidak seri timestamp.
		_backdate_versions("Purchase Order", po.name, when + timedelta(hours=1), owner)
	except Exception:  # pragma: no cover - data seed toleran kegagalan
		frappe.clear_last_message()
		frappe.db.rollback()


# ---------------------------------------------------------------------------
# Orkestrasi
# ---------------------------------------------------------------------------


#: Field penanda batch per DocType (Purchase Order tidak punya `remarks`).
_SEED_MARKER_FIELD = {
	"Purchase Order": "title",
	"Purchase Receipt": "remarks",
	"Purchase Invoice": "remarks",
}


def _wipe_batch() -> int:
	"""Hapus semua dokumen batch seed (idempoten). Urut: PI → PR → PO.

	Menggunakan SQL langsung agar tidak memicu efek stok/GL saat reset.
	"""
	removed = 0
	for doctype in ("Purchase Invoice", "Purchase Receipt", "Purchase Order"):
		field = _SEED_MARKER_FIELD[doctype]
		names = frappe.get_all(doctype, filters={field: SEED_TAG}, pluck="name", limit_page_length=0)
		for name in names:
			frappe.db.delete(f"{doctype} Item", {"parent": name})
			frappe.db.delete(doctype, {"name": name})
			frappe.db.delete("Version", {"ref_doctype": doctype, "docname": name})
			removed += 1
	return removed


def run(
	cases: int = DEFAULT_CASES,
	seed: int = 42,
	rework_ratio: float = 0.08,
	bottleneck_ratio: float = 0.25,
	wipe: bool = True,
) -> dict:
	"""Seed kasus P2P idempoten (SRS §8).

	:param cases: jumlah kasus P2P (diklem ke 200–500).
	:param seed: seed RNG agar reproducible.
	:param rework_ratio: proporsi kasus yang disuntik rework.
	:param bottleneck_ratio: proporsi kasus dengan approval lambat (bottleneck).
	:param wipe: hapus batch lama lebih dulu (idempoten).
	:return: ringkasan ``{created, rework, bottleneck, cases}``.
	"""
	cases = max(MIN_CASES, min(MAX_CASES, int(cases)))
	rng = random.Random(seed)

	company = _default_company()
	warehouse = _default_warehouse(company)
	suppliers = _ensure_suppliers()
	items = _ensure_items(company)
	owner = "Administrator"

	removed = _wipe_batch() if wipe else 0

	created = rework_count = bottleneck_count = 0
	failed = 0
	first_error: str | None = None
	for index in range(cases):
		try:
			start = _random_start(rng)
			supplier = rng.choice(suppliers)
			item_code = rng.choice(items)
			qty = rng.randint(1, 50)
			rate = round(rng.uniform(5, 250), 2)

			is_bottleneck = rng.random() < bottleneck_ratio
			is_rework = rng.random() < rework_ratio

			# PO → (approval delay) → PR → (billing delay) → PI
			po_when = start
			# Delay approval: normal 0.5–3 jam; bottleneck 48–168 jam (2–7 hari).
			approval_hours = rng.uniform(48, 168) if is_bottleneck else rng.uniform(0.5, 3)
			pr_when = po_when + timedelta(hours=approval_hours)
			billing_hours = rng.uniform(2, 72)
			pi_when = pr_when + timedelta(hours=billing_hours)

			po = _create_purchase_order(
				company, warehouse, supplier, item_code, qty, rate, po_when, owner
			)
			if is_rework:
				_inject_rework(po, item_code, qty, rate, po_when, owner)
				# Buat PO pengganti di hari yang sama dengan PO awal, agar PR
				# (yang tanggalnya setelah po_when) tetap >= tanggal PO pengganti.
				po = _create_purchase_order(
					company,
					warehouse,
					supplier,
					item_code,
					qty,
					rate,
					po_when,
					owner,
				)
				rework_count += 1
				# Pastikan PR tidak mendahului PO pengganti.
				if pr_when < po_when:
					pr_when = po_when + timedelta(hours=1)
					pi_when = pr_when + timedelta(hours=billing_hours)

			pr = _create_purchase_receipt(
				company, warehouse, supplier, po, item_code, qty, rate, pr_when, owner
			)
			_create_purchase_invoice(company, supplier, pr, po, item_code, qty, rate, pi_when, owner)

			# Commit per kasus agar kegagalan berikutnya tidak membatalkan
			# kasus yang sudah sukses (mencegah rollback global).
			frappe.db.commit()
			created += 1
			if is_bottleneck:
				bottleneck_count += 1
		except Exception as exc:
			frappe.clear_last_message()
			frappe.db.rollback()
			failed += 1
			if first_error is None:
				first_error = f"{type(exc).__name__}: {exc}"

	summary = {
		"cases": created,
		"failed": failed,
		"first_error": first_error,
		"rework": rework_count,
		"bottleneck": bottleneck_count,
		"removed_previous": removed,
		"company": company,
		"warehouse": warehouse,
	}
	print(f"[seed_demo_data] selesai: {summary}")
	return summary


def reset() -> dict:
	"""Hapus seluruh batch seed tanpa membuat baru (NFR4)."""
	removed = _wipe_batch()
	frappe.db.commit()
	print(f"[seed_demo_data] reset: {removed} dokumen dihapus")
	return {"removed": removed}
