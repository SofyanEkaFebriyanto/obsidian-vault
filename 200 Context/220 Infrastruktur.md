---
type: moc
status: active
last-updated: 2026-08-25
ai-first: true
tags: [infrastruktur, index]
---

## For future agent
Peta infrastruktur jaringan/server yang dipakai lintas proyek. Dari agent memory (confidence high). Tanpa secret.

# Infrastruktur

## Perangkat & server
| Node | Role |
|---|---|
| STB H680P (Armbian aarch64) | Proxy host 24/7; source of truth konfigurasi |
| VPS SG 13.250.28.88 (ubuntu) | Main VPS; melayani 9router.sefy.my.id; Paperclip AI (:3100) |
| VPS Lightsail SG 13.212.26.122 (ubuntu) | Hermes Agent kedua (default/crypto-bot/otnay); key LightsailDefaultKey-ap-southeast-1 |
| UpCloud 213.163.205.4 | upcload-sofyan, 12c/24GB; FinceptTerminal |
| VPS 82.153.126.137 | qoder-farm (vps1-3) |
| Laptop Fedora | Primary Hermes + vault + farming suite |

## Jaringan & proxy
- Warp rotator: `~/.9router-warp/` — 50 akun, wireproxy SOCKS5 port 51001, 9Router v16+, provider openai-compatible-opencode-free, auto-switch 1x 429 + cooldown 60s.
- Di VPS 13.212.26.122 juga ada WARP bridge: wireproxy :51001 → privoxy :51003 (HTTP).
- Proxychains config: `/etc/proxychains-warp.conf`.
- BrightData proxy: brd.superproxy.io:33335 (di VPS 13.212.26.122).
- Akses permanen: Cloudflare named tunnels (preferensi atas quick-tunnel).
- DNS/email: Cloudflare — sefy.my.id catch-all → Gmail IMAP. Email transactional via Resend HTTP API (SMTP port diblokir beberapa VPS).
- Domains aktif: sefy.my.id & sefy.web.id.

## Konvensi ops
- User-systemd + linger, bukan system service.
- Auto-sync STB→VPS di-STOP (STB = source of truth).
- Multi-step setup via SCP/rsync, hindari heredoc (bug terminal lokal).

Terkait: [[100 Projects/Proyek Aktif]], [[200 Context/210 hermes-agent/index|Hermes Agent MOC]]
