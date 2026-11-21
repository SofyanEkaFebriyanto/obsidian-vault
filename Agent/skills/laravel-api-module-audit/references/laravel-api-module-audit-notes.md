# Laravel API Module Audit Notes

Condensed checklist and project-specific audit patterns from `01.API-UJIKOM`.

## Typical Spec Requirements

- Tables: `users`, `kategori`, `alat`, `peminjaman`, `detail_pinjam`, `pengembalian`, `log_aktivitas`.
- Roles: `admin`, `petugas`, `peminjam`.
- Auth API: Sanctum `register`, `login`, `me`, `logout` returning `access_token`.
- RBAC: middleware aliases for role checks.
- Status enums for `peminjaman.status`: `diajukan`, `dipinjam`, `dikembalikan`, `telat`.
- Web routes for admin/petugas/peminjam dashboards and CRUD.

## Common Findings in Student Projects

- Missing ENTIRE API layer while web/Blade side is complete: check `app/Http/Controllers/API/` (only AuthController?), `app/Http/Requests/*` subdirs, `app/Http/Resources/`, `app/Observers/`, and empty role groups in `routes/api.php`.
- Missing `scopeTersedia` (stok > 0 + kondisi Baik) used by katalog endpoint.
- `UserResource` `bergabung_sejak` without null-safe `?->format()` can 500 on null `created_at`.
- `docker-compose.yml` absent from project root even though module mandates 3 services (mysql-server, app-laravel:8000, phpmyadmin:8081); `.env.example` may still show sqlite while real `.env` differs.
- Extra enum migration (e.g. adding `ditolak` to `peminjaman.status`) drifting from the 4-value spec enum.
- Missing API endpoints in `routes/api.php`; only auth routes present.
- Duplicate `AuthController` classes in `web` and `API` namespaces.
- Middleware alias mismatch: `role:admin` vs `role.admin`.
- Duplicate middleware registration in `bootstrap/app.php`.
- Stock logic inconsistency: decrement on create vs decrement on approval.
- Missing transaction wrappers around master-detail inserts.
- Missing `down()` implementations in migrations.
- Missing `storage:link` for public file access.
- Enum drift between migration, validation, seeders, and UI.
- IDOR risks in web controllers if ownership checks are absent.

## Quick Check Commands

```bash
cd backend
find app -maxdepth 4 -type f | sort
find database/migrations -type f | sort
git status
```

## OpenCode Tip

For long audits, prefer direct inspection over `opencode run` with many `-f` attachments; the CLI may time out before producing a report.
