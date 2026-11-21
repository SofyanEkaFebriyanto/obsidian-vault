# Xyris — HTTP-Only Account Farming (Supabase Auth)

Xyris uses **Supabase Auth** + custom REST API, so the entire signup→verify→login→key creation flow runs over HTTP without a browser. No Playwright, no Camoufox, no CAPTCHA.

**Architecture**: Frontend at `api.xyris.site` (Next.js SPA). Backend API at `api.xyris.in` (direct, no proxy). The JS bundles embed `window.API_BASE_URL = 'https://api.xyris.in'`. Supabase ref: `seoojdsgndjnnqejdvps`.

## Flow

```
signup (POST /api/auth/signup) → IMAP poll for verify link → 
GET Supabase verify URL (follow redirect) → extract access_token from hash → 
login (POST /api/auth/login) → profile → create API key → 
optional: 9router inject
```

## Key API Details

### Signup
```
POST https://api.xyris.in/api/auth/signup
{"name": "...", "email": "...@sefy.my.id", "password": "..."}
→ 201 {"message": "Signup successful!...", "emailConfirmationRequired": true}
```

### Verify Email
- Supabase sends email from `noreply@xyris.in` with verify link:
  `https://seoojdsgndjnnqejdvps.supabase.co/auth/v1/verify?token=<token>&type=signup&redirect_to=https://api.xyris.site/login`
- Follow the verify link (GET, `allow_redirects=True`) — the final URL has a hash fragment:
  `https://api.xyris.site/login#access_token=eyJhbG...&expires_in=3600&refresh_token=...&token_type=bearer`
- Extract `access_token` from hash fragment via `urllib.parse.parse_qs(fragment)`

**IMPORTANT**: Unlike typical Supabase apps that return a 303 redirect with Location header, Xyris's flow ends at a client-side URL. The `access_token` is in the **URL hash fragment** of the final destination (never sent to the server). You must use `allow_redirects=True` and parse the final `response.url`.

### Login
```
POST https://api.xyris.in/api/auth/login
{"email": "...", "password": "..."}
→ 200 {"token": "eyJhbG...", "role": "user", "credits": 15, "name": "...", "email": "..."}
```

### Profile
```
GET https://api.xyris.in/api/user/profile
Authorization: Bearer <token>
→ {"name": "...", "email": "...", "role": "user", "credits": 15, "createdAt": "..."}
```

### Create API Key
```
POST https://api.xyris.in/api/keys
Authorization: Bearer <token>
{"name": "xyris-key"}
→ 201 {"key": "xy-<32hex>", "name": "xyris-key"}
```
Key format: `xy-` prefix followed by hex string (36-40 chars).

### Chat (OpenAI-compatible)
```
POST https://api.xyris.in/v1/chat/completions
Authorization: Bearer <api-key>
```
Models: `XYRIS-FLASH`, `XYRIS-FLASH-2`, `GPT-5.5`, `CLAUDE-FABLE-5`, `minimax-m3`, `zai-org/GLM-5.2`

## supabaseRef Field

`supabaseRef` in config.json is the Supabase project ref embedded in verify URLs (`seoojdsgndjnnqejdvps`). It's defined but **never used** in the script — the verify endpoint is extracted from the email body, not constructed from config.

## Frontend vs Backend Domain Split

**Critical insight**: `api.xyris.site` is a Next.js SPA that returns Vercel 404 for any non-frontend path. All `/api/auth/`, `/api/user/`, `/api/keys/` requests are proxied by the frontend to `api.xyris.in` at the JS level via Axios/fetch with `baseURL = 'https://api.xyris.in'`.

If you hit `api.xyris.site` directly with API calls you get:
```
404 POST /api/auth/signup → "The page could not be found" (Vercel)
```

Always use `api.xyris.in` for direct API calls.

### How to Discover a Split Domain

1. Browse the frontend page, check `<script src>` for JS bundles
2. Look for `window.API_BASE_URL`, `const API_BASE_URL`, `baseURL`, `baseUrl` in JS
3. Check browser network tab after clicking "Register" — the POST goes to a different domain
4. Example from Xyris: `curl -s https://api.xyris.site/js/core.js | grep API_BASE_URL`

## 9router Auto-Inject

Direct SQLite insert into `~/.9router/db/data.sqlite`:

### Database Schema
```sql
CREATE TABLE providerConnections (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    authType TEXT NOT NULL,
    name TEXT,
    email TEXT,
    priority INTEGER,
    isActive INTEGER DEFAULT 1,
    data TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
);
```

### data JSON Blob
```json
{
    "apiKey": "xy-...",
    "testStatus": "active",
    "backoffLevel": 0,
    "providerSpecificData": {
        "prefix": "xyris",
        "apiType": "chat",
        "baseUrl": "https://api.xyris.in/v1",
        "nodeName": "Xyris-GPT5.5",
        "connectionProxyEnabled": false,
        "connectionProxyUrl": "",
        "connectionNoProxy": ""
    }
}
```

