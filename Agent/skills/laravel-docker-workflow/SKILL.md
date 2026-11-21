---
name: laravel-docker-workflow
description: Work on Dockerized Laravel projects (kenfa-2.0 et al) — run tests/migrations correctly across host vs container, validate docs claims against the real repo, and fix root-owned storage dirs created by the container.
---

# Dockerized Laravel workflow

For projects like `kenfa-2.0` (Laravel in Docker, MySQL, source mounted at `src/`, CLAUDE.md is authoritative context).

## Validating a memo/progress doc against the real code

When asked to "cek perkembangan / validasi memo":
1. Read the doc's concrete claims only: file paths, migration filenames, test counts, seeder/resource names.
2. Verify existence with one batched shell loop (`[ -f "$f" ] && echo OK || echo MISSING`) over every claimed path.
3. Count tests by grepping `function test` across test files — compare to the claimed number.
4. Only then run the suite. Report deviations explicitly; don't take the doc at its word.

### Validating PDF course modules / tutorial docs
- Extract with `pdftotext <doc>.pdf /tmp/out.txt` (works well even for 130+ page modules); screenshot-heavy PDFs yield only headings — pair them with a sibling .md of the same content and diff the extractions to confirm identity before reviewing twice.
- Build a claim→status table (feature/file claimed vs present in repo) rather than quoting prose. Common findings: container names in docs go stale (`alat_app` → `laravel-api`), docs carry typos the repo already fixed (`kategoris` table name), and docs cover only part of the repo (web Blade vs REST API halves live in different documents).
- When multiple docs describe one project, state explicitly which doc each part of the repo implements and compute % coverage per doc — that becomes the user's work roadmap.

## Running tests

- Tests run on SQLite in-memory via `tests/bootstrap.php`; safe against dev MySQL.
- Run from the HOST: `cd src && php artisan test` (vendor is bind-mounted).
- Or run inside the container (reliable, avoids host PHP version drift):
  ```sh
  docker exec -w /var/www/html kenfa-app php artisan test
  docker exec -w /var/www/html kenfa-app php artisan test --filter PdpActionBarTest
  docker exec -w /var/www/html kenfa-app npm run build   # Vite asset build
  ```
  **Container working dir is `/var/www/html`, NOT `src/`.** `docker exec -w /var/www/html/src ...`
  fails with `OCI runtime exec failed: chdir ... /var/www/html/src ... no such file or dir`
  (the app code is mounted at the container root, not under `src/`). Always use `-w /var/www/html`.
- If a test fails with `UnableToCreateDirectory .../storage/framework/testing/disks/local`: the dir was created **as root by a container-run test** and the host user can't write into it. Fix:
  ```
  docker exec -u root <app-ctr> sh -c "rm -rf <app>/storage/framework/testing/disks && chown -R 1000:1000 <app>/storage/framework/testing"
  mkdir -p src/storage/framework/testing/disks/local
  ```
  Then re-run. This is environment drift, not a code bug.

## Pitfalls

- SCHOOL PROJECTS: if the repo is the user's school assignment (ujikom/tugas), do NOT write or edit project code — provide step-by-step guidance, artisan commands, and review only; let them implement. Confirm this mode early.
- Audit findings that recur in Laravel CRUD inventory apps: enum status mismatch between validation rules and migration (`'ditolak'` validated but absent from enum → raw SQL error); stock decremented in two flows (admin store + petugas approve) causing double-deduction; request arrays without integer cast or stock check letting oversize loans through; empty migration `down()` methods; double `.php.php` migration filenames.
  - Fix pattern for enum mismatch: new migration with `$table->enum('status', [...full list...])->default(...)->change()` (Laravel 12 native, no doctrine/dbal); down() restores the old list. Verify with `SHOW COLUMNS`.
  - Renaming migration files post-migrate desyncs the `migrations` table → UPDATE its `migration` column to match, or just `migrate:fresh --seed` when demo data is disposable. Check `migrate:status` after any rename.
  - Optional-password update: `'password' => 'nullable|string|min:6'` + only include in the update array `if ($request->filled('password'))` with `Hash::make()`; form field has NO required and NO old(). Replace all `$model->create/update($request->all())` on user/alat input with `$request->only([...])`.
  - Image upload recipe: form needs `enctype="multipart/form-data"`; validate `nullable|image|mimes:jpg,jpeg,png|max:2048`; `store('folder','public')`; delete old file via `Storage::disk('public')->delete()` on replace AND delete; `storage:link` once; render with `asset('storage/'.$path)` behind an `@if`. Test the nullable path (no file) too — that's where mass-assignment refactors break.
  - Guard cascade deletes: block deleting a parent whose children exist (`$kategori->alat()->exists()` → back with error flash) instead of silently cascading away inventory.
