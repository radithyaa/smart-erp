"""A4 — Audit log helper (RULE 5.4).

Setiap aksi agen dicatat ke ``Smart ERP Audit Log`` DocType dengan korelasi
``session_id``. Tidak pernah mencatat secret/API key.
"""

from __future__ import annotations

import json

import frappe

#: Batas ukuran hasil yang disimpan (karakter).
_MAX_RESULT_LEN = 10000


def log_action(
	user: str,
	tool_name: str,
	doctype_affected: str,
	arguments: dict,
	result: dict | str,
	status: str,
	session_id: str | None = None,
) -> None:
	"""Buat catatan audit log untuk satu aksi agen.

	:param user: user yang memicu aksi.
	:param tool_name: nama tool, mis. ``"create_document"``.
	:param doctype_affected: DocType yang disentuh, mis. ``"Purchase Order"``.
	:param arguments: argumen tool sebagai dict.
	:param result: hasil tool sebagai dict/string.
	:param status: ``"Success"`` / ``"Blocked"`` / ``"Error"`` /
	    ``"Confirmed"`` / ``"Rejected"``.
	:param session_id: ID sesi chat (opsional).
	"""
	doc = frappe.get_doc(
		{
			"doctype": "Smart ERP Audit Log",
			"user": user,
			"tool_name": tool_name,
			"doctype_affected": doctype_affected or "",
			"arguments": json.dumps(arguments, default=str),
			"result": json.dumps(result, default=str)[:_MAX_RESULT_LEN],
			"status": status,
			"session_id": session_id or "",
		}
	)
	doc.insert(ignore_permissions=True)
