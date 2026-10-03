---
type: project
status: active
last-updated: 2026-08-25
ai-first: true
tags: [farming, automation]
---

## For future agent
Farming suite = kumpulan proyek farming akun/API key. Detail dari agent memory (confidence high). Tanpa secret di notes — token disimpan di env/config masing-masing repo.

# Farming Suite

| Proyek | Teknologi | Catatan |
|---|---|---|
| alibaba-cloud-farm | — | ~/Documents/project/ |
| bluk-cf | nodriver | ~/Documents/project/ |
| xyris-farm | HTTP | ~/Documents/project/ |
| mekithil | Playwright + 2Captcha | ~/Documents/project/ |
| qoder-farm | Qoder PAT farm | github fazulfi/qoder-farm; qodercli-wake @ /usr/local/bin v1.1.8, PAT via QODER_PERSONAL_ACCESS_TOKEN |
| freeai-farmer | Bright Data sticky proxies | **TUNTAS 2026-10-03**: 750 akun dari 762 proxy (~98%). Script `/home/sofyan/freeai_farmer_stb.py`, output `/home/sofyan/out/freeai_accounts.jsonl`, 751 koneksi di 9Router |

## Infrastruktur
- Email: catch-all sefy.my.id → Cloudflare email routing → Gmail IMAP.
- Proxy: Warp rotator `~/.9router-warp/` (50 akun, wireproxy SOCKS5 :51001), proxychains config `/etc/proxychains-warp.conf`.
- VPS: qoder-farm di 82.153.126.137 (vps1-3); alias 'tokoserver' stale (.133) — konek .137 langsung.

Terkait: [[100 Projects/Proyek Aktif]]
