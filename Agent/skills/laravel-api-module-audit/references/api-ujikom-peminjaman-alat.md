# 01.API-UJIKOM — Audit Detail (Peminjaman Alat, Laravel 12 REST API)

Verified state of `~/Documents/project/01.API-UJIKOM` as of 2026-10-01.
Spec source: `API-UJIKOM.pdf` (132 pages, "STUDI KASUS: Sistem Peminjaman Alat",
PPLG SMKN7 Baleendah). Extracted with
`pdftotext -layout API-UJIKOM.pdf /tmp/ujikom.txt` → ~5071 lines.

## Project shape

- Stack: Docker Compose, `mysql:8.0` + `app-laravel` + `phpmyadmin`.
- Host port conflict avoidance: MySQL mapped to **3309** (not 3306, which collides
  with the kenfa-2.0 stack); Laravel 8000; phpMyAdmin 8081.
- Compose file is named `docker-compose.yaml`; spec says `docker-compose.yml`.
  Both work, but commands referencing the spec's name will fail.
- `.env` DB block matches compose: `DB_HOST=mysql-server`, `DB_DATABASE=API_ujikom`,
  `DB_USERNAME/PASSWORD=api_ujikom`.

## Status enum timeline (the drift story)

1. Spec's 04 migration: `enum ['diajukan','dipinjam','dikembalikan','telat']`.
2. Repo later added `2026_08_26_042608_add_ditolak_to_peminjaman_table.php`
   → `['diajukan','dipinjam','dikembalikan','ditolak','telat']`.
3. `AdminController` (web) and `PetugasController` (web) both validate
   `in:...,ditolak,...` and `AdminController` has reject-with-stock-restore logic.
4. **`app/Http/Controllers/API/LaporanController.php` still lists only
   `in:diajukan,dipinjam,dikembalikan,telat`.**

→ Real defect: `GET /api/laporan-peminjaman?status=ditolak` returns 422.
The spec itself has a different typo (`dikembangkan` instead of
`dikembalikan`) — the repo fixed that one but missed `ditolak`.

## Naming: spec-inconsistent, repo-consistent

- Model class is `DetilPinjam` (single `t`), table is `detail_pinjam`.
- Used consistently in `Models/DetilPinjam.php`, `Models/Peminjaman.php`
  (`hasMany(DetilPinjam::class)`), and `PeminjamanController` (import + 2 `create`).
- Spec alternates `DetilPinjam` / `DetailPinjam` across its own sections.
- **Not a bug. Leave it.** Do not "fix" toward the spec's inconsistent spelling.

## Scope placement corrected vs spec

- Spec instructs adding `scopeTersedia` to **model User**. User table has no
  `stok` / `status_kondisi` columns; `Alat` does.
- Repo correctly places it in `app/Models/Alat.php`.
  Filter: `where('stok','>',0)->where('status_kondisi','Baik')`.
- Spec is wrong here. Repo is right.

## RBAC — repo is better than spec

- Spec registers `/katalog`, `/peminjaman/{id}/approve`, `/laporan-peminjaman`
  in two separate role groups each, which per the SKILL.md pitfall section
  silently shadows one role.
- Repo instead has `app/Http/Middleware/CheckRole.php` with a variadic
  `...$roles` signature and `in_array()` check, aliased as `'role'`, used as
  `role:admin,peminjam` / `role:admin,petugas`. Single registration each.
- All aliases live in ONE `$middleware->alias([...])` call in `bootstrap/app.php`
  (`role.admin`, `role.petugas`, `role.peminjam`, `role`).
- Note: `IsPeminjam`/`IsPetugas` still use strict `role === '...'`; the spec text
  for `IsPeminjam` itself has a copy-paste bug (says check `petugas`).
  Not reached in practice since routes use `role:` / `role.*` groups.

## Observers — registered

`AppServiceProvider::boot()` wires `Alat::observe(AlatObserver::class)`,
`Peminjaman::observe(...)`, `Pengembalian::observe(...)`.
Each observer guards `LogAktivitas::create()` behind `if (Auth::check())` so
seeders/CLI don't blow up on `Auth::id()`.

## Beyond the spec

`AdminController`, `PetugasController`, `PeminjamanController` (web/Blade),
`CheckRole` middleware, `add_ditolak` migration. These are not in the PDF —
expected for a project that outgrew its school module. Audit them separately
rather than flagging as scope creep.