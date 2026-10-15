"""A2/A4 — Agent loop dengan tool-calling + confirmation gate (F8).

State percakapan dimuat dari dan disimpan ke DB via ``session.py``.
READ tool dieksekusi langsung dalam loop. WRITE tool menjeda → menyimpan
``pending_action`` di DB → mengembalikan ``pending_confirmation``.
Pada panggilan berikutnya dengan ``confirm=True``, server memuat pending
dari DB, mengeksekusi, lalu melanjutkan.
"""

from __future__ import annotations

import json

import frappe
from langchain_core.messages import SystemMessage, ToolMessage

from smart_erp_ai import audit, session
from smart_erp_ai.agent import llm as llm_module
from smart_erp_ai.agent import prompt
from smart_erp_ai.tools import registry

#: Batas iterasi agent (mencegah infinite loop).
MAX_ITERATIONS = 6


def _describe_action(tool_name: str, args: dict) -> str:
	"""Hasilkan deskripsi ramah-pengguna untuk aksi tulis."""
	doctype = args.get("doctype", "")
	name = args.get("name", "")
	if tool_name == "create_document":
		return f"membuat {doctype} baru dengan data: {json.dumps(args.get('data', {}), ensure_ascii=False)}"
	elif tool_name == "update_document":
		return f"memperbarui {doctype} {name} dengan data: {json.dumps(args.get('data', {}), ensure_ascii=False)}"
	elif tool_name == "submit_document":
		return f"men-submit/menyetujui {doctype} {name}"
	return f"menjalankan {tool_name} pada {doctype}"


def _execute_tool(tool_name: str, args: dict, user: str) -> dict:
	"""Eksekusi tool berdasarkan nama dan args. Kembalikan hasil dict."""
	entry = registry.get_tool(tool_name)
	fn = entry["fn"]
	return fn(**args)


def _build_llm_messages(session_id: str) -> list:
	"""Bangun daftar pesan untuk LLM: SystemMessage + history dari DB."""
	messages = [SystemMessage(prompt.SYSTEM_PROMPT)]
	messages.extend(session.get_history_for_llm(session_id))
	return messages


def run_agent(session_id: str, message: str, confirm: bool = False) -> dict:
	"""Jalankan satu putar agent.

	:param session_id: ID sesi DB (state percakapan tersimpan server-side).
	:param message: pesan baru user (string kosong jika konfirmasi pending action).
	:param confirm: ``True`` bila user mengkonfirmasi pending write action.
	:return: ``{"reply": str, "tool_calls": list, "pending_confirmation": dict | None}``.
	"""
	user = frappe.session.user

	# --- Jalur konfirmasi: user mengkonfirmasi aksi tulis pending ---
	pending = session.get_pending_action(session_id)
	if confirm:
		if not pending:
			return {
				"reply": "Tidak ada aksi yang menunggu konfirmasi.",
				"tool_calls": [],
				"pending_confirmation": None,
			}
		# User mengkonfirmasi — eksekusi write tool
		result = _execute_tool(pending["tool"], pending["args"], user)
		audit.log_action(
			user,
			pending["tool"],
			pending["args"].get("doctype", ""),
			pending["args"],
			result,
			"Confirmed",
			session_id=session_id,
		)
		session.append_message(
			session_id, "tool", json.dumps(result),
			tool_call_id=pending.get("tool_call_id"),
		)
		session.set_pending_action(session_id, None)

		# Feed result ke LLM untuk ringkasan akhir
		messages = _build_llm_messages(session_id)
		messages.append(
			ToolMessage(
				content=json.dumps(result),
				tool_call_id=pending.get("tool_call_id") or "",
			)
		)
		llm = llm_module.get_llm().bind_tools(registry.get_langchain_tools())
		response = llm.invoke(messages)
		session.append_message(session_id, "assistant", response.content)
		return {
			"reply": response.content,
			"tool_calls": [pending],
			"pending_confirmation": None,
		}

	# --- Jalur normal: pesan baru dari user ---
	session.append_message(session_id, "user", message)

	llm = llm_module.get_llm().bind_tools(registry.get_langchain_tools())
	messages = _build_llm_messages(session_id)

	tool_calls_log: list[dict] = []

	for _iteration in range(MAX_ITERATIONS):
		response = llm.invoke(messages)

		if not response.tool_calls:
			# Jawaban akhir — simpan ke DB
			session.append_message(
				session_id, "assistant", response.content, tool_calls=[]
			)
			return {
				"reply": response.content,
				"tool_calls": tool_calls_log,
				"pending_confirmation": None,
			}

		for tool_call in response.tool_calls:
			tool_name = tool_call["name"]
			tool_args = tool_call["args"]
			tool_entry = registry.get_tool(tool_name)

			if tool_entry["is_write"]:
				# WRITE — jeda: simpan pending action, minta konfirmasi
				pending_action = {
					"tool": tool_name,
					"args": tool_args,
					"description": _describe_action(tool_name, tool_args),
					"tool_call_id": tool_call["id"],
				}
				session.set_pending_action(session_id, pending_action)
				session.append_message(
					session_id,
					"assistant",
					f"Saya akan {pending_action['description']}. Lanjutkan?",
					tool_calls=[{"name": tool_name, "args": tool_args, "id": tool_call["id"]}],
				)
				return {
					"reply": f"Saya akan {pending_action['description']}. Lanjutkan?",
					"tool_calls": tool_calls_log,
					"pending_confirmation": pending_action,
				}
			else:
				# READ — eksekusi langsung
				result = _execute_tool(tool_name, tool_args, user)
				audit.log_action(
					user,
					tool_name,
					tool_args.get("doctype", ""),
					tool_args,
					result,
					"Success",
					session_id=session_id,
				)
				tool_calls_log.append(
					{
						"tool": tool_name,
						"args": tool_args,
						"result_preview": str(result)[:200],
					}
				)
				# Simpan AI tool-call message + tool result ke DB
				session.append_message(
					session_id,
					"assistant",
					"",
					tool_calls=[{"name": tool_name, "args": tool_args, "id": tool_call["id"]}],
				)
				session.append_message(
					session_id,
					"tool",
					json.dumps(result),
					tool_call_id=tool_call["id"],
				)
				messages.append(response)
				messages.append(
					ToolMessage(
						content=json.dumps(result),
						tool_call_id=tool_call["id"],
					)
				)

	# Melebihi batas iterasi
	return {
		"reply": "Maaf, saya tidak bisa menyelesaikan permintaan ini dalam batas iterasi.",
		"tool_calls": tool_calls_log,
		"pending_confirmation": None,
	}
