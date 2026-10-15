# DEV-A-STATUS.md — Status Jalur Eksekusi (Dev A)

> Ringkasan pekerjaan **Dev A** (jalur eksekusi: *agent + tool layer + guardrail + chat*).
> Merujuk `docs/SRS.md` (F5–F8, NFR1–NFR3, NFR6, §10) dan `docs/DEV-TASKS.md` (§2, §6).
>
> Aturan yang dipatuhi: seluruh kode ada di **L2** (`apps/smart_erp_ai`), tidak
> menyentuh L1 (`RULE 1.1–1.2`); tool layer generik berbasis DocType (`RULE 2.3`);
> izin user login (`RULE 5.1`); konfirmasi aksi tulis (`RULE 5.2`); blokir
> destruktif (`RULE 5.3`); audit log (`RULE 5.4`); no hardcoded secret (`RULE 5.5`);
> allowlist DocType (`RULE 5.6`).

## ✅ Status: SEMUA TUGAS DEV A SELESAI + F4 & REMINDER

Seluruh task (A1–A7 + prerequisite DocTypes) terimplementasi, **42/42 unit test
lulus** (`bench run-tests`), dan **diverifikasi di site hidup**. Tambahan di iterasi
ini: **F4 Visualisasi** (panel analitik di UI) dan **fitur kirim reminder**
(skenario demo SRS §9 #4).

| Task | Req | Status | Lokasi |
|---|---|---|---|
| **A4-pre** DocType Audit Log | F8/NFR2 | ✅ | `smart_erp_audit_log/smart_erp_audit_log.json` + `.py` |
| **A2/A5-pre** DocType Chat Session + Message | F5 | ✅ | `smart_erp_chat_session/`, `smart_erp_chat_message/` |
| **§9#4-pre** DocType Reminder Log | §9/NFR2 | ✅ | `smart_erp_reminder_log/` |
| **A1** Tool layer generik | F5 | ✅ | `tools/frappe_tools.py` |
| **A6** Jembatan analisis→aksi | F7 | ✅ | `tools/analysis_tools.py` |
| **§9#4** Kirim reminder | §9/F7 | ✅ | `tools/analysis_tools.send_reminder` + adapter `send_reminder` |
| **A1/A6** Registry + schema (9 tool) | F5/F7 | ✅ | `tools/registry.py` |
| **A4** Audit log helper | F8/NFR2 | ✅ | `audit.py` |
| **A2/A5** Session CRUD (DB-backed) | F5 | ✅ | `session.py` |
| **A2** System prompt | F5 | ✅ | `agent/prompt.py` |
| **A2** LLM client (LangChain) | F5/NFR6 | ✅ | `agent/llm.py` |
| **A2/A4** Agent loop + confirmation gate | F5/F8 | ✅ | `agent/loop.py` |
| **A5** Chat endpoint | F5 | ✅ | `api.py` |
| **F4** Panel visualisasi (grafik + diagram alur) | F4 | ✅ | `api.py::analytics_overview` + `www/chat.html` |
| **F5-UI** Chat UI | F5 | ✅ | `www/chat.html` |
| **A7** Metrik validasi (≥20 commands) | §10/NFR1 | ✅ | `scripts/test-commands.md` |
| **A1–A8** Unit tests (42) | — | ✅ | `tests/test_agent.py` |
| **Config** pyproject.toml | — | ✅ | `pyproject.toml` (langchain deps) |

### Angka hasil verifikasi site hidup

| Hasil | Angka nyata |
|---|---|
| Unit test | **42/42 LULUS** (`bench run-tests`) |
| F4 bottleneck | Purchase Invoice 37.0j, Purchase Receipt 29.43j (keduanya `is_bottleneck`) |
| F4 diagram alur | 3 node (PO→PR→PI) dengan anotasi bottleneck |
| Rework (F3) | 10 kasus terdeteksi di panel |
| Reminder (§9#4) | 2 dikirim → 2 `ToDo` di Desk + 2 baris `Smart ERP Reminder Log` |

---

## Modul & Library yang Dibutuhkan

### Dependencies (pyproject.toml)

| Package | Versi | Kegunaan |
|---|---|---|
| `langchain` | `>=0.3,<0.4` | Framework agent loop, tool binding, message types |
| `langchain-openai` | `>=0.2,<0.3` | `ChatOpenAI` client (OpenAI-compatible: OpenAI, GLM, Azure) |
| `pydantic` | (transitif via langchain) | Args schema untuk `StructuredTool` |
| `frappe` | (via ERPNext stack) | ORM, `@frappe.whitelist()`, `frappe.conf`, session |

### Konfigurasi LLM (RULE 5.5 — no hardcoded secrets)

Konfigurasi dibaca dari **environment variable** (prioritas tertinggi) atau
**`site_config.json`**:

| Sumber | Key | Contoh |
|---|---|---|
| Env var | `SMART_ERP_LLM_API_KEY` | `sk-...` |
| Env var | `SMART_ERP_LLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4/` (GLM) |
| Env var | `SMART_ERP_LLM_MODEL` | `gpt-4o-mini` atau `glm-4-flash` |
| `site_config.json` | `llm_api_key` | `"sk-..."` |
| `site_config.json` | `llm_base_url` | `"https://api.openai.com/v1"` |
| `site_config.json` | `llm_model` | `"gpt-4o-mini"` |

Cara set di `site_config.json`:

```sh
bench --site erpnext.localhost set-config llm_api_key "sk-xxxxx"
bench --site erpnext.localhost set-config llm_base_url "https://api.openai.com/v1"
bench --site erpnext.localhost set-config llm_model "gpt-4o-mini"
```

Atau via environment variable di container:

```sh
export SMART_ERP_LLM_API_KEY="sk-xxxxx"
export SMART_ERP_LLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
export SMART_ERP_LLM_MODEL="glm-4-flash"
```

### Module Structure

```
apps/smart_erp_ai/smart_erp_ai/
├── agent/
│   ├── __init__.py
│   ├── llm.py              # ChatOpenAI client (config dari env/site_config)
│   ├── loop.py             # Agent loop: tool-calling + confirmation gate + audit
│   └── prompt.py           # System prompt (identitas, scope, aturan)
├── tools/
│   ├── __init__.py
│   ├── registry.py         # TOOL_REGISTRY + Pydantic schemas + get_langchain_tools()
│   ├── frappe_tools.py     # 5 generic DocType tools (list/get/create/update/submit)
│   └── analysis_tools.py   # 3 wrappers → process_intelligence/api.py (Dev B)
├── smart_erp_audit_log/    # DocType: audit trail
│   ├── __init__.py
│   ├── smart_erp_audit_log.json
│   └── smart_erp_audit_log.py
├── smart_erp_chat_session/ # DocType: session parent
│   ├── __init__.py
│   ├── smart_erp_chat_session.json
│   └── smart_erp_chat_session.py
├── smart_erp_chat_message/ # DocType: message child table
│   ├── __init__.py
│   ├── smart_erp_chat_message.json
│   └── smart_erp_chat_message.py
├── api.py                  # @frappe.whitelist() ask() endpoint
├── audit.py                # log_action() → Smart ERP Audit Log
├── session.py              # Session CRUD (DB-backed conversation state)
├── www/
│   └── chat.html           # Minimal chat UI (/chat)
├── tests/
│   └── test_agent.py       # 25+ unit tests
└── scripts/
    └── test-commands.md    # 20 validation commands (A7/NFR1)
```

---

## Yang Diimplementasi (Detail per Task)

### Task 1 — DocType `Smart ERP Audit Log` (A4 prerequisite)

- **File:** `smart_erp_audit_log/smart_erp_audit_log.json`, `.py`, `__init__.py`
- **Naming:** `autoincrement`
- **Fields:** `user` (Link→User), `tool_name` (Data), `doctype_affected` (Data),
  `arguments` (Code/JSON), `result` (Code/JSON), `status` (Select: Success/Blocked/
  Error/Confirmed/Rejected), `session_id` (Data)
- **Permissions:** `All` read-only (if_owner); `System Manager` full CRUD
- **Not submittable**

### Task 1b — DocTypes `Smart ERP Chat Session` + `Smart ERP Chat Message`

**Chat Session (parent):**
- **Naming:** `hash`
- **Fields:** `user` (Link→User), `status` (Select: Active/Awaiting Confirmation/
  Completed), `message_count` (Int, read-only), `messages` (Table→Chat Message),
  `pending_action` (Code/JSON)
- **Permissions:** `All` with `if_owner` (user hanya lihat sesi sendiri);
  `System Manager` full
- **Not submittable**

**Chat Message (child table):**
- **`istable`: 1**, naming: `hash`
- **Fields:** `role` (Select: user/assistant/tool), `content` (Long Text),
  `tool_calls` (Code/JSON), `tool_call_id` (Data), `created_on` (Datetime)

### Task 2 — `tools/frappe_tools.py` (A1 — Tool Layer Generik)

5 tool berbasis DocType (RULE 2.3 — generik, bukan per-fitur):

| Tool | Tipe | Konfirmasi? | Deskripsi |
|---|---|---|---|
| `list_documents(doctype, filters, limit)` | READ | Tidak | List dokumen via `frappe.get_all()` |
| `get_document(doctype, name)` | READ | Tidak | Ambil 1 dokumen via `frappe.get_doc()` |
| `create_document(doctype, data)` | WRITE | **Ya (F8)** | Buat via `frappe.new_doc()` + `.insert()` |
| `update_document(doctype, name, data)` | WRITE | **Ya (F8)** | Update via `.save()` |
| `submit_document(doctype, name)` | WRITE | **Ya (F8)** | Submit via `.submit()` |

Guardrails:
- `ALLOWED_DOCTYPES`: `Purchase Order`, `Purchase Receipt`, `Purchase Invoice`,
  `Supplier`, `Item` (RULE 5.6)
- `BLOCKED_ACTIONS`: `delete`, `cancel`, `amend` — **tidak ada fungsi sama sekali**
  (RULE 5.3)
- `_validate_doctype()` dipanggil di setiap tool
- Semua via Frappe ORM → otomatis memakai permission user login (RULE 5.1)

### Task 3 — `tools/analysis_tools.py` (A6 — Jembatan Analisis → Aksi)

4 thin wrapper ke `process_intelligence/api.py` (kontrak Dev B):

| Tool | Delegasi | Return | Konfirmasi? |
|---|---|---|---|
| `get_bottlenecks(process, period)` | `analysis_api.get_bottlenecks()` | `list[dict]` peringkat tahap | Tidak (READ) |
| `get_rework_cases(process, limit)` | `analysis_api.get_rework_cases()` | `list[dict]` kasus rework/deviasi | Tidak (READ) |
| `get_pending_at_stage(process, stage)` | `analysis_api.get_pending_at_stage()` | `list[dict]` dokumen tertahan | Tidak (READ) |
| `send_reminder(process, stage, references, message)` | `analysis_api.send_reminder()` | `dict` ringkasan pengiriman | **Ya (F8/WRITE)** |

`send_reminder` adalah **aksi tulis** (mengirim pengingat ke pemilik dokumen),
sehingga melewati confirmation gate di `agent/loop.py` dan dicatat di audit log
(RULE 5.2 & 5.4). Detail mekanisme pengiriman ada di adapter (RULE 2.4).

### Task 3b — Fitur Kirim Reminder (SRS §9 demo #4)

Skenario demo #4 SRS: *"Tampilkan daftar PO yang tertahan di approval **dan
kirim reminder**."*

**Alur:**
1. Agen memanggil `get_pending_at_stage` (READ) → daftar dokumen tertahan.
2. Agen merangkum & meminta konfirmasi (WRITE gata).
3. Setelah dikonfirmasi, `send_reminder` dipanggil → adapter membuat satu
   dokumen **`ToDo`** per dokumen tertahan (assignment ke `owner` dokumen),
   sehingga pengingat **terlihat nyata di ERPNext Desk**.
4. Setiap pengiriman dicatat di DocType **`Smart ERP Reminder Log`**
   (stage, reference, recipient, message, sent_by).
5. Aksi tercatat di `Smart ERP Audit Log` oleh `agent/loop.py` (status `Confirmed`).

**Mengapa `ToDo`, bukan email?** Agar pengingat **tidak bergantung pada
konfigurasi SMTP** (reprodusibel di demo sesuai NFR4) namun tetap dapat
diverifikasi di dalam ERP. Mekanisme ini dipilih di **adapter**
(`ERPNextSource.send_reminder`) — mengganti ke email/WhatsApp di masa depan
cukup mengubah adapter, tanpa menyentuh agent (RULE 2.4 & NFR5).

**Guardrail:** `references` divalidasi terhadap daftar yang **benar-benar masih
tertahan**; daftar kosong / dokumen yang sudah maju akan ditolak.

### Task 4 — `tools/registry.py` (A1/A6 — Registry + Schemas)

- `TOOL_REGISTRY`: dict **9 tool** → `{fn, args_schema, is_write, description}`
- Setiap tool punya Pydantic `BaseModel` args schema (untuk `StructuredTool`)
- `get_langchain_tools()`: menghasilkan `list[StructuredTool]` untuk
  `ChatOpenAI.bind_tools()`
- `get_tool(name)`: lookup tool entry (raises `KeyError` bila tidak ada)

### Task 5 — `audit.py` (A4 — Audit Log Helper)

- `log_action(user, tool_name, doctype_affected, arguments, result, status, session_id)`
- Membuat record `Smart ERP Audit Log` via `frappe.get_doc().insert(ignore_permissions=True)`
- Result di-truncate ke 10.000 karakter
- Tidak pernah mencatat secret/API key (RULE 5.4)

### Task 5b — `session.py` (A2/A5 — Session CRUD)

State percakapan disimpan **server-side** di DB. Klien hanya mengirim
`session_id` + `message` + `confirm` — tidak ada transfer history.

| Fungsi | Deskripsi |
|---|---|
| `get_or_create_session(session_id)` | Return session_id; buat baru bila None/not found |
| `load_messages(session_id)` | Load semua pesan sebagai `list[dict]` |
| `append_message(session_id, role, content, tool_calls, tool_call_id)` | Tambah pesan ke child table |
| `get_pending_action(session_id)` | Load pending write action (atau None) |
| `set_pending_action(session_id, action)` | Simpan/hapus pending; update status sesi |
| `get_history_for_llm(session_id, max_messages=20)` | Konversi pesan DB → objek LangChain; truncate 20 terakhir |

### Task 6 — `agent/prompt.py` (A2 — System Prompt)

System prompt dalam **Bahasa Indonesia**:
- **Identitas:** asisten Smart ERP untuk proses P2P
- **Scope:** hanya P2P (Purchase Order → Purchase Receipt → Purchase Invoice)
- **Aturan konfirmasi:** semua aksi tulis wajib konfirmasi eksplisit
- **Aturan destruktif:** tidak bisa delete/cancel
- **Panduan analitik:** gunakan tool analitik untuk pertanyaan proses; tawarkan
  tindak lanjut setelah menjawab

### Task 7 — `agent/llm.py` (A2 — LLM Client)

- `get_llm()` → `ChatOpenAI` (LangChain)
- Config dari env var / `site_config.json` (RULE 5.5)
- `base_url` configurable → mendukung GLM, Azure, atau endpoint OpenAI-compatible lainnya
- `temperature=0.3`, `timeout=30`
- `frappe.throw()` bila API key tidak dikonfigurasi

### Task 8 — `agent/loop.py` (A2/A4 — Agent Loop + Confirmation Gate)

`run_agent(session_id, message, confirm)`:

**Jalur konfirmasi** (`confirm=True`):
1. Load `pending_action` dari DB
2. Eksekusi write tool
3. Audit log (status: `Confirmed`)
4. Simpan tool result ke DB
5. Clear pending action
6. Feed result ke LLM untuk ringkasan akhir

**Jalur normal** (`confirm=False`):
1. Simpan pesan user ke DB
2. Bangun messages: SystemMessage + history dari DB
3. Loop (max 6 iterasi):
   - LLM response tanpa tool_calls → jawaban akhir, simpan ke DB, return
   - LLM request WRITE tool → simpan `pending_action` di DB, return
     `pending_confirmation`
   - LLM request READ tool → eksekusi langsung, audit log, simpan ke DB,
     lanjut loop
4. Melebihi 6 iterasi → return pesan batas

### Task 9 — `api.py` (A5 — Chat Endpoint)

```python
@frappe.whitelist()
def ask(message="", session_id=None, confirm="false") -> dict
```

- Mengembalikan `{session_id, reply, tool_calls, pending_confirmation}`
- First call: `session_id=None` → server buat sesi baru, return `session_id`
- Subsequent calls: klien kirim `session_id` yang sama

### Task 10 — `www/chat.html` (Chat UI + Panel Visualisasi F4)

- Single-page HTML dengan embedded JS/CSS
- Chat bubble area (user/assistant/tool/system)
- Konfirmasi gate: tombol "Konfirmasi" / "Batal"
- Collapsible tool call list
- Session ID disimpan di JS variable
- Accessible at `http://erpnext.localhost:8080/chat`
- Calls `frappe.call("smart_erp_ai.api.ask", {message, session_id, confirm})`

**Panel Analitik (F4)** — tombol "Panel Analitik" di header membuka panel yang
memanggil `smart_erp_ai.api.analytics_overview` dan merender:
1. **Grafik batang SVG** durasi rata-rata antar tahap proses (F2); tahap di atas
   threshold diberi warna berbeda (bottleneck).
2. **Diagram alur beranotasi** P2P (PO → PR → PI) dengan tanda bottleneck (F4).
3. Ringkasan tahap terlama + jumlah rework/deviasi (F3).

Panel dirancang rapi untuk **screenshot bersih** (bukti Prototype Alpha, SRS §4.1
F4 & §12). Warna memakai **CSS variables Frappe** (`--primary`, `--text-color`,
dst.) dengan token terpusat di `#analytics-panel`/`.chat-wrapper` (RULE 4.4),
bukan hex tersebar.

### Task 12 — `tests/test_agent.py` (Unit Tests)

**42** test case dalam 8 test class (½ diverifikasi: `bench run-tests` → OK):

| Test Class | Cakupan | Butuh Frappe? |
|---|---|---|
| `TestAllowlist` | DocType di luar allowlist ditolak | Tidak |
| `TestBlockedActions` | Tidak ada delete/cancel/amend di registry | Tidak |
| `TestRegistryIntegrity` | 9 tool terdaftar, write/read flag benar | Tidak |
| `TestFrappeToolsWithMock` | list/get/create/update/submit dengan mock | Mock |
| `TestAnalysisToolsWithMock` | 4 analysis tool (termasuk `send_reminder`) dengan mock | Mock |
| `TestAuditLogHelperWithMock` | log_action + truncation | Mock |
| `TestSessionWithMock` | CRUD + pending action + truncation | Mock |
| `TestLoopConfirmationGate` | Write tool marked, MAX_ITERATIONS=6 | Tidak |
| `TestDescribeAction` | Deskripsi aksi tulis (termasuk reminder) | Tidak |

### Task 13 — `scripts/test-commands.md` (A7 — Metrik Validasi)

21 test command dalam 4 kategori:
1. Basic document queries (1–5)
2. Create/submit flow (6–10)
3. Analysis queries (11–15)
4. Bridge/guardrail + reminder queries (16–21)

Target: success rate ≥80%, latency <10s per tool call.

### Task 14 — `api.py::analytics_overview` + `scripts/verify_f4_reminder.py` (F4 & Demo #4)

- Endpoint tipis `analytics_overview(process, period)` melayani panel F4 di UI,
  menggabungkan F2 (bottleneck) + F3 (rework) + diagram alur. Perhitungan tetap di
  `process_intelligence` (RULE 2.2).
- `scripts/verify_f4_reminder.py::run()` — helper verifikasi cepat di site hidup
  (bukan bagian alur demo), memanggil endpoint F4 + `send_reminder`.

---

## Cara Run

### 1. Setup (sekali saja)

```sh
# Pastikan app ter-install di site
bench --site erpnext.localhost install-app smart_erp_ai

# Migrate untuk membuat DocType baru
bench --site erpnext.localhost migrate

# Konfigurasi LLM
bench --site erpnext.localhost set-config llm_api_key "sk-xxxxx"
bench --site erpnext.localhost set-config llm_base_url "https://api.openai.com/v1"
bench --site erpnext.localhost set-config llm_model "gpt-4o-mini"
```

### 2. Seed data (prasyarat dari Dev B)

```sh
bench --site erpnext.localhost execute smart_erp_ai.scripts.seed_demo_data.run
```

### 3. Chat UI

Buka browser: `http://erpnext.localhost:8080/chat`

### 4. Via REST API

```sh
# Percakapan baru
curl -X POST http://erpnext.localhost:8080/api/method/smart_erp_ai.api.ask \
  -H "Content-Type: application/json" \
  -d '{"message":"apa status PO terakhir?","session_id":null,"confirm":"false"}'

# Konfirmasi aksi tulis
curl -X POST http://erpnext.localhost:8080/api/method/smart_erp_ai.api.ask \
  -H "Content-Type: application/json" \
  -d '{"message":"","session_id":"SES-xxx","confirm":"true"}'
```

### 5. Unit Tests

```sh
# Via bench (memerlukan site hidup)
bench --site erpnext.localhost set-config allow_tests true
bench --site erpnext.localhost run-tests --module smart_erp_ai.tests.test_agent

# Via pytest (pure python, tanpa site — hanya test yang tidak butuh frappe)
cd apps/smart_erp_ai
python -m pytest smart_erp_ai/tests/test_agent.py -v
```

### 6. Verifikasi DocTypes

```sh
# Cek DocType terdaftar
bench --site erpnext.localhost execute frappe.client.get_value \
  --args '["DocType", "Smart ERP Audit Log", "name"]'

# Cek audit log records
bench --site erpnext.localhost execute frappe.client.get_list \
  --args '["Smart ERP Audit Log", {"limit": 5}]'
```

---

## Peta ke SRS

| Req | Implementasi | Bukti |
|---|---|---|
| **F5** Agent + tool layer | `agent/`, `tools/`, `api.py` | Chat UI `/chat`, `ask()` endpoint |
| **F6** Alur P2P end-to-end | `frappe_tools.py` create/submit + confirmation gate | "buat PO" → konfirmasi → PO nyata di Desk |
| **F2/F3** Analysis queries | `tools/analysis_tools.py` (READ) | "bottleneck?", "rework?" |
| **F4** Visualisasi | `api.py::analytics_overview` + panel di `www/chat.html` | Grafik batang + diagram alur di `/chat` |
| **F7** Jembatan analisis→aksi | `analysis_tools.py` + prompt guidance | "bottleneck?" → analitik → tawaran "PO tertahan?" |
| **§9 #4** Kirim reminder | `tools/analysis_tools.send_reminder` → adapter `ToDo` + `Smart ERP Reminder Log` | "kirim reminder" → konfirmasi → ToDo di Desk |
| **F8** Guardrail + audit | `frappe_tools.py` (no delete/cancel), `loop.py` (confirmation gate), `audit.py` | Audit log records, confirmation flow |
| **NFR1** Respons <10s | LLM timeout=30s, MAX_ITERATIONS=6 | `scripts/test-commands.md` |
| **NFR2** Auditable | `audit.py` → Audit Log DocType | Setiap tool call tercatat dengan session_id |
| **NFR3** Aman | No delete/cancel function, allowlist DocType, confirmation gate | `BLOCKED_ACTIONS`, `ALLOWED_DOCTYPES` |
| **NFR6** LLM via API | `agent/llm.py` → `ChatOpenAI` (external API) | Config dari env/site_config |
| **§10** Metrik | `scripts/test-commands.md` | 20 test commands |

---

## Titik Integrasi dengan Dev B

| Titik | Dev A (konsumen) | Dev B (penyedia) | Kontrak |
|---|---|---|---|
| AnalysisQueryAPI | `tools/analysis_tools.py` | `process_intelligence/api.py` | `get_bottlenecks()`, `get_rework_cases()`, `get_pending_at_stage()` — return shape fixed |
| Event log | Tidak langsung | `process_intelligence/event_log.py` | Dev A hanya via `analysis_tools.py` |
| Adapter | Tidak langsung | `adapter/erpnext_source.py` | Dev A tidak import adapter langsung |
| Seed data | Prasyarat demo | `scripts/seed_demo_data.py` | Dev A butuh data P2P untuk demo chat |

---

## Asumsi & Catatan

- **Indentation:** Semua kode L2 memakai **tab** (konvensi Frappe/ERPNext), bukan
  spasi.
- **`modules.txt`:** Berisi `Smart ERP AI` — ini adalah nama modul Frappe yang
  dirujuk di field `module` pada semua DocType JSON.
- **LangChain + Frappe WSGI:** Memakai sync `invoke()`, bukan `ainvoke()`.
  Frappe request lifecycle bersifat synchronous.
- **Conversation state:** Disimpan server-side di DB (`Smart ERP Chat Session`
  + `Smart ERP Chat Message`). Klien hanya mengirim `session_id` + `message` +
  `confirm`. Survives page reload.
- **Child table DocType:** `Smart ERP Chat Message` memakai `"istable": 1`,
  `"autoname": "hash"`. Parent field `messages` bertipe `Table` dengan
  `options: "Smart ERP Chat Message"`.
- **DocType permissions:** `Smart ERP Audit Log` — `All` read-only,
  `System Manager` full. `Smart ERP Chat Session` — `All` dengan `if_owner`
  (user hanya lihat sesi sendiri), `System Manager` full.
- **`frappe.conf.get("llm_api_key")`:** Membaca dari `site_config.json`
  (site-specific, bukan `common_site_config.json`).
- **Frappe auto-routing:** `www/chat.html` otomatis di-serve di `/chat` tanpa
  konfigurasi `website_route_rules` di `hooks.py`.
- **Hooks.py:** Tidak ada perubahan yang diperlukan — DocType auto-discovered
  oleh Frappe. `fixtures` tetap `[]`.
- **`hooks.py` tidak diubah** — DocType baru auto-discovered oleh Frappe.
- **Tidak ada patch L1** → `docs/CHANGELOG-L1-PATCHES.md` tetap kosong.
- **Dependensi baru:** `langchain` + `langchain-openai` ditambahkan ke
  `pyproject.toml`. Catat di `docs/THIRD-PARTY.md` bila diperlukan.
