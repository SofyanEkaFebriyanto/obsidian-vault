# Deploy Disaster Recovery (shared hosting, live root already destroyed)

When a deploy mistake has already deleted/mangled the live root — most commonly the
multi-source `rsync --delete` into the domain root (see SKILL.md Pitfalls), which
flattens code into the root AND deletes `public_html/`, `public/`, `vendor/`,
`.env`, `storage/` — the site 404s. This is the recovery procedure that brought
test.kenfa.id back in ~20 min on 2026-09-07 with **zero data loss**.

## 0. STOP and triage — no more writes until you know the blast radius
- `ls -la ~/domains/<domain>/` and eyeball what's gone (`public_html`, `.env`,
  `vendor`, `storage`, `artisan`…).
- Confirm the **crown jewels survived** before anything else:
  - **DB is the priority, not the code.** Check it over SSH with the host creds
    (see "tinker over SSH" pitfall in SKILL.md for the no-quote-pitfall form), e.g.
    `SELECT COUNT(*) FROM orders; SELECT COUNT(*) FROM products;`. On Hostinger the
    real DB is the `u716977336_*`-prefixed one, NOT the Docker `kenfa` DB — verify
    you're counting the right one.
  - **Code is in git** (if committed). `git status`/`git log --oneline -3` locally.
  - **A dated backup exists** — `ls -lh ~/backup-<domain>*.tar.gz` /
    `test-kenfa-backup-*.tar.gz`. List what it contains:
    `tar tzf ~/backup-….tar.gz | cut -d/ -f2 | sort -u` — you need to see `.env`,
    `public_html`, `storage`, `vendor` in there. The backup is what makes this a
    20-minute job instead of a rebuild-from-scratch.
- If DB is gone and there's no DB dump: STOP and tell the user. Do not "recovery"
  a deleted production DB by guessing.

## 1. Identify the source of truth for each lost artifact
| Artifact | Source of truth | Why not the obvious one |
|---|---|---|
| app code (`app/ config/ routes/ database/ resources/ tests/ lang/ bootstrap/`) | **local git** working tree (already committed) | git is clean + current; the live root is now garbage |
| `vendor/` | re-sync from **local** `vendor/` (its `composer.lock` matches) — or the backup | re-runs composer install on the host = slow + needs composer |
| `storage/app/public/` (photos) | local working tree **if it's in sync with what was serving**, else the dated backup | verify `git ls-files --others storage/app/public` is empty → no unsaved uploads to lose |
| `.env` | **REBUILD from the dated backup's host-side values**, layer in new keys | the **local `.env` holds Docker values** (`DB_HOST=mysql`, `DB_DATABASE=kenfa`) — copying it to the host breaks every DB connection. Host creds are `u716977336_*`. |
| `public_html/` + `public/build` + `.htaccess` | local `public/` (freshly built) → BOTH docroot locations | the Vite two-dir manifest rule (SKILL.md) still applies |
| `public_html/storage` symlink | recreate on host | rsync doesn't carry the right target path |

**Sanity check that local was synced-from-live:** compare `APP_KEY` between local
`.env` and the backup `.env` — if they match, local genuinely tracks the live app
and you can trust local code/build as the source. Extract the backup `.env` once:
`tar xzf ~/backup-….tar.gz <domain>/.env -O > /tmp/live-env-<date>`.

## 2. Rebuild `.env` for the host (do this carefully, secrets stay on host)
Start from the **host** values (backup), NOT the local file:
- DB block from backup: `DB_DATABASE=u716977336_…`, `DB_USERNAME=u716977336_…`,
  `DB_PASSWORD=***`, `DB_HOST=localhost`.
- APP_KEY from backup (or local if identical).
- APP_URL = the live domain, `APP_ENV=production`, `APP_DEBUG=false`,
  `APP_LOCALE=id`, `QUEUE_CONNECTION=sync` (shared host has no queue worker).
- Mail (465/smtps), Midtrans, Biteship blocks from the backup.
- **Add any brand-new keys from this session** (e.g. `GOOGLE_CLIENT_ID/SECRET`)
  from local — those don't exist in the old backup.
- Keep DB_PASSWORD handling server-side where possible (don't paste the raw value
  into the transcript): e.g. pull the `DB_PASSWORD=` line from the extracted
  backup `.env` with `grep` and append it to the rebuilt file on the host.

