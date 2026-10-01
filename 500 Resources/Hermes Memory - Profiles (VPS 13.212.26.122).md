---
type: resource
status: active
freshness: snapshot
source: Hermes Agent di VPS Lightsail ap-southeast-1 (13.212.26.122) — profiles/
pulled: 2026-08-25
tags: [hermes, memory, dump]
---

# Hermes Memory — Profiles (VPS 13.212.26.122)

Dump memory dari dua profil lain di VPS yang sama: `crypto-bot` dan `otnay`.

## Profile: crypto-bot

### MEMORY.md

- User = Indonesian crypto bot trader. Prefers Indonesian/English mix, bro-style. Uses Telegram.
- crypto-bot: data source = Binance (public API), execution = MEXC (exec_exchange=mexc, needs env MEXC_API_KEY + MEXC_SECRET). $2 balance on MEXC for live testing.
- Entry gating: max_concurrent (3) + daily/weekly loss caps only. max_trades_per_day removed. L3 auto-execution totally silent (no proposal reports in chat, only errors).
- Daily EOD report + journal saved to journal/YYYY-MM-DD.md at 23:55 WIB via cron job crypto-eod-journal. Trade recap queries filter out TG timeout noise.
- MEXC API fee structure: MX-token discounts do NOT apply to API trades. API uses independent fee schedule ~0.1% maker+taker for spot, ~0.02/0.06% futures. Filter signals with TP < 2x round-trip fee.
- No-KYC options (verified 2026-07-13):
    - HYPERLIQUID = DEX perp, no-KYC permanent, ccxt OK if walletAddress set, min deposit $5 USDC (Arbitrum only), min notional $10, fee 0.045% taker, USDC-margined.
    - PHEMEX = CEX no-KYC (API key made, no KYC), official CCXT, 2 BTC/day, ~$1 min.
    - REJECTED/DEAD: Lbank (fetch_positions NotSupported), BloFin (needs passphrase), BingX & CoinEx (KYC), Weex, Bitunix (not in ccxt).
    - FUTURES layer built for HL: lib_ccxt `_spot_to_futures_symbol(perp_quote=USDC)`, set_leverage, live_market_order(reduceOnly), fetch_positions_live; leverage-aware risk cap. PAPER open+close $2+15x BTC VERIFIED. Live needs HYPERLIQUID_API_KEY+SECRET+HL_WALLET_ADDRESS env + agent wallet (trade-only). Settings: exec_exchange=hyperliquid, leverage=15, min_notional_usdt=10, per_trade_risk_pct=3, daily_loss_cap_pct=9, weekly_loss_cap_pct=20.

### USER.md

- Active crypto bot trader using paper mode at ~$10 equity baseline. Bro-style casual Indo/English. Wants frequent updates, daily recaps, journals via Telegram. Silent cron delivery unless proposals/PnL events occur.
- Risk: conservative default, tapi removed max_trades_per_day (no entry cap); prefers loss-based kill-switch (daily 3% / weekly 10%).
- Evaluation-driven workflow: after each session wants trade analysis (entry/exit/R:R/win rate), journal file, actionable improvements. Wants code fixes, not just settings tweaks. Measured changes over rapid tuning.
- Prefers practical action ("langsung modifikasi aja"). Running MEXC futures $2 modal at 5x leverage. Strict risk plan (5%/trade, 20% daily cap, max 1 concurrent position).

## Profile: otnay

### MEMORY.md

- User sends audio/music files to be saved at /home/ubuntu/music/.
- OTNAY v3.0.0 The Mirror, approved 2026-07-07. Filosofi: OTNAY adalah cermin — suara pembaca sendiri (first person "Aku"), bukan teman dari luar. Semua rasa sah. Tidak resolve. Success = "ini tentang aku." Brief structure → skill `otnay-idea`.
- Paperclip AI @ http://13.250.28.88:3100. Company OTNAY Editorial (e97b2072-624f-42d2-be0a-e1a3e72b6971) 21 agents, all on OTNAY v3.0.0. Provider: custom:Local (127.0.0.1:20128), model oc/deepseek-v4-flash-free. Agents auto-disposition ke done.
- Kenfa.id @ /home/ubuntu/kenfa/src: Laravel + Filament + MySQL 8.0 (Docker: app:8080, mysql:3308, phpmyadmin:8888). admin@kenfa.id/password. Midtrans disabled.
- "Gw pengen terima beres aja" — fix sampai benar-benar selesai, jangan setengah-setengah.
- "Daily model" user = 'opencode-free' via custom:9router (http://127.0.0.1:20128/v1). Jangan ganti sendiri.
- OTNAY style: captions baku KBBI (saya/tidak/sudah/ketika/Anda; NO gue/nggak/udah/pas/kayak/emang/tau/doang), puisi body 'Aku/kau' baku sastra. 'kau' VALID sebagai monolog dalam; gagal HANYA kalau nyapa pembaca dari luar. Puisi: baris 2–4 kata, napas naik-turun (jangan seragam = jejak AI), ujung huruf tiap bait nyambung (asonansi), WAJIB tanda baca. Rasa dr celah, jgn blak-blakan, jgn nyalahin tuhan/takdir berlebihan, 'berusaha' not 'bekerja', jgn resolve. Napas+tanda baca pas = 9/10; kepanjangan/rapat = 5/10.

### USER.md

- OTNAY creator/editor (@catatan.otnay). Runs Paperclip AI with 21 agents. Short Indonesian commands — 'lanjut' = execute immediately. Values brief, direct, terse responses. Dislikes: bicara dari luar, resolve di akhir, motivasi, self-healing, klise, fake deep.
- Pipeline `!otnay <role>` — step-by-step tanpa micromanaging; trusts editorial pipeline output, langsung lanjut role berikutnya.
- Owns project Kenfa @ /home/ubuntu/kenfa — e-commerce sepatu/sandal lokal (Laravel 13 + Filament 5). Stack: Home/PLP/PDP storefront, Cart + Midtrans Snap checkout, Filament admin. MySQL 8 Docker. Midtrans disabled by default (MIDTRANS_ENABLED=false).
- OTNAY writing sessions: user roleplay as READER and grades drafts ("9/10", dst), then tells what to fix. Score + critique = the spec. Iterates until draft hits his standard.

## Related

- [[500 Resources/Hermes Memory - VPS 13.212.26.122|Memory utama (default profile)]]
