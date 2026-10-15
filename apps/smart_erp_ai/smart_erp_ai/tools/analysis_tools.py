"""A6 — Jembatan analisis → aksi.

Thin wrappers di sekitar ``process_intelligence/api.py`` (kontrak Dev B).
Tool-tool ini bersifat READ-only dan dieksekusi langsung tanpa konfirmasi.
"""

from __future__ import annotations

from smart_erp_ai.process_intelligence import api as analysis_api


def get_bottlenecks(process: str = "purchase-to-pay", period: str | None = None) -> list[dict]:
	"""Ambil peringkat tahap proses berdasarkan durasi (SRS F2).

	:param process: nama proses, mis. ``"purchase-to-pay"``.
	:param period: filter opsional ``"YYYY-MM"``; ``None`` = semua periode.
	:return: daftar dict ``{stage, label, avg_duration_hours, ...}``.
	"""
	return analysis_api.get_bottlenecks(process, period=period)


def get_rework_cases(process: str = "purchase-to-pay", limit: int = 20) -> list[dict]:
	"""Ambil daftar kasus rework/deviasi (SRS F3).

	:param process: nama proses.
	:param limit: jumlah maksimum kasus.
	:return: daftar dict ``{case_id, deviation, from_stage, to_stage, timestamp}``.
	"""
	return analysis_api.get_rework_cases(process, limit=limit)


def get_pending_at_stage(process: str = "purchase-to-pay", stage: str = "purchase_order") -> list[dict]:
	"""Ambil daftar dokumen tertahan di sebuah tahap (SRS F7).

	:param process: nama proses.
	:param stage: tahap proses, mis. ``"purchase_order"``,
	    ``"purchase_receipt"``, ``"purchase_invoice"``.
	:return: daftar dict ``{case_id, reference, age_hours, owner}``.
	"""
	return analysis_api.get_pending_at_stage(process, stage)
