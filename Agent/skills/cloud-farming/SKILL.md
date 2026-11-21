---
name: cloud-farming
title: Cloud Account Farming
description: Bulk-register accounts and harvest free API keys across multiple cloud AI providers (Alibaba Cloud, Cloudflare, Qwen, Mistral, SiliconFlow, etc.)
triggers:
  - farm
  - bulk register
  - account creation automation
  - API key harvesting
  - multiple accounts
  - byNara
  - byNara farm / pro trial / PAT claim
  - provider signup recon
  - "no verification email arrived"
  - tempik / self-hosted mail sink
  - laravel blade http-only signup
tags:
  - automation
  - browser
  - CAPTCHA
  - email-verification
  - proxy
---

# Cloud Account Farming

## Overview

Bulk-register accounts across AI/cloud providers that offer free API tokens. Each provider has unique quirks (CAPTCHA type, email requirements, iframe structure).

## General Pipeline

1. **Email** — disposable (tempmail.plus), catch-all domain with IMAP, or Gmail dot trick
2. **Browser** — undetected automation (Camoufox, Playwright+stealth, nodriver)
3. **CAPTCHA** — slider, Turnstile, or press-and-hold; each needs different solver
4. **Registration** — fill form → verify email/OTP → login
5. **Token harvest** — navigate dashboard → create API key → validate
6. **Storage** — save to JSON + CSV with email, password, API key, account ID

**.env auto-loading**: For standalone scripts (not Camoufox/Playwright framework), add a simple `.env` parser at the top of `main.py`:
```python
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())
```
This avoids requiring `python-dotenv` and works with App Passwords containing spaces.

## Key Techniques

### Email Strategies
- **Catch-all domain** (e.g. `sefy.my.id`): set up Cloudflare Email Routing → forward to Gmail → read OTP/verification links via IMAP
- **Gmail dot trick**: `you+randomstring@gmail.com` → all land in same inbox, no custom domain needed
- **tempmail.plus**: 9 free domains, REST API, no registration, works for Alibaba and Cloudflare
- **Self-hosted tempik** (`https://<host>/api/session` → `POST /api/inboxes` → poll `/api/inboxes/{addr}/messages` with the same `x-session-id`): free and own-domain, but see the MX precheck below

### Mail Path Precheck — do this BEFORE writing the farm script

**Self-hosted tempik MX check.** `GET /api/config`'s `mailDomain` is a config value, not proof
of delivery. If the domain's MX is owned by Cloudflare Email Routing, mail goes to the
forwarder and tempik never sees it — inbox creation returns `201` and the inbox stays
permanently empty, which looks identical to a code bug.

```bash
dig +short MX <domain-advertised-by-tempik>
# route1/2/3.mx.cloudflare.net => Cloudflare owns MX => tempik is blind
```

One domain cannot be both a Cloudflare Email Routing forwarder and a tempik sink. Give tempik
its own domain with MX pointed at the tempik host.

**Provider mailer liveness check.** If a provider gates tokens behind email verification,
confirm the provider can actually send mail before investing in a full pipeline: POST its
`/forgot-password` form to an address you KNOW is deliverable (one with inbound history in
your own IMAP) and poll 60–90s. If the reset never arrives, the provider's mailer is dead —
usually an unverified sending domain (no SPF/DKIM). No client-side fix exists; report the
blocker and stop. Do not brute-force a 6-digit OTP — that is unauthorized access, not farming.

See `references/provider-mailer-diagnosis.md` for the full control ladder and the
Laravel/Blade HTTP-only signup mechanics (referral cookies, CSRF, 302-as-success).

### CAPTCHA Solvers
- **Slider (Baxia/NC)**: OS-level mouse events required (Playwright mouse fails). Use xdotool + uinput on Linux, pyautogui on Windows
- **Turnstile**:
  - **nodriver built-in**: `await page.verify_cf()` — simplest approach, works for most cases, no template needed
  - **Fallback**: find Turnstile iframe via `page.select("iframe[src*='challenges.cloudflare.com']")`, get bounding box via `page.evaluate("rect = iframe.getBoundingClientRect()")`, OS-level click center with `page.mouse_click(x, y)`
  - Cross-origin sandboxed iframe blocks CDP events — OS-level click essential
  - Poll for `cf-turnstile-response` hidden input value after clicking to confirm solve
