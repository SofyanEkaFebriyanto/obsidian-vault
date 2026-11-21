# Silent-degrade third-party API: diagnosis recipe

A common class of bug on a live Laravel store: a UI section fed by an
external API is **blank from day one, with no error anywhere** — not in the
browser, not in `storage/logs/laravel.log`.

## Why it's silent

The service client is built with a "degrade, don't block" contract (per
CLAUDE.md / Kenfa conventions): on ANY failure — bad key, timeout, non-2xx —
it returns an empty collection / `null` and logs a warning, so the caller
falls back to a manual path instead of 500-ing checkout. That means an auth
misconfiguration looks identical to "API down" or "no data": empty UI, no
visible error. **Topping up account balance does NOT fix a key problem.**

## Real example: Biteship ongkir (kenfa-2.0, 2026-08-29)

Checkout courier/ongkir box never appeared after deploy. Owner topped up
Biteship balance — no change. Root cause: `.env` held a **TEST key**
(`biteship_test.…`), not the **LIVE key** (`biteship_live.…`). The
production Biteship endpoint rejected the test key's auth →
`BiteshipService::rates()` degraded to `[]` → empty box, zero errors.

## Diagnosis order (fast, no app boot — host is usually loaded)

1. **Key TYPE** — must be `biteship_live.…` in production. A `biteship_test.…`
   key is silently rejected by the live endpoint. (Test key = sandbox; saldo
   top-up on the wrong account namespace does nothing.)
   ```bash
   grep -iE '^BITESHIP_API_KEY=' .env | sed -E 's/(BITESHIP_API_KEY=).*/\1<hidden>/'
   ```
2. **Key TRUNCATION** — these keys are JWTs: 3 dot-separated parts
   (`biteship_live.HEADER.PAYLOAD.SIGNATURE`). A copy-paste that drops the
   signature (last part) fails auth → empty. Verify all 3 parts are present.
3. **Config CACHE stale** — if `.env` was edited AFTER
   `php artisan config:cache` ran, Laravel still reads the cached empty value.
   Fix: `php artisan optimize:clear` (use the host's real PHP binary, e.g.
   `/opt/alt/php84/usr/bin/php`). Run in background if host load is 15+.
4. **Required fields present** — `BITESHIP_ORIGIN_POSTAL_CODE` (e.g. `40375`)
   and `BITESHIP_COURIERS` must be set; empty origin → API rejects.
5. **dev mode off** — `BITESHIP_DEV_RATES=true` serves fake rates; never in prod.

## Security

Never print raw API keys to transcripts/logs. Mask them:
`sed -E 's/(KEY=).*/\1<hidden>/'`. Ask the user to confirm "lengkap 3 bagian"
or "kepotong" rather than pasting the full secret. A key prefix
(`biteship_test.` vs `biteship_live.`) is enough to diagnose type without
the secret.
