"""Adapter ERPNext — implementasi ``ERPSource`` untuk L1 (ERPNext).

Membungkus event-log extractor (B1) dan query dokumen tertahan, sehingga
``process_intelligence`` & agent tidak pernah menyentuh ORM ERPNext secara
langsung (AGENT-RULES RULE 2.4 / NFR5).

Menambah dukungan Odoo/SAP di masa depan = tambah file adapter baru yang
mengimplementasi ``ERPSource``; kode analitik tidak berubah.
"""

from __future__ import annotations

import frappe
from frappe.utils import get_datetime, now_datetime

from smart_erp_ai.adapter.base import ERPSource, ProcessEvent
from smart_erp_ai.process_intelligence import event_log


class ERPNextSource(ERPSource):
	"""Sumber data berbasis ERPNext (submodule L1, GPLv3)."""

	process_name = "purchase-to-pay"

	def supported_processes(self) -> list[str]:
		return ["purchase-to-pay"]

	def fetch_events(self, process: str, *, period: str | None = None) -> list[ProcessEvent]:
		rows = event_log.extract_events(process, period=period)
		return [ProcessEvent(**row) for row in rows]

	def list_pending(self, process: str, stage: str) -> list[dict]:
		"""Dokumen tertahan di sebuah tahap (dipakai F7 & reminder).

	``stage`` dipetakan ke DocType. Sebuah dokumen dianggap "tertahan" bila:
	  * masih **Draft** (``docstatus = 0``) — belum di-submit/approve, ATAU
	  * sudah di-submit tetapi **belum maju** ke dokumen berikutnya dalam rantai
	    (mis. PO submitted tanpa Purchase Receipt → tertahan menuju penerimaan).

	``age_hours`` dihitung sejak ``creation`` dokumen hingga sekarang.
	"""
		if process != self.process_name:
			frappe.throw(f"Proses tidak didukung: {process}")

		doctype = _STAGE_DOCTYPE.get(stage)
		if not doctype:
			frappe.throw(f"Tahap tidak dikenal: {stage}")

		now = now_datetime()
		rows = frappe.get_all(
			doctype,
			filters={"docstatus": ["<=", 1]},
			fields=["name", "owner", "creation", "docstatus"],
			order_by="creation asc",
			limit_page_length=0,
		)

		# Nama dokumen yang sudah punya kelanjutan di rantai (tidak tertahan).
		advanced = _advanced_references(stage)

		out: list[dict] = []
		for row in rows:
			row = dict(row)
			is_draft = int(row.get("docstatus") or 0) == 0
			if not is_draft and row["name"] in advanced:
				# Sudah di-submit dan sudah lanjut → tidak tertahan.
				continue
			age = (now - get_datetime(row["creation"])).total_seconds() / 3600.0
			out.append(
				{
					"case_id": row["name"],
					"reference": row["name"],
					"stage": stage,
					"doctype": doctype,
					"status": "Draft" if is_draft else "Awaiting next step",
					"age_hours": round(age, 2),
					"owner": row.get("owner") or "Administrator",
				}
			)
		out.sort(key=lambda r: r["age_hours"], reverse=True)
		return out

	def send_reminder(self, process: str, stage: str, references: list[str], message: str) -> dict:
		"""Kirim pengingat untuk dokumen tertahan (SRS §9 demo #4).

		Mekanisme di ERPNext: buat satu dokumen ``ToDo`` per dokumen tertahan,
		di-assign ke ``owner`` dokumen tersebut, sehingga pengingat muncul sebagai
		*assignment* di ERPNext Desk. Mekanisme ini dipilih karena **tidak
		bergantung pada konfigurasi SMTP** (reprodusibel di demo) namun tetap
		terlihat nyata di dalam ERP (NFR4).

		Setiap pengiriman dicatat di DocType ``Smart ERP Reminder Log``.

		:raises frappe.ValidationError: bila ``references`` kosong.
		"""
		if process != self.process_name:
			frappe.throw(f"Proses tidak didukung: {process}")

		doctype = _STAGE_DOCTYPE.get(stage)
		if not doctype:
			frappe.throw(f"Tahap tidak dikenal: {stage}")

		references = [r for r in (references or []) if r]
		if not references:
			frappe.throw("Tidak ada dokumen yang dipilih untuk dikirimi pengingat.")

		# Batasi ke dokumen yang benar-benar valid & benar tertahan di tahap ini.
		pending_by_ref = {row["reference"]: row for row in self.list_pending(process, stage)}
		valid = [r for r in references if r in pending_by_ref]
		if not valid:
			frappe.throw("Dokumen yang dipilih tidak lagi tertahan di tahap ini.")

		message = (message or "").strip() or "Mohon tindak lanjuti dokumen ini."
		recipients: list[str] = []

		for reference in valid:
			row = pending_by_ref[reference]
			recipient = row.get("owner") or "Administrator"
			if recipient not in recipients:
				recipients.append(recipient)
			self._create_todo(reference, doctype, recipient, stage, message)
			self._log_reminder(stage, reference, recipient, message)

		return {
			"sent": len(valid),
			"recipients": recipients,
			"references": valid,
			"stage": stage,
		}

	def _create_todo(self, reference: str, doctype: str, recipient: str, stage: str, message: str) -> None:
		"""Buat ToDo (assignment) ke owner dokumen sebagai pengingat nyata di ERP."""
		description = (
			f"[Smart ERP] Pengingat proses {stage.replace('_', ' ')}: "
			f"dokumen {reference} ({doctype}) tertahan. {message}"
		)
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": description,
				"allocated_to": recipient,
				"reference_type": doctype,
				"reference_name": reference,
				"priority": "High",
				"status": "Open",
			}
		)
		todo.insert(ignore_permissions=False)

	def _log_reminder(self, stage: str, reference: str, recipient: str, message: str) -> None:
		"""Catat pengingat ke ``Smart ERP Reminder Log`` (jejak, NFR2)."""
		if not frappe.db.exists("DocType", "Smart ERP Reminder Log"):
			return
		frappe.get_doc(
			{
				"doctype": "Smart ERP Reminder Log",
				"stage": stage,
				"reference": reference,
				"recipient": recipient,
				"message": message,
				"sent_by": getattr(frappe.session, "user", None) or "Administrator",
			}
		).insert(ignore_permissions=True)


#: DocType lanjutan per tahap (untuk menilai sebuah dokumen sudah "maju").
_NEXT_STAGE: dict[str, str] = {
	"purchase_order": "Purchase Receipt",
	"purchase_receipt": "Purchase Invoice",
}


def _advanced_references(stage: str) -> set[str]:
	"""Nama dokumen (di tahap ini) yang sudah punya kelanjutan di rantai P2P."""
	next_doctype = _NEXT_STAGE.get(stage)
	if not next_doctype:
		return set()

	# Purchase Receipt Item.purchase_order / Purchase Invoice Item.purchase_receipt
	link_field = "purchase_order" if stage == "purchase_order" else "purchase_receipt"
	rows = frappe.get_all(
		f"{next_doctype} Item",
		fields=[link_field],
		limit_page_length=0,
	)
	return {r[link_field] for r in rows if r.get(link_field)}


_STAGE_DOCTYPE = {
	"purchase_order": "Purchase Order",
	"purchase_receipt": "Purchase Receipt",
	"purchase_invoice": "Purchase Invoice",
}


def get_source() -> ERPSource:
	"""Factory adapter aktif (titik ganti multi-ERP di masa depan)."""
	return ERPNextSource()
