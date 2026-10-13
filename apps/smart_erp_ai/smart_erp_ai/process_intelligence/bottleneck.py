"""B2 — Bottleneck Analysis (SRS F2).

Menghitung **rata-rata & median durasi antar tahap** proses P2P dari event log
kanonik. Modul ini murni bekerja pada ``ProcessEvent`` (tidak menyentuh ERP),
sesuai AGENT-RULES RULE 2.2 & 2.4.

Definisi durasi tahap (untuk proses P2P):

    tahap                = selang antara kedatangan suatu dokumen dan
                           penyelesaiannya (submit), lalu dijumlahkan sebagai
                           waktu "di dalam" tahap tersebut.

Pendekatan yang dipakai (sederhana & dapat dijelaskan ke juri):
  * untuk tiap ``case_id``, ambil event per DocType;
  * durasi satu tahap doc = ``submitted`` − ``created`` (jam);
  * agregasi ``avg`` / ``median`` / ``count`` per tahap;
  * tandai tahap di atas threshold (default: median seluruh tahap × 1.5).

Output kompatibel dengan kontrak AnalysisQueryAPI v1 (docs/DEV-TASKS.md §1).
"""

from __future__ import annotations

import statistics
from typing import Iterable

from frappe.utils import get_datetime

from smart_erp_ai.adapter.base import ProcessEvent

#: Urutan tahap proses P2P (dipakai untuk konsistensi label).
P2P_STAGES: tuple[str, ...] = ("purchase_order", "purchase_receipt", "purchase_invoice")

#: Label ramah-pengguna per tahap.
STAGE_LABELS: dict[str, str] = {
	"purchase_order": "Purchase Order",
	"purchase_receipt": "Purchase Receipt",
	"purchase_invoice": "Purchase Invoice",
}

#: Multiplier threshold untuk menandai bottleneck (median global × faktor).
DEFAULT_THRESHOLD_FACTOR = 1.5


def _parse_ts(value: str):
	"""Parse timestamp kanonik (``YYYY-MM-DD HH:MM:SS``) → datetime."""
	return get_datetime(value)


def _durations_from_events(events: Iterable[ProcessEvent]) -> dict[str, list[float]]:
	"""Kelompokkan durasi transisi antar-tahap (jam) per tahap (SRS F2).

	Model: satu kasus = satu rantai P2P. Untuk setiap ``case_id`` kita ambil
	waktu **masuk** tiap tahap (event ``*_created`` pertama di DocType tsb,
	jatuh ke ``*_submitted`` bila tidak ada), lalu hitung selang antar tahap:

	  * tahap ``purchase_order``  → jarak dari mulai kasus ke masuk PO
	    (mendekati 0, tapi tetap dihitung agar lengkap),
	  * tahap ``purchase_receipt`` → jarak PO → PR (menangkap *approval delay*),
	  * tahap ``purchase_invoice`` → jarak PR → PI (menangkap *billing delay*).

	Ini yang membuat bottleneck yang disuntik generator (PO tertahan sebelum PR)
	muncul sebagai durasi besar pada tahap ``purchase_receipt``.
	"""
	# case_id → {stage: timestamp_masuk}
	entered: dict[str, dict[str, str]] = {}
	for event in events:
		stage = event.doctype.lower().replace(" ", "_")
		if stage not in P2P_STAGES:
			continue
		slot = entered.setdefault(event.case_id, {})
		# hanya catat kedatangan paling awal per tahap
		if stage not in slot or event.timestamp < slot[stage]:
			slot[stage] = event.timestamp

	durations: dict[str, list[float]] = {stage: [] for stage in P2P_STAGES}
	for _case_id, stages in entered.items():
		prev_ts = None
		for stage in P2P_STAGES:
			ts = stages.get(stage)
			if ts is None:
				continue
			if prev_ts is not None:
				delta = (_parse_ts(ts) - _parse_ts(prev_ts)).total_seconds() / 3600.0
				# transisi dicatat pada tahap *tujuan* (mis. PO→PR → tahap PR).
				if delta >= 0:
					durations[stage].append(delta)
			prev_ts = ts
	return durations


def compute_bottlenecks(
	events: Iterable[ProcessEvent],
	*,
	threshold_factor: float = DEFAULT_THRESHOLD_FACTOR,
) -> list[dict]:
	"""Hitung peringkat tahap berdasarkan durasi rata-rata (SRS F2).

	:return: daftar dict, terurut dari tahap **terlama**:
	    ``{stage, label, avg_duration_hours, median_duration_hours, case_count,
	       is_bottleneck}``.
	"""
	durations = _durations_from_events(events)

	# median global dipakai sebagai ambang relatif.
	all_values = [v for values in durations.values() for v in values]
	global_median = statistics.median(all_values) if all_values else 0.0
	threshold = global_median * threshold_factor

	result: list[dict] = []
	for stage in P2P_STAGES:
		values = durations[stage]
		if not values:
			result.append(
				{
					"stage": stage,
					"label": STAGE_LABELS.get(stage, stage),
					"avg_duration_hours": 0.0,
					"median_duration_hours": 0.0,
					"case_count": 0,
					"is_bottleneck": False,
				}
			)
			continue
		avg = statistics.fmean(values)
		result.append(
			{
				"stage": stage,
				"label": STAGE_LABELS.get(stage, stage),
				"avg_duration_hours": round(avg, 2),
				"median_duration_hours": round(statistics.median(values), 2),
				"case_count": len(values),
				"is_bottleneck": avg >= threshold,
			}
		)

	result.sort(key=lambda row: row["avg_duration_hours"], reverse=True)
	return result


def bottleneck_summary(bottlenecks: list[dict]) -> str:
	"""Ringkasan satu-dua kalimat untuk jawaban agen (dipakai F7/A6)."""
	if not bottlenecks or bottlenecks[0]["case_count"] == 0:
		return "Belum ada data cukup untuk analisis bottleneck."
	top = bottlenecks[0]
	return (
		f"Tahap paling lambat adalah {top['label']} "
		f"(rata-rata {top['avg_duration_hours']} jam, median "
		f"{top['median_duration_hours']} jam dari {top['case_count']} kasus)."
	)
