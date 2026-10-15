"""A1 — Tool layer generik berbasis DocType (AGENT-RULES RULE 2.3).

Lima tool baca/tulis yang bekerja pada DocType ERPNext via Frappe ORM.
Semua eksekusi memakai izin user yang login (RULE 5.1). Aksi destruktif
(``delete``, ``cancel``, ``amend``) tidak diimplementasi sama sekali (RULE 5.3).
DocType yang diizinkan dibatasi oleh allowlist (RULE 5.6).
"""

from __future__ import annotations

import frappe

#: DocType yang diizinkan untuk tool layer (RULE 5.6).
ALLOWED_DOCTYPES: frozenset[str] = frozenset(
	{
		"Purchase Order",
		"Purchase Receipt",
		"Purchase Invoice",
		"Supplier",
		"Item",
	}
)

#: Aksi terlarang — tidak ada fungsi untuk ini (RULE 5.3).
BLOCKED_ACTIONS: frozenset[str] = frozenset({"delete", "cancel", "amend"})

#: Tool tulis yang memerlukan konfirmasi (F8).
WRITE_TOOLS: frozenset[str] = frozenset(
	{"create_document", "update_document", "submit_document"}
)


def _validate_doctype(doctype: str) -> None:
	"""Validasi DocType terhadap allowlist (RULE 5.6)."""
	if doctype not in ALLOWED_DOCTYPES:
		raise ValueError(f"DocType not allowed: {doctype}")


# ---------------------------------------------------------------------------
# READ tools — dieksekusi langsung tanpa konfirmasi
# ---------------------------------------------------------------------------


def list_documents(doctype: str, filters: dict | None = None, limit: int = 20) -> list[dict]:
	"""Baca — daftar dokumen dari sebuah DocType.

	:param doctype: nama DocType (harus dalam ``ALLOWED_DOCTYPES``).
	:param filters: filter Frappe (dict).
	:param limit: jumlah maksimum baris.
	:return: daftar dict field dokumen.
	"""
	_validate_doctype(doctype)
	rows = frappe.get_all(
		doctype,
		filters=filters or {},
		fields=["*"],
		limit_page_length=min(limit, 100),
		ignore_permissions=False,
	)
	return [dict(r) for r in rows]


def get_document(doctype: str, name: str) -> dict:
	"""Baca — ambil satu dokumen berdasarkan nama.

	:param doctype: nama DocType.
	:param name: ID/nama dokumen.
	:return: dict field dokumen.
	"""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	if hasattr(doc, "check_permission"):
		doc.check_permission("read")
	return doc.as_dict()


# ---------------------------------------------------------------------------
# WRITE tools — memerlukan konfirmasi pengguna (F8 / RULE 5.2)
# ---------------------------------------------------------------------------


def create_document(doctype: str, data: dict) -> dict:
	"""Tulis — buat dokumen baru. Memerlukan konfirmasi (F8).

	:param doctype: nama DocType.
	:param data: field-value dict untuk dokumen baru.
	:return: dict dokumen yang dibuat (termasuk ``name``).
	"""
	_validate_doctype(doctype)
	doc = frappe.new_doc(doctype)
	doc.update(data)
	doc.insert()
	return {"name": doc.name, "doctype": doctype, "docstatus": doc.docstatus}


def update_document(doctype: str, name: str, data: dict) -> dict:
	"""Tulis — perbarui dokumen yang ada. Memerlukan konfirmasi (F8).

	:param doctype: nama DocType.
	:param name: ID/nama dokumen.
	:param data: field-value dict untuk pembaruan.
	:return: dict dokumen yang diperbarui.
	"""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.update(data)
	doc.save()
	return {"name": doc.name, "doctype": doctype, "docstatus": doc.docstatus}


def submit_document(doctype: str, name: str) -> dict:
	"""Tulis — submit/approve dokumen. Memerlukan konfirmasi (F8).

	:param doctype: nama DocType.
	:param name: ID/nama dokumen.
	:return: dict konfirmasi submit.
	"""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.submit()
	return {"name": doc.name, "doctype": doctype, "docstatus": doc.docstatus}
