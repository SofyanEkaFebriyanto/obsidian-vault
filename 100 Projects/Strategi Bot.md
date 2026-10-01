---
type: project
status: active
last-updated: 2026-08-25
tags: [trading, freqtrade, strategy]
---

## For future agent
Detail strategi bot dari agent memory Hermes. Klaim infrastruktur confidence: high (dari sesi operasional). Detail parameter entry belum diverifikasi ke source code bot — TBD bila butuh presisi.

# Strategi Bot

Catatan strategi trading otomatis.

- [[100 Projects/ConfluenceTrend v8|ConfluenceTrend v8]] — Donchian20 + ADX25 + EMA200

## Infrastruktur trading
- Freqtrade futures.
- Exchange: Bitget (KYC) atau Hyperliquid (zero-KYC, ETH key).
- Settle: USDC di Arbitrum.
- Deployment: VPS SG (13.250.28.88).
- Role Hermes: strategis/risk supervisor saja — BUKAN eksekusi order live.
- Pola kerja: local-first dulu, baru deploy VPS.

## Risk management
- (belum dicatat — tambahkan saat dispesifikkan)

## Backtest & forward-test
- (belum dicatat — log hasil di [[100 Projects/Trading Journal]])

Terkait: [[100 Projects/Proyek Aktif]]
