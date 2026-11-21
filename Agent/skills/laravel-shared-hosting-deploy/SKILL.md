---
name: laravel-shared-hosting-deploy
description: Deploy a Laravel app to shared hosting (Hostinger hPanel etc.) over SSH — rsync strategy, PHP CLI version aliases, storage symlink pitfalls, DB seeding without breaking existing data.
---

# Deploying Laravel to Shared Hosting (hPanel-style)

Shared hosting is NOT a VPS: no Docker, no node, restricted PHP CLI on PATH,
docroot is `~/domains/<domain>/public_html`, and MySQL creds come from hPanel.
Plan the deploy around those four constraints.

## Workflow

1. **Recon first** (one SSH call):
   - `php -v`, `which composer mysql`, `ls ~/domains`
   - Check whether an older deploy already lives in the domain dir — often it
     has vendor/, storage photos, and a seeded DB you can REUSE instead of
     re-uploading gigabytes.
2. **Backup the old deploy** before touching anything:
   `tar czf ~/backup-<domain>-$(date +%m%d).tar.gz -C ~/domains <domain>`
   (can take minutes; run with generous timeout and verify the tarball exists).
3. **Rsync selectively** — the big win is NOT re-uploading what's already there:
   ```
   rsync -az --delete -e "sshpass -p 'PW' ssh -p PORT -o PubkeyAuthentication=no" \
     --exclude Archive.zip --exclude vendor --exclude node_modules \
     --exclude .env --exclude storage/app/public/products \
     src/ user@host:~/domains/<domain>/
   ```
   Keep host-side `.env`, `vendor/`, and existing uploaded photos if they match
   the app version; only re-upload when code requires it.
   **One source dir → one mapped dest subdir per rsync.** NEVER pass several
   source dirs (`app/ config/ routes/ ...`) to a single destination root —
   see the multi-source `--delete` pitfall below; it deletes the live root.
4. **PHP CLI version mismatch** — see Pitfalls below before running artisan.
5. **DB**: reuse existing DB creds from the host `.env`; run
   `artisan migrate --force` (new migrations only), then seed per-seeder with
   `--class=` for anything missing. Full `db:seed` fails with unique-constraint
   errors when tables are partly populated.
6. **Symlinks — check BOTH after every rsync** (see Pitfalls):
   `readlink public/storage` AND the `public_html -> public` docroot link.
7. **Frontend assets**: no node on host. Build locally (`npm run build`) and
   rsync the build up. On a real-directory docroot layout you must sync to
   BOTH `public_html/build` (what the webserver serves) AND the app-dir
   `public/build` (what `@vite()` reads the manifest from at runtime) — see
   Pitfalls. Never rely on `npm install` server-side.
8. **Smoke test from OUTSIDE** the host (`curl https://domain/path` from local
   machine): localhost checks on shared hosting hit the wrong vhost and give
   misleading results. Test page URLs AND one real image URL.
9. **Scheduler on shared hosting**: many hPanel hosts have NO crontab binary
   (`crontab: command not found`). Workaround = nohup'd loop script with flock;
   durable fix = hPanel UI Cron Jobs running `/opt/alt/phpXX/.../php artisan schedule:run`.

## Pitfalls

