---
name: cloud-api-key-farming
description: >-
  Automate bulk account registration + API key extraction across cloud AI providers
  (Alibaba Cloud DashScope, Qwen Cloud, Cloudflare Workers AI, etc.).
  Covers headless browser orchestration, CAPTCHA/slider solving, IMAP OTP reading,
  catch-all email forwarding, and proxy rotation for rate-limit evasion.
---

# Cloud API Key Farming

Bulk-register accounts and harvest free API keys from cloud AI providers.

## Email: Two Approaches

### Catch-all (simpler, no API dependency)
- Use Cloudflare Email Routing catch-all on custom domain → forward to Gmail
- Generate random@yourdomain.com in-process
- No external mail API needed, but can't programmatically poll for verification emails
- Best for: Cloudflare signup (doesn't need email verification before dashboard)

### Temp Mail API (with inbox polling)
- Preferred when the signup flow requires email verification before dashboard/key creation
- Keep this section provider-agnostic; provider-specific quirks belong in `references/`
- Default reusable wrapper pattern:
  - `GET /api/session` → `sessionId`
  - `POST /api/inboxes` with `x-session-id` → inbox address
  - `GET /api/inboxes/{address}/messages` with `x-session-id` → message list
- Poll for verification links or tokens, don’t hardcode provider-specific fields beyond `address`/`messages`

## Workflow

1. **Email setup** — catch-all domain or mail API endpoint
2. **IMAP OTP reader** — poll Gmail for verification codes (for providers that need OTP)
3. **Headless browser** — Camoufox (Firefox anti-detect), Playwright, or nodriver (Chrome)
4. **CAPTCHA solving** — slider (uinput/xdotool), Turnstile (iframe-center click)
5. **Proxy rotation** — round-robin through `proxies.txt` to avoid rate limits
6. **Account registration** — fill form, solve CAPTCHA, submit, extract API key

## bluk-cf (Cloudflare-specific project)

Project at `~/bluk-cf/` — nodriver-based Cloudflare Workers AI account creator.

Core src modules:
- `signup_flow.py` — Turnstile bypass + signup form
- `token_creator.py` — UI-based API token creation
- `token_validator.py` — validates `cfut_*` tokens against Workers AI API
- `turnstile_bypass.py` — nodriver `verify_cf()` for Turnstile solving
- `email_verifier.py` — IMAP-based email verification (catch-all → Gmail)
- `email_catchall.py` — generates random@sefy.my.id addresses

### Signup Flow (working as of latest session)
1. Navigate to `/sign-up`, wait 20s for SPA to load
2. Fill email + password inputs
3. Scroll to make Turnstile visible
4. Call `page.verify_cf()` — solves Turnstile, form remains intact
5. Click submit button
6. Wait for redirect — Cloudflare redirects to `/?to=%2F%3Aaccount%2Fhome` first
7. **Wait up to 30s for account ID (32 hex chars) to appear in URL**
8. If URL doesn't contain account ID, extract from page links or meta tags

### Token Creation Flow
1. Navigate to `/{account_id}/api-tokens`
2. Click "Create a token" button
3. Select "Custom" → "AI & Machine Learning" → search "Workers AI"
4. Tab+Space to check the Workers AI permission checkbox
5. Click "Review token"
6. Click final "Create token" button
7. Extract `cfut_*` token from page body

## Variant: HTTP-Only Registration

Some providers expose a REST API behind their frontend. If the provider doesn't require CAPTCHA during signup and the API can be reverse-engineered from JS bundles, you can skip the browser entirely.

See `references/http-api-registration.md` for the full technique — mapping API endpoints, extract-and-follow verify flow, Supabase auth patterns, full-flow transient-retry wrapper, unattended `--loop` + systemd pattern, and 9router injection.

Reusable assets:
- `scripts/inject_accounts_to_9router.py` — batch-inject existing `accounts.txt` keys into a 9router SQLite DB (skips dups).
- `templates/xyris-farm.service` — systemd unit for unattended continuous farming (`Restart=always`, journald logging).

**Concrete example (CodeCraft):** see `references/codecraft-registration.md`.

**Concrete example (Xyris):**
- Frontend: `api.xyris.site`, Backend: `api.xyris.in`
- Signup: `POST /api/auth/signup` → 201
- Verify: Supabase `verify?token=...` → redirect with `#access_token=` hash
- Login: `POST /api/auth/login` → JWT token + `credits: 15`
- Keys: `POST /api/keys` → `xy-*` API key
- Chat: `POST /v1/chat/completions` (OpenAI-compatible)

## Tech Stack

| Component | Tool |
|-----------|------|
| Browser engine | Camoufox (for Alibaba), nodriver (for Cloudflare), Playwright |
| Headless display | `xvfb-run -a -s "-screen 0 1920x1080x24"` |
| Slider solving | uinput + xdotool (OS-level mouse events) |
| Turnstile bypass | nodriver `mouse_click()` on iframe center |
| OTP reading | IMAP4_SSL → Gmail inbox |
| Email forwarding | Cloudflare Email Routing catch-all |
| Proxy rotation | Round-robin from `proxies.txt` (`host:port:user:pass`) |
| Python | 3.12 for nodriver (3.14 incompatible); 3.14 for Camoufox |

## Common Issues & Fixes

### Cloudflare signup form destroyed after Turnstile
- **Problem**: After `page.verify_cf()` solves Turnstile, the signup form disappears (Forms: 0, Buttons: 0)
- **Cause**: Cloudflare's SPA reloads the page after Turnstile challenge, destroying the form DOM
- **Solution**: Use `page.verify_cf()` which handles the challenge correctly. Do NOT use manual iframe clicking or OpenCV template matching — these don't work with Cloudflare's current anti-bot flow
- **Alternative**: If form is destroyed, reload the page and try again (but this often triggers IP flagging)

### Account ID not in URL immediately after signup redirect
- **Problem**: After form submit, Cloudflare redirects to `/?to=%2F%3Aaccount%2Fhome` but the account ID isn't in the URL yet
- **Solution**: Wait up to 30s for the account ID (32 hex chars) to appear in the URL. If not found in URL, extract from page links or meta tags using JavaScript:
  ```javascript
  const links = Array.from(document.querySelectorAll('a[href*="/"]'));
  for (const link of links) {
    const match = link.href.match(/\/([a-f0-9]{32})\//);
    if (match) return match[1];
  }
  ```

### Browser connection failures in retry loops
- **Problem**: `Failed to connect to browser` error after multiple signup retries
- **Cause**: Chrome process not fully cleaned up between retries, or event loop closed
- **Solution**: Add retry logic with `await asyncio.sleep(2)` between attempts. Use `browser_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-software-rasterizer", "--disable-extensions"]` for stability

### Cloudflare IP flagging after successful signup
- **Problem**: Signup succeeds (form submits, redirects to dashboard) but token creation fails with "email_not_verified" or similar errors
- **Cause**: Cloudflare flags the IP/proxy for suspicious activity after detecting automated signup pattern
- **Symptoms**: Email verification link works, but API token creation returns errors
- **Mitigation**: Use cleaner residential proxies (BrightData Web Unlocker), add longer delays between actions, or rotate to different proxy zones

### Turnstile auto-solve doesn't work
- **Problem**: Waiting for `input[name="cf-turnstile-response"]` to have a value never succeeds
- **Cause**: Cloudflare's Turnstile requires explicit interaction, not just auto-solve
- **Solution**: Use `page.verify_cf()` which triggers the Turnstile challenge flow. Do NOT rely on auto-solve via hidden input polling

### OTP never arrives
- Check catch-all rule is Active + set to "Send to an email" in Cloudflare Email Routing
- Check MX records: `dig MX sefy.my.id +short`
- Alibaba rate-limits verification emails after ~3 accounts from same IP → use proxies

### Slider not solved
- Install xdotool: `pkexec dnf install -y xdotool`
- Playwright mouse API can't bypass Alibaba's canvas-based slider detection
- uinput with OS-level drag is the only reliable method on Linux

### Nodriver Python 3.14 incompatibility
- `nodriver/cdp/network.py` has non-UTF-8 byte → SyntaxError on 3.14
- Fix: use `python3.12 -m venv venv` (or any 3.10-3.13)

### Proxy format
- Standard: `host:port:user:pass`
- Scripts accept either single `--proxy` or list via `proxies.txt`

## Quick Reference

```bash
# Alibaba Cloud (Camoufox)
xvfb-run -a -s "-screen 0 1920x1080x24" python3 farm.py

# Alibaba Cloud (Playwright + tempmail)
xvfb-run -a ./venv/bin/python3 farm_headless.py --auto-captcha

# Cloudflare (nodriver + catch-all)
xvfb-run -a ./venv/bin/python3 main.py --accounts N --delay 120

# Test proxies
curl -s --max-time 8 -x "http://user:pass@host:port" https://cloudflare.com/cdn-cgi/trace
```
