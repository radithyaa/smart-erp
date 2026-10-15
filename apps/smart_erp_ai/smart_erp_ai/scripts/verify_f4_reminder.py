"""Guardrail check untuk ``send_reminder`` (SRS §9 #4).

Memverifikasi bahwa pengingat ditolak untuk daftar kosong atau dokumen yang
tidak lagi tertahan. Jalankan::

    bench --site <site> execute smart_erp_ai.scripts.verify_f4_reminder.guardrail
"""

from __future__ import annotations

import frappe


def guardrail() -> dict:
	"""Kembalikan hasil uji guardrail reminder (raise terlihat / aman)."""
	from smart_erp_ai.process_intelligence import api

	results: dict[str, str] = {}

	cases = {
		"empty_references": [],
		"not_pending": ["PUR-ORD-9999-00001"],
	}
	for label, refs in cases.items():
		try:
			api.send_reminder("purchase-to-pay", "purchase_order", refs, "x")
			results[label] = "FAIL: no error raised"
		except Exception as err:  # noqa: BLE001 - cukup laporkan jenisnya
			results[label] = f"OK: {type(err).__name__}"

	print(frappe.as_json(results))
	return results
