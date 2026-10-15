"""A2 — LLM client via LangChain (RULE 5.5 — no hardcoded secrets).

Membaca konfigurasi dari environment variable atau ``site_config.json``.
Mendukung OpenAI, GLM, dan endpoint OpenAI-compatible lainnya via ``base_url``.
"""

from __future__ import annotations

import os

import frappe
from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
	"""Buat klien LLM. Konfigurasi dari env / site_config (RULE 5.5).

	Environment variables (prioritas tertinggi):
	    SMART_ERP_LLM_API_KEY   — API key
	    SMART_ERP_LLM_BASE_URL  — base URL (opsional; untuk GLM dll.)
	    SMART_ERP_LLM_MODEL     — nama model (default: ``gpt-4o-mini``)

	Atau dari ``site_config.json``:
	    ``llm_api_key``, ``llm_base_url``, ``llm_model``
	"""
	api_key = os.environ.get("SMART_ERP_LLM_API_KEY") or frappe.conf.get("llm_api_key")
	base_url = os.environ.get("SMART_ERP_LLM_BASE_URL") or frappe.conf.get("llm_base_url")
	model = os.environ.get("SMART_ERP_LLM_MODEL") or frappe.conf.get("llm_model") or "gpt-4o-mini"

	if not api_key:
		frappe.throw(
			"LLM API key not configured. Set SMART_ERP_LLM_API_KEY env var or "
			"llm_api_key in site_config.json."
		)

	kwargs: dict = {
		"model": model,
		"api_key": api_key,
		"temperature": 0.3,
		"timeout": 30,
	}
	if base_url:
		kwargs["base_url"] = base_url

	return ChatOpenAI(**kwargs)
