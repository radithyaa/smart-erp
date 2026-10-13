"""Test unit untuk analitik proses (B2 & B3) — jalankan tanpa ERP hidup.

Karena :class:`ProcessEvent` adalah struktur kanonik murni, seluruh logika
bottleneck & rework bisa diuji dengan event sintetis. Ini menjaga `[MVP]` tetap
hijau (AGENT-RULES RULE 6.5) dan memberi bukti bahwa analitik konsisten dengan
data yang disuntik generator B4.

Jalankan::

    bench --site <site> run-tests --module smart_erp_ai.tests.test_process_intelligence

Atau tanpa site (pure python)::

    python -m pytest smart_erp_ai/tests/test_process_intelligence.py
"""

from __future__ import annotations

import unittest

from smart_erp_ai.adapter.base import ProcessEvent
from smart_erp_ai.process_intelligence import bottleneck, rework


def _ev(case_id, activity, ts, doctype, reference=None):
	return ProcessEvent(
		case_id=case_id,
		activity=activity,
		timestamp=ts,
		actor="Administrator",
		doctype=doctype,
		reference=reference or case_id,
	)


class TestBottleneck(unittest.TestCase):
	def test_transition_into_receipt_uses_earliest_entries(self):
		# PO dibuat 08:00, PR dibuat 12:00 → transisi PO→PR = 4 jam.
		events = [
			_ev("PO-1", "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_order_submitted", "2026-01-01 09:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_receipt_created", "2026-01-01 12:00:00", "Purchase Receipt"),
			_ev("PO-1", "purchase_receipt_submitted", "2026-01-01 13:00:00", "Purchase Receipt"),
		]
		rows = bottleneck.compute_bottlenecks(events)
		pr = next(r for r in rows if r["stage"] == "purchase_receipt")
		self.assertEqual(pr["case_count"], 1)
		self.assertAlmostEqual(pr["avg_duration_hours"], 4.0, places=2)

	def test_slow_stage_outranks_fast_stage(self):
		# 4 kasus; transisi PR→PI (100 jam) jauh lebih lambat dari PO→PR (2 jam).
		events = []
		for i in range(4):
			case = f"PO-{i}"
			events += [
				_ev(case, "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
				_ev(case, "purchase_receipt_created", "2026-01-01 10:00:00", "Purchase Receipt"),
				_ev(case, "purchase_invoice_created", "2026-01-05 14:00:00", "Purchase Invoice"),
			]
		rows = bottleneck.compute_bottlenecks(events)
		# terurut dari terlama → PI di atas PR
		self.assertEqual(rows[0]["stage"], "purchase_invoice")
		self.assertTrue(rows[0]["is_bottleneck"])
		pi = next(r for r in rows if r["stage"] == "purchase_invoice")
		pr = next(r for r in rows if r["stage"] == "purchase_receipt")
		self.assertEqual(pi["case_count"], 4)
		self.assertGreater(pi["avg_duration_hours"], pr["avg_duration_hours"])

	def test_summary_mentions_slowest_stage(self):
		events = [
			_ev("PO-1", "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_receipt_created", "2026-01-01 18:00:00", "Purchase Receipt"),
		]
		rows = bottleneck.compute_bottlenecks(events)
		self.assertIn("Purchase Receipt", bottleneck.bottleneck_summary(rows))


class TestRework(unittest.TestCase):
	def test_cancel_after_submit_is_rework(self):
		events = [
			_ev("PO-1", "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_order_submitted", "2026-01-01 09:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_order_cancelled", "2026-01-01 15:00:00", "Purchase Order"),
		]
		cases = rework.detect_rework(events)
		self.assertEqual(len(cases), 1)
		self.assertEqual(cases[0]["deviation"], "rework")
		self.assertEqual(cases[0]["case_id"], "PO-1")

	def test_cancel_without_submit_is_not_rework(self):
		events = [
			_ev("PO-1", "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
			_ev("PO-1", "purchase_order_cancelled", "2026-01-01 15:00:00", "Purchase Order"),
		]
		self.assertEqual(rework.detect_rework(events), [])

	def test_invoice_without_receipt_is_deviation(self):
		events = [
			_ev("CASE-1", "purchase_order_created", "2026-01-01 08:00:00", "Purchase Order"),
			_ev("CASE-1", "purchase_order_submitted", "2026-01-01 09:00:00", "Purchase Order"),
			_ev("CASE-1", "purchase_invoice_submitted", "2026-01-03 09:00:00", "Purchase Invoice"),
		]
		cases = rework.detect_deviations(events)
		self.assertEqual(len(cases), 1)
		self.assertEqual(cases[0]["deviation"], "skipped_stage")
		self.assertEqual(cases[0]["from_stage"], "purchase_receipt")

	def test_normal_flow_has_no_deviation(self):
		events = [
			_ev("CASE-1", "purchase_order_submitted", "2026-01-01 09:00:00", "Purchase Order"),
			_ev("CASE-1", "purchase_receipt_submitted", "2026-01-02 09:00:00", "Purchase Receipt"),
			_ev("CASE-1", "purchase_invoice_submitted", "2026-01-03 09:00:00", "Purchase Invoice"),
		]
		self.assertEqual(rework.detect_deviations(events), [])


if __name__ == "__main__":
	unittest.main()
