# Catch-All Email Setup + IMAP OTP Reading

## Cloudflare Email Routing (Free)

### Setup
1. Add domain to Cloudflare (MX records automatic)
2. Go to Email → Email Routing
3. Add destination address (your Gmail) → verify via confirmation link
4. Create Catch-All rule: **Send to an email** → your Gmail
5. Default state is **Drop** — must change to **Send to an email**

### Verification
- Check `dig MX yourdomain.com` — should show `route1/2/3.mx.cloudflare.net`
- Send test email to `test@yourdomain.com` → should appear in Gmail within seconds

## Gmail IMAP OTP Reading

### Gmail App Password
```python
# Required: Gmail with 2FA enabled
# Generate at: Google Account → Security → App passwords
# Format: 16 chars with spaces: "abcd efgh ijkl mnop"

IMAP_USER=your@gmail.com
IMAP_PASS=abcd efgh ijkl mnop
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
```

### IMAP Search Strategy
- Search `(FROM "alibaba")` for Alibaba Cloud emails
- Search `(FROM "cloudflare")` for Cloudflare verification — filter further by `To:` header matching target email
- For Cloudflare: extract verification link via `https://dash\.cloudflare\.com/[^\"\'<>\s]+` pattern, then filter links containing "verify"/"confirm"/"activation"/"email"/"token"/"challenge"
- Mark emails as `\\Seen` after processing to avoid re-reading on next poll
- OTP regex: `r'>\s*(\d{6})\s*</span>'` (HTML span) then generic 6-digit fallback

### Gmail Dot Trick (Alternative)
- `you+randomstring@gmail.com` — all deliver to `you@gmail.com`
- Gmail strips `+` suffix for delivery, but Alibaba sees it as unique email
- No custom domain or forwarding setup needed
- Works for QwenCloud (home.qwencloud.com) and some other platforms

## Temp Mail Alternative
- tempmail.plus: 9 domains (`mailto.plus`, `fexpost.com`, `fexbox.org`, etc.)
- REST API at `https://tempmail.plus/api/mails`
- No registration needed — generate address, poll for inbox
- Works for Alibaba Cloud registration (OTP emails arrive)
