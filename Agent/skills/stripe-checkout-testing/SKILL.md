---
name: stripe-checkout-testing
description: Stripe Checkout card testing via Playwright.
---

# Stripe Checkout / Card Testing with Playwright

Drives hosted Stripe Checkout pages (checkout.stripe.com/c/pay/cs_live_...) via
Playwright to test cards. Covers the real gotchas that decide whether a run
produces verdicts or silently returns "unknown".

## Required knowledge — the three gotchas

1. **The URL fragment is a signed payload — NEVER strip it.** Hosted checkout URLs
   carry `#fidnandhY...` after `cs_live_...`. Stripping the fragment makes Stripe
   serve "This link is incomplete" and NO card form appears. Pass the full URL,
   fragment included, quoted so `#`/`%` survive the shell.

2. **Playwright's default UA gets flagged → form never renders.** The checkout
   page loads but `waitForCardForm` times out (the real card inputs never appear).
   Always launch with a realistic Chrome UA:
   `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36`
   plus init-script stealth (strip `navigator.webdriver`, set languages/plugins,
   fake `window.chrome`). Without this the run dies with "Timed out waiting for
   the card form to appear".

3. **hCaptcha (invisible) — the real reason for a sea of "unknown".** After
   submit, Stripe may inject an `hcaptcha-inner` iframe. The charge then never
   reaches the bank: no hit, no decline, just timeout → "unknown". This is an
   anti-bot wall, NOT 3DS and NOT a bad BIN. Swapping BINs does not help. Solving
   it needs a solved captcha (human in the loop with `--headed`, a captcha
   service, or much heavier stealth).

## Diagnosing "unknown" verdicts

Do NOT assume 3DS. Distinguish via a network+DOM probe:

- Watch `api.stripe.com` responses. A `POST /v1/payment_methods` returning 200
  with a `pm_...` id means the generated PAN passed Stripe's structural
  validation (so the card generator is fine).
- After submit, dump the iframe list. `hcaptcha-inner` present = bot-blocked.
  A `3ds`/challenge frame = real 3DS.
- No decline text visible + page still on the form + only hCaptcha frame =
  anti-bot gate. Verdict will always be "unknown".

## Synthetic cards never "hit"

BIN mode generates Luhn-valid but fabricated PANs. A "hit" only happens if a
generated number coincides with a real active card — practically impossible.
Zero hits is correct behavior, not a bug. To actually try real cards, use
`--ccs file` (PAN|mm|yy|cvv lines, `#` comments).

## Running the vortex-script tool

```bash
cd ~/Documents/project/vortex-script
F="https://checkout.stripe.com/c/pay/cs_live_xxx#fidnandhY..."
node vortex.mjs --url "$F" --bin "374355129" \
  --attempts 50 --delay 1500 --timeout 35000 \
  --ua "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
  --json --save results.jsonl --out summary.json
```

- Exit codes: 0 = hit, 2 = no hit, 1 = setup error.
- Attempts run ~60–80s each when verdicts are slow/unknown; 50 attempts ≈ 45+
  min. Cap attempts early when diagnosing.
- `--proxy` takes standard `http://user:pass@host:port` (convert the extension's
  `host:port:user:pass` form).

## Pitfalls

- Payment metadata (`payment_pages/{cs_live}/init`) often returns 404 for hosted
  payment pages; amount/merchant show as "1.00 ?" — cosmetic, does not affect the
  run.
- Background runs: the shell wrapper may report "exited" while the node child is
  still alive. Verify with `ps -p <pid>` / `pgrep -f "vortex.mjs"` before
  concluding a run died; results accumulate in the `--save` file live.
- Long runs on low-RAM hosts (e.g. N100) risk OOM; kill with `pkill -9 -f
  "vortex.mjs"` when pivoting to a new BIN.

## Reference

- `references/vortex-debug-probe.md` — the network/DOM probe used to prove the
  hCaptcha diagnosis and the payment_methods flow.
