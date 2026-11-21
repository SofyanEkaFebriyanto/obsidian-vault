---
name: laravel-api-module-audit
description: "Audit Laravel projects against module/spec docs."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Laravel, Audit, API, Module-Review, REST]
    related_skills: [opencode, requesting-code-review, laravel-docker-workflow]
---

# Laravel API Module Audit

## When to Use

- User asks to audit a Laravel project against a module/spec document, PDF requirement, or checklist.
- User wants findings grouped by severity with a remediation checklist.
- User says: "audit project", "review against spec/module PDF", "check migrations/models/controllers/routes", or "compare implementation to requirements".

## Trigger

- "audit project"
- "review against spec/module PDF"
- "check migrations/models/controllers/routes"
- "compare implementation to requirements"

## Output Modes

Pick the lightest mode that satisfies the ask. Do NOT force the full severity report every time.

1. **Orient mode** (user just says "baca <file>", "summarize this module", "what does this doc say"):
   - Report the doc's structure: purpose, feature list, layer-by-layer outline.
   - Then a short "what differs from your repo now" list — only items you actually verified with grep/read.
   - End with a one-line offer to patch or to run a full audit.
2. **Full audit mode** (user says audit/review/compare, or asks for severity grouping):
   - Everything below, severity-grouped, with file:line and remediation checklist.

## Procedure

0a. Extract large spec PDFs efficiently — do not read the PDF binary in chunks.
   - `pdfinfo <file>.pdf` for page count and title first.
   - `pdftotext -layout <file>.pdf /tmp/spec.txt` then read `/tmp/spec.txt` with `read_file` using `offset`/`limit` until `truncated: false`. The layout flag preserves code-block indentation, which matters for PHP snippets.
   - Images of code in the PDF extract as nothing — say so rather than guessing at content you could not see.

0. Respect read-only audit mode when requested.
   - If user says check only / no edits (e.g. Indonesian: "jangan lakukan pengeditan, cukup lihat dan cek"), use read_file + search_files only. No patch/write_file, no state-changing terminal commands, and leave .env/credential files alone.
   - Batch independent reads in one turn; paginate large PDF extractions via read_file offset/limit until `truncated: false`.
   - When two spec docs exist (e.g. one API/JSON module + one web/Blade module), audit each track separately and label findings per track so web completeness does not mask missing API endpoints.

1. Map project structure first.
   - `find backend -maxdepth 4 -type f | sort` or equivalent.
   - Identify migrations, models, controllers, routes, middleware, form requests, resources, seeders.

2. Read the requirement source.
   - Extract expected tables, fields, status enums, roles, endpoints, auth flow, and any special behaviors.
   - Note deviations early: extra statuses, missing tables, renamed columns.

3. Inspect implementation in parallel where possible.
   - `routes/api.php` and `routes/web.php` for endpoint coverage and middleware aliases.
   - `bootstrap/app.php` for middleware registration.
   - Models for `$fillable`, `$hidden`, `casts`, and relationships.
   - Controllers for validation, transactions, stock logic, auth guards, redirect vs JSON.
   - Migrations for column types, defaults, foreign keys, composite keys.
   - Auth controllers for token/session handling consistency.

4. Cross-check common failure modes.
   - Auth: duplicate controllers with same class name in different namespaces; mixing Sanctum API tokens with web session login.
   - RBAC: alias mismatch (`role.admin` vs `role:admin`), duplicate middleware registration, missing route protection.
   - Transactions: missing `DB::beginTransaction()` around master-detail writes; missing rollback on catch.
   - Inventory: stock decrement on approval vs create; double-decrement risk; missing stock restore on delete/reject.
   - Status enums: migration enum values vs validation `in:` lists vs seeders vs UI labels.
   - **Reverse drift is the common case.** The spec PDF is often the stale artifact, not the code. A later `add_*_to_*_table` migration that introduces a new status (e.g. `ditolak`) makes the *validation `in:` list* the thing that falls behind — the migration and the web controller both know about `ditolak`, but the API's filter/validator silently 422s on it. Grep every `in:` / `Rule::in(` list for a status enum and compare against the live migration, not only against the spec.
   - **Scope placement in the spec can be wrong.** A module may say "add `scopeTersedia` to model User" when the columns (`stok`, `status_kondisi`) live on a different table entirely. If the user's code puts the scope on the model that actually owns the columns, that is a *correction*, not a deviation — say so explicitly so it doesn't get "fixed" backwards.
   - API resources: missing or inconsistent JSON shape; sensitive fields leaking.
   - File uploads: missing `storage:link`, missing old-file deletion, wrong disk.
   - Duplicate routes: POST `/login` defined in both `web.php` and `api.php` with different controllers.

5. Produce the report.
   - Group by severity: Critical, High, Medium, Low.
   - For each finding: file:line, what’s wrong, impact, suggested fix.
   - End with a short prioritized remediation checklist.

## Output Format

```markdown
# Audit Report

## Critical
- ...

## High
- ...

## Medium
- ...

## Low
- ...

## Remediation Checklist
1. ...
```

## Pitfalls

- Don’t assume the PDF’s Docker commands match the actual repo layout; inspect the real paths.
- PDFs may contain typos in code examples; validate against working Laravel conventions.
- **Distinguish spec typo from user bug — and say which it is.** A spec may spell a model `DetilPinjam` in the class section but `DetailPinjam` in resource/controller snippets, or list a status enum as `dikembangkan` where `dikembalikan` is meant. When the user's code is internally *consistent*, it is not a defect. Report it as "the spec is inconsistent here, your naming is fine, don't change it" so a later session or a teacher doesn't "correct" working code back into a broken state.
- Never leave a language slip of your own in the report (stray non-Indonesian fragments, half-finished sentences). Match the user's language throughout; if they wrote in Indonesian, the whole report is Indonesian.
- If two `AuthController` classes exist, verify both route files aren’t colliding on the same URI.
- Enum values in migrations are stricter than PHP validation rules; keep them synchronized.
- “Add status later” migrations can create drift; audit spec vs migration vs validation vs seeder.
- Missing `down()` methods in migrations reduce reversibility; flag but don’t block.
- Duplicate URI+method route registrations do NOT union access — Laravel matches the FIRST registered route, so the same endpoint placed in two different middleware groups (e.g. approve in both `role.admin` and `role.petugas` groups) leaves the second registration dead; the shadowed role gets 403. Register once with a multi-role middleware (`role:admin,petugas`) instead.
- Multiple `$middleware->alias([...])` calls in `bootstrap/app.php` do NOT merge — a later call replaces earlier aliases, silently unregistering them (`Target class [role.admin] does not exist` at runtime). Keep ONE `alias()` call containing every alias, including generic ones like `role`.

## References

See `references/laravel-api-module-audit-notes.md` for condensed checklist templates and common Laravel audit patterns.

See `references/api-ujikom-peminjaman-alat.md` for a fully-audited concrete example (Peminjaman Alat, Laravel 12 + Sanctum): enum-drift timeline, spec-typo vs real-defect calls, and port/compose quirks.
