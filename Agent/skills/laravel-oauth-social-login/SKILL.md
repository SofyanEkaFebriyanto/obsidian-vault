---
name: laravel-oauth-social-login
description: Add Google login to a Laravel app via laravel/socialite.
---

# OAuth Social Login in Laravel (laravel/socialite)

## When to Use
- A founder/user asks why they can't "login with Google / GitHub / others like
  other sites," or asks to add social/one-click login to a Laravel app.
- Wiring Google (or any socialite provider) into an app that has existing
  auth, a guest-order-claim listener, and/or a NOT-NULL `password` column.

"Every other site lets you login with Google" = one package + one
controller + two routes + a button. The hard parts are all the edge cases:
it must be a no-op while credentials are blank, it must mark the account
verified (email is provider-guaranteed), it must auto-claim the visitor's
guest orders, and it must survive the NOT-NULL `password` column.

## Workflow

1. **Recon first** — before writing any code, confirm:
   - `composer.json` PHP floor vs installed PHP (Socialite v5 needs ^8.2).
   - The `User` model's **`$fillable`** (is `email_verified_at` in it? almost
     never) and **`role`** (must stay OUT of fillable so OAuth can't self-promote).
   - Whether an existing **Login-event listener** already claims guest orders
     (e.g. `Event::listen(Login::class, ClaimGuestOrders::class)`) — if so, you
     get the auto-claim for free and must NOT dispatch a second Login event.
   - Whether the `password` column is **NOT NULL** (`SHOW COLUMNS FROM users`).
     If it is, OAuth users need a random hash, not `null` — see Pitfall.
2. **Install** in the container/host that has composer:
   `composer require laravel/socialite` (v5 for Laravel 11+).
3. **Config**: a `services.google` block reading `GOOGLE_CLIENT_ID` /
   `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` from env. Default the
   redirect to `http://localhost:8080/auth/google/callback`.
4. **Controller** `app/Http/Controllers/Auth/GoogleController.php` — two
   methods, both guarded by `blank(config('services.google.client_id'))`
   (feature-off ⇒ redirect back to login with a friendly `session('status')`,
   never 500). See the concrete file in `references/kenfa-google-login.md`.
5. **Routes** — put `GET /auth/google` (redirect) and
   `GET /auth/google/callback` in the **guest** middleware group. On a site
   with a top-level catch-all slug route, they MUST sit **above** the
   catch-all (Laravel won't fall through). Both get `->name('auth.google')` /
   `->name('auth.google.callback')`.
6. **Feature-off test + real-flow test** — force the keys blank in the test
   bootstrap (so a real key never leaks), then `config()->set(...)` them inside
   the test and stub the provider with `Socialite::extend(...)` +
   `\Laravel\Socialite\Two\User::fake([...])`. See the test in the reference.
7. **Env**: add the three `GOOGLE_*` keys to `.env` and `.env.example` with a
   comment listing the EXACT redirect URIs the owner must register in Google
   Cloud Console (one per environment: sandbox + production).
8. **Run the full suite**, then verify the redirect URL points at
   `accounts.google.com` with the right `client_id` before asking the founder
   for keys.

## Pitfalls

- **Feature must be OFF-by-default and harmless.** Until the owner pastes real
  `GOOGLE_CLIENT_ID`/`SECRET`, `/auth/google` and `/auth/google/callback` must
  302 back to the login page with a "not enabled" `status` message — NOT
  throw, NOT 500, NOT a broken redirect. Guard BOTH methods with
  `blank(config('services.google.client_id'))`. The login/register button can
  render unconditionally; clicking it while unconfigured just returns the
  message.
- **`password` column is usually NOT NULL → never set it to `null`.** `firstOrNew`
  + `$user->password = null` + `save()` throws a `QueryException`. With the
  `'password' => 'hashed'` cast, set a **random string** and let the cast hash
  it: `$user->password = Str::random(40);`. The hash is unguessable, so email
  login to an OAuth account can never succeed — exactly the intent. Only if
  you'd rather keep it truly empty do you write a migration to `nullable()`,
  and that's a prod-schema change to avoid for a one-line fix.
- **`email_verified_at` is NOT in `$fillable` — `firstOrCreate([...], $attrs)`
  silently drops it.** You'd end up with an unverified account and the guest-
  order claim (which requires `hasVerifiedEmail()`) would never fire. Use
  `firstOrNew` + set the attribute **directly** (`$user->email_verified_at =
  now();`) + `save()`. Same rule for any attribute the form must not fill.
- **Don't dispatch the Login event yourself — `Auth::login()` already fires it.**
  Any `Event::listen(Login::class, ...)` (guest-order claim, activity log)
  runs automatically. A second manual `Event::dispatch(new Login(...))`
  double-runs those listeners.
- **Race (two tabs, same Google account): `firstOrCreate` is atomic; the
  `firstOrNew`+`save()` path is not.** Wrap the `save()` in a `try` and, on
  `QueryException`, re-`where('email',...)->firstOrFail()`.
- **Socialite v5: `new Two\User([...])` does NOT populate the getters** —
  `getEmail()`/`getName()` return `null` even though the raw array is there.
  In tests you MUST build the fake with `\Laravel\Socialite\Two\User::fake([...])`
  (it calls `setRaw`+`map`). This is the #1 reason a social-login test
  "creates a user but the assert fails."
- **A social callback that "404s" is often a swallowed `ModelNotFoundException`.**
  If the controller wraps the whole flow in `catch (\Throwable)` → redirect,
  a real error becomes a redirect to a page that renders the custom 404, and
  you chase a phantom routing bug. Debug with
  `$this->withoutExceptionHandling();` in the test and print
  `$e->getTrace()` — the true cause (e.g. `firstOrFail` after a failed `save()`)
  appears immediately.
- **Force the provider keys BLANK in the test bootstrap** (`GOOGLE_CLIENT_ID=''`
  etc.) so a developer's real `.env` key can never make a test hit Google.
  Then `config()->set('services.google.client_id', 'test-...')` per-test.

## Reference
- `references/kenfa-google-login.md` — concrete kenfa-2.0 GoogleController,
  route snippet, config block, the full `GoogleLoginTest` (including the
  `Socialite::extend` + `User::fake` stub), and the NOT-NULL-password →
  ModelNotFound debugging path that got it green.
