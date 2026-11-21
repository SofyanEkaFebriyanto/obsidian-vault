# Stripe Checkout — Live-Run Gotchas

Operational lessons from running a Playwright-driven Stripe checkout tester
(`~/Documents/project/vortex-script`, port of the VortexHitter extension)
against a live checkout. These are the three things that silently break a run.

## 1. The URL fragment is REQUIRED — never strip it

Live checkout URLs carry a signed payload in the fragment:

```
https://checkout.stripe.com/c/pay/cs_live_XXXX#fidnandhYHdWcXx...
```

If you drop the `#fidn...` fragment, Stripe renders:

> "This link is incomplete — Use the unmodified checkout URL, or ask the
> business for a new one."

and there is **no card form** — the driver times out waiting for it. The
fragment is the token that validates the link. Copy the URL exactly as given,
fragment and all. In bash, wrap the full URL in double quotes so `#` and
`%2F` etc. are not interpreted. (`#` inside quotes does not start a comment.)

## 2. Override the user-agent, or the card form never renders

Playwright's default UA gets fingerprinted. The page loads, but Stripe never
mounts the card fields, so `waitForCardForm()` times out (~20s) with no form.
Fix: pass a real Chrome UA.

```
--ua "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
```

A stealth-lite init script (hide `navigator.webdriver`) helps too but the UA
override is the decisive one. Debug loop: if "page loaded" then "Timed out
waiting for the card form", first suspect UA detection — the page's
`innerText` will show a challenge/incomplete message instead of the checkout.

## 3. Synthetic generated cards return "unknown" — that is normal

BIN mode generates Luhn-valid but synthetic PANs (e.g. Amex BIN 374355129 →
15-digit PANs). These are not real card numbers, so they regularly hit
3-D Secure / extra verification. The classifier reports `status:"unknown"`
and moves on. This is expected behaviour, not a bug — a `hit` on a synthetic
number would actually be unexpected. Don't chase "unknown" as a failure.

## Other notes

- `--timeout` (default 20000ms) is the budget for BOTH the form-wait AND each
  attempt's verdict wait. A single attempt can burn the full timeout (~35s),
  so N attempts ≈ N × timeout. With `--attempts 50` and a 35s timeout,
  a run can take ~30 min — budget accordingly, or reduce timeout/attempts.
- Payment-metadata extraction (`payment_pages/{cs_live}/init`) can return 404
  / be rate-limited. That is cosmetic (just fills amount/merchant in the
  record); it does not affect the run.
- Run `--headed` + `--slow-mo` first on a fresh checkout to watch the iframe
  fill before trusting headless.
