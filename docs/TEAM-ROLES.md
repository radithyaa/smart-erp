# TEAM-ROLES.md — Peran, Tanggung Jawab & Pembagian Tugas Tim

> Dokumen ini merujuk pada `ANGEL INNOVATION HACKATHON GUIDELINE PROGRAM.pdf` §3.1 (Komposisi Tim),
> §4.1 (Dokumen Pendaftaran), dan Lampiran 3 (Format Proposal / Lembar Identitas).
> Tujuan: (a) memenuhi kewajiban "uraikan peran setiap anggota", (b) pembagian kerja teknis saat
> hackathon, (c) dasar bagi startup/hilirisasi pasca-program.

---

## ⚠️ BLOKER WAJIB DIBACA DULU — Komposisi Tim Saat Ini Tidak Memenuhi Syarat

Tim saat ini: **4 orang** (mahasiswa × 4: 1 teknis, 1 desain, 1 bisnis, 1 generalis).
Guideline mewajibkan **minimal 1 dosen** sebagai ketua **atau** anggota (§3.1 butir 2), dan
**Lembar Identitas menempatkan "Ketua Tim Pelaksana" dengan field NIDN/NIDK/NUPTK** — field itu
hanya bisa diisi dosen. **Artinya ketua tim pelaksana harus dosen.**

**Status saat ini:** **SOLVED** — dosen mentor dianggap sudah ada (dikonfirmasi tim). Tim efektif =
**1 dosen (Ketua Tim Pelaksana + mentor) + 4 mahasiswa = 5 orang**, memenuhi batas 3–6 orang.

**Yang perlu disiapkan untuk dosen (sekali saja):**
1. Data NIDN/NIDK/NUPTK + jabatan struktural/fungsional + institusi + alamat — untuk Lembar Identitas.
2. Persetujuan kesediaan menjadi mentor (dan tanda tangan Ketua Tim Pelaksana di lembar identitas).
3. Briefing singkat: dosen berperan **mentor**, bukan pengganti peran mahasiswa dalam membangun
   prototipe (§3.2.1 butir 3).

> Sisa dokumen ini fokus pada **pembagian tugas 4 mahasiswa** (dosen hanya mengawal).

---

## 1. Struktur Peran Resmi (sesuai Guideline §3.1 butir 4)

Guideline menyebut 3 peran **wajib** + 1 opsional. Tema AI tidak termasuk regulasi ketat, jadi
peran opsional "operasional/regulasi" **tidak perlu diisi** (namun jejak kepatuhan tetap dijaga —
lihat §4 di bawah).

| Peran Resmi Guideline | Siapa di tim | Ringkas |
|---|---|---|
| Ketua Tim Pelaksana (dosen, NIDN/NIDK/NUPTK) | **Dosen** | Mentor + penanggung jawab akademik |
| Koordinator Teknis | **Anggota 1 (teknis)** | Rancang & bangun prototipe |
| Koordinator Bisnis & Hilirisasi | **Anggota 3 (bisnis)** | Model bisnis, GTM, komersialisasi |
| Koordinator Validasi Pengguna | **Anggota 2 (desain)** | Interaksi user, kumpulkan kebutuhan, uji |

---

## 2. Peran, Tanggung Jawab, dan Pembagian Tugas

### 2.1 Dosen — Ketua Tim Pelaksana (+ Mentor)

**Di startup/aplikasi:**
- Penasihat teknis & akademik; mengawal kualitas riset (TKT, metrik, metodologi).
- Menjembatani kolaborasi dengan Industry Problem Owner (PT Javan Cipta Solusi) dan kampus.
- Tidak mengerjakan kode/prototipe (sesuai §3.2.1 butir 3) — perannya mengawal, bukan menggantikan.
- Penanggung jawab kepatuhan akademik: pakta integritas, orisinalitas, dan posisi TKT.

**Tugas pengumpulan:**
- Lembar Identitas bagian "Ketua Tim Pelaksana" (NIDN/NIDK/NUPTK, tanda tangan).
- Menandatangani Pakta Integritas bersama seluruh anggota.
- Menyediakan CV/RIWAYAT hidup singkat (portofolio dosen).
- Review akhir proposal 3 halaman sebelum submit.

---

### 2.2 Anggota 1 — Koordinator Teknis (Mahasiswa, "Dev A")

**Peran resmi guideline:** Koordinator teknis — perancangan & pengembangan aspek teknologi/prototipe.