## 3. Reconstruct per-directory — ONE source → ONE dest, never multi-source
```
# clean the flattened junk first (the root now has stray config/*.php, web.php, …)
ssh <alias> 'cd ~/domains/<d> && rm -rf <each stray flattened file/dir except real ones>'
# then per-dir, each its own rsync, with a trailing subdir on BOTH sides:
rsync -az --delete vendor/      <alias>:~/domains/<d>/vendor/       # biggest; background it
rsync -az --delete app/         <alias>:~/domains/<d>/app/
rsync -az --delete config/      <alias>:~/domains/<d>/config/
rsync -az --delete routes/      <alias>:~/domains/<d>/routes/
rsync -az --delete database/    <alias>:~/domains/<d>/database/
rsync -az --delete resources/   <alias>:~/domains/<d>/resources/
rsync -az --delete tests/       <alias>:~/domains/<d>/tests/
rsync -az --delete lang/        <alias>:~/domains/<d>/lang/
rsync -az --delete bootstrap/   <alias>:~/domains/<d>/bootstrap/
rsync -az artisan composer.json composer.lock package*.json vite.config.js phpunit.xml .env.example <alias>:~/domains/<d>/
# storage media: background, verify size landed (see "1GB+ over a slow proxy" pitfall)
rsync -az storage/app/ <alias>:~/domains/<d>/storage/app/
# public → BOTH docroot build locations + .htaccess, then the storage symlink
rsync -az --exclude storage public/ <alias>:~/domains/<d>/public_html/
rsync -az --exclude storage public/ <alias>:~/domains/<d>/public/
rsync -az public/.htaccess <alias>:~/domains/<d>/public_html/.htaccess
ssh <alias> 'cd ~/domains/<d> && rm -f public_html/storage && ln -s "$(pwd)/storage/app/public" public_html/storage && mkdir -p storage/framework/{cache,sessions,views} storage/logs'
```
`vendor/` and `storage/` are the two that need background + `notify_on_complete`
and a **post-land size check** (`du -sh`, `ls`) — trust the landed bytes, not
rsync's exit code, especially over a SOCKS proxy.

## 4. Verify vendor actually loaded the new deps
`ssh <alias> 'cd ~/domains/<d> && /opt/alt/php84/…/php -r "require \"vendor/autoload.php\"; echo class_exists(Laravel\\Socialite\\Facades\\Socialite::class)?"'`
(or whichever new class you added). Confirms the vendor re-sync wasn't partial.

## 5. Cache + smoke FROM OUTSIDE (via the proxy, like a real customer)
```
ssh <alias> 'cd ~/domains/<d> && P=/opt/alt/php84/…/php; $P artisan optimize:clear && $P artisan route:cache && $P artisan config:cache && $P artisan view:cache'
# then from LOCAL, through the proxy — never trust localhost on the host:
for p in / /<cat> /masuk /daftar /faq /lacak …; do curl -s -o /dev/null -w "%{http_code} $p\n" -x socks5h://127.0.0.1:51001 https://<domain>$p; done
```
Beyond 200s, verify the *substance*:
- any **OAuth/redirect** route actually 302s to the right provider (grep the
  `Location:` header for the client_id),
- the **CSS hash** in live HTML returns 200 AND `public/build/manifest.json` ==
  `public_html/build/manifest.json` (md5 both) — the two-dir Vite rule,
- **one real image** from `storage/` returns 200,
- `/admin` (or the auth gate) 302s.

## 6. Restart what the deploy killed
The **nohup scheduler** (`~/scheduler-runner.sh`) dies with the deploy.
`pkill -f scheduler-runner; nohup ~/scheduler-runner.sh > ~/scheduler.log 2>&1 &`
then confirm `pgrep -f scheduler-runner` and that `~/schedule.log` is fresh
(`filemtime`).

## 7. Clean up + report honestly
- Remove any staging extractions you made (`rm -rf ~/recover-staging` — ~1.2 GB).
- Keep the dated backup(s) — they're what just saved you.
- Report to the user: what broke (own it plainly), what survived, the SOP added,
  and any manual step the user must still do.

## Gotchas that cost time on the 2026-09-07 recovery
- **A background `rsync` that starts BEFORE your cleanup re-flattens the root** —
  sequence: finish the vendor/storage background jobs *before* (or re-check after)
  removing stray files, or the old process re-copies junk into the root.
- **Local `public/build` can be root-owned** (container wrote it) → `npm run build`
  fails `EACCES unlink`. `rm -rf public/build` then rebuild inside the container
  (root) and `chown -R 1000:1000 public/build` so the host-owned user can read it.
- **The live DB creds ≠ local `.env`.** Local is Docker (`kenfa`/`kenfa`,
  `DB_HOST=mysql`); the host is `u716977336_*`. Always source host secrets from the
  dated backup, never the local file.
- **A stale "build marker" dir** from an aborted multi-source rsync can litter the
  local `src/` (it got flattened too) — `git status` will show it as untracked;
  remove it so the tree is clean.
