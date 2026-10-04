---
type: project
status: active
last-updated: 2026-10-04
ai-first: true
tags: [portfolio, web, homelab]
---

## For future agent
Web portofolio statis milik Sofyan Eka Febriyanto di `sefy.my.id`, dihosting di STB homelab. JANGAN sebut status PKL / "mahasiswa" di kontennya — dia siswa SMK.

# Portfolio (sefy.my.id)

- **URL**: `https://sefy.my.id` (+ `www.sefy.my.id`)
- **Stack**: Next.js 14 + Tailwind (static export), Bricolage Grotesque + Spectral fonts.
- **Konten**: hero (foto profil GitHub avatar + nama), values, featured project, notes, now, about, projects, services, contact.
- **Hosting**: STB — file di `/opt/portfolio/`, service systemd `portfolio.service` (python http.server, `127.0.0.1:8090`). Ingress via tunnel Cloudflare STB.
- **Source**: repo `SofyanEkaFebriyanto/vibe-portofolio` (clone lokal `~/workspace/vibe-portofolio/`). Build: `npm run build` dengan `output: 'export'` + `trailingSlash: true` → deploy isi `out/` ke `/opt/portfolio/`.
- **Riwayat**:
  - 2026-10-03: versi HTML/CSS/JS buatan Noir (diganti).
  - 2026-10-04 pagi: ganti ke repo vibe-portofolio milik Sofyan + konten proyek asli (Noir App, URL Shortener, API Ujikom, Kenfa) + ilustrasi SVG statis + update `content/now.ts`, toolbelt Go/Laravel/Linux, timeline 2026.
  - 2026-10-04: hero pakai GitHub avatar (460×460, `public/images/profile.jpg`, cache-bust `?v=2`) — foto IG 100×100 terlalu blur.
  - 2026-10-04: 4 notes baru (MDX, tgl 2026-10-04): one-brain-many-bodies, self-host-everything, from-laravel-to-go, test-cases-first.
  - 2026-10-04: dark mode (Tailwind class mode, toggle 🌙/☀️ di header, localStorage, default system, anti-flash script).
  - 2026-10-04: halaman Services (Backend APIs, Mobile Apps, Web Apps, AI Integration, Deploy & Self-hosting + proses 5 langkah + CTA homepage). Nav: About, Services, Notes, Projects, Now, Contact.
  - 2026-10-04: mobile-friendly — hamburger menu ☰ di HP, hero foto 144px + teks center, H1 responsif (text-3xl di mobile).
- **Housekeeping (belum beres)**: perubahan lokal vibe-portofolio BELUM di-commit/push ke GitHub; `layout.tsx` masih pakai metadata base `sofyanekafebriyanto.my.id` (ganti ke `sefy.my.id`); audit klaim client-facing di Services (mis. "live 24/7 berbulan-bulan", "Android dan iOS") sebelum dianggap final.

Terkait: [[100 Projects/Noir App]], [[200 Context/220 Infrastruktur]]
