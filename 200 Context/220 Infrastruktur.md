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
| STB H680P (Ubuntu 26.04 aarch64, 4c/1.7GB) | Proxy host 24/7; source of truth konfigurasi; noir-brain :8080 |

## Inventaris STB (audit 2026-10-02 via SSH)
- **OS**: Ubuntu 26.04 (Resolute Raccoon), kernel 6.18.22-ophub, aarch64. Uptime 3 hari, load rendah.
- **Spek**: 4 core ARMv8, RAM 1.7 GB (terpakai ~1 GB), disk 6.5 GB.
- **Optimasi disk 2026-10-02 ~23:50** (atas permintaan Sofyan, tanpa sentuh 9router/tunneling): apt clean + npm cache + go build cache → **72% → 65% (bebas ~500 MB, sisa 2.3 GB)**. Docker prune: 0B. Tidak disentuh: `.opencode` (244 MB, instalasi tool — tanya dulu), data user, noir-brain.
- **Sistem**: CasaOS (app management + gateway). User: root + sofyan.
- **Docker (6 kontainer)**: qbittorrent, jellyfin, jellyseerr, syncthing, pihole, uptimekuma — stack media + DNS adblock + monitoring.
- **noir-brain**: service systemd aktif, `:8080`, binary+data di `/opt/noir-brain` (17 MB), repo di `/root/noir-app`.
- **9router + tunneling SEHAT** ( diverifikasi, tidak disentuh): wireproxy `:51001` listen, proses 9router/rotator.py/cloudflared/wireproxy jalan, tailscale online (100.84.6.21), cloudflared tunnel `9router-stb.yml` jalan.
- **Port penting**: 80 (casaos), 53 (pihole DNS), 139/445 (samba), 8080 (noir-brain), 22000/8384 (syncthing), 51001 (warp SOCKS5 rotator).
- **Lainnya**: rclone.service jalan, Go toolchain di `/root/go`, node22 di `/opt`.
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
