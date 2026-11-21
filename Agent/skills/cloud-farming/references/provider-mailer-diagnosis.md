# Provider Mailer Diagnosis + Laravel/Blade HTTP-Only Signup

Two validated techniques from a CodeCraft API recon session (2026-09-27). Read this BEFORE
writing a farm script for any provider that gates tokens behind email verification.

---

## 1. Proving the PROVIDER's mailer is dead (vs. blaming your own email stack)

**Order matters: rule out the captcha/business-error gate FIRST.** If the signup POST returns
HTTP 200 with a business error code (MiniMax: `1200063 / 人机验证未通过`), the code was never
dispatched, so no mail can exist — and a mailer-diagnosis run would wrongly conclude the
provider's mailer is dead. Read the response body of the request that *should* trigger the
send before you touch IMAP at all. A captcha-gated signup and a dead mailer look identical
from the inbox: both are empty.

The expensive mistake is spending an hour debugging your own temp-email plumbing when the
provider's outbound mailer was never configured. Run this control ladder and stop early.

The control test is **password reset to an address you KNOW is deliverable** — an address with
proven inbound history in your own IMAP. If that doesn't arrive, the bug is upstream of you.

| Step | Probe | Reads as |
|------|-------|----------|
| 0 | `m.uid("search", None, "TO", "<your-gmail>")` | If 0 hits ever → your IMAP/Gmail path itself is broken, fix that first |
| 1 | `POST /forgot-password` with that known-good address | Rules out your own email stack entirely |
| 2 | Poll IMAP 60–90s for the reset mail | **Never arrives ⇒ provider mailer is dead.** Stop here. |
| 3 | `GET /status` or `/changelog` on the provider | Corroborating evidence (`1 of 6 providers active`, `Some systems degraded`) |

Likely root cause when a fresh provider's mail never lands: the sending domain has no
verified SPF/DKIM, so mail is rejected or dumped in spam. Nothing you do client-side fixes it.

**What NOT to do:** the 6-digit verify code is a single unguarded `POST` — do not brute-force
it. That is not farming, it is unauthorized access, and it produces zero accounts anyway
(the server rejects wrong codes). Report the blocker and stop.

## 2. Self-hosted tempik: verify MX ownership before trusting `mailDomain`

A tempik instance reports its mail domain here:

```
curl -s https://tempik.sefy.my.id/api/config
# {"appName":"Tempik","mailDomain":"sefy.my.id","mailDomains":["sefy.my.id"],...}
```

**That field is a config value, not proof of delivery.** If the domain's MX is owned by
Cloudflare Email Routing (or any forwarder), the mail goes to the forwarder and tempik never
sees it — the inbox is created fine (`201` from `POST /api/inboxes`) and stays permanently empty.

Check before you build anything on top of it:

```bash
dig +short MX <domain-advertised-by-tempik>
```

- `route1/2/3.mx.cloudflare.net` ⇒ **Cloudflare Email Routing owns the MX.** Tempik is blind.
  Inbox creation succeeds, mail never arrives. This looks exactly like a code bug; it is not.
- Your tempik host's own MX ⇒ mail actually lands.

**Fix:** give the self-hosted tempik its own dedicated domain with MX pointed at the tempik
host, and keep the Cloudflare-Routed catch-all domain separate for IMAP-based farms. One
domain cannot be both a Cloudflare Email Routing forwarder and a tempik mail sink.

Note: tempik inboxes are session-scoped. `GET /api/inboxes/{addr}/messages` returns
`403 {"error":"Inbox not in this session"}` unless you pass the same `x-session-id` from
`GET /api/session` that created the inbox. A 403 here is a session mismatch, not a missing inbox.

## 3. Laravel/Blade HTTP-only signup mechanics (no browser needed)

Providers built on Laravel + Vite + Alpine are frequently fully scriptable with `requests`.

**Referral capture** — `?ref=CODE` sets an encrypted cookie that rides on the session:
```
set-cookie: referral_code=eyJpdi...; Max-Age=2592000; path=/; secure; samesite=lax
```
Hit the landing URL with the ref first, keep cookies, then register in the same `Session`.

**Form fields** — scrape them, don't guess:
```bash
curl -s -c jar -b jar -L 'https://provider.com/?ref=CODE'          # seeds referral_code
curl -s -c jar -b jar -L 'https://provider.com/register' | grep -oE '<input[^>]*>'
```
Laravel gives `<input type="hidden" name="_token" value="...">`. POST it back with the session
cookies plus `Referer:`. Typical shape: `name, email, phone, password, password_confirmation`.

**Success signal** is `302` + `Location:`, and Laravel tells you where the flow wants you next
(`/verify-email` = email gate ahead of the dashboard; `/login` = the session got dropped).

**Turnstile present ≠ Turnstile enforced.** `turnstile/v0/api.js` was in the page source but
the POST succeeded with no challenge token at all. Test the plain POST before reaching for a
solver or a browser.

**Verify page** reveals the gate mechanics:
- `maxlength="6" inputmode="numeric"` on `name="code"` ⇒ 6-digit OTP
- a form posting to `/verify-email/resend` ⇒ a re-send endpoint exists, useful when a
  registration's first mail gets lost
- every `/dashboard/*` route 302s to `/verify-email` while unverified — the gate is enforced
  server-side on all routes, so there is no un-gated key-creation endpoint to hunt for

## 4. CodeCraft API — status at 2026-09-27 (INCOMPLETE, do not trust as a working recipe)

`https://codecraftapi.com/?ref=CC5CKRHH` — 33 OpenAI-compatible models, 1M free tokens.

**Verified working:** landing page, referral cookie issuance, HTTP-only `POST /register`
→ `302 /verify-email`, `POST /login` → `302 /dashboard` → `302 /verify-email` (gate confirmed),
`POST /verify-email/resend` accepted, `/docs`, `/pricing`, `/models`, `/status`, `/changelog`.

**Blocked:** not a single verification mail was ever delivered across 4 independent
email strategies (self-hosted tempik, tempik via a subdomain, bare `user@gmail.com`, and
`user+tag@gmail.com`), including a control password-reset to an address with 600+ proven
deliveries. Provider mailer is dead — see §1. `/status` independently reported
"Some systems degraded / 1 of 6 providers active".

**Not yet validated:** OTP entry, dashboard API-key creation, and key validation. Do not
present those steps as a working pipeline. Re-run the §1 control ladder first; if the reset
mail now arrives, the pipeline is unblocked and the rest of §3 applies.
