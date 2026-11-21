# HTTP-Only API Registration (No Browser)

Some providers expose a REST API for signup/login/key creation behind their frontend. When the auth flow can be reversed from the web app's JS, you can skip the browser entirely.

## Technique

1. **Map the API surface** by browsing the web app with DevTools or JS bundle inspection:
   - Check `<script src>` files for hardcoded API endpoints
   - Look for `window.API_BASE_URL`, `SERVER_URL`, or similar globals
   - Search bundles for `supabase`, `firebase`, `anon key`, `service_role`
   - Probe known patterns: `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/keys`

2. **Extract the real API base** — the frontend domain is often different from the backend:
   - Frontend proxy may return 404 on API paths (it's just a static SPA)
   - The actual API is often on a different subdomain or TLD
   - Example: frontend `api.xyris.site` → backend `api.xyris.in`
   - **How to find**: check JS bundles for `API_BASE_URL`, `baseURL`, `axios.create({baseURL:...})`
   - **Terminal check**: `curl -s https://api.example.site/js/core.js | grep API_BASE_URL`

3. **Signup flow** — pure HTTP with random fingerprints:
   ```python
   s = requests.Session()
   s.headers.update(generated_fingerprint)  # random User-Agent, sec-ch-ua, etc.
   r = s.post("https://api.backend.in/api/auth/signup",
       json={"name": name, "email": email, "password": password})
   ```

4. **Email verification** — IMAP polling from Gmail catch-all:
   - Provider sends from unique sender (search `FROM "provider"`)
   - Extract verify URL from email body: `re.findall(r'verify\?[^\s"\'<>]+', body)`
   - The verify link often points to a Supabase endpoint, not the provider's domain
   - Follow with `allow_redirects=True` — final URL or redirect Location header carries `#access_token=...` in the hash fragment
   - Parse hash fragment with `urllib.parse.parse_qs`

5. **Login** — credentials-based JWT token retrieval:
   - `POST /api/auth/login` with email + password
   - Returns JWT token + user info + credits balance

6. **API key creation** — authenticated POST:
   - `POST /api/keys` with Bearer token
   - Returns API key string (format varies by provider)

## Key Differences from Browser Farming

| Aspect | Browser (Camoufox/Playwright) | HTTP-Only |
|--------|-------------------------------|-----------|
| Speed | ~60-90s per account | ~10-20s per account |
| Headless req | xvfb-run | None needed |
| CAPTCHA | Turnstile/slider bypass needed | None (CAPTCHA-free providers) |
| Detection | Browser fingerprint + proxy | Minimal (just headers) |
| Reliability | Fragile (DOM changes) | Stable (API contract) |
| Rate limits | Per-IP | Per-IP + per-credential |

## Prerequisites for HTTP-Only Approach

- Provider **must not** require CAPTCHA during signup
- Provider **must not** require email verification before signup (or must use catch-all)
- Auth flow must be extractable from JS bundles
- Verify endpoint must accept GET requests (no CSRF tokens needed)

## Supabase Auth Detection

If the provider uses Supabase for auth, the JS bundles will contain:
- A Supabase `anon` key (starts with `eyJ`) — visible in browser network requests
- The Supabase ref ID in the URL: `seoojdsgndjnnqejdvps.supabase.co`
- Auth endpoints: `/auth/v1/signup`, `/auth/v1/token?grant_type=password`
- Verify links: `supabase.co/auth/v1/verify?token=...&type=signup`

## Provider Status Verification Guard

**Always verify the API is alive before running a batch.** A dead provider burns proxies and clogs email catch-all.

Checklist:
1. Hit the signup endpoint with dummy data — expect a validation error (422) or success (201), never a Vercel 404
   ```python
   r = requests.post("https://api.example.in/api/auth/signup", 
       json={"name":"x","email":"x@x.com","password":"X"}, timeout=10)
   ```
   - Structured JSON response = alive
   - Vercel HTML 404 (`"The page could not be found"`) = dead or wrong base URL
2. Check the landing page for shutdown banners
3. If the frontend loads but all POST paths return 404, the API is on a different domain — find the real base URL

## Frontend/Backend Domain Split Pattern

Common architecture: a Next.js/Vite frontend on one domain proxies API calls to a backend on another domain.

```
Frontend (SPA): https://api.example.site  →  Backend: https://api.example.in
```

**Why this happens:** The frontend is deployed on Vercel/Netlify. API paths return 404 because Vercel only serves the SPA. The real backend is on a different server (could be same subdomain on a different TLD).

**Detection:**
- Browse frontend → click "Register" → check Network tab → the POST goes to a different host
- Extract JS bundles: `curl -s https://api.example.site/js/auth.js` → look for `API_BASE_URL`, `base_url`, `baseURL`
- The frontend's `window.fetch` is monkey-patched to prepend `API_BASE_URL` to API paths

## 9router Auto-Inject

When 9router is enabled, API keys can be injected directly into its SQLite database:

```sql
INSERT INTO providerConnections (id, provider, authType, name, priority, isActive, createdAt, updatedAt, data, email)
VALUES (?, ?, "apikey", ?, 1, 1, ?, ?, ?, NULL)
```

The `data` field contains a JSON blob with apiKey, testStatus, providerSpecificData (baseUrl, nodeName, prefix, etc.).

### Provider Node Registration (required for UI visibility)

After inserting into `providerConnections`, 9router also needs an entry in the `providerNodes` table or the provider **won't appear in the UI** at all:

```sql
INSERT OR REPLACE INTO providerNodes (id, type, name, data, createdAt, updatedAt)
VALUES ('openai-compatible-chat-xyris', 'openai-compatible', 'Xyris-GPT5.5',
        '{"prefix": "xyris", "apiType": "chat", "baseUrl": "https://api.xyris.in/v1"}',
        '2026-07-09T16:06:57.022Z', '2026-07-09T16:06:57.022Z');
```

The `id` must match the `provider` field in `providerConnections`. The `type` should match 9router's expected provider type (e.g. `openai-compatible`). Without this entry, the keys sit in the DB but the provider tab/grid never shows in the dashboard.

### Provider Strategy Registration

After inserting a new provider's API keys, you MUST also register its strategy in the `settings` table, or the rotator won't route through it:

```python
# Get current settings
cur.execute("SELECT data FROM settings WHERE id=1")
s = json.loads(cur.fetchone()[0])

# Add strategy for new provider
s.setdefault("providerStrategies", {})[NEW_PROVIDER_ID] = {
    "fallbackStrategy": "round-robin",
    "stickyRoundRobinLimit": 20
}

# Update
cur.execute("UPDATE settings SET data=? WHERE id=1", (json.dumps(s),))
conn.commit()
```

Without this, the keys sit in the DB but are never used by the rotator.

### Pitfall: ~ expansion in sqliteDb path

Config files often use `"sqliteDb": "~/.9router/db/data.sqlite"`, but `sqlite3.connect()` does NOT expand `~`. Always use `os.path.expanduser()`:

```python
DB_PATH = os.path.expanduser(config.get("sqliteDb", "~/.9router/db/data.sqlite"))
```

Without this, you get: `unable to open database file`.

### CRITICAL Pitfall: per-instance providerId (local vs VPS)

Each 9router install has its OWN provider node IDs. They are NOT portable across machines.

- Local Fedora: `openai-compatible-chat-xyris` (node `Xyris-GPT5.5`)
- AWS VPS: `openai-compatible-chat-a1c162d4-afae-47ac-a6e7-4f392b325b88` (node `Xyris`)

If you sync `config.json` from one machine to another, the inject will write to the wrong provider or fail. ALWAYS read `providerId` from the target instance's own `providerNodes` table / `config.json` — never hardcode or copy it across hosts:

```bash
sqlite3 ~/.9router/db/data.sqlite "SELECT id, name, data FROM providerNodes WHERE data LIKE '%xyris%'"
```

Same for the SQLite DB path (`/home/ubuntu/...` on VPS vs `/home/sofyan/...` locally) — keep `sqliteDb` in config.json absolute per host.

### Pitfall: 9router process must be running for inject to be visible

Inserting rows into `providerConnections` works even if 9router is stopped, but the dashboard/rotator won't pick them up until 9router is (re)started. On the VPS, 9router is NOT a systemd user service by default — start it manually:

```bash
kill $(pgrep -f "9router/cli.js") 2>/dev/null; sleep 1
nohup /usr/bin/node /usr/lib/node_modules/9router/cli.js --tray --skip-update -p 20128 >/tmp/9router.log 2>&1 &
```

Verify in the dashboard (http://localhost:20128, password `${MYSQL_PASS}` for this user) under DNS → Providers.

### Rate-Limit Auto-Retry Pattern (Supabase-backed signup)

Supabase auth rate-limits per source IP. Observed: ~38–51 signups per ~30-min window through 1 Warp IP before `{"error":"email rate limit exceeded"}`. The limit is a time-window throttle, not absolute — after a cooldown the same IP works again.

#### Signup-step retry (basic)

```python
ok, resp = signup(session, name, email, password)
retry = 0
while not ok and retry < 3:
    err = str(resp).lower()
    if "rate limit" in err or "email rate" in err:
        cooldown = 120 * (retry + 1)   # 120s, 240s, 360s backoff
        time.sleep(cooldown)
        session = make_session(proxy_url, gen_fingerprint())  # refresh UA
        ok, resp = signup(session, name, email, password)
        retry += 1
    else:
        break
```

#### FULL-FLOW transient retry (recommended)

Signup-only retry is NOT enough. In practice transient failures (`RemoteDisconnected`, `Connection aborted`, empty verify responses, 5xx) hit at RANDOM steps — verify-email, verify-token, login, profile, create-key. A dropped account at step 5 wastes the whole signup. Wrap EVERY HTTP step with a transient-error detector that rotates the fingerprint + session and backs off:

```python
TRANSIENT_MARKERS = [
    "rate limit", "email rate", "too many requests", "429",
    "remote disconnected", "connection aborted", "connection reset",
    "connection error", "timeout", "timed out", "temporarily",
    "service unavailable", "503", "502", "504", "bad gateway",
    "gateway timeout", "network is unreachable", "broken pipe",
    "remote end closed", "empty response", "failed to establish",
    "connection refused",
]
def is_transient(err):
    return any(m in str(err).lower() for m in TRANSIENT_MARKERS)
def cooldown_for(attempt):
    return min(60 * (2 ** attempt), 360)   # 60,120,240,360(cap)

def run_with_retry(step_name, fn, *args, session_ref, fp_ref, proxy_url):
    last_err = None
    for attempt in range(5):                # MAX_ATTEMPTS
        try:
            ok, resp = fn(*args)
            return ok, resp
        except Exception as e:
            last_err = e
            if is_transient(e):
                cd = cooldown_for(attempt)
                time.sleep(cd)
                # rotate identity + session to dodge per-IP throttle
                fp_ref[0] = gen_fingerprint()
                session_ref[0] = make_session(proxy_url, fp_ref[0])
            else:
                return False, str(e)
    return False, str(last_err)
```

For `wait_verification_email` (returns None, not raise), loop separately: treat empty result as transient, back off 30s→150s, retry up to MAX_ATTEMPTS. Use a `mutable` holder (list) for `fingerprint`+`session` so the wrapper can rotate them across the closure.

Also keep a per-account delay of 30–60s (config `delayMin`/`delayMax`). With 10 rotating BrightData proxies the per-IP budget is larger; with 1 Warp IP keep delays at the higher end.

#### Unattended continuous run (loop until stopped)

User requirement: "don't stop before I stop it" — must survive rate limits AND crashes.

- **Per-account loop**: `try/except Exception` around the whole `create_account()` so any uncaught error just skips one account and continues (never `sys.exit`).
- **Batch loop mode**: accept `--loop [count_per_round]`; run `count` accounts, then a 60–120s cooldown between rounds, forever (`while True`).
- **systemd service** for auto-restart on crash + clean logging. Template: `templates/xyris-farm.service`.
  - `Restart=always` + `RestartSec=10` → crash → auto-restart in 10s.
  - `ExecStart=.../python3 -u ...` (unbuffered) so output hits journald immediately.
  - `StandardOutput=journal` + `StandardError=journal` → view with `journalctl -u xyris-farm -f`.
  - `WantedBy=multi-user.target` + `systemctl enable` → survives reboot.

Commands:
```bash
sudo systemctl start xyris-farm      # begin
systemctl is-active xyris-farm       # health check
journalctl -u xyris-farm -f          # live tail
sudo systemctl stop xyris-farm       # halt (the ONLY way to stop)
```
Without systemd: `nohup python3 -u xyris_creator.py --loop 50 > loop.log 2>&1 &`

## Running the Farm on a Remote VPS

The farm can run headless on the AWS Lightsail VPS (13.250.28.88). Prereqs present: Ubuntu 22.04, Python 3.10, wireproxy (Warp SOCKS5 on :51001), 9router DB, project synced to `~/xyris-farm/`.

```bash
ssh -i ~/LightsailDefaultKey-ap-southeast-1.pem ubuntu@13.250.28.88
cd ~/xyris-farm && source venv/bin/activate
python3 xyris_creator.py 50
```

Notes:
- `requests[socks]` must be installed in the VPS venv for Warp SOCKS5 routing: `pip install 'requests[socks]'`
- Config sets `warpProxy.enabled: true` → proxy file in `proxies.txt` is ignored (Warp priority)
- If 9router isn't running on the VPS, inject fails → either start it or run without inject and use the manual batch script below

## Manual Batch Inject (existing accounts → 9router)

When accounts already exist in `accounts.txt` (e.g. from a proxy-mode run before Warp was enabled, or synced from another host) and were never injected, use the batch script instead of re-running the creator. Reusable script: `scripts/inject_accounts_to_9router.py` — reads `config.json` + `accounts.txt` and inserts each `xy-*` key into the target 9router DB, skipping duplicates.
