"""A5 — Endpoint chat berbasis sesi (session-based).

Klien hanya mengirim ``session_id`` + ``message`` + flag ``confirm`` —
tidak ada transfer history. State percakapan otoritatif di DB.
"""

from __future__ import annotations

import frappe

from smart_erp_ai import session
from smart_erp_ai.agent import loop
from smart_erp_ai.process_intelligence import api as analysis_api


@frappe.whitelist()
def analytics_overview(process: str = "purchase-to-pay", period: str | None = None) -> dict:
	"""Data siap-render untuk panel visualisasi F4 di UI (SRS F4).

	Menggabungkan grafik batang durasi antar tahap (F2) dan diagram alur
	beranotasi bottleneck (F4), plus ringkasan rework (F3).

	Endpoint ini sengaja tipis: seluruh perhitungan tetap di layer analitik
	(``process_intelligence``), agent/UI hanya mengonsumsi (RULE 2.2).
	"""
	bottlenecks = analysis_api.get_bottlenecks(process, period=period or None)
	rework_cases = analysis_api.get_rework_cases(process, limit=10)
	flow = analysis_api.flow_diagram(process)

	return {
		"process": process,
		"period": period or None,
		"bottlenecks": bottlenecks,
		"bottleneck_summary": _top_bottleneck_summary(bottlenecks),
		"rework_count": len(rework_cases),
		"flow": flow,
	}


def _top_bottleneck_summary(bottlenecks: list[dict]) -> str:
	"""Ringkasan satu kalimat tahap terlama (untuk kebutuhan panel UI)."""
	rows = [r for r in bottlenecks if r.get("case_count")]
	if not rows:
		return "Belum ada data cukup untuk analisis bottleneck."
	top = rows[0]
	return (
		f"Tahap paling lambat: {top.get('label', top.get('stage'))} "
		f"(rata-rata {top.get('avg_duration_hours')} jam, {top.get('case_count')} kasus)."
	)


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
