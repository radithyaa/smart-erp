"""B1 — Event Log Extractor (SRS F1).

Membaca riwayat dokumen ERPNext dan menormalkannya menjadi **event log kanonik**:

    case_id | activity | timestamp | actor | doctype | reference

Sumber data (sesuai SRS F1):
  * DocType ``Version`` (riwayat perubahan doc, termasuk transisi ``docstatus``
    Draft→Submitted lewat field ``docstatus`` di diff ``data``),
  * timestamp dokumen (``creation`` / ``modified`` / ``transaction_date`` /
    ``posting_date``),
  * workflow state bila ada (dicatat sebagai aktivitas bila berubah).

Ruang lingkup tahap ini: alur **Purchase-to-Pay** (F1):
``Purchase Order → Purchase Receipt → Purchase Invoice``.

Catatan lisensi: fungsi di modul ini memakai **Frappe ORM & frappe.db** dari L1
(GPLv3) sebagai *service*, bukan menyalin kode GPLv3 ke L2. Tidak ada potongan
kode ERPNext/Frappe yang ditempel (RULE 3.1), sehingga tidak perlu entri baru di
``docs/THIRD-PARTY.md``.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from smart_erp_ai.adapter.base import ProcessEvent

# ---------------------------------------------------------------------------
# Definisi proses Purchase-to-Pay (P2P)
# ---------------------------------------------------------------------------

#: DocType yang membentuk rantai P2P, urut sesuai tahapan normal proses.
P2P_DOCTYPES: tuple[str, ...] = (
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
)

#: Peta DocType → nama "case" tingkat tinggi. Pada P2P, satu kasus proses adalah
#: satu rantai pengadaan. Kita memakai nama Purchase Order sebagai ``case_id``
#: bila rantai bisa disambungkan; jika belum ada PO (mis. dokumen yatim), jatuh
#: kembali ke nama dokumen itu sendiri.
_P2P_DEFINITION = {
	"name": "purchase-to-pay",
	"label": "Purchase-to-Pay",
	"doctypes": P2P_DOCTYPES,
	# Urutan tahap standar (dipakai F3 untuk mendeteksi rework/deviasi).
	"stages": ["purchase_order", "purchase_receipt", "purchase_invoice"],
}


def p2p_definition() -> dict:
	"""Definisi proses P2P (dipakai adapter & analitik)."""
	return dict(_P2P_DEFINITION)


# ---------------------------------------------------------------------------
# Extractors per DocType
# ---------------------------------------------------------------------------

def _resolve_case_id(doctype: str, doc: dict[str, Any], link_cache: dict[str, str]) -> str:
	"""Tentukan ``case_id`` (rantai P2P) untuk sebuah dokumen.

	Purchase Order adalah akar rantai (``case_id = nama PO``). Purchase Receipt
	menyambung ke PO lewat baris item; Purchase Invoice menyambung ke PR (atau PO).
	Bila tidak ada tautan, dokumen berdiri sendiri sebagai kasus.
	"""
	if doctype == "Purchase Order":
		return doc["name"]

	parent = _child_link_target(doctype, doc["name"])
	if parent:
		return link_cache.get(parent) or _walk_to_root(parent)
	return doc["name"]


def _walk_to_root(reference: str) -> str:
	"""Telusuri rantai Link sampai akar (PO), dengan batas aman iterasi.

	Rantai: PI → (child) PR → (child) PO, atau PR → (child) PO.
	"""
	seen: set[str] = set()
	current = reference
	for _ in range(5):
		if current in seen:
			break
		seen.add(current)
		doctype = frappe.db.get_value("Purchase Invoice", current, "name")
		if doctype:
			parent = _child_link_target("Purchase Invoice", current)
		else:
			parent = _child_link_target("Purchase Receipt", current)
		if not parent or parent == current:
			return current
		current = parent
	return current


def _fetch_items(doctype: str, parent: str) -> list[dict]:
	"""Ambil baris item (child) untuk menyambungkan PI→PR dan PR→PO."""
	order_field = {
		"Purchase Receipt": "purchase_order",
		"Purchase Invoice": "purchase_receipt",
	}.get(doctype)
	if not order_field:
		return []
	rows = frappe.get_all(
		f"{doctype} Item",
		filters={"parent": parent},
		fields=["name", order_field],
		limit_page_length=0,
	)
	return [dict(r) for r in rows]


def _child_link_target(doctype: str, parent: str) -> str | None:
	"""Ambil dokumen P2P sebelumnya lewat baris item (untuk ``case_id``).

	Melewati baris dengan nilai kosong: sebagian item bisa tidak tertaut
	(mis. baris tambahan), sehingga kita pindai **semua** baris dan ambil nilai
	pertama yang non-kosong.
	"""
	field = "purchase_order" if doctype == "Purchase Receipt" else "purchase_receipt"
	for row in _fetch_items(doctype, parent):
		value = row.get(field)
		if value:
			return value
	return None


# ---------------------------------------------------------------------------
# Event log dari Version + timestamps dokumen
# ---------------------------------------------------------------------------


def _events_from_timestamps(doctype: str, doc: dict, case_id: str) -> list[ProcessEvent]:
	"""Event dasar dari kolom timestamp dokumen (selalu tersedia).

	Pattern aktivitas::

	  * ``*_created``    → timestamp ``creation`` (Draft dibuat).
	  * ``*_submitted``  → bila ``docstatus == 1``.
	  * ``*_cancelled``  → bila ``docstatus == 2`` (dokumen dibatalkan).

	``modified`` dipakai sebagai proksi waktu submit/cancel; event dari
	``Version`` (bila ada) akan menambah/menghaluskan garis waktu.
	"""
	events: list[ProcessEvent] = []
	actor = cstr(doc.get("owner") or "Administrator")
	reference = cstr(doc.get("name"))
	slug = _doctype_slug(doctype)
	docstatus = int(doc.get("docstatus") or 0)

	if doc.get("creation"):
		events.append(
			ProcessEvent(
				case_id=case_id,
				activity=f"{slug}_created",
				timestamp=cstr(doc["creation"]),
				actor=actor,
				doctype=doctype,
				reference=reference,
			)
		)
	if docstatus in (1, 2) and doc.get("modified"):
		events.append(
			ProcessEvent(
				case_id=case_id,
				activity=f"{slug}_submitted" if docstatus == 1 else f"{slug}_cancelled",
				timestamp=cstr(doc["modified"]),
				actor=cstr(doc.get("modified_by") or actor),
				doctype=doctype,
				reference=reference,
			)
		)
	return events


def _doctype_slug(doctype: str) -> str:
	return doctype.lower().replace(" ", "_")


def _safe_json(data: str | None) -> dict:
	if not data:
		return {}
	try:
		return json.loads(data)
	except (ValueError, TypeError):
		return {}


def _events_from_versions(doctype: str, docname: str, case_id: str) -> list[ProcessEvent]:
	"""Event tambahan dari riwayat ``Version`` (transisi workflow/docstatus).

	``Version.data`` menyimpan diff dalam bentuk
	``{"changed": [[fieldname, old, new], ...], ...}``. Kita memakai baris yang
	mengubah ``docstatus`` atau ``workflow_state`` sebagai aktivitas bernama.
	"""
	out: list[ProcessEvent] = []
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": docname},
		fields=["name", "data", "owner", "creation", "modified"],
		order_by="creation asc",
		limit_page_length=0,
	)
	for version in versions:
		diff = _safe_json(version.get("data"))
		for changed in diff.get("changed", []):
			if not isinstance(changed, (list, tuple)) or len(changed) < 3:
				continue
			fieldname, _old, new = changed[0], changed[1], changed[2]
			if fieldname == "docstatus":
				activity = {
					"0": f"{_doctype_slug(doctype)}_drafted",
					"1": f"{_doctype_slug(doctype)}_submitted",
					"2": f"{_doctype_slug(doctype)}_cancelled",
				}.get(cstr(new), f"{_doctype_slug(doctype)}_status_changed")
			elif fieldname == "workflow_state":
				activity = f"{_doctype_slug(doctype)}_workflow_{cstr(new).lower().replace(' ', '_')}"
			else:
				continue
			out.append(
				ProcessEvent(
					case_id=case_id,
					activity=activity,
					timestamp=cstr(version.get("creation") or version.get("modified")),
					actor=cstr(version.get("owner") or "Administrator"),
					doctype=doctype,
					reference=docname,
				)
			)
	return out


# ---------------------------------------------------------------------------
# API utama
# ---------------------------------------------------------------------------


def extract_events(
	process: str = "purchase-to-pay",
	*,
	period: str | None = None,
	doctypes: tuple[str, ...] | None = None,
) -> list[dict]:
	"""Ekstrak event log kanonik untuk sebuah proses (SRS F1).

	:param process: saat ini hanya ``"purchase-to-pay"``.
	:param period: filter ``"YYYY-MM"`` berdasarkan ``creation`` dokumen; ``None`` = semua.
	:param doctypes: batasi DocType tertentu (default: seluruh rantai P2P).
	:return: daftar dict event kanonik, terurut menaik berdasarkan ``timestamp``.
	"""
	if process != _P2P_DEFINITION["name"]:
		frappe.throw(f"Proses tidak didukung: {process}")

	doctypes = doctypes or _P2P_DEFINITION["doctypes"]
	events: list[ProcessEvent] = []
	link_cache: dict[str, str] = {}

	period_filter = None
	if period:
		try:
			start, end = _period_bounds(period)
			period_filter = ["between", [start, end]]
		except ValueError as err:
			frappe.throw(str(err))

	for doctype in doctypes:
		filters: dict = {}
		if period_filter:
			filters["creation"] = period_filter

		docs = frappe.get_all(
			doctype,
			filters=filters,
			fields=["name", "owner", "creation", "modified", "modified_by", "docstatus"],
			order_by="creation asc",
			limit_page_length=0,
		)
		for doc in docs:
			doc = dict(doc)
			case_id = _resolve_case_id(doctype, doc, link_cache)
			doc["case_id"] = case_id
			link_cache[doc["name"]] = case_id
			events.extend(_events_from_timestamps(doctype, doc, case_id))
			events.extend(_events_from_versions(doctype, doc["name"], case_id))

	return [e.as_dict() for e in _dedupe_and_sort(events)]


def _dedupe_and_sort(events: list[ProcessEvent]) -> list[ProcessEvent]:
	"""Buang duplikat (docstatus dari Version vs timestamp) & urutkan.

	Dua sumber bisa menghasilkan event ``*_submitted`` yang sama: timestamp
	dokumen dan diff Version. Kita anggap event identik (case+activity+reference)
	sebagai satu baris, mengambil timestamp paling awal agar konsisten.
	"""
	unique: dict[tuple, ProcessEvent] = {}
	for event in events:
		key = (event.case_id, event.activity, event.reference)
		if key not in unique or cstr(event.timestamp) < cstr(unique[key].timestamp):
			unique[key] = event
	return sorted(unique.values(), key=lambda e: (cstr(e.timestamp), e.case_id, e.activity))


def _period_bounds(period: str) -> tuple[str, str]:
	"""Ubah ``"YYYY-MM"`` menjadi (awal, akhir) timestamp inklusif."""
	parts = (period or "").strip().split("-")
	if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
		raise ValueError(f"Format periode tidak valid: '{period}'. Gunakan format 'YYYY-MM'.")
	year_int, month_int = int(parts[0]), int(parts[1])
	if month_int < 1 or month_int > 12:
		raise ValueError(f"Bulan tidak valid: {month_int}. Harus antara 01 dan 12.")
	start = f"{year_int:04d}-{month_int:02d}-01 00:00:00"
	if month_int == 12:
		end = f"{year_int + 1:04d}-01-01 00:00:00"
	else:
		end = f"{year_int:04d}-{month_int + 1:02d}-01 00:00:00"
	return start, end


@frappe.whitelist()
def extract_p2p_events(period: str | None = None) -> list[dict]:
	"""Wrapper whitelisted agar bisa diuji lewat REST/desk (F1)."""
	return extract_events("purchase-to-pay", period=period)


@frappe.whitelist()
def count_p2p_events(period: str | None = None) -> dict:
	"""Ringkas jumlah baris event + jumlah kasus (untuk verifikasi cepat F1)."""
	events = extract_events("purchase-to-pay", period=period)
	return {
		"events": len(events),
		"cases": len({e["case_id"] for e in events}),
		"period": period,
	}