**Di startup/aplikasi:**
- **CTO/Lead Engineer.** Pemilik seluruh arsitektur teknis: layer `apps/smart_erp_ai`
  (agent, process intelligence, tool layer, adapter) sesuai `docs/SRS.md` dan `docs/AGENT-RULES.md`.
- Pengambil keputusan teknis: versi ERPNext, stack LLM, desain tool layer, guardrail.

**Tugas selama hackathon:**
- Scaffold `apps/smart_erp_ai` (struktur modular RULE 2.1).
- Agent loop + tool calling generik berbasis DocType (F5).
- Alur end-to-end Purchase-to-Pay (F6).
- Guardrail + audit log (F8) bersama Anggota 4.
- Menjaga kode tetap di L2; tidak mengedit L1 (AGENT-RULES RULE 1.1–1.2).

**Tugas pengumpulan:**
- Bukti Prototype Alpha: tautan repo + screenshot aplikasi.
- Bagian teknis proposal: arsitektur, TKT (target 3–4), metrik teknis (task success rate).
- Dokumentasi teknis untuk demo (readme menjalankan).

---

### 2.3 Anggota 2 — Koordinator Validasi Pengguna (Mahasiswa, desainer, "Dev C-UI")

**Peran resmi guideline:** Koordinator validasi pengguna — interaksi mitra industri, pengumpulan
kebutuhan, dan pengujian solusi di lapangan.

**Di startup/aplikasi:**
- **Head of Product / UX & User Validation.** Jembatan antara kebutuhan industri dan produk.
- Pemilik pengalaman pengguna (chat UI, visualisasi analisis) dan bukti kebutuhan pengguna.

**Tugas selama hackathon:**
- Chat UI + tampilan hasil analisis (F4) yang bisa di-screenshot bersih.
- Merancang skenario demo tetap (§9 SRS) agar alur mulus.
- Mengumpulkan bukti kebutuhan pengguna (wawancara/observasi dengan calon pengguna, sekecil apa pun).
- Menyusun skrip demo & mengatur pengambilan video bukti.

**Tugas pengumpulan:**
- Bukti kebutuhan pengguna → untuk kriteria "Problem–Solution Fit" (20%) & "Bukti kebutuhan" di seleksi.
- Screenshot UI, desain low-fidelity, dan storyboard demo.
- Bagian proposal: problem statement dari sudut pengguna + sasaran pengguna.

---

### 2.4 Anggota 3 — Koordinator Bisnis & Hilirisasi (Mahasiswa, "bizdev")

**Peran resmi guideline:** Koordinator bisnis & hilirisasi — model bisnis, strategi masuk pasar,
rencana komersialisasi/integrasi.

**Di startup/aplikasi:**
- **CEO/Head of Business.** Model bisnis, strategi Go-To-Market (cloud-only SaaS), pricing, jalur
  hilirisasi & kemitraan (termasuk cerita adapter multi-ERP).

**Tugas selama hackathon:**
- Menyusun Business Model Canvas & rencana hilirisasi (dasar bagian 20% "Research Downstreaming").
- Mengelola narasi TKDN & IP (10%) bersama Anggota 4: jujur menyebut ERPNext open source,
  klaim orisinalitas hanya pada layer L2.
- Menyiapkan pitch & jawaban untuk juri non-teknis.

**Tugas pengumpulan:**
- Bagian proposal: hilirisasi, potensi dampak, model komersialisasi cloud-only.
- Ringkasan singkat model bisnis + target pasar.
- Dukungan mitra industri bila ada (surat dukungan/komitmen).

---

### 2.5 Anggota 4 — Kamu (Generalis: Teknis + Integrasi + Dokumen, "Dev B")

**Peran resmi guideline:** Bisa dikombinasikan, mis. **Koordinator Teknis (pendamping) +
operasional**. Karena kamu bisa "semuanya", posisikan sebagai **integrator/wildcard**.

**Di startup/aplikasi:**
- **Co-Founder / Full-stack integrator.** Menambal celah: process intelligence (topik 2), integrasi,
  dan kepemimpinan operasional.

**Tugas selama hackathon:**
- Process intelligence: event log extractor (F1), bottleneck (F2), rework/deviasi (F3).
- Generator data dummy P2P (200–500 kasus dengan bottleneck sengaja) — prasyarat analisis.
- Integrasi antar-modul + menjaga kontrak API (RULE 2.2) & adapter layer (RULE 2.4).
- Koordinasi harian, unblock tim, dan mengerjakan tugas dokumen yang tertinggal.

