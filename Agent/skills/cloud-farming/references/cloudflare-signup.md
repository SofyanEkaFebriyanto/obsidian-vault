# Cloudflare Workers AI Signup (bluk-cf)

## Overview
Creates Cloudflare accounts with Account API Tokens scoped to Workers AI.
Turnstile CAPTCHA is the main obstacle — solved via OpenCV template matching + OS-level clicks.

## Two Architectural Approaches

### 1. Catch-all (simple, with IMAP verification) ⬅ preferred

**Updated for Cloudflare's current enforcement**: Cloudflare now **blocks token creation** on fresh accounts with `email_not_verified` error (both UI and API paths). The catch-all flow must include an IMAP-based email verification step.

- Email: `random@customdomain` via Cloudflare Email Routing catch-all → Gmail  
- Verification: IMAP polls Gmail inbox for Cloudflare email, extracts `dash.cloudflare.com/verify?token=...` link, opens it in browser  
- Flow: **generate email → signup → verify email (IMAP) → create token → validate**  
- Code: `~/bluk-cf/src/email_catchall.py` + `email_verifier.py` (IMAP variant)  
- Project: `~/bluk-cf/` (simplified `main.py`)  

### 2. External Temp Mail API (with polling verification)

- Email: created via HTTP API that returns `{address, jwt}`  
- Can poll inbox for Cloudflare verification email before token creation  
- Flow: **generate email → signup → verify email (poll inbox) → create token → validate**  
- Code: `~/bluk-cf/src/email_generator.py` + `email_verifier.py` (API polling variant)  
- Includes live dashboard (`live_dashboard.py`) and concurrent workers

## Temp Mail API Contract

When using the mail API approach, the endpoint must implement:

```
POST /new_address
  Body: {"domain": "example.com"}
  Response: {"address": "user@example.com", "jwt": "eyJ..."}
  Note: jwt is used for inbox auth

GET /parsed_mails?limit=20&offset=0
  Headers: Authorization: Bearer <jwt>
  Response: list of email objects

GET /parsed_mail/{id}
  Headers: Authorization: Bearer <jwt>
  Response: full email with text/html body fields
```

The `base` URL is derived by stripping `/new_address` from `mail_api` config value.

## Email Verification Flow (mail API variant)
1. Create email → get JWT
2. Start polling `GET /parsed_mails` with JWT Bearer auth
3. For each email, check if text/html contains "Cloudflare" + "verify"/"confirm"/"activate"
4. Extract verification link matching `https://dash.cloudflare.com/...` patterns
5. Open link in browser session
6. Check for "verified"/"success"/"email has been verified" in page body
7. If verified → proceed to token creation; fallback to UI token creation if API fails

## Flow (catch-all variant — bluk-cf)
1. Generate `random@sefy.my.id` via `email_catchall.py`
2. Navigate to `https://dash.cloudflare.com/sign-up`
3. Fill email + password
4. Solve Turnstile (cross-origin sandboxed iframe)
5. Submit form → wait for redirect → extract Account ID from URL (`/[a-f0-9]{32}`)
6. **Verify email via IMAP** — polls Gmail for Cloudflare verification email, extracts `dash.cloudflare.com/verify?token=...` link, opens it in browser, confirms "verified"/"success" page (180s timeout, 10s poll interval)
7. Navigate to `/{account_id}/api-tokens/create`
8. Select "AI & Machine Learning" → Workers AI (Read + Edit)
9. Click "Review token" → "Create Token"
10. Extract `cfut_*` token
11. Validate against Workers AI REST API

## Flow (temp mail API variant)
1. Create email via POST to mail API → get `{address, jwt}`
2. Signup with that email
3. Poll `/parsed_mails` with JWT until Cloudflare verification email arrives
4. Extract verification link, open in browser, confirm verified
5. Create API token (API-first with UI fallback)
6. Validate token

## Turnstile Bypass Technique
- **nodriver** (undetected Chrome) with `mouse_click()` — OS-level mouse event
- **Simplified approach** (no OpenCV needed): find Turnstile iframe, get its bounding box via `page.evaluate()`, then click center of iframe
- Poll for `cf-turnstile-response` hidden input value
- Cross-origin sandboxed iframe blocks CDP events — OS-level click is the only way
- If iframe disappears after click, try clicking submit button to trigger token generation

## Email Verification (IMAP-based for Catch-all)

When using catch-all domain with Cloudflare Email Routing → Gmail, Cloudflare's verification email lands in the Gmail inbox. The IMAP verifier polls for it:

```python
from src.email_verifier import verify_cloudflare_email

result = await verify_cloudflare_email(
    page,                      # nodriver Tab (opens verification link in this session)
    target_email=email,         # e.g. "x8k2m9a@sefy.my.id"
    timeout=180,                # max seconds to poll
    poll_interval=10,           # seconds between polls
)
```

