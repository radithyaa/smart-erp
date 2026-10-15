"""Adapter layer — pemisah akses ERP dari logika analitik (AGENT-RULES RULE 2.4 / NFR5).

Ini inti cerita hilirisasi: analitik (`process_intelligence`) **hanya** bicara ke
interface `ERPSource` di sini, tidak pernah langsung ke ORM/SQL ERPNext. Untuk
mendukung Odoo/SAP di masa depan, cukup tambah implementasi baru — tanpa mengubah
kode analitik maupun agent.

Semua adapter mengembalikan struktur **kanonik** (bukan DocType ERPNext), sehingga
konsumen tidak perlu tahu sistem sumbernya.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProcessEvent:
	"""Satu baris event log kanonik (F1).

	Format ini adalah kontrak antar-adapter: kolomnya identik dengan tabel kanonik
	pada SRS F1 — ``case_id | activity | timestamp | actor | doctype | reference``.
	"""

	case_id: str
	activity: str
	timestamp: str
	actor: str
	doctype: str
	reference: str

	def as_dict(self) -> dict:
		return {
			"case_id": self.case_id,
			"activity": self.activity,
			"timestamp": self.timestamp,
			"actor": self.actor,
			"doctype": self.doctype,
			"reference": self.reference,
		}


class ERPSource(ABC):
	"""Interface sumber ERP yang harus diimplementasi setiap adapter.

	Kontrak sengaja minimal: apa pun yang bisa menyediakan *event log* dan daftar
	*dokumen tertahan* dapat dipakai analitik proses. Tidak ada dependensi ke
	DocType/ORM di sini.
	"""

	#: Nama proses yang didukung adapter (dipakai validasi di layer analitik).
	process_name: str = ""

	@abstractmethod
	def fetch_events(self, process: str, *, period: str | None = None) -> list[ProcessEvent]:
		"""Ambil seluruh event log untuk sebuah proses.

		:param process: nama proses, mis. ``"purchase-to-pay"``.
		:param period: filter opsional ``"YYYY-MM"``; ``None`` = semua periode.
		:return: daftar :class:`ProcessEvent` terurut menaik berdasarkan timestamp.
		"""

	@abstractmethod
	def list_pending(self, process: str, stage: str) -> list[dict]:
		"""Dokumen yang masih tertahan di sebuah tahap proses.

		:return: daftar dict ``{case_id, reference, age_hours, owner}``.
		"""

	@abstractmethod
	def send_reminder(self, process: str, stage: str, references: list[str], message: str) -> dict:
		"""Kirim pengingat untuk dokumen yang tertahan di sebuah tahap (SRS §9 demo #4).

		Adalah tugas **adapter** untuk memutuskan mekanisme pengiriman pada sistem
		sumber (mis. ToDo + notifikasi di ERPNext). Analitik & agent tidak tahu
		detail ini — cukup memanggil method ini (RULE 2.4).

		:param process: nama proses, mis. ``"purchase-to-pay"``.
		:param stage: tahap proses tempat dokumen tertahan.
		:param references: daftar nama dokumen yang akan dikirimi pengingat.
		:param message: isi pesan pengingat dari agen.
		:return: dict ``{sent: int, recipients: list[str], references: list[str]}``.
		"""

	@abstractmethod
	def supported_processes(self) -> list[str]:
		"""Daftar nama proses yang bisa dilayani adapter ini."""