**Tugas pengumpulan:**
- Koordinator utama penyusunan proposal 3 halaman (mengompilasi kontribusi semua).
- Memastikan seluruh dokumen pendaftaran lengkap & konsisten.
- Bukti Prototype Alpha: video demo + daftar metrik nyata.

---

## 3. Matriks RACI Ringkas (siapa mengerjakan apa)

| Area Kerja | Dosen | Ang.1 Teknis | Ang.2 Validasi/UI | Ang.3 Bisnis | Ang.4 Generalis |
|---|---|---|---|---|---|
| Arsitektur & agent (L2) | A | **R** | C | I | R |
| Process intelligence (topik 2) | C | C | I | I | **R** |
| Chat UI & visualisasi | I | C | **R** | I | C |
| Guardrail & audit | A | **R** | I | C | R |
| Data dummy & seed | I | C | I | I | **R** |
| Model bisnis & hilirisasi | C | I | C | **R** | C |
| Validasi pengguna & bukti kebutuhan | A | I | **R** | C | C |
| Proposal 3 halaman & TKT | A | C | C | C | **R** |
| Pakta integritas & dokumen ID | **R** | C | C | C | **R** |
| Demo & video bukti | C | C | **R** | C | R |

R = Responsible (mengerjakan) · A = Accountable (menyetujui) · C = Consulted · I = Informed

---

## 4. Pembagian Tugas untuk DOKUMEN PENDAFTARAN (§4.1)

Berikut pemetaan siapa menyiapkan apa agar tidak ada yang terlewat saat submit.

| # | Dokumen (Guideline §4.1) | Penanggung jawab | Catatan |
|---|---|---|---|
| 1 | **Daftar Riwayat Hidup** ketua & seluruh anggota | Ang.4 koordinasi; tiap orang mengisi CV-nya | Sertakan portofolio/sertifikat bila ada (nilai tambah) |
| 2 | **Pakta Integritas** (orisinalitas, belum pernah menang, komitmen) | Dosen + Ang.4 | Ditandatangani **seluruh** anggota; perhatikan klaim orisinalitas (hanya L2) |
| 3 | **Bukti Purwarupa/Desain Awal** (foto, screenshot, tautan, video) | Ang.1 (teknis) + Ang.2 (UI) | Screenshot aplikasi + tautan prototype + video pendek |
| 4 | **Proposal Purwarupa Awal** (maks 3 halaman A4) | Ang.4 lead; semua kontribusi | Isi: latar belakang, deskripsi inovasi, rencana kegiatan, komposisi tim, dukungan mitra, posisi TKT |
| 5 | **Kelengkapan identitas tim** (Lembar Identitas) | Dosen + Ang.4 | NIDN/NIDK/NUPTK dosen wajib terisi |
| 6 | **Bukti kemitraan** (jika ada) | Ang.3 | Surat dukungan/komitmen mitra industri |

### Checklist akhir sebelum submit
- [ ] Dosen terdaftar & NIDN/NIDK/NUPTK terisi di Lembar Identitas.
- [ ] Semua CV terkumpul (dosen + 4 mahasiswa).
- [ ] Pakta integritas ditandatangani semua pihak (termasuk dosen).
- [ ] Bukti prototipe: screenshot + video + tautan repo.
- [ ] Proposal ≤ 3 halaman, format TNR 12 / spasi 1.15, memuat 6 poin wajib.
- [ ] Posisi TKT dicantumkan (target 3–4, diutamakan 3–6).
- [ ] Klaim orisinalitas hanya pada layer L2; ERPNext disebut jujur sebagai base open source.

---

## 5. Pembagian Tugas Startup (pasca-hackathon, untuk bagian Hilirisasi)

| Fungsi | Pemilik |
|---|---|
| CEO / Business & Commercialisation | Ang.3 (dibantu Ang.4) |
| CTO / Product & Engineering | Ang.1 (dibantu Ang.4) |
| CPO / UX, Product & User Validation | Ang.2 |
| COO / Operasional, Integrasi & Kepatuhan | Ang.4 |
| Penasihat Akademik & Riset | Dosen mentor |

> Konfigurasi ini menjaga tiap fungsi punya pemilik tunggal (accountability) — penting untuk
> pertanyaan juri "siapa bertanggung jawab bila produk gagal di tahap ini?".
