"""A5 — Endpoint chat berbasis sesi (session-based).

Klien hanya mengirim ``session_id`` + ``message`` + flag ``confirm`` —
tidak ada transfer history. State percakapan otoritatif di DB.
"""

from __future__ import annotations

import frappe

from smart_erp_ai import session
from smart_erp_ai.agent import loop


@frappe.whitelist()
def ask(
	message: str = "",
	session_id: str | None = None,
	confirm: str = "false",
	cancel: str = "false",
) -> dict:
	"""Endpoint chat untuk UI (state tersimpan di DB).

	:param message: pesan user (string kosong jika mengkonfirmasi pending action).
	:param session_id: ID sesi DB. ``None`` = buat sesi baru.
	:param confirm: ``"true"`` bila user mengkonfirmasi pending write action.
	:return: ``{"session_id": str, "reply": str, "tool_calls": list,
	    "pending_confirmation": dict | None}``.
	"""
	sid = session.get_or_create_session(session_id)
	if cancel.lower() == "true":
		if session.get_pending_action(sid):
			session.set_pending_action(sid, None)
		return {"session_id": sid, "reply": "Aksi dibatalkan.", "tool_calls": [], "pending_confirmation": None}
	confirm_bool = confirm.lower() == "true"

	result = loop.run_agent(
		session_id=sid,
		message=message,
		confirm=confirm_bool,
	)
	result["session_id"] = sid
	return result
