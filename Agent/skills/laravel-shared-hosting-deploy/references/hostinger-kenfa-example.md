# Hostinger hPanel deploy — concrete sessions (kenfa.id, Aug 2026)

Target: `u716977336@145.79.14.115` port 65002.
Auth: SSH key `~/.ssh/hostinger` + config alias `hostinger-kenfa` (password auth
REJECTED by sshd even byte-exact via sshpass — key is the working path).
Domain layout: `~/domains/{kenfa.id,test.kenfa.id,pengiriman.kenfa.id}`.

## ISP port block (discovered 2026-08-26)
Direct SSH to :65002 from the user's home ISP times out (ping loss 100%,
traceroute dies mid-path) while https://test.kenfa.id = 200. Probe order:
1. `curl -s -o /dev/null -w '%{http_code}' https://site` — server alive?
2. From another box you control (VPS tokoserver 82.153.126.137 works):
   `timeout 8 bash -c 'echo >/dev/tcp/145.79.14.115/65002'`
3. Open from VPS → two-hop: run ssh/rsync FROM the VPS, or just deploy when on
   a different network. Don't blame credentials until probed from a second network.

## Recon findings
- CLI `php -v` = 8.3 but Laravel needs 8.4+ → `/opt/alt/php84/usr/bin/php`
  (aliases in ~/.bashrc don't apply to non-interactive ssh — full path always).
- composer at /usr/local/bin; NO node, NO crontab binary anywhere on the host
  (`crontab: command not found`; no /usr/bin/cron). Scheduler workaround:
  ```bash
  # ~/scheduler-runner.sh = while true; artisan schedule:run; sleep 60; done
  ssh host nohup flock -n ~/scheduler.lock ~/scheduler-runner.sh &
  ```
  Fragile (dies on reboot) — proper fix is hPanel UI Cron Jobs with
  `/opt/alt/php84/usr/bin/php ~/domains/<domain>/artisan schedule:run`.
- Old deploy had vendor/ (207M), storage photos (1.2G), seeded DB — reused all.
- **`public_html` is a REAL directory on this host (NOT a symlink to `public/`).**
  Verify first with `ls -ld public_html` — if it's a real dir, do NOT recreate
  `public_html -> public` (that would clobber the live docroot). Only
  `public_html/storage` is a symlink, and on 2026-08-30 it was found BROKEN
  (pointed at `/var/www/html/storage/app/public`, which does not exist → storage
  images 404 while pages render fine). Recreate it after every rsync:
  ```bash
  cd ~/domains/test.kenfa.id
  rm -f public_html/storage
  ln -s "$(pwd)/storage/app/public" public_html/storage
  readlink public_html/storage   # must print .../domains/test.kenfa.id/storage/app/public
  ```
  On a host where `public_html` IS a symlink, recreate that instead — never
  assume; check `ls -ld` before touching the docroot.

## Commands that worked (2026-08-26 P0 deploy)
```bash
# backup (verify tarball exists!)
tar czf ~/test-kenfa-backup-$(date +%m%d%H).tar.gz -C ~/domains test.kenfa.id

# code sync (~fast, vendor/photos excluded); public/build IS included
rsync -az --delete -e ssh \
  --exclude Archive.zip --exclude vendor --exclude node_modules \
  --exclude .env --exclude "storage/app/public/products" \
  src/ hostinger-kenfa:~/domains/test.kenfa.id/

/opt/alt/php84/usr/bin/php artisan migrate --force      # no-op expected
/opt/alt/php84/usr/bin/php artisan config:cache
/opt/alt/php84/usr/bin/php artisan route:cache
/opt/alt/php84/usr/bin/php artisan event:cache
```

## Per-directory rsync over the SOCKS proxy (learned 2026-08-29)
One combined rsync of `app/ database/ resources/ routes/ ...` over the Warp
proxy (`ProxyCommand socat SOCKS5:51001`) blows the 120s tool timeout AND can
report exit-0 with `--partial` while files never landed. After the public
return-feature deploy, routes + migrations only arrived on the THIRD per-dir
pass. Pattern that works:
```bash
# split code dirs into small batches; verify each landed
for d in app database resources routes config bootstrap; do
  rsync -azP --partial -e ssh src/$d/ hostinger-kenfa:~/domains/test.kenfa.id/$d/
  ssh hostinger-kenfa "ls ~/domains/test.kenfa.id/$d/ | head"   # VERIFY, don't trust exit code
done
# public is special: rsync public/ MINUS .htaccess first, then ship .htaccess alone
rsync -azP -e ssh --exclude .htaccess src/public/ hostinger-kenfa:~/domains/test.kenfa.id/public/
rsync -azP -e ssh src/public/.htaccess hostinger-kenfa:~/domains/test.kenfa.id/public_html/.htaccess
```
The `--partial` flag lets a resumable re-run finish a half-transferred file.

## Config-cache gotcha (env var set AFTER cache = app reads stale empty config)
If you add/change an env var (e.g. `BITESHIP_API_KEY`) and the host already has
a cached config, Laravel keeps reading the OLD (often empty) value until the
cache is cleared — so the feature "never worked" even though the key is in
`.env`. After editing `.env` on the host, ALWAYS run:
```bash
/opt/alt/php84/usr/bin/php artisan optimize:clear   # clears config+route+view+event caches
```
This also flushes `view:cache` (so newly synced Blade compiles) and is the
right post-deploy step whenever you've touched `.env` or views.

## Reading env/secret on a CPU-saturated host WITHOUT booting Laravel
Under shared-host load (avg 15-18) even `php -r` or `artisan tinker` hangs past
60s. To confirm a value is set, grep `.env` directly (mask the secret):
```bash
ssh hostinger-kenfa "cd ~/domains/test.kenfa.id && grep -iE '^BITESHIP' .env | sed -E 's/(BITESHIP_API_KEY=).*/\1<hidden>/'"
```
Never print raw API keys into transcripts/logs. If you must boot the app (e.g.
to confirm config cache picked up the key), run it in the background with
`notify_on_complete` — the bootstrap can take minutes when neighbors spike load.
"Connection to UNKNOWN port 65535 timed out" right after the ProxyCommand
connects = host handshake stalling on CPU, not a proxy/network failure; retry
with the lighter grep/ls until load drops.

## Smoke test from LOCAL machine (host-internal curl hits wrong vhost)
- homepage 200, PLP/PDP 200, rupiah prices sane
- one real `/storage/...jpg` = 200 (proves storage symlink)
- one `/build/assets/app-*.js` = 200 (proves Vite assets synced)
- unknown URL = proper 404 without stack trace

## Contrast: VPS deploy (82.153.126.137)
Docker get.docker.com install → rsync whole project → composer/npm INSIDE the
container because the app container crash-loops without vendor. Checkout smoke
test via PHP probe docker-cp'd into the container (CSRF 419 blocks plain curl
POSTs; cart JSON keys are `variantId`/`quantity`, not variant_id/qty).
