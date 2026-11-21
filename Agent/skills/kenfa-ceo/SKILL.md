---
name: kenfa-ceo
description: "CEO flow untuk project kenfa-2.0: founder memberi direktif → Hermes (CEO) pecah jadi brief per-role → delegasi paralel ke profile agents kenfa-frontend/backend/qa/deploy → review hasil → lapor ke founder. Trigger: 'meeting tim', 'eksekusi lewat tim', 'pakai flow CEO', atau task kenfa-2.0 multi-domain."
version: 1.0.0
---

# Kenfa CEO Flow

Founder memberi direktif high-level. Kamu adalah CEO: pecah jadi brief per-role, jalankan meeting, delegasikan eksekusi, lalu laporkan.

## Tim (Hermes profiles)
| Profile | Role | Domain |
|---|---|---|
| `kenfa-frontend` | Frontend/UI | Blade, Alpine.js, Tailwind v4, Filament |
| `kenfa-backend` | Backend | Laravel, MySQL, Midtrans, migration |
| `kenfa-qa` | QA | artisan test + smoke test live test.kenfa.id |
| `kenfa-deploy` | Ops/Deploy | rsync ke Hostinger, PHP 8.4 CLI, storage symlink |

Repo: /home/sofyan/Documents/project/kenfa-2.0 (CLAUDE.md = sumber konteks). Live: https://test.kenfa.id

## Langkah

1. **Pahami direktif founder.** Kalau ambigu, tanya SEKALI dengan opsi konkret — jangan nebak arah produk.
2. **Rencana & pembagian kerja.** Tulis rencana singkat: siapa mengerjakan apa, urutan dependensi (misal backend dulu baru frontend baru QA baru deploy). Tampilkan rencana ini ke founder sebelum eksekusi kalau dampaknya besar (deploy, migrasi DB, ubah alur pembayaran).
3. **Meeting = briefing paralel.** Kirim brief via `delegate_task` batch mode dengan role yang relevan saja (tidak semua task butuh 4 agent). Brief harus self-contained: goal, file paths, constraint dari CLAUDE.md, definisi done.
4. **Review hasil.** Cek klaim subagent terhadap realita (baca diff, jalankan test sendiri kalau perlu). Subagent bisa salah klaim "sudah selesai".
5. **Iterasi** bila ada bug/handoff antar-role — delegasi ulang ke role terkait dengan konteks bug report.
6. **Laporan founder.** Format ringkas bahasa Indonesia langsung:
   - Yang diminta vs yang dikerjakan
   - Per-agent: status + temuan penting
   - Bug/masalah yang tersisa
   - Next step yang disarankan

## Aturan CEO
- JANGAN eksekusi coding besar sendiri — itu tugas role agents. Kamu koordinasi, review, dan memutuskan.
- Deploy HANYA setelah QA verdict GO dan (untuk perubahan berisiko) persetujuan founder eksplisit.
- Konflik antar-agent (misal frontend butuh endpoint yang backend tidak buat) putuskan sendiri sebagai CEO, jangan bolak-balik ke founder untuk hal teknis.
- Semua agent punya SOUL.md berisi aturan domain mereka — jangan duplikasi aturan di brief; cukup referensikan.

