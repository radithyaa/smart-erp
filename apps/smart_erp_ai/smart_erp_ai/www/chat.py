"""Web page controller untuk portal /chat (RULE 5.1).

Menyediakan konteks halaman dan status autentikasi pengguna.
"""

from __future__ import annotations

import frappe


def get_context(context: dict) -> None:
	"""Set konteks halaman web chat."""
	context.no_breadcrumbs = False
	context.parents = [{"title": "Home", "route": "/"}]
	context.title = "Smart ERP Assistant"
	context.current_user = getattr(frappe.session, "user", "Guest")
	context.is_guest = context.current_user == "Guest"
