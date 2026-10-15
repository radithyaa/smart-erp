"""A1/A6 — Registry tool + JSON schema untuk ``bind_tools()``.

Memetakan nama tool → (callable, schema, is_write). Digunakan oleh:
- ``agent/loop.py`` untuk mengetahui tool mana yang perlu konfirmasi.
- ``agent/llm.py`` untuk menghasilkan definisi tool untuk ``bind_tools()``.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from smart_erp_ai.tools import analysis_tools, frappe_tools


# ---------------------------------------------------------------------------
# Pydantic args schema untuk setiap tool
# ---------------------------------------------------------------------------


class ListDocumentsArgs(BaseModel):
	doctype: str = Field(description="DocType name, e.g. 'Purchase Order', 'Supplier', 'Item'")
	filters: dict | None = Field(default=None, description="Frappe filters dict, e.g. {'docstatus': 1}")
	limit: int = Field(default=20, description="Max number of results (default 20)")


class GetDocumentArgs(BaseModel):
	doctype: str = Field(description="DocType name")
	name: str = Field(description="Document name/ID")


class CreateDocumentArgs(BaseModel):
	doctype: str = Field(description="DocType name")
	data: dict = Field(description="Field-value dict for the new document")


class UpdateDocumentArgs(BaseModel):
	doctype: str = Field(description="DocType name")
	name: str = Field(description="Document name/ID")
	data: dict = Field(description="Field-value dict for the update")


class SubmitDocumentArgs(BaseModel):
	doctype: str = Field(description="DocType name")
	name: str = Field(description="Document name/ID")


class GetBottlenecksArgs(BaseModel):
	process: str = Field(default="purchase-to-pay", description="Process name")
	period: str | None = Field(default=None, description="Optional period filter YYYY-MM")


class GetReworkCasesArgs(BaseModel):
	process: str = Field(default="purchase-to-pay", description="Process name")
	limit: int = Field(default=20, description="Max number of cases")


class GetPendingAtStageArgs(BaseModel):
	process: str = Field(default="purchase-to-pay", description="Process name")
	stage: str = Field(
		default="purchase_order",
		description="Stage: 'purchase_order', 'purchase_receipt', or 'purchase_invoice'",
	)


class SendReminderArgs(BaseModel):
	process: str = Field(default="purchase-to-pay", description="Process name")
	stage: str = Field(
		default="purchase_order",
		description="Stage where documents are stuck: 'purchase_order', 'purchase_receipt', or 'purchase_invoice'",
	)
	references: list[str] = Field(
		description="List of stuck document names (e.g. ['PO-PUR-2026-0001']) to send the reminder to"
	)
	message: str = Field(default="", description="Reminder message body")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
	"list_documents": {
		"fn": frappe_tools.list_documents,
		"args_schema": ListDocumentsArgs,
		"is_write": False,
		"description": "List documents of a given DocType with optional filters.",
	},
	"get_document": {
		"fn": frappe_tools.get_document,
		"args_schema": GetDocumentArgs,
		"is_write": False,
		"description": "Get a single document by DocType and name.",
	},
	"create_document": {
		"fn": frappe_tools.create_document,
		"args_schema": CreateDocumentArgs,
		"is_write": True,
		"description": "Create a new document. Requires user confirmation.",
	},
	"update_document": {
		"fn": frappe_tools.update_document,
		"args_schema": UpdateDocumentArgs,
		"is_write": True,
		"description": "Update an existing document. Requires user confirmation.",
	},
	"submit_document": {
		"fn": frappe_tools.submit_document,
		"args_schema": SubmitDocumentArgs,
		"is_write": True,
		"description": "Submit/approve a document. Requires user confirmation.",
	},
	"get_bottlenecks": {
		"fn": analysis_tools.get_bottlenecks,
		"args_schema": GetBottlenecksArgs,
		"is_write": False,
		"description": "Get process stage bottleneck ranking by duration.",
	},
	"get_rework_cases": {
		"fn": analysis_tools.get_rework_cases,
		"args_schema": GetReworkCasesArgs,
		"is_write": False,
		"description": "Get list of rework/deviation cases.",
	},
	"get_pending_at_stage": {
		"fn": analysis_tools.get_pending_at_stage,
		"args_schema": GetPendingAtStageArgs,
		"is_write": False,
		"description": "Get documents pending at a specific process stage.",
	},
	"send_reminder": {
		"fn": analysis_tools.send_reminder,
		"args_schema": SendReminderArgs,
		"is_write": True,
		"description": "Send a reminder for documents stuck at a process stage. Requires user confirmation.",
	},
}


def get_tool(name: str) -> dict[str, Any]:
	"""Kembalikan entry tool berdasarkan nama.

	:raises KeyError: bila tool tidak ditemukan.
	"""
	if name not in TOOL_REGISTRY:
		raise KeyError(f"Unknown tool: {name}")
	return TOOL_REGISTRY[name]


def get_langchain_tools() -> list[StructuredTool]:
	"""Kembalikan daftar ``StructuredTool`` untuk ``bind_tools()``."""
	tools = []
	for name, entry in TOOL_REGISTRY.items():
		tool = StructuredTool.from_function(
			func=entry["fn"],
			name=name,
			description=entry["description"],
			args_schema=entry["args_schema"],
		)
		tools.append(tool)
	return tools