### Insert
```python
cur.execute(
    "INSERT INTO providerConnections (id, provider, authType, name, priority, isActive, createdAt, updatedAt, data, email) VALUES (?,?,?,?,?,?,?,?,?,NULL)",
    (cid, provider_id, "apikey", account_name, 1, 1, now, now, json.dumps(data))
)
```

### Dedup Check
```python
cur.execute(
    "SELECT id FROM providerConnections WHERE provider=? AND json_extract(data,'$.apiKey')=?",
    (provider_id, api_key)
)
```

### Provider Node Registration (required for UI visibility)

After inserting into `providerConnections`, 9router also needs an entry in the `providerNodes` table or the provider **won't appear in the UI** at all:

```sql
CREATE TABLE providerNodes (
    id TEXT PRIMARY KEY,
    type TEXT,
    name TEXT,
    data TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL
);

INSERT OR REPLACE INTO providerNodes (id, type, name, data, createdAt, updatedAt)
VALUES ('openai-compatible-chat-xyris', 'openai-compatible', 'Xyris-GPT5.5',
        '{"prefix": "xyris", "apiType": "chat", "baseUrl": "https://api.xyris.in/v1"}',
        '2026-07-09T16:06:57.022Z', '2026-07-09T16:06:57.022Z');
```

The `id` must match the `provider` field in `providerConnections`. The `type` should match 9router's expected provider type (e.g. `openai-compatible`). Without this entry, the keys sit in the DB but the provider tab/grid never shows in the dashboard.

### Provider Strategy Registration

After adding a new provider to 9router via direct inject, you must also register its strategy in the `settings` table, or the rotator won't know how to route through it:

```python
s = json.loads(cur.execute("SELECT data FROM settings WHERE id=1").fetchone()[0])
s.setdefault("providerStrategies", {})["openai-compatible-chat-xyris"] = {
    "fallbackStrategy": "round-robin",
    "stickyRoundRobinLimit": 20
}
cur.execute("UPDATE settings SET data=? WHERE id=1", (json.dumps(s),))
```

### Pitfall: ~ expansion in sqliteDb path
Config files often store `"sqliteDb": "~/.9router/db/data.sqlite"`, but sqlite3 and Python's `sqlite3.connect()` do NOT expand `~`. Always call `os.path.expanduser()`:

```python
NR_DB = os.path.expanduser(NR_CFG.get("sqliteDb", os.path.expanduser("~/.9router/db/data.sqlite")))
```

Without this, you get: `unable to open database file`.

## Fingerprinting

Use `requests.Session()` with random browser headers per account:

```python
def gen_fingerprint():
    chrome_major = random.randint(120, 149)
    chrome_full = f"{chrome_major}.0.{random.randint(1000,9999)}.{random.randint(10,200)}"
    os_choices = [
        ("Windows NT 10.0; Win64; x64", '"Windows"'),
        ("Macintosh; Intel Mac OS X 10_15_7", '"macOS"'),
        ("X11; Linux x86_64", '"Linux"'),
    ]
    os_str, os_platform = random.choice(os_choices)
    return {
        "User-Agent": f"Mozilla/5.0 ({os_str}) AppleWebKit/537.36 ...",
        "sec-ch-ua": ...,
        "sec-ch-ua-platform": os_platform,
        "Accept-Language": random.choice(["en-US,en;q=0.9", ...]),
        "Origin": "https://api.xyris.site",
        "Referer": "https://api.xyris.site/",
    }
```

## Warp SOCKS5 Proxy Fallback

When all HTTP proxies (BrightData, datacenter) are exhausted or dead, fall back to a local Warp SOCKS5 tunnel:

```python
WARP_SOCKS5 = "socks5h://127.0.0.1:51001"

def make_session(proxy_url=None, fingerprint=None):
    s = requests.Session()
    if proxy_url:
        s.proxies = {"http": proxy_url, "https": proxy_url}
    elif WARP_ENABLED:
        s.proxies = {"http": WARP_SOCKS5, "https": WARP_SOCKS5}
    ...
```

**Use `socks5h://` not `socks5://`** — the `h` variant resolves DNS through the SOCKS5 proxy (remote DNS, no DNS leak). Without `h`, `requests` resolves DNS locally then sends already-resolved IP, which:
- Raises misleading `Missing dependencies for SOCKS support` error even with PySocks installed
- Leaks DNS lookups outside the proxy tunnel

Install: `pip install requests[socks]`

### Config for Warp + No Proxy File
```json
{
    "warpProxy": { "enabled": true, "socks5": "socks5h://127.0.0.1:51001" }
}
```

```python
proxies = load_proxies(PROXY_FILE)
if not proxies and WARP_ENABLED:
    proxies = [None]  # single virtual slot — make_session() handles routing
```

## BrightData Proxy Integration

- 10 rotating proxies from `zone-cf_1` through `zone-cf_10`
- Format: `http://brd-customer-hl_<id>-zone-cf_N:<pass>@brd.superproxy.io:33335`
- Use with `session.proxies = {"http": proxy_url, "https": proxy_url}`

