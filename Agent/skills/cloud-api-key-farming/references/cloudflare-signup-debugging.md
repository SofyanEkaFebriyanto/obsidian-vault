# Cloudflare Signup Debugging Notes

## Session: 2025-01-XX — bluk-cf signup flow debugging

### Problem: Form destroyed after Turnstile
After `page.verify_cf()` solved Turnstile, the signup form disappeared:
```
[DEBUG] Forms: 0
[DEBUG] Buttons: []
[DEBUG] Turnstile inputs: []
```

**Root cause**: Cloudflare's SPA reloads/replaces the DOM after Turnstile challenge completes. The form is destroyed before the redirect happens.

**Failed approaches**:
1. Manual iframe clicking / OpenCV template matching — doesn't work with current Cloudflare anti-bot
2. Polling for `input[name="cf-turnstile-response"]` auto-solve — never succeeds, Turnstile requires explicit interaction
3. Reloading page after form destruction — triggers IP flagging

**Working solution**: Use `page.verify_cf()` which handles the challenge flow correctly. After it returns, the form may be in a transitional state — wait 5s, then check if form still exists. If form exists, click submit. If form is gone, the signup was rejected server-side.

### Problem: Account ID not in URL after redirect
After successful signup, Cloudflare redirects to `https://dash.cloudflare.com/?to=%2F%3Aaccount%2Fhome` — the account ID is NOT in the URL yet.

**Solution**: Wait up to 30s for the account ID to appear. Extract from:
1. URL path (32 hex chars): `re.search(r"/([a-f0-9]{32})", url)`
2. Page links: `document.querySelectorAll('a[href*="/"]')` → match `/([a-f0-9]{32})/`
3. Meta tags: `document.querySelector('meta[name="account-id"]')`

### Problem: Browser connection failures in retry loops
```
Exception: Failed to connect to browser
One of the causes could be when you are running as root.
In that case you need to pass no_sandbox=True
```

**Solution**: Add retry logic with sleep between attempts:
```python
for attempt in range(3):
    try:
        browser = await uc.start(
            headless=headless,
            lang="en-US",
            proxy=proxy,
            sandbox=False,
            browser_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
            ],
        )
        break
    except Exception as e:
        if attempt < 2:
            await asyncio.sleep(2)
        else:
            raise
```

### Problem: IP flagging after successful signup
Signup succeeds (form submits, redirects to dashboard, email verification works), but token creation fails with "email_not_verified" or similar errors.

**Symptoms**:
- Account ID extracted successfully
- Email verification link clicked successfully
- Token creation fails with `email_not_verified` even though email was verified

**Cause**: Cloudflare flags the IP/proxy for suspicious activity after detecting automated signup pattern. The session is tainted.

**Mitigation**:
- Use cleaner residential proxies (BrightData Web Unlocker zone)
- Add longer delays between actions (5-10s instead of 1-2s)
- Rotate to different proxy zones/countries
- Use `--proxy http://user:pass@host:port` format for BrightData

### BrightData Proxy Zones
- `residential_proxy1` — standard residential IPs, may be flagged for signup
- `web_unlocker1` — cleaner IPs, better for signup, handles anti-bot challenges
- Format: `http://brd-customer-<id>-zone-<zone>:<password>@brd.superproxy.io:33335`

### Token Creation UI Flow
The token creation UI flow is fragile — button labels change between Cloudflare versions:
1. Navigate to `/{account_id}/api-tokens`
2. Click "Create a token" (or "Create Token" or "Create token")
3. Select "Custom" → "AI & Machine Learning"
4. Search "Workers AI" in permission search box
5. Tab+Space to check the Workers AI permission checkbox
6. Click "Review token" (or "Continue to summary" or "Review" or "Continue")
7. Click final "Create token" (or "Create Token" or "Create")
8. Extract `cfut_*` token from page body

**Debugging**: After each click, log visible buttons to see what's available:
```python
buttons = await page.evaluate("""
    (() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return JSON.stringify(buttons.map(b => ({
            text: b.textContent.trim().substring(0, 50),
            disabled: b.disabled,
            visible: b.offsetParent !== null
        })).filter(b => b.visible && b.text.length > 0));
    })()
""")
```
