# Docker-on-host gotchas (SELinux/Fedora + bind mounts)

Lessons from kenfa-2.0 sprint 2026-08-26. Class: Laravel/Docker dev on Fedora with SELinux enforcing + btrfs.

## Container root permanently changes host file ownership
When a root-running container writes into a bind-mounted volume (`./src:/var/www/html`), files it creates are owned `root:root` on the HOST — and this persists after the container stops.

**Symptom:** host-side builds fail with EACCES in paths like `node_modules/.vite-temp/` and `public/build/` while most of `node_modules` is still user-owned.

**Fix (targeted, not blanket):**
```bash
find <dir> -user root | wc -l          # scope the damage first
sudo chown -R $USER:$USER <affected-subpaths>
```
Don't blanket-chown huge trees blindly; find what's actually root-owned.

## Root-owned test dirs are arbitrarily nested (not just disks/local)
Feature tests that write to `Storage` fakes create their OWN nested subdirs as
root when a container-run test made them first. kenfa-2.0 sprint 2026-08-27:
full suite had 1 error — `FilesystemIterator ... /storage/framework/testing/disks/local/return-proofs: Permission denied`
(an order-return test writing upload proofs), not the `disks/local` dir the main
skill names. Don't chase individual leaf dirs.

**Pragmatic host-side fix** (when the host user has sudo — Sofyan does):
```bash
sudo chown -R $USER:$USER src/storage/framework/testing
```
Chown the WHOLE `storage/framework/testing` tree, not just `disks`, because the
offending subdir varies per feature test. Re-run the suite; goes green.

Prefer this over the `docker exec -u root` route on this box: the `kenfa-app`
container often can't read the bind mount at all (see loop below), so `docker exec`
for cleanup/artisan/tests is unreliable. Run artisan + tests from the HOST
(PHP 8.5, vendor bind-mounted; SQLite in-memory so no MySQL needed). If you DO
need dev MySQL from a host-side `artisan tinker`, it's published on `127.0.0.1:3308`
— override `database.connections.mysql.host/port` in the tinker call.

## Waiting-for-app-source loop after recompose
A container whose entrypoint waits for a mounted file (`while [ ! -f /var/www/html/artisan ]; ...`) can hit transient permission errors on the btrfs/SELinux bind mount right after `docker compose up -d` recreates containers — even though the source dir is fine on the host.

**Diagnosis:** `docker exec <app> ls /var/www/html/artisan` → Permission denied, but host sees the file fine; mount shows `container_file_t` SELinux label.
**Fix:** `docker restart <container>` — remount resolves it. Verify with curl before investigating deeper.

## Verification workflow for changed server code
1. Extract the real function from TS source; strip types via the repo's own esbuild:
   `node_modules/.bin/esbuild --loader=ts` (feed function text via stdin).
2. Execute against fixtures covering: the bug case, no-regression case, false-negative case.
3. Grep the compiled bundle for the guard — remember esbuild normalizes `'claude'` to `"claude"`.

## Compose service patterns (scheduler + queue for Laravel)
```yaml
  scheduler:
    entrypoint: ["php", "/var/www/html/artisan", "schedule:work"]
  queue:
    entrypoint: ["php", "/var/www/html/artisan", "queue:work", "--tries=3", "--timeout=60"]
```
Override `entrypoint:` when the Dockerfile CMD is a wait-then-serve script. Check `docker compose logs <svc>` shows normal polling ("No scheduled commands are ready to run" = healthy idle).