## Pitfalls
- Subagents inherit NO approval context — interactive approvals (`docker exec`, `sudo chown`, service restarts) stall them until timeout and they halt asking permission. Pre-authorize in the brief ("docker exec di-approve, jalankan langsung") AND tell them "kalau tetap diblokir, STOP dan laporkan, jangan retry". When a blocked command is small, CEO just runs it itself after results come back (happened twice in sprint 2026-08-26: QA `docker exec` and frontend `sudo chown` both stalled).
- Parallel agents editing ONE repo need EXPLICIT file-ownership boundaries in each brief: list files each agent must NOT touch ("backend sedang pegang routes/console.php — jangan sentuh") and sequence shared-file changes last. Without this, compose/env/test-file edits race each other.
- Briefs that require running the full test suite repeatedly make that agent 5-10x slower than others (suite ~35s/run). Don't ask for suite runs at every step in parallel batches — one final full-suite run per agent.
- Subagent summaries are self-reports. Verify claims yourself (run the test suite, spot-check diffs, curl the endpoint) before reporting to founder. In sprint 2026-08-26 the deploy agent reported port 8080 dead — was actually a transient bind-mount permission fixed by `docker restart`; CEO's own check caught the true state.
- Keep audit briefs read-only explicit ("audit read-only, jangan ubah file") so agents don't start fixing mid-audit.
- Ad-hoc verification of changed logic: NEVER re-implement the function inside your test script — transcription drift produces false FAILs. Extract the REAL function from source, strip TS types with the project's own esbuild (`node_modules/.bin/esbuild --loader=ts`), then execute it against fixtures. Check the compiled bundle contains the change (mind quote-normalization: single quotes become double in bundles).
- Scope ONE workstream per subagent. A 3-task brief (env fix + docs + compose containers) runs many minutes and looks hung from the office view ("running:" with no visible progress). Founder will ask why it's stuck. Split heavy briefs, or state expected duration in the report to founder immediately after dispatch.
- Serializing agents by design ("do X last to avoid race") makes them LOOK idle. If you serialize, say so proactively when reporting dispatch status.
- Verifying code claims: NEVER re-implement the function inside your test fixture — transcription drift produces false failures (burned 2 iterations). Instead extract the REAL function from source, strip TS types via the repo's own esbuild (`node_modules/.bin/esbuild --loader=ts`), and execute it against fixtures. Check compiled bundle content too (quote-style may differ: esbuild emits `"claude"` not `'claude'`).
- Root-owned build artifacts are rarely just one directory. kenfa case: `node_modules` AND `node_modules/.vite-temp` AND `public/build` all root-owned from container writes — fix ownership of ALL of them (`sudo chown -R sofyan:sofyan node_modules public/build`) before concluding npm/vite is broken.
- Race between parallel agents sharing docker containers: backend running tests while deploy restarts compose = flaky failures. Assign container-mutating work to ONE agent only, others get "jangan sentuh X" constraints naming exact files.
- **Brief kegedean + provider flaky = agent mati sebelum nulis (2026-08-29).** Dua agent paralel dikasih brief "lengkap" (backend: migrasi+model+controller+notifikasi+Filament+test sekaligus) habis budget iterasi cuma buat baca file — backend 20 api_call, NOL file ditulis — lalu kena HTTP 524 (timeout) / 403 quota habis. Ini pelanggaran nyata pitfall "Scope ONE workstream". Perbaikinya: (a) pecah jadi stage kecil & SERIAL kalau perlu, bukan paralel besar; (b) KUTIP skema/kode persis di brief (pasta isi migrasi, const, body method seperti `Order::generateOrderNumber()`) supaya agent TIDAK perlu buka file; (c) batasi eksplorasi eksplisit: "baca MAKSIMAL N file lalu LANGSUNG tulis", target <12 iterasi; (d) kalau log agent (`.hermes/logs/agent.log`) menunjukkan 524/403 quota BERUNTUN dalam jendela kerja, JANGAN andalkan delegasi untuk tahap kecil & fully-specified — CEO kerjakan langsung via `terminal`/`write_file` lalu verifikasi (`docker exec -i kenfa-app php artisan migrate` + `migrate:rollback --step=1`). Stage 1 (migrasi + model `OrderReturn`) ditembus CEO langsung SETELAH 2 delegasi gagal. Jangan lapor "agent selesai" tanpa cek `git status` dulu — agent bisa mati di tengah tanpa menulis.
- **Verifikasi migrasi = migrate + rollback + re-migrate.** Setelah tulis migrasi, jalankan `php -l` per file, lalu `docker exec -i kenfa-app php artisan migrate --force`, `migrate:rollback --step=1`, dan `migrate` lagi untuk bukti reversible. Pola backfill untuk kolom UNIQUE di tabel berisi data: lihat `references/laravel-migration-patterns.md`.
- **Pola migrasi: extend tabel berisi data + kolom UNIQUE baru (Laravel 13, 2026-08-29, TERVERIFIKASI).** Urutan wajib: (1) FK jadi nullable — bungkus `Schema::disableForeignKeyConstraints()`/`enableForeignKeyConstraints()` karena ubah FK di SQLite rewel; (2) tambah kolom baru semua nullable dulu; (3) BACKFILL baris lama (isi `ticket_number`+`access_token` unik) SEBELUM index dipasang; (4) baru `->unique('ticket_number')` + `->index(...)`. Kalau unique dipasang sebelum backfill, baris lama tanpa nilai membatalkan migrasi. `->change()` native di Laravel 13 (tanpa doctrine/dbal). `down()` yang mengembalikan FK ke NOT NULL sengaja GAGAL begitu ada data marketplace (order_id null) — itu benar, jangan diam-diam buang data. Token 40-char `Str::random(40)` → model `$hidden` + DI LUAR `$fillable`. Test DB SQLite in-memory kosong saat migrate, jadi backfill loop tak teruji data nyata di local — verifikasi via `->count()` di tinker.

## Support files
- `references/adhoc-code-verification.md` — proven pattern for verifying code claims when no test suite exists (extract real fn + esbuild strip + fixtures; gotchas: quote normalization in bundles, fixture-drift anti-pattern).
- CEO harus jalankan sendiri perintah verifikasi kunci (test suite, smoke curl) SETELAH subagent balik — jangan percaya klaim "164 passed" tanpa cek. Subagent juga bisa berhenti di approval interaktif (docker exec, systemctl restart) dan menganggap tugas selesai; brief yang memerlukan itu harus bilang "di-approve, jalankan langsung" atau CEO eksekusi ulang.
- Untuk audit multi-domain, minta format output terstandar dari awal: `[AREA] judul — deskripsi — severity P0/P1/P2 — effort S/M/L` supaya gabungan laporan founder langsung jadi risk meter tanpa rework.

## Catatan Pixel Agents
Profile agents yang di-spawn akan muncul otomatis sebagai karakter di Pixel Agents office (plugin pixel_observer aktif, server :3100). Founder bisa pantau visual di browser office-nya selama meeting berjalan. Jika office kosong padahal subagent jalan: lihat skill `pixel-agents-office` dan `references/pixel-agents-troubleshooting.md` di skill ini (termasuk bug teammate-cull yang sudah difix 2026-08-25 — jangan diagnosa ulang dari nol).
