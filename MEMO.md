# MEMO

Catatan cepat, konteks aktif, dan hal yang perlu diingat antar sesi.

---

## PKL November 2026 — URL Shortener Portfolio

- **Deadline:** November 2026
- **Stack:** Go (Gin) + React (Vite) + SQLite + TailwindCSS + Recharts
- **Level Sofyan:** Nol di Go & React. Background Laravel + Flutter (paham REST API, routing, component thinking).
- **Mode:** Mentor-only. JANGAN auto-generate code/boilerplate. Sofyan harus ketik sendiri, gw bantu debug dan jelasin konsep.
- **Modul panduan lengkap:** `/home/sofyan/Documents/project/porto-guide.md`
- **Project dir:** `/home/sofyan/Documents/project/url-shortener/`
- **Target tempat PKL:** Dominan Go + React, ada program magang (khususnya mahasiswa, Sofyan masuk via koneksi guru). Ekspektasi tinggi.

### Timeline 6 Minggu

| Minggu | Fokus |
|--------|-------|
| 1 | Go basics: syntax, struct, interface, Gin routing |
| 2 | React basics: components, hooks, fetch |
| 3 | Backend: URL CRUD, redirect handler, JWT auth |
| 4 | Frontend: dashboard, auth flow, connect API |
| 5 | Polish: error handling, loading states, responsive |
| 6 | Deploy (Railway/Render), README, latihan interview |

### Fitur Core

- Shorten URL + custom slug opsional
- Redirect dengan tracking (timestamp, user-agent, IP region)
- Dashboard: total klik, klik per hari (line chart), top URLs
- Register/login JWT

### Catatan Penting

- Sofyan harus bisa jelaskan setiap baris kode sendiri pas interview
- Bukan todo app biasa — ini showcase concurrency Go + analytics React
- Cross-platform: Windows primary, fallback Linux/macOS

---

*Terakhir update: 2026-09-22*
