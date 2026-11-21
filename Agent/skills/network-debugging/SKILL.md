---
name: network-debugging
description: "Systematic network connectivity debugging: DNS hijacking detection, proxy scanning/audit, port/route diagnostics, and connectivity verification on Linux."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [network, dns, proxy, troubleshooting, connectivity, linux]
    related_skills: [systematic-debugging, warp-proxy-rotation]
---

# Network Debugging

## Overview

Systematic approach to network connectivity issues on Linux. Covers DNS resolution problems (including hijacking/interception), proxy infrastructure auditing, port/route diagnostics, and connectivity verification.

## Core Principle: Source-First Diagnostics

Always check the actual system state (listening ports, routing tables, DNS response bytes) before theorizing. Let the OS tell you what's happening.

---

## 1. Proxy Infrastructure Audit

Use when you need to find ALL proxies on a system — SOCKS, HTTP, transparent, proxychains, VPN tunnels.

### Step 1: Environment Variables

```bash
env | grep -i proxy
```

Check: `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `SOCKS_PROXY`

### Step 2: Listening Ports

```bash
# SOCKS ports
ss -tlnp | grep -E ':1080|:5100|:9050'

# HTTP proxies
ss -tlnp | grep -E ':3128|:8080|:8888'

# All listening
ss -tlnp
```

### Step 3: Proxychains Configs

```bash
ls /etc/proxychains*.conf
cat /etc/proxychains.conf         # default (often Tor: socks4 127.0.0.1 9050)
cat /etc/proxychains-warp.conf    # custom variant
```

### Step 4: WireGuard / WireProxy Tunnels

```bash
# WireProxy (Socks5 over WireGuard)
ls ~/.9router-warp/configs/wireproxy.conf
pgrep -a wireproxy

# Warp accounts
ls ~/.9router-warp/accounts/
```

### Step 5: Application Proxy Files

Search farm automation project directories:

```bash
find ~/Documents/project/ -maxdepth 4 -type f \( -name "proxies.txt" -o -name "*.toml" \)
```

### Step 6: XDG / System Proxy Configs

```bash
ls /etc/xdg/autostart/*proxy* 2>/dev/null
```

---

## 2. DNS Hijacking Detection

Use when a site loads on phone (same WiFi) but not on laptop, or DNS returns unexpected private IPs.

### Symptoms
- `curl` / browser times out
- `dig` returns addresses in `10.x.x.x`, `172.x.x.x`, `192.168.x.x` ranges
- `ping` returns "Destination Host Unreachable" to a public domain
- Phone works fine on same WiFi (phones use DNS-over-HTTPS by default)

### Root Cause

Router or ISP intercepts UDP DNS traffic (port 53) and injects forged A records for certain domains. The fake IP often falls in a Docker/bridge/VPN subnet that is unreachable from the host.

### Detection: Compare UDP DNS vs DNS-over-HTTPS

**Quick check:**

```bash
# UDP DNS (local resolver - may be hijacked)
dig +short example.com

# DNS-over-HTTPS (bypasses router)
curl -s "https://cloudflare-dns.com/dns-query?name=example.com&type=A" \
  -H "accept: application/dns-json" | python3 -m json.tool
```

If the IPs differ → DNS hijacking confirmed.

### Why Even `dig @1.1.1.1` Lies

`dig @1.1.1.1 example.com` still uses UDP port 53. If the router intercepts ALL traffic to port 53 (not just to specific resolvers), the response is hijacked regardless of the resolver IP. Only **DNS-over-HTTPS** (port 443, indistinguishable from normal HTTPS) bypasses this.

### Bypass Options

| Method | Command | Requires |
|--------|---------|----------|
| Browser DoH | Firefox: Settings → DNS over HTTPS → Cloudflare | Browser only |
| /etc/hosts | `echo 'REAL_IP domain.com' \| sudo tee -a /etc/hosts` | sudo, real IP |
| systemd-resolved | `resolvectl dns wlan0 1.1.1.1; resolvectl domain wlan0 '~.'` | sudo |
| Router | Disable DNS intercept/hijack in admin panel | Router access |

### Finding the Real IP

```bash
# Cloudflare DOH
curl -s "https://cloudflare-dns.com/dns-query?name=example.com&type=A" \
  -H "accept: application/dns-json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for a in data.get('Answer', []):
    if a['type'] == 1:
        print(a['data'])
"

# Google DOH
curl -s "https://dns.google/resolve?name=example.com&type=A" | python3 -m json.tool
```

### Verify Connectivity via Real IP

```bash
curl -sI --connect-timeout 10 --resolve example.com:443:REAL_IP https://example.com
```

---

## 3. Connectivity & Route Diagnostics

### Default Gateway & Interface

```bash
ip route get 1.1.1.1
```

### Route to a Specific IP

```bash
# Check which interface/route a target uses
ip route get <TARGET_IP>
```

### Check ICMP (ping) vs TCP

`ping` shows routing and firewall issues at layer 3. `curl` tests layer 4-7. Don't assume one implies the other.

```bash
ping -c 3 -W 5 example.com
curl -sI --connect-timeout 10 https://example.com
```

### Check Docker / Container Network Interference

Docker bridge network (`docker0`, `br-*`) uses `172.17.0.0/16` and similar ranges. If a DNS response returns a `172.x.x.x` address, check if it falls in a Docker bridge subnet:

```bash
ip addr show docker0
ip addr show br-* 2>/dev/null
docker network ls
```

### iptables Interference

Check for DNAT rules that might redirect traffic:

```bash
sudo iptables -t nat -L -n -v
sudo iptables -L -n -v
```

---

## 4. Proxy Connectivity Test

```bash
# Test SOCKS5 proxy
curl -sI --connect-timeout 10 --proxy socks5://127.0.0.1:51001 https://httpbin.org/ip

# Test HTTP/HTTPS proxy
curl -sI --connect-timeout 10 --proxy http://proxy:port https://httpbin.org/ip

# Compare direct vs proxied IP
echo "Direct: $(curl -s https://httpbin.org/ip)"
echo "Proxy:  $(curl -s --proxy socks5://127.0.0.1:51001 https://httpbin.org/ip)"
```

---

## Pitfalls

- **`dig @X.X.X.X` still uses UDP**: if the router intercepts all port 53 traffic, changing the resolver IP doesn't help
- **`dig +tcp` can also be intercepted**: some routers do transparent TCP MITM
- **Docker IP conflicts**: a fake DNS IP in `172.17.x.x` or `172.18-21.x.x` ranges may coincidentally match a Docker bridge network, making `Destination Host Unreachable` the result
- **Warp proxy timeouts**: if Warp/Wireproxy fails, `curl --proxy socks5://...` will hang for ~30s per request (use `--connect-timeout 10`)
- **Ping lies**: `ping` may take a different route than `curl` (e.g., bypasses `LD_PRELOAD` hooks like proxychains)
- **Don't assume /etc/hosts survives reboot**: systemd-resolved may override it on systems with `NetworkManager` managing resolv.conf
