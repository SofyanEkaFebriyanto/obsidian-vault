---
name: cloud-account-farming  
description: Bulk-register accounts and harvest free API keys from cloud AI providers (Alibaba Cloud, Cloudflare, etc.) using browser automation.
tags:
  - alibaba-cloud
  - cloudflare
  - automation
  - playwright
  - nodriver
  - camoufox
  - captcha
  - proxy-rotation
  - imap-otp
---

# Cloud Account Farming — API Key Harvest Automation

Patterns for automated account registration + API key extraction across AI cloud providers.

## Providers Covered

| Provider | Free Quota Per Account | Automation Stack | Catch-All Domain? | CAPTCHA Type |
|----------|----------------------|-----------------|-------------------|--------------|
| **Alibaba Cloud Model Studio** | 1M tokens/model | Camoufox or Playwright | Yes (via catch-all or gmail dot trick) | Alibaba Baxia slider |
| **Cloudflare Workers AI** | Variable | nodriver | Yes (via catch-all) | Turnstile checkbox |

## Email Strategies (for OTP)

### Option A: Catch-All Domain + Cloudflare Email Routing
1. Own a domain (e.g. `sefy.my.id`) pointed at Cloudflare nameservers
2. Add MX records to Cloudflare Email Routing (`route1/2/3.mx.cloudflare.net`)
3. Create a **Catch-All** rule: `*@domain → your-gmail@gmail.com`
4. In the farm script: generate `randomstring@domain` — all emails forward to Gmail
5. Read OTP via IMAP from Gmail (App Password, not regular password)

### Option B: Gmail Dot Trick
- Use `you+randomalias@gmail.com` — Gmail ignores `+alias`
- All emails land in the same inbox
- **No custom domain needed** — simpler than catch-all
- Example: `intunericetern+abc123@gmail.com`

### Option C: Temp Mail (tempmail.plus)
- No config needed, uses disposable email addresses
- Works for initial testing, unreliable for mass farming
- Alibaba Cloud OTP works with tempmail.plus

## IMAP OTP Reading

```python
import imaplib, email

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login(gmail_user, app_password)
mail.select("INBOX")
_, data = mail.search(None, '(FROM "alibaba")')  # or 'cloudflare'
for mid in data[0].split()[-10:]:
    _, msg_data = mail.fetch(mid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    if target_email in msg["To"]:
        # extract 6-digit OTP from body
```

**Requirements**: Gmail account with 2FA enabled → App Password (16 chars, format: `abcd efgh ijkl mnop`).

## Proxy Rotation

Use multiple proxies round-robin to avoid per-IP rate limits:

### Format
One proxy per line in `proxies.txt`:
```
host:port:user:pass
```

### Code Pattern
```python
proxies = [l.strip() for l in open("proxies.txt") if l.strip() and not l.startswith("#")]
proxy = proxies[idx % len(proxies)]; idx += 1
```

### Proxy URL Format for nodriver/Playwright
```
http://user:pass@host:port
```

Datacenter proxies work but get rate-limited faster. Residential proxies recommended for 1000+ accounts.

## CAPTCHA Solving

### Alibaba Baxia Slider
- **Best**: `xdotool` + `uinput` — OS-level mouse drag (Linux, requires `sudo dnf install xdotool`)
- **Fallback**: `humanly_drag_playwright()` — Playwright built-in mouse API (less reliable)
- Alibaba slider uses a canvas that detects automation — JS dispatchMouseEvent won't work
- uinput creates a virtual mouse device that bypasses detection

### Cloudflare Turnstile
- **Approach**: Click center of embedded Turnstile iframe with OS-level mouse click
- Turnstile runs in a cross-origin sandboxed iframe — CDP click events blocked
- nodriver's `page.mouse_click()` sends OS-level events, bypassing sandbox
- Poll for `cf-turnstile-response` hidden input after clicking

### Turnstile Code Pattern
```python
iframe = await page.select("iframe[src*='challenges.cloudflare.com']")
rect = await iframe.evaluate("this.getBoundingClientRect()")
await page.mouse_click(rect.x + rect.w//2, rect.y + rect.h//2)
```

## Browser Engine Selection

| Engine | Best For | Notes |
|--------|----------|-------|
| **Camoufox** (Firefox) | Alibaba Cloud registration | Best anti-detection, built-in fingerprint spoofing, geoip |
| **nodriver** (Chrome) | Cloudflare signup | Undetected Chrome, better for Turnstile bypass |
| **Playwright** (Chrome/Firefox) | General automation | Familiar API, playwright-stealth for anti-detection |

**Python version note**: nodriver has a non-UTF-8 encoding issue with Python 3.14+. Use Python 3.12 for nodriver-based automation.

## File Structure (Modular Approach)

```
project/
├── main.py                    # Orchestrator (count, proxy rotation, results)
├── config.json                # Config (delay, token name, headless flag)
├── proxies.txt                # Proxy list (one per line)
├── src/
│   ├── email_catchall.py      # Catch-all email generator + IMAP OTP reader
│   ├── signup_flow.py         # Provider registration flow
│   ├── token_creator.py       # API key/token creation
│   ├── token_validator.py     # Token validation
│   └── turnstile_bypass.py    # Cloudflare Turnstile CAPTCHA solving
```

## Cooldown Between Accounts

Avoid rate limiting with escalating delays:

```python
# After success: 30-45s
cooldown = 30 + random.randint(0, 15)

# After failure: increasing 15s, 20s, 25s...
cooldown = 15 + fail_count * 5

# Bulk farming: 2-5 min between accounts
delay_between_accounts = 120  # seconds
```

## Qoder Farm (Qwen/Alibaba agent — PAT harvest + Pro Trial)

Qoder (Alibaba Qwen coding agent) farming — CLI install, Pro-Trial claim, full SSO pipeline.
See `references/qoder-farm.md` for the complete recipe, gotchas (`sudo &&` precedence,
harmless tar xattr warnings, full-64-char PAT requirement), and the standalone
`qodercli-wake` vs Python-farm-scripts distinction.

## Jango AI Farm (jango-bulk — Go)

Jango AI (jangoai.chat) bulk accounts via the `jango-bulk` Go tool: mail.tm inbox →
Firebase-auth signup → email verify → session/credit capture → 9Router bridge.
API auth flow, the Turnstile blocker, mail.tm shape/rate-limit gotchas, and test
seams in `references/jango-bulk-farm.md`.

## Pitfalls

- **Gmail App Passwords expire** — regenerate if IMAP auth fails
- **Cloudflare catch-all created but emails don't arrive** — set action to "Send to an email" not "Drop"
- **Alibaba Cloud rate-limits after 3 email OTPs per IP** — rotate proxies after every 2-3 accounts
- **nodriver + Python 3.14** — SyntaxError in network.py; use Python 3.12
- **Camoufox proxy warning** — LeakWarning when proxy without geoip=True; add `geoip=True`
- **Auto-slider often commented out** — devs disable it for testing; check `handle_captcha()` for commented code