- **Multi-source `rsync --delete` into a live root = P0 (verified 2026-09-07, deleted a whole site).** `rsync -az --delete app/ config/ routes/ database/ resources/ tests/ user@host:~/domains/<domain>/` is a **disaster**. When you give rsync SEVERAL source dirs for ONE destination, it flattens their *contents* directly into that destination — `config/services.php` lands at the domain root next to `artisan`, `routes/web.php` at root, etc. Worse, `--delete` then removes every entry in the root that isn't in that flattened set: **`public_html/`, `public/`, `vendor/`, `.env`, `storage/` all vanish** and the site 404s. It looks "done" (exit 0, "total size N") and is trivially missed because you were thinking of it as "sync the code". CORRECT form is **one source → one mapped subdir**, each its own command: `rsync -az --delete src/app/ host:~/domains/<d>/app/`, `... src/config/ host:.../config/`, `... src/routes/ host:.../routes/` — the trailing subdir on BOTH sides is what keeps `artisan`, `.env`, `public_html`, `vendor`, `storage` alive. Rule of thumb: if the destination path does NOT name a subdirectory, STOP. (Recovery that day: `vendor/` re-synced, code re-synced per-dir, `.env` rebuilt from a dated backup's DB/Mail/Midtrans/Biteship block — local `.env` holds Docker values `DB_HOST=mysql`/`DB_DATABASE=kenfa`, NOT the Hostinger `u716977336_*` creds — so always pull live secrets from a host backup, not the local file.) **Full ordered recovery runbook (triage → rebuild .env → per-dir reconstruct → verify → restart scheduler): `references/deploy-disaster-recovery.md`.**
- **`rsync --delete` destroys docroot symlinks** (e.g. `public_html -> public`, `public/storage`). After any --delete deploy, re-check and recreate both; a missing `public_html` symlink makes the whole domain 404 ("This Page Does Not Exist") even though artisan works over SSH. Better: add the symlinks as excludes or run a post-deploy symlink check every time.
- **`.htaccess` missing from the docroot ⇒ every route but `/` 404s** ("This Page Does Not Exist"), because the Laravel front-controller rewrite is gone — only `index.php` (`/`) resolves. This bites when `public_html` is a REAL directory of copied assets (not a symlink to `public/`): rsyncing `resources/`+`public/build/` doesn't carry `public/.htaccess`. FIX: explicitly `rsync public/.htaccess → public_html/.htaccess` (or a docroot .htaccess) as a mandatory post-deploy step. Symptom is identical to the missing-symlink 404 above but the cause is different — check BOTH after a deploy that 404s everything but home.
- **Shared hosts often have NO crontab CLI** (Hostinger hPanel does not expose `crontab` to SSH users). For Laravel scheduler fallback: write a loop script (`while true; do artisan schedule:run; sleep 60; done`) guarded with `flock -n ~/scheduler.lock ~/runner.sh`, start with `ssh -f ... "nohup ... &"`. It dies on server reboot — the durable fix is creating the cron job through the hPanel web UI.
- **ISP/port blocks vs wrong credentials**: if SSH times out but the site itself serves HTTP 200 from the same machine, the network path is blocked (traceroute dying mid-path confirms) — do NOT conclude the password is wrong until you've tried from another host (e.g. a VPS jump box that can reach the port). Conversely, "Permission denied" after a clean TCP connect means credentials/key issues, not networking.
- **SSH keys beat passwords for repeat deploys**: generate locally (`ssh-keygen -t ed25519 -f ~/.ssh/<alias>`), user pastes the .pub into hPanel, then pin it in `~/.ssh/config` as an alias so deploys are `rsync -e ssh <alias>:path`.

- **CLI php ≠ webserver php.**

- **CLI php ≠ webserver php.** The web panel may serve PHP 8.x fine while bare
  `php` on SSH is old. Multi-PHP hosts keep binaries under `/opt/alt/phpXX/usr/bin/php`.
  Fix permanently by appending to `~/.bashrc`:
  `alias php='/opt/alt/php84/usr/bin/php'` — but scripts/non-interactive shells
  don't load aliases, so use the full path in artisan/cron commands.
- **Composer platform check**: if `composer.json` requires newer PHP than CLI,
  artisan dies with "Composer detected issues". Either use the right binary or
  `composer config platform.php <ver>`.
- **Concrete Hostinger hPanel binary (verified 2026-08-29):** bare `php` on SSH
  is **8.3.30**, but kenfa-2.0's `composer.json` requires **>=8.4.1** → every
  `php artisan` dies with "Composer detected issues in your platform". The
  working CLI is **`/opt/alt/php84/usr/bin/php` (8.4.19)**. ALWAYS invoke
  artisan/migrate/cron on this host with that full path (alias doesn't load in
  non-interactive shells, and the `~/.ssh/config` ProxyCommand is separate from
  the PHP version). e.g. `/opt/alt/php84/usr/bin/php artisan migrate --force`.