- **Press-and-hold**: similar to slider, requires OS-level mouse hold
- **Server-validated captcha ticket**: some providers (MiniMax/M Code) POST a `ticket` field
  produced by an *invisible* reCAPTCHA Enterprise widget, and the **server** re-validates it.
  Symptom: HTTP 200 with a business error code in the body (`1200063` /
  `人机验证未通过` for MiniMax) instead of a 403. The tell is a `ticket`/`randStr` field in
  the request body plus `enterprise.js?render=<sitekey>` in the network trace. No solver
  key on the box ⇒ no bypass path; report the gate and stop. See
  `references/minimax-signup-recon.md`.

### Endpoint discovery — Next.js consoles hide the API in the bundle
Provider signup/API paths are usually absent from the HTML and assembled in the client
JS as `"".concat(base, "/backend/...")`. Recover them from the webpack runtime's chunk
map rather than guessing paths:

1. `curl -sL <page>` → collect `/_next/static/chunks/*.js`.
2. Read the **webpack runtime** (`webpack-*.js`) for its `chunkId → filename` map — it
   names chunks the HTML never references, including the page chunks that hold the
   endpoint constants.
3. Fetch every chunk **from the host that served the runtime**. A CDN mirror of the same
   build id can 404 for some chunk ids and return an XML `NoSuchKey` body that looks
   like JS unless you sanity-check the payload.
4. `grep -ohE '"(/v1/api|/backend)/[A-Za-z0-9/_.-]+"' chunks/*.js | sort -u` — the path
   literal survives the `concat(base, "...")` form, so a plain grep recovers it.

`scripts/extract_nextjs_endpoints.py` automates steps 1–4 for any URL.

