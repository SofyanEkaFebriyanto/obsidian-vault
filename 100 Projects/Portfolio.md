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
- **Stack**: Next.js 14 + Tailwind (static export), Bricolage Grotesque + Spectral fonts.
- **Konten**: hero (foto profil IG + nama), values, featured project, notes, now, about, projects, contact.
- **Hosting**: STB — file di `/opt/portfolio/`, service systemd `portfolio.service` (python http.server, `127.0.0.1:8090`). Ingress via tunnel Cloudflare STB.
- **Source**: repo `SofyanEkaFebriyanto/vibe-portofolio` (clone lokal `~/workspace/vibe-portofolio/`). Build: `npm run build` dengan `output: 'export'` + `trailingSlash: true` → deploy isi `out/` ke `/opt/portfolio/`.
- **Riwayat**: 2026-10-03: versi HTML/CSS/JS buatan Noir (diganti). 2026-10-04: ganti ke repo vibe-portofolio milik Sofyan + konten proyek asli + foto IG di hero. Jangan sebut status PKL di konten.

Terkait: [[100 Projects/Noir App]], [[200 Context/220 Infrastruktur]]
