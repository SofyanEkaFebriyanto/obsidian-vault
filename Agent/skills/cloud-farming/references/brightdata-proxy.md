# BrightData Proxy Setup for Cloud Farming

## Proxy Types

### Residential Proxy
```
Username: brd-customer-<CUSTOMER_ID>-zone-residential_proxy1
Password: <PASSWORD>
Host: brd.superproxy.io
Port: 33335
```
- Rotating residential IPs, clean for most registration forms
- Default countries: Singapore, Indonesia (configurable in BrightData zone settings)
- Used for: Cloudflare signup, Alibaba Cloud registration

### Web Unlocker
```
Username: brd-customer-<CUSTOMER_ID>-zone-web_unlocker1
Password: <PASSWORD>
Host: brd.superproxy.io
Port: 33335
```
- Handles Turnstile/anti-bot challenges at proxy level
- Still may not bypass Cloudflare server-side signup blocks ("Unable to sign up at this time")
- Used for: sites with aggressive anti-bot protection

## SSL / CA Certificate

For port 33335, BrightData provides a CA certificate for explicit SSL verification.
Path example: `/home/sofyan/brightdata_proxy_ca/New SSL certifcate - MUST BE USED WITH PORT 33335/`

**Not needed for nodriver** — Chrome handles HTTPS tunneling automatically. The CA cert is only relevant for tools like curl that verify server cert explicitly.

## Proxy URL Format for nodriver/Playwright

```python
# Single proxy via --proxy arg
proxy = "http://brd-customer-<ID>-zone-residential_proxy1:<PASS>@brd.superproxy.io:33335"

# Or from proxies.txt (host:port:user:pass format)
# Lines: brd.superproxy.io:33335:brd-customer-<ID>-zone-residential_proxy1:<PASS>
proxies = [l.strip() for l in open("proxies.txt") if l.strip() and not l.startswith("#")]
# Parsed to: http://user:pass@host:port
import re
for line in proxies:
    parts = line.split(":")
    if len(parts) == 4:
        proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
```

## Verification

```bash
# Test proxy is working
curl -s --max-time 8 -x "http://user:pass@brd.superproxy.io:33335" https://httpbin.org/ip

# With SSL cert verification
curl -s --proxy brd.superproxy.io:33335 --proxy-user user:pass --cacert /path/to/ca.crt "https://geo.brdtest.com/welcome.txt"
```
