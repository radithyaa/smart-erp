"""B3 — Rework & Deviation Analysis (SRS F3).

Mendeteksi dua pola menyimpang dari urutan proses P2P normal:

  * **Rework** — dokumen kembali ke tahap sebelumnya, mis. Purchase Order
    di-cancel lalu dibuat ulang, atau Purchase Invoice di-cancel setelah
    di-submit lalu dibuat ulang (``*_cancelled`` muncul setelah
    ``*_submitted`` pada rantai yang sama).
  * **Deviation** — dokumen melewati urutan normal, mis. Purchase Invoice
    di-submit tanpa Purchase Receipt sebelumnya.

Modul murni bekerja pada ``ProcessEvent`` kanonik (tidak menyentuh ERP),
sesuai AGENT-RULES RULE 2.2 & 2.4. Output kompatibel dengan kontrak
``get_rework_cases()`` (docs/DEV-TASKS.md §1).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from smart_erp_ai.adapter.base import ProcessEvent
from smart_erp_ai.process_intelligence.bottleneck import P2P_STAGES

#: Nama aktivitas per tahap yang menandakan dokumen "maju".
_STAGE_ORDER: dict[str, int] = {stage: index for index, stage in enumerate(P2P_STAGES)}

_STAGE_LABELS: dict[str, str] = {
	"purchase_order": "Purchase Order",
	"purchase_receipt": "Purchase Receipt",
	"purchase_invoice": "Purchase Invoice",
}


def _stage_of(doctype: str) -> str | None:
	stage = doctype.lower().replace(" ", "_")
	return stage if stage in _STAGE_ORDER else None


def _is_cancel(event: ProcessEvent) -> bool:
	return "cancel" in event.activity


def _is_submit(event: ProcessEvent) -> bool:
	return event.activity.endswith("_submitted")


def detect_rework(events: Iterable[ProcessEvent]) -> list[dict]:
	"""Deteksi kasus rework (dokumen dibatalkan setelah di-submit).

	:return: daftar dict ``{case_id, deviation, from_stage, to_stage, timestamp}``
	    kompatibel dengan kontrak ``get_rework_cases()``.
	"""
	# Kelompokkan event per (case_id, doctype), terurut waktu.
	grouped: dict[tuple[str, str], list[ProcessEvent]] = defaultdict(list)
	for event in events:
		grouped[(event.case_id, event.doctype)].append(event)

	cases: list[dict] = []
	for (case_id, doctype), group in grouped.items():
		group.sort(key=lambda e: e.timestamp)
		stage = _stage_of(doctype)
		if stage is None:
			continue
		for index, event in enumerate(group):
			if not _is_cancel(event):
				continue
			had_submit = any(_is_submit(prev) for prev in group[:index])
			if not had_submit:
				continue
			cases.append(
				{
					"case_id": case_id,
					"deviation": "rework",
					"from_stage": stage,
					"to_stage": group[max(index - 1, 0)].activity,
					"timestamp": event.timestamp,
					"reference": event.reference,
					"detail": (
						f"{_STAGE_LABELS.get(stage, doctype)} {event.reference} "
						f"dibatalkan setelah di-submit"
					),
				}
			)
	return cases


def detect_deviations(events: Iterable[ProcessEvent]) -> list[dict]:
	"""Deteksi kasus yang melewati urutan normal (mis. Invoice tanpa Receipt).

	Aturan sederhana (dapat dijelaskan ke juri): untuk tiap ``case_id``, tentukan
	tahap-tahap yang benar-benar "maju" (submit), lalu tandai:

	  * Purchase Invoice di-submit tanpa Purchase Receipt di-submit sebelumnya.
	  * Purchase Receipt di-submit tanpa Purchase Order di-submit sebelumnya.
	"""
	# kumpulkan (case_id → set stage yang di-submit, beserta waktu submit pertama)
	submitted: dict[str, dict[str, str]] = defaultdict(dict)
	for event in events:
		if not _is_submit(event):
			continue
		stage = _stage_of(event.doctype)
		if stage is None:
			continue
		submitted[event.case_id].setdefault(stage, event.timestamp)

	cases: list[dict] = []
	for case_id, stages in submitted.items():
		# Urutan maju yang diharapkan: PO → PR → PI.
		for stage, required_prev in (("purchase_receipt", "purchase_order"), ("purchase_invoice", "purchase_receipt")):
			if stage in stages and required_prev not in stages:
				cases.append(
					{
						"case_id": case_id,
						"deviation": "skipped_stage",
						"from_stage": required_prev,
						"to_stage": stage,
						"timestamp": stages[stage],
						"reference": case_id,
						"detail": (
							f"{_STAGE_LABELS.get(stage, stage)} diproses tanpa "
							f"{_STAGE_LABELS.get(required_prev, required_prev)}"
						),
					}
				)
	return cases


def detect_rework_and_deviations(events: Iterable[ProcessEvent]) -> list[dict]:
	"""Gabungan rework + deviasi, terurut menaik berdasarkan timestamp."""
	combined = detect_rework(events) + detect_deviations(events)
	combined.sort(key=lambda row: row["timestamp"])
	return combined


def rework_summary(cases: list[dict]) -> str:
	"""Ringkasan rework/deviasi untuk jawaban agen (F7/A6)."""
	if not cases:
		return "Tidak ditemukan kasus rework atau deviasi."
	rework = sum(1 for c in cases if c["deviation"] == "rework")
	deviation = len(cases) - rework
	return (
		f"Ditemukan {len(cases)} kasus menyimpang: "
		f"{rework} rework dan {deviation} deviasi urutan proses."
	)
