---
type: project
status: active
last-updated: 2026-10-03
ai-first: true
tags: [portfolio, web, homelab]
---

## For future agent
Web portofolio statis milik Sofyan Eka Febriyanto di `sefy.my.id`, dihosting di STB homelab. JANGAN sebut status PKL / "mahasiswa" di kontennya — dia siswa SMK.

# Portfolio (sefy.my.id)

- **URL**: `https://sefy.my.id` (+ `www.sefy.my.id`)
- **Stack**: HTML + CSS + JS murni (tanpa framework), dark theme, animasi scroll-reveal.
- **Konten**: hero (nama lengkap), tentang, fakta singkat, 4 proyek (noir-app, url-shortener, api-ujikom, kenfa via test.kenfa.id), stack, kontak (email + GitHub).
- **Hosting**: STB — file di `/opt/portfolio/`, service systemd `portfolio.service` (python http.server, `127.0.0.1:8090`). Ingress via tunnel Cloudflare STB.
- **Source lokal**: `~/workspace/portfolio/` (`index.html`, `style.css`, `app.js`). Belum ada repo GitHub — pertimbangkan backup.
- **Deploy**: copy 3 file ke `/opt/portfolio/` (server serve dari disk, tanpa restart).
- **Riwayat**: dibuat 2026-10-03 atas permintaan Sofyan. Koreksi: "Mahasiswa — PKL" → "Siswa SMK", semua sebutan PKL dihapus.

Terkait: [[100 Projects/Noir App]], [[200 Context/220 Infrastruktur]]