## IMAP Verification (Gmail)

**Do not copy the old `To:`-header filter.** It was a real bug in `xyris_creator.py`, live on
disk, and it made every routed verification silently time out:

```python
# BROKEN — Cloudflare Email Routing is not indexed by the random local-part,
# so this never matches and the caller just backs off and retries forever.
to_header = msg.get("To", "").lower()
if target_lower not in to_header:
    continue
```

Root cause, evidence, and the mailbox-quoting traps are in
`cloudflare-routing-imap-readback.md`. The working shape, now in `xyris_creator.py`:

```python
MAILBOXES = ("INBOX", '"[Gmail]/All Mail"', "[Gmail]/Spam")

def iter_recent_messages(imap, needle, window=25):
    """Yield messages from every mailbox that mention `needle`."""
    for box in MAILBOXES:
        typ, _ = imap.select(box, readonly=True)   # note the quotes inside the string
        if typ != "OK":
            continue
        # TEXT search covers the original recipient kept in the body.
        typ, data = imap.uid("search", None, "TEXT", f'"{needle}"')
        ids = data[0].split() if typ == "OK" and data and data[0] else []
        if not ids:
            typ, data = imap.uid("search", None, "ALL")
            ids = data[0].split()[-window:] if typ == "OK" and data and data[0] else []
        for uid in reversed(ids[-window:]):
            typ, msg_data = imap.uid("fetch", uid, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            yield email.message_from_bytes(msg_data[0][1])

def wait_verification_email(target_email, timeout=120, link_pattern=None,
                            sender_hint=None):
    """Match across To/Cc/Delivered-To/X-Original-To/Return-Path PLUS the body.

    Returns the verification link, or a 4-8 digit OTP when link_pattern is None.
    """
    target_lower = target_email.lower()
    local = target_lower.split("@")[0]
    link_re = re.compile(link_pattern) if link_pattern else None
    # ... loop until deadline:
    #     blob = headers + " " + body  ->  match target_lower OR bare local part
```

Three things that make the difference:

- **Match the bare local part too.** `local` is a much shorter needle than the full address,
  so it survives header rewriting that mangles the domain.
- **Scan three mailboxes.** Routed mail frequently lands in `[Gmail]/All Mail`, never Inbox.
- **Take `link_pattern` and `sender_hint` as parameters.** The same helper serves providers
  that send a link (Xyris/Supabase) and providers that send a 6-digit code. `sender_hint`
  keeps an unrelated message from being mined for the wrong digits.

**Domain**: `sefy.my.id` — Cloudflare Email Routing catch-all → `intunericetern@gmail.com`.

**Regression-test the matcher before trusting it.** A pure-fixture test that proves old-logic
misses and new-logic-hits, plus one live readback, catches this class of bug in seconds:

```python
msg = email.message_from_string(
    "From: no-reply@xyris.site\n"
    "To: intunericetern@gmail.com\n"          # what Cloudflare rewrote it to
    f"Delivered-To: {sentinel}\n"             # where the real address survives
    f"X-Original-To: {sentinel}\n"
    "Subject: Verify your xyris email\n\n"
    "<p>Click <a href='https://api.xyris.in/auth/v1/verify?token=abc123'>here</a></p>\n")
assert sentinel not in str(msg.get("To", "")).lower()   # old logic must MISS
assert sentinel in blob_of(msg)                          # new logic must HIT
```

## Guard: Provider Status Verification

Before every run, verify the API is actually alive:

```python
import requests
r = requests.get("https://api.xyris.in/api/auth/signup", 
    json={"name":"x","email":"x@x.com","password":"X"}, timeout=10)
# Expected: 422 (validation) or 201 — anything structured JSON
# Bad: Vercel 404 with "The page could not be found"
```

A stale/dead provider wastes proxies, clogs email catch-all, and burns time. Always check first.

## Example: `xyris_creator.py` Structure

```python
create_account(proxy_url, idx):
    name, email_user = gen_name()
    email = f"{email_user}@{random.choice(DOMAINS)}"
    password, fingerprint = gen_password(), gen_fingerprint()
    session = make_session(proxy_url, fingerprint)
    
    # 1. Signup
    ok, resp = signup(session, name, email, password)
    
    # 2. Verify email (IMAP → extract Supabase verify URL → follow → access_token)
    verify_url = wait_verification_email(email, timeout=90)
    access_token = verify_and_get_token(session, verify_url)
    
    # 3. Login
    token, _ = login(session, email, password)
    if not token: token = access_token  # fallback
    
    # 4. Profile + credits
    profile = get_profile(session, token)
    
    # 5. API key
    api_key = create_key(session, token)
    
    # 6. 9router (optional)
    inject_to_9router(api_key, account_name)
    
    return f"{email}:{password}:{api_key}:{credits}"
```

## Dependencies
```bash
pip install requests faker
```
No browser engine needed. Runs on any VPS without Xvfb.
