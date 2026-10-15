"""A4 — Smart ERP Audit Log DocType controller.

Audit trail for every agent tool call. Records are created programmatically
via :func:`smart_erp_ai.audit.log_action` — never via Desk UI.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class SmartERPAuditLog(Document):
	pass
