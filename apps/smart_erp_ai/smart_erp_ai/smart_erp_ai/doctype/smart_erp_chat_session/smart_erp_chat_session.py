"""A2/A5 — Smart ERP Chat Session DocType controller.

Parent DocType for conversation state. Messages are stored as child table rows
(`Smart ERP Chat Message`). Pending write actions are stored on the parent.
"""

from __future__ import annotations

from frappe.model.document import Document


class SmartERPChatSession(Document):
	pass
