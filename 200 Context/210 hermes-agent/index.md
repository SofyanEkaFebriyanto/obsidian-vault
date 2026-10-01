---
type: moc
status: active
last-updated: 2026-08-25
tags: [hermes, moc]
---

# Hermes Agent MOC

Hub operasional Hermes di vault ini.

## Ritme operasi
1. **Session Capture (harian)** — rangkum keputusan/progress/blocker dari sesi Hermes ke daily note. Bukan transcript backup. Tanpa outcome → [SILENT].
2. **Weekly Wiki Maintenance** — audit broken wikilink, orphan, duplicate, source drift, stale content, tag taxonomy. Raw source immutable.

## Sistem
- Vault path: `/home/sofyan/Documents/Obsidian Vault` (`OBSIDIAN_VAULT_PATH`)
- Skills: obsidian-second-brain (~/.hermes/skills/obsidian-second-brain/), uv 0.12.5 untuk helper Python
- Sync model: primary lokal → VPS pull (belum dipasang)
- Plugin pixel_observer aktif (~/.hermes/plugins/pixel_observer) — bridge ke Pixel Agents office (fork github.com/aiunlocked1412/hermes-agent-pixel), server standalone `node dist/cli.js --port 3100` dari ~/hermes-agent-pixel/pixel-agents (Node 22). UI: http://127.0.0.1:3100; discovery via ~/.pixel-agents/server.json (port+token). Subagent tampil sebagai teammate. hermes-pixel-office lama (:8113) sudah disabled.
- Pixel Agents server auto-start via user-systemd: `pixel-agents.service` (~/.config/systemd/user/), enabled + linger=yes. Verified active, health :3100 OK.
- Memory→vault auto-sync aktif: shell hook post_tool_call (matcher `^memory$`) → ~/.hermes/agent-hooks/memory-vault-sync.py regenerate [[500 Resources/Hermes Memory Mirror]] tiap tool `memory` dipanggil. Allowlisted, hooks doctor clean.

## Instansi Hermes lain (remote)
- **VPS Lightsail SG 13.212.26.122** (key `~/LightsailDefaultKey-ap-southeast-1.pem`, user ubuntu). Punya 3 profile:
    - default — XAUUSD SMC trading, MEXC crypto-bot, IDX gorengan, sefy.* infra. Memory dump: [[500 Resources/Hermes Memory - VPS 13.212.26.122]]
    - crypto-bot — bot MEXC/Hyperliquid, paper mode, silent L3 auto-exec. Dump: [[500 Resources/Hermes Memory - Profiles (VPS 13.212.26.122)|Profiles dump]]
    - otnay — OTNAY v3.0.0 The Mirror editorial, Paperclip AI 21 agents, Kenfa.id.
- Config history di VPS itu panjang (banyak config.yaml.bak) — hati-hati edit config remote, backup dulu.

## Gotchas
- Terminal heredoc bug: pakai python3 -c satu baris atau printf, bukan heredoc.
- kenfa PHP CLI wajib /opt/alt/php84; no node → build aset lokal lalu rsync.
- Symlink public/storage nyasar ke /var/www/html — relink kalau gambar 404.

## SOP terkait
- (tambahkan saat dibuat)
