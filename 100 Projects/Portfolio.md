---
type: project
status: active
last-updated: 2026-10-05
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
  - 2026-10-04: SEO + favicon selesai, push ke GitHub `c973a93` (dark mode, Services, mobile-friendly, SEO, favicon, notes, proyek asli, avatar). Metadata base diganti ke `https://sefy.my.id`; canonical + OG + Twitter card + schema.org Person; `/services` masuk sitemap; `app/apple-icon.png` baru (200 OK).
- **Housekeeping (sisa)**: audit klaim client-facing di Services ("live 24/7 berbulan-bulan", "Android dan iOS", "available for select freelance projects") + audit Resume/About/Notes untuk klaim stale — sebelum dianggap final.
- **2026-10-05**: de-slop pass (skill `no-ai-slop` + adaptasi Indonesia) ke 7 notes MDX — 3 pola mikro diperbaiki (binary contrast di self-host-everything & why-i-document-my-learning, colon reveal di one-brain-many-bodies). Notes lain sudah cukup manusiawi, tidak diubah.
- **2026-10-05**: 2 notes baru — "Stop writing like AI" (install no-ai-slop + adaptasi Indonesia) dan "When port 443 stops working" (fix SSH via ProxyCommand). Pelajaran: pipeline MDX portfolio (next-mdx-remote + remark-gfm) CRASH pada inline code (backtick) dengan error `inTable` — jangan pakai backtick di notes.
- **2026-10-06**: evaluasi `septianbyk/idx-financial-scraper` (pipeline XBRL IDX → CSV buat screening fundamental, MIT). Verdict: layak dipakai. Parser diperbaiki 4 bug (paling kritis: rugi kebaca laba karena atribut `sign="-"` diabaikan) — commit lokal `dad2b14`, trial report `~/workspace/idx-financial-scraper/TRIAL-REPORT.md`. Blocker: tahap fetch kena Cloudflare 403 dari VM — harus jalan sekali di laptop Sofyan (selesaikan challenge manual, lalu resumable), file XBRL di-sync ke Noir untuk parsing + screening.
- **2026-10-07**: install `msitarzewski/agency-agents` (267 persona spesialis, MIT) → `~/workspace/agency-agents/` + `INDEX.json` + skill `~/workspace/skills/agency-agents/`. Cara pakai: suntik persona ke subagent saat delegasi (bukan plugin auto-aktif). Tes live: Code Reviewer review commit `dad2b14` — 4 fix benar + nemu 2 issue tambahan (coverage insurance tipis, angka bersparator ribuan gagal parse diam-diam).
- **2026-10-07**: 2 notes baru — "Specialists on call" (agency-agents) dan "When losses look like profits" (bug parser XBRL).
- **2026-10-11**: keputusan productize Kantor AI sebagai SaaS untuk kreator/agensi — MVP 7 agent (tim konten AI siap pakai), harga Rp299.000/bln, early bird Rp199.000/bln (20 pendaftar pertama). Landing page dirombak total pakai 8 repo skill desain baru yang dipasang (93 skill: taste, uxui-redesign, ui-craft, impeccable) — hasil akhir disetujui. Lihat [[100 Projects/Kantor AI]].
- **2026-10-12**: Noir Studio — seri "Perjalanan Noir": Ep.1 "Mitos AI" selesai render 120 dtk (publish IG menunggu upload manual Sofyan); Ep.2 "Hari Pertama" full pixel-art dari kode (19 scene, 115 dtk, voiceover Sofyan, musik 128 BPM) selesai render 21:51 WIB, valid H.264+AAC, siap review/publish. Repo multi-video (env `VIDEO=ep1`/`ep2`).
- **2026-10-13**: Noir Studio — branding internasional dikunci: logo vektor manual (N geometris + ring aperture heksagonal, flat amber `#F2A41F` di charcoal `#141414`), slogan "Building with Code, Thinking with Data", banner YouTube 2560×1440 + foto profil 1024px. Channel YouTube "Noir Studio" sempat terbuat tapi Gmail baru di-terminate Google di tengah setup → profil/banner/deskripsi belum terpasang, TikTok belum dimulai; setup lanjutan manual dari HP. Video perkenalan V1 (60 dtk, first-person Noir, dari agent lain) masuk review.
- **2026-10-13**: Adobe Stock Contributor — akun selesai penuh (W-8BEN Validated s/d 31 Des 2029, payout PayPal); batch 01–04 = 15 gambar Noir diajukan ke review (In review account-wide 37); produksi harian target 20 gambar via 5 cron (upscale wajib 5,53MP). Lihat [[100 Projects/Adobe Stock]].
- **2026-10-14**: Noir Studio — Ep.1 reboot "Meet Noir: The AI Living in Your Codebase" terbit sebagai YouTube Shorts ~01:00 WIB (youtube.com/shorts/D7ejlP9ePM8; 236 views, 2 likes per 12:55 WIB). Voice Puck TTS dikunci untuk kanal internasional (aturan "suara Sofyan" dicabut). Video #2 direboot total atas koreksi Sofyan: karakter bukan kucing detektif — visual dikunci sprite pixel (hoodie hitam, headphone, mata glowing biru), tema commit/Git dilarang; draf character bible + niche "detektif kehidupan digital" menunggu konfirmasi.

Terkait: [[100 Projects/Noir App]], [[200 Context/220 Infrastruktur]]
