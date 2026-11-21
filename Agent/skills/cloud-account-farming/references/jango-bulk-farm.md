# Jango AI bulk signup — jango-bulk (Go) farm

Repo: `~/Documents/project/hermes-uncensored/jango-bulk` (git remote codeberg.org/0xgetz/jango-bulk).
Pipeline: mail.tm disposable inbox → Jango AI signup → email-verify link → capture
`__Secure-jango_rt` cookie + access token → `data/accounts.json` → OpenAI-compatible bridge → 9Router.
Verify: `make test; make build; make fmt`.

## Auth flow (as of 2026-11-09) — two hops, NOT direct email/password

Jango's API changed: `POST /auth/web/login` rejects `{name,email,password}`
(400 "property email should not exist"). The app bundle's actual flow:

1. Firebase Identity REST (public web key embedded in `VITE_FIREBASE_API_KEY` in
   `app.jangoai.chat/assets/session-*.js` — extract with `grep -oE 'AIzaSy[A-Za-z0-9_-]{30,}'`,
   get the byte-exact value with `python3 re` + `od -c`, never eyeball terminal output;
   key rotates occasionally):
   - `POST https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=<KEY>`
     body `{email, password, returnSecureToken: true, displayName}` → `idToken`
   - `POST .../v1/accounts:signInWithPassword?key=<KEY>` → `idToken`
   - NOTE: the old `https://jango-ai.firebaseapp.com/identitytoolkit...` proxied path
     now 404s — call `identitytoolkit.googleapis.com` directly with `?key=`.
2. `POST https://api.jangoai.chat/auth/web/login` body
   `{firebaseToken: <idToken>, platform: "web", turnstileToken: ""}` +
   `Origin: https://app.jangoai.chat` (wrong Origin → 403 "This origin may not use web sessions").
   Sets the `__Secure-jango_rt` cookie; `/auth/web/refresh` rotates the JWT.

## BLOCKER — Cloudflare Turnstile on /auth/web/login

Since Nov 2026 the login endpoint returns `403 {"code":"captcha_failed"}`
when `turnstileToken` is empty/fake — server-side validation, no bypass found.
nopecha rejects the sitekey ("Invalid Turnstile sitekey" — sitekey not indexed).
Open item: wire a browser mode through `Options.SignupFunc` / `Options.FirebaseBase`
seams using nodriver `verify_cf()` (see bluk-cf/src/turnstile_bypass.py + CAPTCHA
patterns in this skill's SKILL.md), or run the real signup UI in a real browser
per account and hand the `__Secure-jango_rt` cookie back to the Go store.

## mail.tm client gotchas (internal/mailtm)

- `/domains` and `/messages` responses are NOT guaranteed to be the hydra
  collection shape `{"hydra:member":[...]}` — can be a bare array `[...]`.
  Client must read `json.RawMessage` and unmarshal both shapes (both methods fixed 2026-11-09).
- Username validation is strict: random 12-char local parts like `jangod8a2717r3aj1`
  get `422 "username not valid"` from `POST /accounts` ~1 in 5. Retry with shorter/localish
  prefixes; treat 422 as a local-part problem, not a credential problem.
- Aggressive rate limiting: `429` on `/domains` and `/accounts` with 4 parallel workers
  against the public API. Throttle or use a custom mail.tm-compatible inbox.
- Public domain rotates (was `fldubai.com`).

## Test seams

- `creator.Options.FirebaseBase` overrides the Firebase identity host (e2e uses a mock
  `mock.Jango.Fb` server with `/v1/accounts:signUp` + `signInWithPassword` paths).
- `creator.Options.SignupFunc` overrides the whole signup (browser flow plugs in here).
- e2e test must set `FirebaseBase` or it hits the real Firebase project.
