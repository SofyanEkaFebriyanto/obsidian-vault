---
type: project
status: active
last-updated: 2026-10-01
tags: [project, master-list]
---

# Proyek Aktif

| Proyek | Status | Catatan |
|---|---|---|
| Hackintosh N100 | jalan | target Big Sur, external drive |
| kenfa-2.0 | live | test.kenfa.id (Hostinger hPanel) |
| crypto-bot | jalan | Freqtrade futures, Bitget/Hyperliquid, ConfluenceTrend v8 |
| farming suite | jalan | alibaba/bluk/xyris/mekithil/qoder, catch-all sefy.my.id → Gmail IMAP |
| Noir App | jalan (pause) | asisten suara full voice-to-voice; Flutter + Go; APK debug jadi 2026-10-01; butuh Picovoice key + LLM creds; deploy STB pending |

## Infrastruktur pendukung
- **Warp rotator** `~/.9router-warp/` — 50 akun, wireproxy SOCKS5 :51001, 9Router v16+, provider openai-compatible-opencode-free, auto-switch 1x 429 + 60s cooldown.
- **STB H680P** (Armbian aarch64) = source of truth; VPS→9router.sefy.my.id (13.250.28.88). Auto-sync STB→VPS di-STOP.
- **qoder-farm VPS** = 82.153.126.137 (vps1-3); alias 'tokoserver' stale.
- **Proxychains**: `/etc/proxychains-warp.conf` (socks5 127.0.0.1:51001).

Detail masing-masing proyek bikin note sendiri terus link ke sini.
