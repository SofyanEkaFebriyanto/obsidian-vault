---
type: dev-log
project: "[[100 Projects/API-UJIKOM]]"
date: 2026-08-26
tags: [api-ujikom, laravel, panel-admin, ceo-flow, sekolah]
ai-first: true
---

## For future agent
Dev log penyelesaian panel admin project 01.API-UJIKOM (tugas sekolah ujikom SMK — Sofyan mengerjakan sendiri; Hermes HANYA pandu + koordinasi CEO flow, tidak menulis kode proyek secara langsung kecuali cleanup artefak `</parameter>` yang diminta founder). Kiblat implementasi = 3 modul guru di root repo. Semua verifikasi angka (stok, test count) dicek langsung, bukan klaim subagent.

# Dev Log — API-UJIKOM Panel Admin Tuntas (2026-08-26)

## Context
Project: `/home/sofyan/Documents/project/01.API-UJIKOM` — Laravel 12 sistem peminjaman alat, 3 role (admin/petugas/peminjam), Docker compose (`laravel-api` :8000, `MySQL-API` :3309 db `API_ujikom`). Audit awal menemukan sisi web Blade hampir selesai tapi ada 3 bug logika + fitur bolong. Eksekusi via flow skill `kenfa-ceo` adaptasi: backend → frontend → QA → bugfix serial (repo kecil, hindari race).

## What changed
1. **Bug fix**: enum status `ditolak` ditambah via migration baru `2026_08_26_042608_add_ditolak_to_peminjaman_table` (enum kini: diajukan,dipinjam,dikembalikan,ditolak,telat); typo fatal `DetailPinjam::class` → `DetilPinjam::class` di model Peminjaman **dan Alat** (4 endpoint 500 → normal); updateUser bisa ganti password opsional (nullable + filled guard); redirect updateStatus balik ke back().
2. **Upload gambar**: alat (`store('alat','public')`) + foto profile user (`profile/`), validasi image max 2MB, hapus file lama saat replace/delete, storage:link aktif, thumbnail 40px di index.
3. **CRUD Pengembalian untuk Admin** (matriks modul): route index/store/update/destroy di grup admin, transaksi + restok otomatis (stok terverifikasi 15→16 saat kembali, 16→15 saat rollback destroy), menu sidebar "Kelola Pengembalian", form cepat di show/index peminjaman.
4. **Role-aware sidebar** (`layouts/app.blade.php`): judul dinamis per role, admin 5 menu, petugas cuma "Daftar Peminjaman" — fix bug petugas kena 403 karena menu admin tampil semua. Peminjam tetap view standalone.
5. **Form pengembalian petugas**: tombol Setujui (diajukan) + form Proses Pengembalian kondisi/denda (dipinjam) + badge Dikembalikan, di `petugas/peminjaman/index.blade.php`.
6. **Peminjam "Ajukan Pengembalian"** di riwayat — FALLBACK saja: kolom `pengembalian.petugas_id` NOT NULL sehingga tanpa migration baru peminjam tak bisa bikin record menunggu-konfirmasi; tombol hanya memunculkan pesan info. IDOR-safe (404 utk milik orang lain).
7. **Kerapian**: pagination indexAlat paginate(5); guard delete kategori masih dipakai alat; log aktivitas konsisten di ketiga controller; cleanup artefak literal `</parameter>` di 6 file blade (oleh Hermes langsung).

## Verifikasi
- QA smoke E2E 10 skenario curl+CSRF: PASS semua setelah bugfix DetailPinjam (login/logout/dashboard/CRUD user-alat-kategori/peminjaman+enum ditolak/pengembalian/log/logout/RBAC 403).
- Stok before-after diverifikasi query MySQL langsung, bukan klaim agent.
- `php artisan test`: 2 passed; migrate:status bersih 11 Ran; seed data utuh (users 6, kategori 5, alat 5); QA data tes dibersihkan.
- Seeder TIDAK diubah — sesuai modul pola foreach+create; reset data = `docker exec laravel-api php artisan migrate:fresh --seed` (keputusan opsi A).

## Decisions
- **Opsi A seeder**: ikut modul mentah (create() biasa), idempotency diabaikan — biar 1:1 sama modul guru saat demo; aturan pakai: selalu migrate:fresh --seed.
- **Pengembalian = domain petugas + admin** sesuai matriks PDF hal.1; peminjam cuma ajukan (fallback karena constraint NOT NULL).
- **Tidak buat migration baru** untuk fitur ajukan-pengembalian penuh — butuh keputusan founder/guru dulu (nullable vs kolom status_pengajuan).

## Next steps
- [ ] Keputusan founder: migration nullable `petugas_id` untuk fitur ajukan pengembalian sungguhan?
- [ ] Fitur "Mencetak Laporan" (Petugas) via dompdf — sudah ter-install composer, belum dipakai.
- [ ] REST API per API-UJIKOM.pdf bab 5+ (Kategori API dst.) — baru ~35% materi modul API terimplementasi.
- [ ] Commit: banyak perubahan uncommitted di backend/.