- **Don't boot Laravel just to read one config value on a loaded shared host.**
  When the host is CPU-saturated (load avg 15-18, common on neighbors' noise),
  even `php -r` config reads or `artisan tinker` hang past a 60s timeout. To
  check whether an env var is set, grep `.env` directly instead of booting the
  app — fast and never blocks:
  `grep -iE '^BITESHIP' .env | sed -E 's/(BITESHIP_API_KEY=).*/\1<hidden>/'`
  (the `sed` masks the secret so it never lands in logs/transcripts; never print
  raw API keys). For a real boot check (e.g. config:clear after editing .env),
  run it in the background with `notify_on_complete` rather than a foreground
  wait, because the bootstrap can take minutes under load.
  - **Remote one-off Eloquent query over SSH: pipe PHP into `artisan tinker`'s stdin — don't use `--execute=`.** `ssh host "php artisan tinker --execute=\"...where('x','y')...\"` dies with a bash `syntax error near unexpected token` because the inner `--execute="..."` single-quotes collide with the outer ssh double-quote. The working form is to keep the WHOLE remote command in a single-quoted ssh arg and pipe a multiline PHP string into tinker (tinker reads its REPL from stdin when not a TTY), so all the PHP stays inside the echo and no quote crosses the ssh boundary:
    ```
    ssh <alias> 'cd ~/domains/<domain> && echo "
    echo \"manual: \".DB::table(\"orders\")->where(\"payment_method\",\"manual\")->count();
    echo \"midtrans: \".DB::table(\"orders\")->where(\"payment_method\",\"midtrans\")->count();
    " | /opt/alt/php84/usr/bin/php artisan tinker'
    ```
    (the `\"` inside the single-quoted outer string reach the remote shell intact; tinker prints each statement's result). Use this to count/inspect rows before a destructive change (e.g. "how many orders use `manual` before I delete that payment option?") — it's the fast, non-blocking way to ground a decision in live data on a host with no GUI DB client.
- **SSH "timed out during banner exchange" via a known-good proxy = host CPU
  saturation, not a network/proxy failure.** The proxy (Warp wireproxy
  `127.0.0.1:51001`) may be fine, but if the shared host's load is 15-18 the SSH
  handshake itself stalls. Symptom: `Connection to UNKNOWN port 65535 timed out`
  right after `ProxyCommand socat SOCKS5...` connects. Fix: retry with lighter
  commands (grep .env, `ls`) or wait for load to drop — do NOT keep raising
  timeouts on a full `artisan` bootstrap; that just burns more minutes.
- **Stale `public/storage` symlink** = images 404 with zero log noise. Always verify.
- **`public_html/storage` can resolve to a NON-EXISTENT path (not just be missing).** On kenfa-2.0 (test.kenfa.id) the symlink *existed* but pointed at `/var/www/html/storage/app/public` — a path from an old container layout that no longer exists — so every `storage/app/public/*` image 404'd with no error anywhere. A plain `ls -ld public_html/storage` looks healthy; you MUST `readlink -f public_html/storage` and confirm the resolved directory actually exists. Fix: `rm -f public_html/storage && ln -s "$(pwd)/storage/app/public" public_html/storage` (run from the domain root `~/domains/test.kenfa.id`). Re-check after every `--delete` rsync.
- **Real-directory docroot mapping** (when `public_html` is a REAL dir, not a symlink to `public/`): rsync is per-folder, never `src/public/` wholesale with `--delete` (that would wipe other webroot assets like user uploads). Map: `src/resources/views/ → resources/views/`, `src/public/build/ → public_html/build/` **AND `src/public/build/ → public/build/`** (both — see next pitfall), `src/public/images/ → public_html/images/`, `src/public/.htaccess → public_html/.htaccess`.
- **Vite build must land in TWO dirs or the CSS silently 404s ("styles not loading").** On a real-directory docroot, the webserver serves asset FILES from `public_html/build/`, but `@vite()` in Blade reads the **manifest** from the APP dir `public/build/manifest.json` at runtime. If a deploy only syncs the new build to `public_html/build/`, the HTML keeps pointing at the OLD hash from the stale `public/build/manifest.json` → the browser requests an old-hash file that no longer exists → **CSS 404, page unstyled, zero log noise** (JS can look fine if its hash didn't change). Symptom: HTML's `<link rel="stylesheet">`/`modulepreload` reference a hash ≠ the file present in `public_html/build/assets/`. FIX: after every build-touching deploy, rsync the build to BOTH `public_html/build` and `public/build` (files + `manifest.json`), then `view:clear`. Verify: the asset URL in live HTML must return 200, and `public/build/manifest.json` must name the same hash as the file on disk. (Kenfa 2026-09-05: `app-CmMpScSW.css` rendered from a 27-aug manifest while only `app-1oMYEjOX.css` existed → site unstyled overnight; fixed by copying the new build into `public/build`.)
- **Full seeder re-runs explode** on populated tables (unique constraints).
  Seed individual classes idempotently instead.
- **Seeders using `firstOrCreate`/`upsert`-into-existing do NOT update rows they
  already created.** So if you change seeded *content* (e.g. a static page's HTML
  text in a `PageSeeder`), re-running the seeder does nothing — the live page keeps
  the OLD text, and you'll "verify" the change locally (fresh SQLite) and think it
  shipped when the production DB row is untouched. When you change seeded content,
  either (a) update the live DB row directly (`Page::where('slug',…)->update([…])`
  over tinker — note the DB text often has real newlines, so match on a stable
  substring, not a multi-line literal), or (b) make the seeder an idempotent
  upsert that also sets the changed columns. (Kenfa 2026-09-07: removed "Transfer
  Manual" from the FAQ in `PageSeeder`, but `/faq` live still said the old thing
  until the DB row was fixed by hand.)
- **rsync of 1GB+ asset dirs over one command will blow past timeouts** — split:
  sync code first (fast), then media separately, or skip media that's already current.
- Password-auth SSH needs `sshpass` + `-o PubkeyAuthentication=no`; install keys
  afterward (`ssh-copy-id`) to drop the password from future commands.
- **"Permission denied" via sshpass with a user-supplied password means the password is wrong — not the quoting.** If you suspect shell escaping of `#`/special chars, verify by piping through `od -c` on the remote host; if bytes are exact and auth still fails, stop retrying variants (KbdInteractive, etc.) and ask the user to check/reset the password in hPanel → FTP/SSH Accounts.
- **Host unreachable from the user's network → route SSH through a SOCKS proxy, don't give up.** When the home ISP null-routes the host's IP (ping 100% loss, ssh/rsync time out) but the host is reachable from other networks, add a `ProxyCommand` to the ssh config alias and everything (ssh, rsync, git push via `HTTPS_PROXY`) works again:
  ```
  Host hostinger-kenfa
      HostName 145.79.14.115
      ProxyCommand socat - SOCKS5:127.0.0.1:%h:%p,socksport=51001
  ```
  (socat's `SOCKS5:` + `socksport=` connects through a local SOCKS5 proxy, e.g. warp wireproxy `127.0.0.1:51001`. Verify the proxy path first with
  `timeout 25 socat - SOCKS5:127.0.0.1:HOST:PORT,socksport=51001 < /dev/null` → prints `SSH-2.0-...`.) One-time, then `rsync -e ssh`/`git push` just work.
- **rsync over a slow SOCKS proxy: big combined syncs time out AND silently never land.** One command rsyncing `app/ database/ resources/ routes/ ...` together blows the 120s tool timeout, and `--partial`/exit-0 can report success while the files never reached the host. Fix: rsync **per-directory, small batches**, then ALWAYS verify the key files landed with a follow-up `ssh 'ls path'`/`grep` — never trust rsync's exit code over a proxy. (Happened 2026-08-29: routes/migrations arrived only on the third per-dir pass.)
- **ISP can null-route the CDN's whole IP range, not just the SSH IP — and it can change day-to-day.** 2026-08-26 the home ISP only blocked the SSH IP (`https://...` = 200 from home). 2026-08-29 the SAME ISP started timing out on BOTH `kenfa.id` and `test.kenfa.id` from home WiFi — server healthy (403 WAF from other networks), cellular works, changing DNS resolver changes nothing → IP-level null-route of the Hostinger CDN ranges `147.93.77.0/24` + `213.210.57.0/24`. Diagnosis order: (1) server alive from a different network? (2) cellular vs home WiFi differ? (3) DNS change fixes nothing? If all three → ISP IP block, not a site problem. Mitigations: VPN/cellular for the blocked user, or put Cloudflare proxying in front of the domain so customers resolve Cloudflare's never-blocked ranges instead of the origin's.
- **AAAA/`IPv6` on Hostinger CDN cannot be removed from hPanel.** The hPanel DNS zone has NO AAAA records — `test.kenfa.id`/`kenfa.id` still resolve to `2a02:4780:...` because the CDN target `*.cdn.hstgr.net` publishes AAAA in its OWN zone. To force IPv4-only you must bypass the CDN (static A record to an origin IP — risky, origin IPs rotate), not delete hPanel records. Check where AAAA actually comes from: `dig +short <domain> AAAA` vs `dig +short <cdn-host> AAAA`.
- **Silent-degrade third-party API = "blank UI, no error".** A service built with a "degrade, don't block" contract (bad key/timeout/non-2xx → returns `[]`/null, logs a warning, falls back) makes an AUTH misconfig look like "API down". Symptom: a UI section fed by an external API is empty from day one with zero errors anywhere. Topping up account BALANCE never fixes a wrong/missing KEY. Full diagnosis recipe (key type `live` vs `test`, JWT truncation to 3 parts, config-cache staleness, mask secrets) in `references/third-party-api-silent-empty.md`.

## Session notes
- See `references/hostinger-kenfa-example.md` for the concrete commands used on
  a Hostinger hPanel deploy (test subdomain, reused DB + photos).
- See `references/deploy-disaster-recovery.md` for the full recovery procedure
  after a deploy destroyed the live root (triage, .env rebuild from a dated
  backup, per-dir reconstruction, outside smoke test, scheduler restart).
