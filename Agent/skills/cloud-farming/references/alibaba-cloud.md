# Alibaba Cloud / Model Studio Farming

## Registration Flow
- URL: `https://account.alibabacloud.com/register/intl_register.htm`
- Complex iframe-based registration through `passport.alibabacloud.com`
- Requires password (not OTP-only like QwenCloud)
- After signup, Model Studio activation dialog may appear — must accept "Model Management Service Agreement"

## Key Pitfalls

### 1. Slider CAPTCHA (Baxia/NC slider)
- Playwright's built-in mouse API DOES NOT solve it — OS-level mouse events required
- **Linux**: install xdotool + use uinput virtual mouse
- The slider handle has `id="nc_1_n1z"` or class `btn_slide`
- After xdotool/uinput drag, a JS fallback is often needed for the final solve

### 2. Email Rate Limiting
- Alibaba Cloud blocks verification emails after ~3 registrations from the same IP within minutes
- **Fix**: rotate proxies per attempt + 30-45s cooldown after success
- Email sender: `system-sg@notice.alibabacloud.com` — search IMAP with `FROM "alibaba"`

### 3. Model Activation (`AccessDenied.Unpurchased`)
- New accounts need Model Studio activated + model subscription
- Navigate to Model Studio console → check/click activation button
- Look for "Activate", "Subscribe", "Free", "Try" buttons on dashboard/model cards
- The SPA console hash routes include `#/api-key`, `#/efm/model_experience_center/text`

### 4. Session Loss
- Registration session carries to Model Studio via cookies — no login needed
- If session is lost, script attempts login with the just-registered credentials
- Use `no_viewport=True` in Camoufox to avoid detection

### 5. farm_headless.py Gotchas
- Auto-slider solver is COMMENTED OUT by default (lines 1241-1243) — uncomment before use
- Pass `--auto-captcha` flag to enable slider solving
- `--browser camoufox` for best anti-detection (Camoufox handles fingerprints)
- On Linux, `taskkill` at script exit will fail — needs `platform.system()` check