**How it works:**
1. Connects to Gmail via `imaplib.IMAP4_SSL` (credentials from `.env`: `IMAP_USER`, `IMAP_PASS`, `IMAP_HOST`, `IMAP_PORT`)
2. Searches inbox for `(FROM "cloudflare")` — focuses on unread Cloudflare emails
3. Filters by `To:` header matching the target email address
4. Extracts verification link matching `https://dash.cloudflare.com/...` with verification keywords
5. Opens link in the existing browser session
6. **Solves Turnstile if present** — Cloudflare now shows Turnstile on the verification page itself
7. Checks for "verified"/"success"/"email has been verified" in response body

**CRITICAL PITFALL**: Cloudflare's email verification page now shows a **Turnstile challenge**. The verifier must detect and solve this Turnstile before checking verification status. Without this step, the verification link opens but the email remains unverified, causing `email_not_verified` errors during token creation.

```python
# After opening verification link:
turnstile_present = await is_turnstile_present(page)
if turnstile_present:
    await verify_cf(page, timeout=60)  # Solve Turnstile
    await asyncio.sleep(5)
```

**.env auto-loading in main.py:**
```python
# At the top of main.py, before any other imports
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())
```

**Required .env variables:**
```
IMAP_USER=intunericetern@gmail.com
IMAP_PASS=<Gmail App Password with spaces>
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
```

**Pitfall:** Cloudflare now rejects token creation with `email_not_verified` on fresh accounts — the IMAP step is **mandatory** for the catch-all approach. Without it, both UI and API token creation fail with `email_not_verified`.

## Email Strategy
- **Catch-all domain** (`random@sefy.my.id`): no temp mail API needed, email arrives in Gmail via Cloudflare Email Routing. Must pair with IMAP verifier for Cloudflare's required email verification step.
- **Mail API**: self-hosted or third-party temp mail service that returns `{address, jwt}`. The `email_verifier.py` API-polling variant polls `/parsed_mails` with JWT auth.
- Cloudflare now enforces email verification before token creation — the verify step is **not optional** regardless of email strategy.

## Proxy Rotation
- Pass `--proxy-list proxies.txt` to rotate proxies per account
- On rate limit error, switch proxy mid-retry
- Format: `host:port:user:pass` per line (parsed to `http://user:pass@host:port`)
- Round-robin across attempts
- Proxies are picked fresh for each `uc.start()` call (nodriver needs new browser for new proxy)
- Also reads from `../alibaba-cloud-farm/proxies.txt` as fallback

## bluk-cf Project Structure
```
~/bluk-cf/
├── main.py              # Orchestrator (catch-all or mail API variant)
├── config.json          # Proxy, delay, token_name, etc.
├── proxies.txt          # host:port:user:pass per line
├── .env → .../.env      # IMAP credentials (for catch-all OTP fallback)
├── src/
│   ├── email_catchall.py     # (catch-all variant) generates random@sefy.my.id
│   ├── email_generator.py    # (mail API variant) HTTP client for temp mail API
│   ├── email_verifier.py     # (mail API variant) polls inbox for CF verification link
│   ├── signup_flow.py        # Core signup logic + Turnstile bypass
│   ├── token_creator.py      # API token creation (UI flow)
│   ├── token_validator.py    # Token validation against Workers AI API
│   ├── turnstile_bypass.py   # OpenCV + nodriver Turnstile solver
│   ├── utils.py             # Password gen, config loading, result saving
│   ├── live_dashboard.py     # (mail API variant) Rich live TUI
│   └── __init__.py
├── scripts/             # batch_runner.sh, add_to_9router.py, etc.
└── docs/                # ARCHITECTURE.md, RATE_LIMITS.md, WAF_BYPASS.md
```

## Important
- **nodriver is incompatible with Python 3.14** (non-UTF-8 bytes in cdp/network.py). Use Python 3.12.
- Cloudflare now **requires email verification** before creating API tokens on fresh accounts. Both UI and API paths return `email_not_verified` if skipped. The catch-all approach must include the IMAP-based verification step.
- When using catch-all domain, the `.env` file must be loaded before running — either via the auto-loader in `main.py` or by sourcing manually.
- Rate limiting: Cloudflare may return "unable to process" — wait 5+ min and retry with different proxy
- `create_token_api()` (direct dashboard API) may fail for fresh accounts — `create_token()` (UI flow then API fallback) handles both paths
- `sandbox=False` required in `uc.start()` when running as root in VPS/Xvfb
- Gmail App Passwords include spaces (e.g. `"abcd efgh ijkl mnop"`) — the `.env` parser handles them as-is
