---
name: laravel-docker-vps-deploy
description: Deploy a Laravel + Docker Compose app to an Ubuntu VPS — key bootstrap, build order pitfalls, and end-to-end smoke testing including CSRF-gated POST flows.
---

# Laravel + Docker → Ubuntu VPS Deployment

Class-level workflow for taking a repo with `Dockerfile` + `docker-compose.yml` (Laravel/PHP container + MySQL) and standing it up on a fresh Ubuntu VPS, then proving it actually works.

## Workflow

1. **SSH access first.** If only a password exists: `sshpass -p 'PASS' ssh-copy-id -i ~/.ssh/<key>.pub user@host`, then verify key login works before anything else.
2. **Install Docker:** `curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ubuntu` (re-login or use sudo for the immediate next commands).
3. **Rsync the repo**, excluding `.git`, `vendor`, `node_modules`, and any large local backups (`--exclude 'src/Archive.zip'`). Check `du -sh` afterwards — gigabyte-scale results usually mean a storage/ dir full of product images got copied; that may be intentional for this app class.
4. **Edit `.env` on the VPS** (sed over ssh): `APP_ENV=production`, `APP_DEBUG=false`, `APP_URL=http://<ip>:<port>`. Keep the existing `APP_KEY` if copying from dev so encrypted data stays readable.
5. **`docker compose up -d --build`** — but see Pitfall #1 about vendor/.
6. **Inside the app container:** `composer install --no-dev --optimize-autoloader`, `npm install && npm run build`, `php artisan migrate:fresh --seed --force` (fresh VPS only), `php artisan storage:link`.
7. **Smoke test from OUTSIDE the VPS** (see below), not just localhost on the box.

## Pitfalls

1. **App container crash-loops before vendor exists.** The compose CMD boots `artisan serve` immediately; without `vendor/autoload.php` it restarts forever, and `docker exec` refuses ("container is restarting"). Fix: run composer via a throwaway container from the already-built image:
   `docker run --rm -v ~/apps/<app>/src:/var/www/html -w /var/www/html <project>-app composer install --no-interaction --no-dev`
   Then `docker compose restart app`.
2. **Root-owned storage subdirs break things later.** Any command ever run as root in the container chowns `storage/framework/testing/disks` etc. to root; subsequent host-user test runs fail with `UnableToCreateDirectory`. Fix: `docker exec -u root <app> sh -c "rm -rf ... && chown -R 1000:1000 ..."` then recreate as the host user. Prevent by never running artisan as root interactively.
3. **`APP_URL` vs actual host.** After changing `.env`, run `php artisan optimize:clear` — a stale config cache keeps serving old URLs. Note `asset()` uses the request Host, so pages fetched as `localhost` show `localhost` URLs; always smoke-test via the public IP/domain to see what real users get.
4. **MySQL healthcheck gate:** compose `depends_on: condition: service_healthy` means first 500s are usually just "DB not migrated yet", not a code bug. Check `storage/logs/laravel.log` for e.g. missing `sessions` table before debugging code.

## Smoke-testing CSRF-gated POST flows

Browser-less checkout/order testing hits two traps:

- **419 Page Expired:** you must GET a page first to seed session+csrf, then POST with `_token` and the GET's cookies. Easiest reliable route is a PHP script executed in the container:
  ```php
  $kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
  $res1 = $kernel->handle(Illuminate\Http\Request::create('/checkout', 'GET'));
  foreach ($res1->headers->getCookies() as $c) { $req->cookies->set($c->getName(), $c->getValue()); }
  // POST with '_token' => csrf_token()
  ```
- **Payload shape comes from the FRONTEND, not your guess.** Read the JS cart-store / controller validation before building test payloads (e.g. this app expects `cart=[{"variantId":N,"quantity":N}]` plus structured `shipping_{province,city,district}_id` DB ids — not `variant_id`/`qty` text names). Validation error arrays land in `session('errors')`; dump them on non-302 instead of assuming success.

Verify the write side-effects directly in DB (order row totals, stock decrement), then **clean up test rows and restore stock** so the demo DB stays pristine.

## Verification checklist

- [ ] Public URL: home / category / PDP / search / static page / sitemap.xml all 200
- [ ] One product image serves 200 via `/storage/...`
- [ ] One guest checkout creates an order, decrements stock, redirects to confirmation
- [ ] Test data removed, stock restored
- [ ] `docker compose ps` all Up (+ mysql healthy)

Session-specific detail (concrete values, proven commands): see `references/kenfa-vps-deploy-notes.md`.
