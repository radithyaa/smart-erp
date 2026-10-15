"""Test unit untuk tool layer, guardrail, session, dan agent loop (A1–A8).

Bagian yang dapat diuji tanpa ERP hidup (pure python):
  - Allowlist rejection
  - Blocked actions (no delete/cancel function)
  - Tool registry integrity

Bagian yang memerlukan Frappe site (frappe.* calls):
  - Confirmation gate
  - Audit log write
  - Analysis tools
  - Session persistence
  - History truncation

Jalankan::

    bench --site <site> run-tests --module smart_erp_ai.tests.test_agent
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from smart_erp_ai.tools import frappe_tools, registry


class TestAllowlist(unittest.TestCase):
	"""RULE 5.6 — DocType di luar allowlist ditolak."""

	def test_blocked_doctype_raises(self):
		with self.assertRaises(ValueError):
			frappe_tools._validate_doctype("Sales Invoice")

	def test_blocked_doctype_sales_order_raises(self):
		with self.assertRaises(ValueError):
			frappe_tools._validate_doctype("Sales Order")

	def test_allowed_doctypes_pass(self):
		for dt in ("Purchase Order", "Purchase Receipt", "Purchase Invoice", "Supplier", "Item"):
			frappe_tools._validate_doctype(dt)


class TestBlockedActions(unittest.TestCase):
	"""RULE 5.3 — delete dan cancel tidak ada di registry."""

	def test_no_delete_tool(self):
		self.assertNotIn("delete_document", registry.TOOL_REGISTRY)
		self.assertNotIn("delete", registry.TOOL_REGISTRY)

	def test_no_cancel_tool(self):
		self.assertNotIn("cancel_document", registry.TOOL_REGISTRY)
		self.assertNotIn("cancel", registry.TOOL_REGISTRY)

	def test_no_amend_tool(self):
		self.assertNotIn("amend_document", registry.TOOL_REGISTRY)
		self.assertNotIn("amend", registry.TOOL_REGISTRY)

	def test_blocked_actions_set(self):
		self.assertIn("delete", frappe_tools.BLOCKED_ACTIONS)
		self.assertIn("cancel", frappe_tools.BLOCKED_ACTIONS)
		self.assertIn("amend", frappe_tools.BLOCKED_ACTIONS)


class TestRegistryIntegrity(unittest.TestCase):
	"""Verifikasi struktur TOOL_REGISTRY."""

	def test_all_write_tools_marked(self):
		write_tools = {"create_document", "update_document", "submit_document", "send_reminder"}
		for name, entry in registry.TOOL_REGISTRY.items():
			if name in write_tools:
				self.assertTrue(entry["is_write"], f"{name} should be write tool")
			else:
				self.assertFalse(entry["is_write"], f"{name} should be read tool")

	def test_nine_tools_registered(self):
		expected = {
			"list_documents", "get_document",
			"create_document", "update_document", "submit_document",
			"get_bottlenecks", "get_rework_cases", "get_pending_at_stage",
			"send_reminder",
		}
		self.assertEqual(set(registry.TOOL_REGISTRY.keys()), expected)

	def test_get_tool_raises_on_unknown(self):
		with self.assertRaises(KeyError):
			registry.get_tool("nonexistent_tool")

	def test_langchain_tools_count(self):
		tools = registry.get_langchain_tools()
		self.assertEqual(len(tools), 9)


class TestFrappeToolsWithMock(unittest.TestCase):
	"""Tes frappe_tools dengan mock frappe.get_all/get_doc/new_doc."""

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_list_documents_calls_get_all(self, mock_frappe):
		mock_frappe.get_all.return_value = [{"name": "PO-001", "docstatus": 1}]
		mock_frappe.BLOCKED_ACTIONS = frozenset()
		result = frappe_tools.list_documents("Purchase Order", limit=5)
		self.assertEqual(len(result), 1)
		mock_frappe.get_all.assert_called_once()

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_list_documents_rejects_disallowed(self, mock_frappe):
		with self.assertRaises(ValueError):
			frappe_tools.list_documents("Sales Invoice")

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_get_document_calls_get_doc(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.as_dict.return_value = {"name": "PO-001", "docstatus": 1}
		mock_frappe.get_doc.return_value = mock_doc
		result = frappe_tools.get_document("Purchase Order", "PO-001")
		self.assertEqual(result["name"], "PO-001")

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_create_document_calls_new_doc(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "PO-NEW-001"
		mock_doc.docstatus = 0
		mock_frappe.new_doc.return_value = mock_doc
		result = frappe_tools.create_document("Purchase Order", {"supplier": "Test Supplier"})
		self.assertEqual(result["name"], "PO-NEW-001")
		mock_doc.insert.assert_called_once()

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_update_document_calls_save(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "PO-001"
		mock_doc.docstatus = 0
		mock_frappe.get_doc.return_value = mock_doc
		result = frappe_tools.update_document("Purchase Order", "PO-001", {"status": "Updated"})
		self.assertEqual(result["name"], "PO-001")
		mock_doc.save.assert_called_once()

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_submit_document_calls_submit(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.name = "PO-001"
		mock_doc.docstatus = 1
		mock_frappe.get_doc.return_value = mock_doc
		result = frappe_tools.submit_document("Purchase Order", "PO-001")
		self.assertEqual(result["docstatus"], 1)
		mock_doc.submit.assert_called_once()

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_create_document_rejects_disallowed(self, mock_frappe):
		with self.assertRaises(ValueError):
			frappe_tools.create_document("Sales Invoice", {})

	@patch("smart_erp_ai.tools.frappe_tools.frappe")
	def test_submit_document_rejects_disallowed(self, mock_frappe):
		with self.assertRaises(ValueError):
			frappe_tools.submit_document("Journal Entry", "JE-001")


class TestAnalysisToolsWithMock(unittest.TestCase):
	"""Tes analysis_tools dengan mock analysis_api."""

	@patch("smart_erp_ai.tools.analysis_tools.analysis_api")
	def test_get_bottlenecks_returns_list(self, mock_api):
		mock_api.get_bottlenecks.return_value = [
			{"stage": "purchase_receipt", "avg_duration_hours": 4.0}
		]
		from smart_erp_ai.tools import analysis_tools as at
		result = at.get_bottlenecks("purchase-to-pay")
		self.assertEqual(len(result), 1)
		mock_api.get_bottlenecks.assert_called_once()

	@patch("smart_erp_ai.tools.analysis_tools.analysis_api")
	def test_get_rework_cases_returns_list(self, mock_api):
		mock_api.get_rework_cases.return_value = [
			{"case_id": "PO-1", "deviation": "rework"}
		]
		from smart_erp_ai.tools import analysis_tools as at
		result = at.get_rework_cases("purchase-to-pay", limit=5)
		self.assertEqual(len(result), 1)
		mock_api.get_rework_cases.assert_called_once()

	@patch("smart_erp_ai.tools.analysis_tools.analysis_api")
	def test_get_pending_at_stage_returns_list(self, mock_api):
		mock_api.get_pending_at_stage.return_value = [
			{"case_id": "PO-1", "age_hours": 10.0}
		]
		from smart_erp_ai.tools import analysis_tools as at
		result = at.get_pending_at_stage("purchase-to-pay", "purchase_order")
		self.assertEqual(len(result), 1)
		mock_api.get_pending_at_stage.assert_called_once()

	@patch("smart_erp_ai.tools.analysis_tools.analysis_api")
	def test_send_reminder_delegates_to_api(self, mock_api):
		mock_api.send_reminder.return_value = {"sent": 2, "recipients": ["a@x"]}
		from smart_erp_ai.tools import analysis_tools as at
		result = at.send_reminder("purchase-to-pay", "purchase_order", ["PO-1", "PO-2"], "tolong")
		self.assertEqual(result["sent"], 2)
		mock_api.send_reminder.assert_called_once_with(
			"purchase-to-pay", "purchase_order", ["PO-1", "PO-2"], "tolong"
		)

	@patch("smart_erp_ai.tools.analysis_tools.analysis_api")
	def test_send_reminder_defaults_empty_references(self, mock_api):
		mock_api.send_reminder.return_value = {"sent": 0}
		from smart_erp_ai.tools import analysis_tools as at
		at.send_reminder("purchase-to-pay", "purchase_order", None, "")
		mock_api.send_reminder.assert_called_once_with(
			"purchase-to-pay", "purchase_order", [], ""
		)


class TestAuditLogHelperWithMock(unittest.TestCase):
	"""Tes audit.log_action dengan mock frappe."""

	@patch("smart_erp_ai.audit.frappe")
	def test_log_action_creates_doc(self, mock_frappe):
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import audit

		audit.log_action(
			user="test@example.com",
			tool_name="list_documents",
			doctype_affected="Purchase Order",
			arguments={"doctype": "Purchase Order"},
			result={"rows": []},
			status="Success",
			session_id="SES-001",
		)
		mock_frappe.get_doc.assert_called_once()
		mock_doc.insert.assert_called_once()

	@patch("smart_erp_ai.audit.frappe")
	def test_log_action_truncates_long_result(self, mock_frappe):
		mock_doc = MagicMock()
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import audit

		long_result = {"data": "x" * 20000}
		audit.log_action(
			user="test@example.com",
			tool_name="list_documents",
			doctype_affected="Purchase Order",
			arguments={},
			result=long_result,
			status="Success",
		)
		call_args = mock_frappe.get_doc.call_args[0][0]
		self.assertLessEqual(len(call_args["result"]), 10000)


class TestSessionWithMock(unittest.TestCase):
	"""Tes session.py dengan mock frappe."""

	@patch("smart_erp_ai.session.frappe")
	def test_get_or_create_session_new(self, mock_frappe):
		mock_frappe.session.user = "test@example.com"
		mock_frappe.db.exists.return_value = False
		mock_doc = MagicMock()
		mock_doc.name = "SES-NEW-001"
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		result = session.get_or_create_session(None)
		self.assertEqual(result, "SES-NEW-001")
		mock_doc.insert.assert_called_once()

	@patch("smart_erp_ai.session.frappe")
	def test_get_or_create_session_existing(self, mock_frappe):
		mock_frappe.session.user = "test@example.com"
		mock_frappe.db.exists.return_value = True
		from smart_erp_ai import session

		result = session.get_or_create_session("SES-EXISTING-001")
		self.assertEqual(result, "SES-EXISTING-001")

	@patch("smart_erp_ai.session.frappe")
	def test_load_messages_round_trip(self, mock_frappe):
		mock_msg1 = MagicMock(role="user", content="Halo", tool_calls=None, tool_call_id=None)
		mock_msg2 = MagicMock(role="assistant", content="Halo!", tool_calls=None, tool_call_id=None)
		mock_doc = MagicMock()
		mock_doc.messages = [mock_msg1, mock_msg2]
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		result = session.load_messages("SES-001")
		self.assertEqual(len(result), 2)
		self.assertEqual(result[0]["role"], "user")
		self.assertEqual(result[1]["role"], "assistant")

	@patch("smart_erp_ai.session.frappe")
	def test_append_message_increments_count(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.message_count = 3
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		session.append_message("SES-001", "user", "test")
		self.assertEqual(mock_doc.message_count, 4)
		mock_doc.save.assert_called_once()

	@patch("smart_erp_ai.session.frappe")
	def test_set_pending_action_sets_status(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.pending_action = ""
		mock_doc.status = "Active"
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		session.set_pending_action("SES-001", {"tool": "create_document", "args": {}})
		self.assertEqual(mock_doc.status, "Awaiting Confirmation")
		mock_doc.save.assert_called_once()

	@patch("smart_erp_ai.session.frappe")
	def test_clear_pending_action_resets_status(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.pending_action = '{"tool": "create_document"}'
		mock_doc.status = "Awaiting Confirmation"
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		session.set_pending_action("SES-001", None)
		self.assertEqual(mock_doc.status, "Active")

	@patch("smart_erp_ai.session.frappe")
	def test_get_pending_action_returns_none_when_empty(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.pending_action = ""
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		result = session.get_pending_action("SES-001")
		self.assertIsNone(result)

	@patch("smart_erp_ai.session.frappe")
	def test_get_pending_action_returns_dict(self, mock_frappe):
		mock_doc = MagicMock()
		mock_doc.pending_action = json.dumps({"tool": "create_document", "args": {"doctype": "Purchase Order"}})
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		result = session.get_pending_action("SES-001")
		self.assertIsNotNone(result)
		self.assertEqual(result["tool"], "create_document")

	@patch("smart_erp_ai.session.frappe")
	def test_get_history_for_llm_truncation(self, mock_frappe):
		msgs = []
		for i in range(30):
			m = MagicMock()
			m.role = "user" if i % 2 == 0 else "assistant"
			m.content = f"msg-{i}"
			m.tool_calls = None
			m.tool_call_id = None
			msgs.append(m)
		mock_doc = MagicMock()
		mock_doc.messages = msgs
		mock_frappe.get_doc.return_value = mock_doc
		from smart_erp_ai import session

		history = session.get_history_for_llm("SES-001", max_messages=10)
		self.assertEqual(len(history), 10)


class TestLoopConfirmationGate(unittest.TestCase):
	"""Tes confirmation gate: WRITE tool → pending_confirmation, bukan eksekusi."""

	def test_write_tool_marked_in_registry(self):
		for name in ("create_document", "update_document", "submit_document"):
			self.assertTrue(registry.get_tool(name)["is_write"])

	def test_read_tool_not_marked_in_registry(self):
		for name in ("list_documents", "get_document", "get_bottlenecks", "get_rework_cases", "get_pending_at_stage"):
			self.assertFalse(registry.get_tool(name)["is_write"])

	def test_max_iterations_is_six(self):
		from smart_erp_ai.agent import loop
		self.assertEqual(loop.MAX_ITERATIONS, 6)


class TestDescribeAction(unittest.TestCase):
	"""Tes _describe_action menghasilkan deskripsi ramah-pengguna."""

	def test_describe_create(self):
		from smart_erp_ai.agent.loop import _describe_action
		desc = _describe_action("create_document", {"doctype": "Purchase Order", "data": {"supplier": "Vendor A"}})
		self.assertIn("membuat Purchase Order", desc)
		self.assertIn("Vendor A", desc)

	def test_describe_update(self):
		from smart_erp_ai.agent.loop import _describe_action
		desc = _describe_action("update_document", {"doctype": "Purchase Order", "name": "PO-001", "data": {}})
		self.assertIn("memperbarui Purchase Order PO-001", desc)

	def test_describe_submit(self):
		from smart_erp_ai.agent.loop import _describe_action
		desc = _describe_action("submit_document", {"doctype": "Purchase Order", "name": "PO-001"})
		self.assertIn("men-submit", desc)
		self.assertIn("PO-001", desc)

	def test_describe_reminder(self):
		from smart_erp_ai.agent.loop import _describe_action
		desc = _describe_action(
			"send_reminder",
			{"stage": "purchase_order", "references": ["PO-001", "PO-002"]},
		)
		self.assertIn("pengingat", desc)
		self.assertIn("2 dokumen", desc)
		self.assertIn("PO-001", desc)


if __name__ == "__main__":
	unittest.main()
