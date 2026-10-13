"""B2/B3 — Kontrak AnalysisQueryAPI v1 (docs/DEV-TASKS.md §1).

**Dev B menyediakan, Dev A mengonsumsi.** Ini satu-satunya interface analitik
yang mengikat kedua jalur (AGENT-RULES RULE 2.2 — kontrak eksplisit).

Kontrak (bentuk return TIDAK boleh berubah tanpa notifikasi Dev A):

    get_bottlenecks(process, period=None) -> list[dict]
    get_rework_cases(process, limit=20)   -> list[dict]
    get_pending_at_stage(process, stage)  -> list[dict]

Seluruh fungsi mengakses ERP **hanya lewat adapter** (``adapter.get_source()``),
bukan ORM langsung (RULE 2.4).
"""

from __future__ import annotations

import frappe

from smart_erp_ai.adapter.erpnext_source import get_source
from smart_erp_ai.process_intelligence import bottleneck, rework

SUPPORTED_PROCESSES = ("purchase-to-pay",)


def _check_process(process: str) -> None:
	if process not in SUPPORTED_PROCESSES:
		frappe.throw(f"Proses tidak didukung: {process}")


# ---------------------------------------------------------------------------
# Kontrak publik v1
# ---------------------------------------------------------------------------


def get_bottlenecks(process: str, period: str | None = None) -> list[dict]:
	"""Tahap proses diurutkan dari yang terlama (SRS F2).

	Return::

	    [{"stage": str, "avg_duration_hours": float,
	      "median_duration_hours": float, "case_count": int}, ...]

	``process`` contoh: ``"purchase-to-pay"``. ``period``: ``"2026-10"``,
	``None`` = semua periode.
	"""
	_check_process(process)
	events = get_source().fetch_events(process, period=period)
	return bottleneck.compute_bottlenecks(events)


def get_rework_cases(process: str, limit: int = 20) -> list[dict]:
	"""Kasus yang mundur ke tahap sebelumnya / melewati urutan normal (SRS F3).

	Return::

	    [{"case_id": str, "deviation": str,
	      "from_stage": str, "to_stage": str, "timestamp": str}, ...]
	"""
	_check_process(process)
	events = get_source().fetch_events(process)
	cases = rework.detect_rework_and_deviations(events)
	return cases[: max(int(limit), 0)]


def get_pending_at_stage(process: str, stage: str) -> list[dict]:
	"""Dokumen yang masih tertahan di sebuah tahap (F7 & reminder).

	Return::

	    [{"case_id": str, "reference": str, "age_hours": float, "owner": str}, ...]
	"""
	_check_process(process)
	return get_source().list_pending(process, stage)


# ---------------------------------------------------------------------------
# Endpoint whitelisted (dipakai UI Dev C-UI / agent Dev A via HTTP)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def bottlenecks(process: str = "purchase-to-pay", period: str | None = None) -> dict:
	"""Endpoint REST untuk grafik bottleneck (F4/B5)."""
	_check_process(process)
	rows = get_bottlenecks(process, period=period)
	return {
		"process": process,
		"period": period,
		"bottlenecks": rows,
		"summary": bottleneck.bottleneck_summary(rows),
	}


@frappe.whitelist()
def rework_cases(process: str = "purchase-to-pay", limit: int = 20) -> dict:
	"""Endpoint REST untuk daftar rework/deviasi (F3/B5)."""
	_check_process(process)
	rows = get_rework_cases(process, limit=int(limit))
	return {
		"process": process,
		"cases": rows,
		"summary": rework.rework_summary(rows),
	}


@frappe.whitelist()
def pending_at_stage(process: str = "purchase-to-pay", stage: str = "purchase_order") -> dict:
	"""Endpoint REST untuk dokumen tertahan (F7)."""
	_check_process(process)
	rows = get_pending_at_stage(process, stage)
	return {"process": process, "stage": stage, "pending": rows, "count": len(rows)}


@frappe.whitelist()
def process_overview(process: str = "purchase-to-pay") -> dict:
	"""Gabungan ringkasan untuk satu kartu di UI (F4/B5)."""
	_check_process(process)
	bottlenecks_rows = get_bottlenecks(process)
	rework_rows = get_rework_cases(process, limit=10)
	return {
		"process": process,
		"bottlenecks": bottlenecks_rows,
		"bottleneck_summary": bottleneck.bottleneck_summary(bottlenecks_rows),
		"rework_cases": rework_rows,
		"rework_summary": rework.rework_summary(rework_rows),
		"flow": flow_diagram(process),
	}


@frappe.whitelist()
def flow_diagram(process: str = "purchase-to-pay") -> dict:
	"""Struktur diagram alur beranotasi bottleneck untuk UI (F4/B5).

	Return::

	    {"nodes": [{"id", "label", "avg_duration_hours", "is_bottleneck"}],
	     "edges": [{"from", "to", "label"}]}
	"""
	_check_process(process)
	rows = get_bottlenecks(process)
	by_stage = {row["stage"]: row for row in rows}
	nodes = [
		{
			"id": stage,
			"label": bottleneck.STAGE_LABELS.get(stage, stage),
			"avg_duration_hours": by_stage.get(stage, {}).get("avg_duration_hours", 0.0),
			"is_bottleneck": by_stage.get(stage, {}).get("is_bottleneck", False),
		}
		for stage in bottleneck.P2P_STAGES
	]
	edges = [
		{"from": bottleneck.P2P_STAGES[i], "to": bottleneck.P2P_STAGES[i + 1], "label": "next"}
		for i in range(len(bottleneck.P2P_STAGES) - 1)
	]
	return {"process": process, "nodes": nodes, "edges": edges}
