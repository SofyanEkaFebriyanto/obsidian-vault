---
type: project
project: API-UJIKOM
date: 2026-08-26
tags: [api-ujikom, laravel, sekolah, ujikom]
ai-first: true
status: panel-web-selesai
---

## For future agent
Project note untuk tugas sekolah ujikom SMK: sistem peminjaman alat Laravel 12. Repo `/home/sofyan/Documents/project/01.API-UJIKOM`. ATURAN PENTING: ini tugas sekolah — Hermes hanya memberi panduan/koordinasi CEO flow; Sofyan mengerjakan kodenya sendiri. Kiblat = 3 modul guru di root repo (API-UJIKOM.pdf 132 hal = REST API utama; Modul Projek Inventory System.pdf = web Blade; Membuat_Hak_Akses...md = versi markdown dari PDF kedua).

# API-UJIKOM — Sistem Peminjaman Alat (Ujikom)

## Status
- **Sisi web Blade: SELESAI + teruji** (2026-08-26). Semua 14 baris matriks fitur modul kecuali "Mencetak Laporan".
- REST API (API-UJIKOM.pdf bab 5+): ~35% — baru sampai autentikasi (register/login/me/logout, FormRequest, UserResource, middleware role).
- Docker: `laravel-api` :8000, `MySQL-API` :3309 (db API_ujikom / api_ujikom), phpMyAdmin :8081.

## Struktur
- 3 role: admin (CRUD user/alat/kategori/peminjaman/pengembalian + log aktivitas), petugas (setujui peminjaman, proses pengembalian), peminjam (katalog, ajukan, riwayat).
- Model: Alat, Kategori, Peminjaman, DetilPinjam (tabel `detail_pinjam`), Pengembalian, LogAktivitas. Enum status peminjaman: diajukan/dipinjam/dikembalikan/ditolak/telat.
- Akun seed (password `password123`): admin@gmail.com, petugas@gmail.com, rian@gmail.com.

## Recent Activity
- 2026-08-26: Panel admin tuntas via CEO flow — bug fix enum+DetilPinjam typo, upload gambar, CRUD pengembalian admin, role-aware sidebar, form petugas. Log: [[400 Daily/Dev Logs/2026-08-26 - API-UJIKOM panel admin]]

## Open items
- [ ] Fitur ajukan-pengembalian sungguhan butuh migration nullable `petugas_id` (keputusan founder/guru).
- [ ] Cetak laporan (petugas) via dompdf — package ter-install, belum dipakai.
- [ ] REST API bab Kategori dst. sesuai API-UJIKOM.pdf.
- [ ] Banyak perubahan uncommitted.