- Runtime-only typos survive static checks — a wrong class name in a relation (`hasMany(DetailPinjam::class)` vs actual model `DetilPinjam`) passes lint/tests-without-feature-coverage and kills every endpoint that eager-loads or iterates the relation (500s). Catch via curl smoke test of each route group, not by reading code alone. When found: grep -rn the misspelling across app/ before fixing.
- Stock-integrity invariant for loan apps: restock must fire on EVERY path that un-loans items (return, reject/ditolak, delete-while-borrowed). If stock is deducted at create time but only restored on one branch, rejected loans silently lose stock. Wrap multi-row stock mutations in DB::transaction.
- Blade files may carry stray literal artifacts (`</parameter>` lines) from copy-paste sources; they compile fine but render garbage. Sweep with `grep -rn "</parameter>" resources/views/` during review, then `view:cache` to verify all templates still compile.

- Container processes run as root → any file/dir they create on the bind mount is root-owned on the host. Prefer running artisan/npm on the host; if you must use the container, chown back afterward.

## Blade + Alpine.js pitfalls (kenfa-2.0 storefront)

- **Don't interpolate `route()` / `url()` inside a JS string literal in a `@push('scripts')` block.**
  `'{{ route('checkout') }}'` breaks the JS parser because the inner single quotes
  close the string prematurely — the LSP flags `';' expected` at the route call.
  Fix: bind the URL in the Alpine data object via `@js(...)` and read `this.checkoutUrl`.
  The rest of the file already does this (`images: @js($galleryImages)` etc.) — follow suit.
- **Hide desktop vs mobile UI with Tailwind responsive classes, never duplicate logic.**
  To "replace" the sitewide mobile bottom-nav with a PDP action bar, do NOT detect the
  route in PHP/JS. Instead set a Blade flag section (`@section('pdp_action_bar')@endsection`)
  on the PDP and wrap the nav include in
  `@unless(View::hasSection('pdp_action_bar')) @include('partials.mobile-bottom-nav') @endunless`
  in `layouts/app.blade.php`. Keep both bars `lg:hidden`/`hidden lg:block` so only one shows.
- **Alpine component instances must not double-bind.** If a header component (`headerSearch`)
  is reused for both a desktop icon-panel and a mobile inline bar, give the mobile one
  `lg:hidden` and the desktop one `hidden lg:block`. Two `x-data="headerSearch(...)"` on the
  page are fine as long as exactly one is visible per viewport; the `@click.outside`/`@keydown`
  handlers then never fight.
- **Price is per-variant; never re-derive it in JS.** Pass `formatRupiah($v->price)` as
  `v.formatted` from PHP and render `x-text="v.formatted"` / the reactive getter
  `displayPrice` in Alpine. Searching the rendered HTML for `formatRupiah(` will still match
  the PHP prep block — so to test "no manual re-derive in JS", extract `<script>` bodies via
  `preg_match_all('/<script>(.*?)<\/script>/s', $html, $m)` and assert on those, NOT on the
  whole `$html` (the `@push('scripts')` directive text does NOT appear in rendered output).
