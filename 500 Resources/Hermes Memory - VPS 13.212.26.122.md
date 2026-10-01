---
type: resource
status: active
freshness: snapshot
source: Hermes Agent di VPS Lightsail ap-southeast-1 (13.212.26.122)
pulled: 2026-08-25
tags: [hermes, memory, dump]
---

# Hermes Memory — VPS 13.212.26.122

Dump memory dari `~/.hermes/memories/` (MEMORY.md + USER.md) di VPS Lightsail Singapore.

## MEMORY.md

- Zernio MCP @ mcp.zernio.com/mcp (Bearer), 481 tools.
- BrightData proxy brd.superproxy.io:33335.
- Camofox-browser: ~/tradingview-mcp/camofox-browser `npm start` (:9377). persistence OFF di config. WARP bridge: wireproxy :51001 (SOCKS5) → privoxy :51003 (HTTP). Detail: skill camofox-automation.
- Crypto-bot profile: MEXC spot-only (no leverage), paper mode, L3 auto. Settings: equity_start=2.77, per_trade_risk_pct=30, max_position_pct=80, min_notional_usdt=2.0, universe_size=15.
- XAUUSD persona lengkap ada di USER PROFILE store — jangan duplikat di sini.
- XAUUSD SMC: ASLI PF1.75/46.7%/31yr vs Varian N PF1.37/40.6%/60yr (Kaggle 23y). Counter-trend SHORT ok. TV MCP: /tmp/tv_client2.js.
- IDX gorengan: HUNT FALSE-NEGATIVES > ranking. Fix real bugs: triple-buy GDST (idempotency guard), fake-loss (limit-fill vs close).
- XAUUSD ASLI cronjobs (2): NY H1→M5 (bb1c4d561973) + scalp M15→M1 (719789c4ed50), daily 21:05 WIB. User rutin minta cek news USD 21:00 WIB + dampak XAUUSD.
- Gateway QRIS manual, upgrade Tripay/GoBiz nanti. Email: Resend HTTP ACTIVE (VPS block SMTP 465/587, 443 OK) — sefy.web.id belum verify (SPF+DKIM+CNAME bounce). Skill: pterodactyl-game-hosting.
- Exness XAUUSDc: MT server time = GMT+0 (no DST) → WIB +7h. Journal CSV ~/trading_journal/ (strategy momentum_candle, kolom time_gmt0+time_wib, running balance).
- UpCloud 213.163.205.4 (upcload-sofyan, 12c/24GB). FinceptTerminal /usr/bin (xvfb→VNC). Zapi calendar ET (WIB=ET+11).
- AWS native bedrock REMOVED Aug 2026 (bentrok). Custom bedrock-mantle TETAP (key config + AWS_BEARER_TOKEN_BEDROCK .env, qwen3-235b=1M ctx default, deepseek.v3.2/3.1 cadangan). Skills model-ranking-audit & llm-selfhosting punya ref-nya.
- wigolo (web-intel MCP keyless, 10 tools) TERPASANG: Hermes stdio npx -y wigolo (args wajib ['-y','wigolo']) + claude-code + codex.
- TokenHarbor ~/tokenharbor-auto: camofox API client. Server anti-abuse AKTIF — signup dari IP ini direject (banner: couldn't create account, team alerted), bukan cuma rate-limit. Password 16-char alfanumerik. Verify email: Gmail catchall IMAP creds ~/cloudflare-auto-signup/.env. Skill: camofox-automation.
- Poetry reels @catatan.otnay (poem + piano, 25s 4:5, original captions only).
- XAUUSD SMC: transparent tooling (thresholds, not black-box). Sweep→CHoCH→FVG-pullback M5+H1 on Kaggle 20y. Rejects fake stats. PF 1.5-2.0=IDEAL, >2.0 suspect. MaxDD<15-20% + ≥100 trades required. REJECTS SL%>~70% even at high PF ("jelek psikologi") → prefer lower PF + higher WR. Target RR1:2 / WR45-55% / PF1.5-2.0 / 2-3 setups/minggu. Engine: varian N (sl_pct 1.2% + disp ≥1.5ATR + RR1:2 → PF1.93/WR49.9%). NY session mapping: daily 21:05 WIB pure ASLI (OB entry). Output Entry/SL/TP only. ASLI degrades on H1, native M5.
- ASLI OB entry precision: SHORT entry = LOW of OB zone (bottom), LONG entry = HIGH of OB zone (top). NOT midpoint. All prices must be 3 decimal places. User rejected 4089.255 for SHORT entry, wanted 4081.447.
- Domains: sefy.my.id & sefy.web.id. Exploring PartyRock (AWS no-code AI).
- Catatan etika agent: user repeatedly pushed TokenHarbor live account farming (proxy rotation evading anti-abuse) dan invoke godmode untuk override refusals; agent menolak — godmode tidak override pelanggaran ToS.

## USER.md (User Profile)

- Trades XAUUSD (Gold) in WIB; prefers concise bro-style Indo/English, honest stats, structured prompts, real tooling, direct execution with only manual login/auth steps. Likes staged validation: debug visual first, per-phase logs ([1/5], page state, failure reason), fix-rerun until clean.
- Poetry reels @catatan.otnay (poem + piano, 25s 4:5, original captions only).
- XAUUSD SMC: transparent tooling (thresholds, not black-box). Sweep→CHoCH→FVG-pullback M5+H1 on Kaggle 20y. Rejects fake stats. PF 1.5-2.0=IDEAL, >2.0 suspect. MaxDD<15-20% + ≥100 trades required. REJECTS SL%>~70% even at high PF ("jelek psikologi"). Target RR1:2/WR45-55%/PF1.5-2.0/2-3 setups/minggu. Engine: varian N (sl_pct1.2%+disp≥1.5ATR+RR1:2→PF1.93/WR49.9%). NY session mapping: daily 21:05WIB pure ASLI (OB entry). Output Entry/SL/TP only. ASLI degrades on H1, native M5.
- ASLI OB entry precision: SHORT entry = LOW of OB zone, LONG entry = HIGH of OB zone. NOT midpoint. Semua harga 3 desimal.
- Domains: sefy.my.id & sefy.web.id. Exploring PartyRock (AWS no-code AI).
- Riwayat: repeatedly pushed TokenHarbor live account farming + godmode overrides; ditolak agent.

## Related

- [[500 Resources/Hermes Memory - Profiles (VPS 13.212.26.122)|Memory profiles crypto-bot & otnay]]
- [[200 Context/220 Infrastruktur|Infrastruktur]]
