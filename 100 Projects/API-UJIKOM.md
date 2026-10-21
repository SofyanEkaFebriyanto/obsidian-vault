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
- 2026-10-16: Audit statis repo `SofyanEkaFebriyanto/api-ujikom` terhadap 3 PDF modul guru (API-UJIKOM.pdf 132 hal, Membuat_Hak_akses, Modul_Projek_Inventory) selesai — migrations, models, Form Requests, Resources, controllers, observers, seeders, routes, middleware, package utama sesuai spek. Tindakan: selaraskan wording respons 403 `IsAdmin.php`, `IsPetugas.php`, `IsPeminjam.php` dengan PDF; commit `dad2cac` (`fix: selaraskan pesan 403 middleware role dengan spek modul`) dipush ke `main`. Klarifikasi: `/laporan-peminjaman` untuk role admin+petugas (PDF hal. 126) — repo sudah benar. Log: [[400 Daily/Noir 2026-10-16]].
- 2026-10-19: Verifikasi 5 jebakan drill di repo atas pertanyaan Sofyan — semua sudah benar: wording 403 persis PDF (`dad2cac` di main), `IsPeminjam` cek `'peminjam'` (typo di PDF, bukan di kode), `/laporan-peminjaman` admin+petugas, migrasi status `ditolak` ada, alias middleware di `bootstrap/app.php`. **Repo 100% sesuai PDF** untuk Tes Praktik Kamis 22 Okt (Gelombang 2, RPS A; Tes Tulis 21 Okt). Log: [[400 Daily/Noir 2026-10-19]].
- 2026-10-21: Pra Ujikom hari praktik LANGSUNG (koreksi Sofyan 20 Okt 22:42 mengalahkan PDF: tidak ada tes tulis). Insiden 09:27 dari lab: Laravel `InvalidArgumentException: Please provide a valid cache path` — root cause: root `.gitignore` meng-ignore `storage/framework/views`, `sessions`, `logs` tanpa placeholder → fresh clone tidak membentuk folder → `realpath()` false. Fix: hapus aturan ignore + tambah placeholder (commit `cd276f5`); PANDUAN-PRAKTIK.md ditambahkan ke root repo (commit `7ae195d`: flow Docker, blok .env MySQL, akun seed, troubleshooting, pola nambah fitur, jebakan PDF). Keduanya pushed 10:50 + terverifikasi clone fresh. Log: [[400 Daily/Noir 2026-10-21]].
- 2026-10-21: Koreksi pengawas 8 poin (dari sesi praktik) diimplementasikan malam hari — commit `a9d1885` (fix) + `cfd2ec2` (docs), pushed `7ae195d..cfd2ec2`: timezone 3 lapis (app +07:00, config database, compose), migrasi `2026_10_21_214500` DATE→DATETIME + form datetime-local + resource format Y-m-d H:i:s, kolom Foto di katalog peminjam + kelola user, ProfilController (web + API `/api/me`), register web paksa role peminjam + auto-login, cabang cetak Excel `.xls` + tombol PDF/Excel selalu tampil, KOREKSI-PENGAWAS.md (per poin: masalah, demo, jawaban buat pengawas). Verifikasi beneran: PHP statis 8.4.23, migrate:fresh+seed SQLite lolos, `php -l` bersih, artisan test 2 passed, smoke HTTP 17 cek lolos. **Semua pushed atas nama SofyanEkaFebriyanto** (perintah eksplisit Sofyan). Log: [[400 Daily/Noir 2026-10-21]].

## Open items
- [ ] Fitur ajukan-pengembalian sungguhan butuh migration nullable `petugas_id` (keputusan founder/guru).
- [ ] Cetak laporan (petugas) via dompdf — package ter-install, belum dipakai.
- [ ] REST API bab Kategori dst. sesuai API-UJIKOM.pdf.
- [ ] Banyak perubahan uncommitted.