- **Alpine `x-data` is REQUIRED on any element carrying `@click` / `$store` / `$dispatch` —
  even a plain `<nav>` or `<div>` wrapper.** (Verified fix 2026-08-30, commit `4f12b49`.)
  Symptom: a `<button @click="$store.cart.toggle()">` (or `$dispatch('toggle-mobile-menu')`)
  does nothing on tap, while sibling `<a href>` links work fine and `window.Alpine` is present
  (v3.x). Root cause: Alpine only binds directives on elements that sit inside an `x-data`
  subtree. A fragment rendered at layout level (e.g. `partials/mobile-bottom-nav.blade.php`
  included directly under `<body>`, no parent `x-data`) has NO component scope, so its
  `@click` is silently ignored — not a JS error, not an overlay, not `pointer-events`.
  Fix: put `x-data` (empty `x-data="{}"` is enough) on the wrapper, e.g.
  `<nav x-data class="lg:hidden fixed bottom-0 ...">`. Rule of thumb: if an element uses any
  Alpine directive but isn't already inside a component (`stickyHeader`, `headerSearch`,
  `productPage`, `mobileMenu`, `cart` store usage in a header that has `x-data="stickyHeader"`),
  add `x-data` to its nearest ancestor. `pointer-events-none` on icon/label/badge children is
  still good hygiene so taps always land on the button, but it does NOT substitute for `x-data`.
- **Verify mobile Alpine behaviour with headless Chromium, not the browser_use tool.** The
  browser_use harness can't emulate Tailwind `lg:` breakpoints (CDP `setDeviceMetricsOverride`
  doesn't retrigger `@media (min-width:1024px)` in that harness) and Cloudflare challenges
  block it on the live host. Instead run Playwright (host has `google-chrome-stable` +
  `playwright` python) through the Warp SOCKS5 proxy (`socks5://127.0.0.1:51001`) against
  `https://test.kenfa.id/`, set `viewport={"width":390,"height":844}`, `wait_for_selector` the
  nav, then `page.click('nav[aria-label="..."] [aria-label="Kategori"]')` and read
  `document.body.style.overflow` / `Alpine.store('cart').open` to prove the handler fired.
  This caught the `x-data` bug that static Blade tests + `node --check` could not.

- **Livewire v4 (loaded because Filament is present) mangles MULTI-LINE inline `@php(...)` in Blade → 500.** Symptom: a page 500s with `Call to undefined function php()` or `Undefined variable $x` even though the source `.blade.php` looks fine and the identical pattern compiles in a plain (non-Livewire) context. Root cause: the inline form that spans lines — `@php($steps = [` + body + `])` — is compiled by `Livewire\Mechanisms\ExtendBlade` into a raw `<?php($steps = [` that never executes, so the assignment doesn't run and the variable is undefined at the following `@foreach`. Single-line inline `@php($x = [...])` and the BLOCK form `@php ... @endphp` both compile fine. FIX: use the block form. VERIFY with a probe (no browser needed):
  ```sh
  docker exec -w /var/www/html <app> php -r 'require "vendor/autoload.php"; $app=require "bootstrap/app.php"; $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
  $bad = Blade::compileString("@php(\$x = [\n  \"a\" => 1,\n])\n@foreach (\$x as \$k=>\$v)\n<li>{{\$k}}</li>\n@endforeach");
  echo "broken-inline=". (str_contains($bad, "<?php(\$x = [") ? "YES" : "no") . "\n";'
  ```
  A 500 here is a SERVER-side render error — the Livewire engine recompiles the view in-memory per request, so the on-disk file in `storage/framework/views/` (which may look correct) is a RED HERRING. Check the in-memory `Blade::compileString` output, not the file.

- **A model you call `->notify()` on MUST `use Notifiable`** (`Illuminate\Notifications\Notifiable`). Missing trait → `$model->notify(new SomeNotification)` throws `Call to undefined method ... notify()`. The trap: if the call site wraps `notify()` in `try { ... } catch (Throwable) { Log::warning(...) }` (a "degrade-don't-500" pattern), the failure is **swallowed silently** — the request still returns 200, the feature "works", but the email never sends and only a WARNING line lands in `storage/logs/laravel.log`. After deploying any feature that emails from a NON-`User` model (order, ticket, return, etc.), grep the log for `Gagal mengirim notifikasi` / `undefined method ... notify` to confirm the notification path actually fired — a green 200 does not prove the email went out.