### Proxy Rotation
- Read `host:port:user:pass` from `proxies.txt`
- Round-robin per account attempt
- Switch proxy on retry if rate-limited
- Fresh browser instance per account (Playwright/nodriver can't change proxy mid-session)

### Dead Proxy Fallback: Warp SOCKS5

When all HTTP proxies are dead/expired (BrightData pool exhausted, datacenter proxies stale), fall back to a local **Cloudflare Warp SOCKS5 tunnel**. This is a general pattern for any `requests`-based HTTP farming script:

```python
WARP_CFG = CFG.get("warpProxy", {})
WARP_ENABLED = WARP_CFG.get("enabled", False)
WARP_SOCKS5  = WARP_CFG.get("socks5", "socks5h://127.0.0.1:51001")

def make_session(proxy_url=None, fingerprint=None):
    s = requests.Session()
    if proxy_url:
        s.proxies = {"http": proxy_url, "https": proxy_url}
    elif WARP_ENABLED:
        s.proxies = {"http": WARP_SOCKS5, "https": WARP_SOCKS5}
    if fingerprint:
        s.headers.update(fingerprint)
    s.verify = False
    return s
```

**Key detail — use `socks5h://` not `socks5://`**:
- `socks5h://` resolves DNS through the SOCKS5 proxy (remote DNS, preserves anonymity)
- `socks5://` resolves DNS locally before sending to proxy — leaks DNS
- With `socks5://`, requests raises misleading `Missing dependencies for SOCKS support` even when PySocks 1.7.1 is properly installed
- Install: `pip install requests[socks]`

In `main()`, **Warp should take priority over the proxy file** — if Warp is enabled, skip loading proxies entirely:
```python
if WARP_ENABLED:
    proxies = [None]  # single virtual slot — make_session() handles routing
else:
    proxies = load_proxies(PROXY_FILE)
    if not proxies:
        print("No proxies and Warp not enabled!")
        return
```

### BrightData Proxy Variants
- **Residential** (`zone-residential_proxy1`): rotating residential IPs, better for registration forms
- **Web Unlocker** (`zone-web_unlocker1`): handles Turnstile/anti-bot at proxy level but doesn't bypass server-side signup blocks
- **CA cert**: on port 33335, optional SSL verification cert available at a local path for curl/testing
- **No SSL config needed for nodriver** — Chrome handles HTTPS tunneling automatically; the CA cert is only needed for tools like curl that verify server cert explicitly
- **Proxy URL format**: `http://user:pass@host:port` for nodriver/Playwright

#### Provider Status Verification

**Always verify the provider's API/backend is operational before running automation.** 
A dead or shutdown backend wastes time, burns proxies, and clogs email catch-all queues.

Checklist before every run:
1. Visit the provider's landing page — look for shutdown/rebuild banners or announcements
2. **Hit the signup endpoint** with dummy data — expect structured JSON (422 validation, 201 success). Vercel HTML 404 ≠ dead API — it may mean the API is on a **different domain**
3. **Check for frontend/backend domain split**: if the frontend loads but API paths return 404, the real API base may be in JS bundles. Extract: `curl -s https://frontend.example/js/core.js | grep API_BASE_URL`
4. For Supabase-based providers: verify the supabase ref is reachable
5. Search X/Twitter or the provider's socials for recent "shutdown", "maintenance", or "transition" posts
6. **A landing-page shutdown banner does not necessarily mean the API is dead** — it may apply to the consumer app only. Always test the actual API endpoints independently.

Example: `api.xyris.site` returned Vercel 404 on POST paths, and `xyris.site` had a shutdown banner. But the real API base was `api.xyris.in` which was fully operational. The shutdown only affected the consumer chat app (`xyris.site`), not the developer API (`api.xyris.in` / `xyris.site/register`).

**Check 7 — for Laravel/Blade providers, probe the mail path too.** A clean signup `302` to
`/verify-email` is not a working provider. A free-token page with a dead mailer is the most
common half-alive state on a young provider. Run the `/forgot-password` control test in the
Mail Path Precheck section before building a pipeline.

## Rate Limit Avoidance
- 30-45s cooldown after each success
- Escalating cooldown on failures: `15 + fail_count * 5` seconds
- 2-5 min delay between accounts (configurable)
- Change IP (proxy) when rate-limited

## Tooling

| Tool | Use | Install |
|------|-----|---------|
| Camoufox | Anti-detect browser (Firefox-based) | `pip install camoufox[geoip]` |
| Playwright | Standard browser automation | `pip install playwright` |
| nodriver | Undetected Chrome automation | `pip install nodriver` |
| playwright-stealth | Chrome fingerprint masking | `pip install playwright-stealth` |
| uinput | OS-level mouse (Linux slider) | `pip install python-uinput` + `modprobe uinput` |
| xdotool | X11 mouse automation (Xvfb) | `dnf install xdotool` (Fedora) / `apt install xdotool` (Debian) |
| OpenCV | Image template matching | `pip install opencv-python-headless` |

## Python Version Notes
- **nodriver** has encoding issues with Python 3.14 (non-UTF-8 in cdp/network.py) — use Python 3.12
- Camoufox works with 3.12+ (including 3.14)
- `farm_headless.py` (from ryankaisabu-svg/alibaba-cloud-farm repo) needs Python 3.12 for the same reason

## nodriver API Quirks
- No `element.get_attribute("name")` → use `element.attrs.get("name", "")` (property, not method)
- No `element.evaluate(js)` → use `page.evaluate(js)` with `querySelector` to find the element
- `page.select_all("iframe")` returns list of elements (not None)
- `page.mouse_click(x, y)` works at OS level (bypasses iframe sandbox)
- `page.select(selector, timeout=N)` returns `None` (not raises) on timeout

## Platform-Specific Fixes
- **`taskkill`**: `farm_headless.py` runs `subprocess.run(['taskkill', ...])` at exit — crashes on Linux. Wrap with `if platform.system() == 'Windows':`
- **Auto-slider commented out**: In `farm_headless.py`, `handle_captcha()` has the auto-slider solver (`# if AUTO_CAPTCHA and solve_baxia_slider_dynamic...`) commented out by the developer. Uncomment to enable `--auto-captcha` flag.
- **xdotool**: Needed for reliable slider solving on Linux Xvfb. Install via `dnf install xdotool` (Fedora) or `apt install xdotool` (Debian). Playwright's built-in mouse API is detected by Alibaba's slider.

## Cloudflare Farming Pitfalls

### "Unable to sign up at this time" (server-side block)
Even when Turnstile is solved successfully, Cloudflare may reject the signup at the server level. This is **not** a captcha issue — it's IP/device reputation, email domain scoring, or rate limiting. Neither Web Unlocker nor residential proxies consistently bypass this. No reliable workaround yet — try different proxy pools, clean residential IPs, or manual signup.

### email_not_verified blocks token creation
Cloudflare now **enforces** email verification on fresh accounts before API token creation. Both UI (`/api-tokens/create`) and API (`POST /api/v4/user/tokens`) return `email_not_verified`. The catch-all flow must include an IMAP verification step. See `references/cloudflare-signup.md` for the IMAP-based verifier pattern.

### Turnstile solved but no redirect after signup
If Turnstile passes but the page stays at `/sign-up`, the form submission was accepted but Cloudflare didn't redirect. Increase sleep/wait values:
- Initial page load: `sleep(15)` instead of `sleep(8)`
- Email input timeout: `timeout=30` instead of `timeout=15`
- Post-submit redirect wait: `max_wait=45` instead of `max_wait=30`
- Post-redirect: `sleep(15)` instead of `sleep(10)`
These longer waits accommodate high-latency residential proxies (Singapore/Indonesia routes).

## Reference Files
- `references/brightdata-proxy.md` — BrightData residential and Web Unlocker proxy setup
- `references/alibaba-cloud.md` — Alibaba Cloud / Model Studio specifics
- `references/cloudflare-signup.md` — Cloudflare Workers AI signup with Turnstile bypass
- `references/slider-solving.md` — Baxia/NC slider techniques
- `references/catchall-email-setup.md` — Cloudflare Email Routing + Gmail IMAP OTP
- `references/nodriver-notes.md` — nodriver quirks (evaluate() nesting, never close pages), Python version compatibility
- `references/xyris-http-farming.md` — Xyris HTTP-only account farming (Supabase Auth, no browser, IMAP verify, 9router auto-inject)
- `references/byNara-farm.md` — byNara PAT farming + Pro Trial claim (CLI install, injector vs claim-trial split, `--list-models` false-positive, plan/quota verify)
- `references/provider-mailer-diagnosis.md` — Mailer liveness control ladder (forgot-password control test), self-hosted tempik MX precheck, Laravel/Blade HTTP-only signup mechanics, CodeCraft API status (incomplete)
- `references/provider-farmability-triage.md` — Is this provider farmable at all? 4-step ladder + **browser-confirmed captcha sweep (§5)**. `grep turnstile` produces false positives on every SPA
- `references/cloudflare-routing-imap-readback.md` — Catch-all IMAP gotchas: `To:` header not searchable, "Missing email from" is a loop guard, imaplib quoting on 3.14
- `references/minimax-signup-recon.md` — MiniMax / M Code: full unified-login endpoint map (`/oauth2/login`, captcha-gated `/v1/api/user/login/sms/send`, code `1200063` = reCAPTCHA ticket rejected), the free-credit paths that actually work (pay-as-you-go starter quota, daily `/minimax-cloud/api/v1/signin/claim`), the CLI device-OAuth flow, and the Next.js bundle-extraction technique
- `scripts/provider_signup_recon.py` — batch browser triage of many providers in one Chrome. Run it instead of hand-rolling a probe: `xvfb-run -a ./venv/bin/python scripts/provider_signup_recon.py` (py3.12, needs `nodriver opencv-python-headless`). Read-only, creates no accounts.
- `scripts/extract_nextjs_endpoints.py` — recover a Next.js console's hidden API paths from its client bundles (reads the webpack runtime chunk map, downloads every chunk, greps path literals). Use when a provider's endpoints are not in the HTML: `python3 scripts/extract_nextjs_endpoints.py https://provider.example/console/plan`.
- `templates/provider_signup_driver.py` — Playwright signup driver that captures the whole XHR contract, accepts the Terms consent (custom `<button>`, not a checkbox), polls IMAP for the code, and saves cookies per account. Copy it, set `DOMAIN`/`PROXY`/`LOGIN_URL`, run under `xvfb-run -a`. It stops where the provider's captcha gate stops — the captured contract is the deliverable.

## Reporting discipline for recon work

When a sweep is the deliverable:

- **One line per provider, verdict plus the measured code.** No padding, no "you could try a
  browser automation approach" when the evidence says OAuth-only.
- **Never name a blocker you did not measure.** If a claim came from a grep, label it as
  unconfirmed or go confirm it in a browser. Overstating a blocker wastes the next session
  as surely as missing a real one.
- **When you get a correction, state the correction plainly and early** — what was wrong, what
  the real answer is. Do not bury a retraction under the rest of the report.
- **Distinguish recon from completion.** "Read the signup DOM" and "created an account" are
  different claims. Never let the first imply the second.
- **Name the specific blocker and stop** when a target is closed off. A named blocker plus a
  recommended next target is a complete answer.
