---
type: project
status: active
last-updated: 2026-10-07
tags: [idx, finance, data-pipeline, screening]
---

# IDX Financial Scraper

Pipeline Python (repo `septianbyk/idx-financial-scraper`, MIT) buat scrape laporan keuangan kuartalan emiten IDX → CSV rapi siap screening fundamental. Dievaluasi 2026-10-06 atas permintaan Sofyan ("maksimalin aja").

- **Lokasi**: `~/workspace/idx-financial-scraper/` (clone) + venv + `TRIAL-REPORT.md`
- **3 tahap**: master data (yfinance → emitens.csv) → fetch XBRL dari IDX → parse → financial_reports.csv
- **Verdict**: LAYAK dipakai. Data dari XBRL resmi IDX, bukan scraping portal berita.

## Bug parser yang diperbaiki (commit lokal `dad2b14`)

1. File FY (Audit) tidak pernah di-parse — PERIODS cuma Q1–Q3.
2. Mapping taxonomy Non-Financial unreachable — classify_taxonomy tidak pernah emit tipe itu.
3. **Rugi terbaca sebagai laba** — atribut `sign="-"` diabaikan (paling kritis buat screening).
4. `outstanding_shares` ketimpa 0 — placeholder yfinance ikut hilang.

Validasi: lolos uji XBRL sintetis. Review persona Code Reviewer (agency-agents) 2026-10-07: 4 fix benar, tanpa blocker.

## Issue terbuka

- Coverage taxonomy `insurance` tipis (cuma revenue) — diakui README upstream.
- Angka ber-separator ribuan ("1,234,567") gagal `float()` dan ke-skip diam-diam.

## Blocker: fetch harus jalan di laptop

Tahap fetch (download XBRL dari IDX) kena Cloudflare 403 dari VM Noir. Harus dijalankan Sofyan sekali di laptop/desktop: Chrome kebuka → selesaikan challenge manual → tekan Enter → download jalan otomatis (2 dtk/ticker, resumable, skip file existing).

## Next step

1. Sofyan: `python run.py --skip-master --tickers BBCA TLKM UNTR --start-year 2024` di laptop, sync folder XBRL ke Noir/STB.
2. Noir: parse + bangun layer screening (ROE, DER, net margin, revenue growth) untuk riset value investing.

Terkait: [[100 Projects/Trading Journal]], [[100 Projects/Portfolio]]
