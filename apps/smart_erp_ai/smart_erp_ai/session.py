"""A2/A5 — Session CRUD untuk conversation state yang disimpan di DB.

Seluruh state percakapan (messages + pending_action) disimpan server-side
di ``Smart ERP Chat Session`` DocType. Klien hanya mengirim ``session_id``,
``message``, dan flag ``confirm`` — tidak ada transfer history.
"""

from __future__ import annotations

import json

import frappe

#: Jumlah maksimum pesan yang dikirim ke LLM (kontrol token).
DEFAULT_MAX_MESSAGES = 20


def _get_session_doc(session_id: str):
	"""Ambil dokumen sesi dan validasi kepemilikan sesi (RULE 5.1)."""
	doc = frappe.get_doc("Smart ERP Chat Session", session_id)
	user = getattr(frappe.session, "user", None)
	doc_user = getattr(doc, "user", None)
	if (
		user
		and doc_user
		and isinstance(user, str)
		and isinstance(doc_user, str)
		and user != "Administrator"
		and doc_user != user
	):
		frappe.throw("Akses sesi ditolak: sesi ini milik pengguna lain.", frappe.PermissionError)
	return doc


def get_or_create_session(session_id: str | None = None) -> str:
	"""Kembalikan ``session_id``. Buat sesi baru bila perlu.

	:param session_id: ID sesi yang ada, atau ``None`` untuk buat baru.
	:return: session_id string.
	"""
	user = getattr(frappe.session, "user", "Guest")
	if session_id:
		if frappe.db.exists("Smart ERP Chat Session", session_id):
			_get_session_doc(session_id)
			return session_id
	doc = frappe.get_doc(
		{
			"doctype": "Smart ERP Chat Session",
			"user": user,
			"status": "Active",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def load_messages(session_id: str) -> list[dict]:
	"""Muat semua pesan dari sesi sebagai daftar dict.

	:return: daftar ``{role, content, tool_calls, tool_call_id}``,
	    terurut kronologis.
	"""
	doc = _get_session_doc(session_id)
	return [
		{
			"role": m.role,
			"content": m.content or "",
			"tool_calls": json.loads(m.tool_calls) if m.tool_calls else None,
			"tool_call_id": m.tool_call_id or None,
		}
		for m in doc.messages
	]


def append_message(
	session_id: str,
	role: str,
	content: str,
	tool_calls: list | None = None,
	tool_call_id: str | None = None,
) -> None:
	"""Tambah satu pesan ke child table sesi dan simpan."""
	doc = _get_session_doc(session_id)
	doc.append(
		"messages",
		{
			"role": role,
			"content": content,
			"tool_calls": json.dumps(tool_calls) if tool_calls else "",
			"tool_call_id": tool_call_id or "",
		},
	)
	doc.message_count = (doc.message_count or 0) + 1
	doc.save(ignore_permissions=True)


def get_pending_action(session_id: str) -> dict | None:
	"""Muat pending write action dari sesi (atau ``None``)."""
	doc = _get_session_doc(session_id)
	if doc.pending_action:
		return json.loads(doc.pending_action)
	return None


def set_pending_action(session_id: str, action: dict | None) -> None:
	"""Simpan atau hapus pending action. Status sesi diubah sesuai."""
	doc = _get_session_doc(session_id)
	doc.pending_action = json.dumps(action) if action else ""
	doc.status = "Awaiting Confirmation" if action else "Active"
	doc.save(ignore_permissions=True)


def get_history_for_llm(session_id: str, max_messages: int = DEFAULT_MAX_MESSAGES) -> list:
	"""Muat pesan dan konversi ke objek pesan LangChain.

	Truncate ke ``max_messages`` terakhir untuk kontrol token.
	"""
	from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

	raw = load_messages(session_id)
	if len(raw) > max_messages:
		raw = raw[-max_messages:]
	messages = []
	for m in raw:
		if m["role"] == "user":
			messages.append(HumanMessage(content=m["content"]))
		elif m["role"] == "assistant":
			messages.append(AIMessage(content=m["content"], tool_calls=m["tool_calls"] or []))
		elif m["role"] == "tool":
			messages.append(ToolMessage(content=m["content"], tool_call_id=m["tool_call_id"] or ""))
	return messages