- **A third-party API 400 `missing parameter(s)` is often YOUR payload shape, not a rejected/revoked key.** Before concluding a key is invalid, reproduce the EXACT request the app sends — read the service code for the field TYPES, don't hand-roll a curl. kenfa Biteship case: a direct `curl` with `"couriers": ["jne","pos"]` (JSON array) → 400 `missing parameter(s)`, but `BiteshipService` sends `"couriers": "jne,pos"` (comma STRING) and got 200 — the key was valid the whole time. Match the real request's content-type and field shapes; a generic "missing parameter" 400 body is a schema/shape mismatch, not an auth rejection. (Don't write the wrong conclusion into notes — I first recorded "test key rejected" and had to walk it back.)

- **`type="tel"` does NOT enforce numeric-only on desktop browsers — letters pass straight through.** Full phone validation requires three layers: (1) HTML: `type="tel"` + `pattern="^(08|\+62|62)[0-9]{7,13}$"` + `inputmode="numeric"` on the input; (2) Server: `'regex:/^(08|\+62|62)[0-9]{7,13}$/'` rule in the controller validate() array; (3) Message: `'phone.regex' => 'Nomor WhatsApp tidak valid. Gunakan format 08xx, +62xx, atau 62xx.'`. The `pattern` attr gives native browser validation tooltip; `inputmode="numeric"` brings up number keyboard on mobile. Without server-side regex, a forged POST with letters still creates the record. When adding this regex, grep ALL test files for `'customer_phone'` / `'phone'` to find fixtures using short dummy values like `'08111'` or `'08123'` — they will fail the new regex (min length = 9 chars: `08` + 7 digits). Bulk-fix with sed: `sed -i "s/'customer_phone' => '08111'/'customer_phone' => '081234567890'/g" tests/Feature/*.php`. Also grep for test POST payloads that don't include `phone` at all — if phone is now `required`, those tests will 422 and the test will assert on the wrong error.

- **The `patch` tool double-escapes backslashes when writing PHP/JS regex literals.** Writing `\s` (single backslash) into a `.php` file via `patch`/`write_file` landed as a literal `\\s` (double backslash), which silently breaks the regex (matches a literal backslash then `s`). Hit twice in one session editing PHPUnit `assertMatchesRegularExpression` strings. After any patch that adds/edits a regex, `grep ... | cat -A` the line to confirm exactly ONE backslash and re-patch if doubled. (Same class of trap: watch `\\n` inside double-quoted PHP strings passed through the tool.)

## Testing server-rendered Alpine/Blade (Feature tests)

Alpine behaviour can't be unit-tested without a browser, but the *rendered markup* can.
Pattern that works for kenfa-2.0 PDP/header changes (see `tests/Feature/PdpActionBarTest.php`):
- Create a `Product` + `ProductVariant` (variant needs `sku` — it's NOT NULL; a bare
  `ProductVariant::create([...])` without `sku` throws `SQLSTATE[23000] NOT NULL constraint failed`).
- `get(route('product.show', $slug))->assertOk()` then `assertSee('Beli Sekarang', false)`
  for mobile action-bar text, `assertSee('aria-label="Pilih ukuran"', false)` for the sheet,
  and `assertStringNotContainsString('aria-label="Navigasi utama mobile"', $html)` to prove
  the flag-section hid the sitewide bottom-nav.
- For "desktop unchanged" sanity, also assert the desktop control is still in the HTML
  (`assertSee('Add to Cart', false)`) — its `hidden lg:flex` class hides it visually but
  keeps it in markup, so this catches accidental deletion.
- `sudo` may prompt for password in agent shells — prefer the `docker exec -u root` route for root-owned cleanups (docker group membership usually suffices).
- After compose recreate, a container may loop "Waiting for app source..." with Permission denied on the bind mount even though the host side is fine. `docker restart <ctr>` is only a BAND-AID (breaks again on the next recreate). ROOT CAUSE on SELinux hosts: the bind mount uses `:Z` (uppercase = PRIVATE label with a per-container MCS category that changes every recreate), so a freshly-recreated container can't read files still labelled with the old category → `artisan` invisible, `php artisan serve` waits forever, `:8080` dead. PERMANENT FIX: change every shared bind mount to `:z` (lowercase = SHARED label) in docker-compose.yml (`./src:/var/www/html:z`), then `docker compose up -d --force-recreate`. Use `:z` whenever multiple containers (app+scheduler+queue) mount the SAME source. See references/docker-selinux-gotchas.md.
- Laravel scheduler + queue worker as compose sidecars: override `entrypoint:` with `artisan schedule:work` / `queue:work --tries=3`. In production without Docker (shared hosting), scheduler = cron running `artisan schedule:run` every minute.
