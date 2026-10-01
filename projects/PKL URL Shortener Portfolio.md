# PKL URL Shortener Portfolio

## Konteks

Project portfolio untuk persiapan PKL November 2026. Tempat PKL dominan pakai Go + React. Sofyan masuk via koneksi guru (program magang sebenarnya khusus mahasiswa), jadi ekspektasi kemampuan lebih tinggi dari standar anak SMK.

Background Sofyan: Laravel + Flutter. Nol di Go dan React, tapi paham konsep REST API, routing, component thinking.

## Stack

- **Backend:** Go + Gin framework + GORM + SQLite
- **Frontend:** React + Vite + TailwindCSS + Recharts
- **Auth:** JWT
- **Deploy:** Railway (backend) + Vercel (frontend)

## Fitur Core

- Shorten URL dengan custom slug opsional
- Redirect handler dengan tracking (timestamp, user-agent, IP region)
- Dashboard analytics: total klik, klik per hari (line chart), top URLs
- Register/login dengan JWT

## Timeline 6 Minggu

| Minggu | Target | Status |
|--------|--------|--------|
| 1 | Go basics: syntax, struct, interface, Gin routing | ⬜ |
| 2 | React basics: components, hooks (useState, useEffect), fetch | ⬜ |
| 3 | Backend: URL CRUD, redirect handler, JWT auth | ⬜ |
| 4 | Frontend: dashboard, auth flow, connect ke API | ⬜ |
| 5 | Polish: error handling, loading states, responsive | ⬜ |
| 6 | Deploy, README, latihan interview | ⬜ |

## Aturan Main

- **Mentor-only mode.** Noir tidak auto-generate code atau boilerplate. Sofyan ketik sendiri.
- Noir bantu debug, jelasin konsep, review logic.
- Sofyan harus bisa jelaskan setiap baris kode pas interview intern.
- Modul panduan lengkap: [[porto-guide]] (`/home/sofyan/Documents/project/porto-guide.md`)

## Referensi

- Modul: `/home/sofyan/Documents/project/porto-guide.md`
- Project dir: `/home/sofyan/Documents/project/url-shortener/`
- [Go Documentation](https://go.dev/doc/)
- [Gin Framework](https://github.com/gin-gonic/gin)
- [React Documentation](https://react.dev)
- [Vite](https://vitejs.dev)

## Interview Prep Notes

Pertanyaan yang kemungkinan ditanya:
- Kenapa pake Gin?
- Gimana handle concurrent request di Go?
- Beda goroutine vs thread?
- Kenapa SQLite dulu, kapan upgrade Postgres?
- Gimana JWT flow lo?
- Kenapa React bukan framework lain?

*Catatan jawaban akan diupdate seiring progress belajar.*

---

Tags: #pkl #portfolio #golang #react #internship
Created: 2026-09-22
