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
- **2026-10-15**: @raka.tekno 6 karusel terbit (run #30–#35: roundup 12–15 Okt, UE vs OpenAI/Anthropic AI Act, Anthropic Q3 $16,8B, Apple vs OpenAI tuduhan dagang, Jensen Huang chip-cutoff, Cohere-AISLE) — counter 29→35; `instagram-cli` HTTP 500 = false negative ke-8 dalam 6 hari, feed check sebelum retry. @fya.n9 3 karusel terbit (ekonomi: arus modal asing Rp131,1T; bisnis: EQT Q3; programming: Cloudflare akuisisi Deno).
- **2026-10-15**: Adobe Stock — audit portal (atas permintaan Sofyan) membuktikan abstract generatif dan foto orang photorealistic selalu ditolak, motif batik lolos (4/4 approved). Aturan baru mulai 16 Okt: STOP abstract & orang photorealistic, fokus batik/budaya Indonesia, urban farming, still life; batch-09 ditahan (hemat kuota).
- **2026-10-15**: Noir Studio — `NOIR-CHARACTER-BIBLE.md` dibuat (karakter final: bukan kucing, tanpa tema commit/Git; niche masih draf). Jalur income technical writing (sampel dari repo URL shortener, tawaran jasa Fastwork/Projects) ditawarkan — menunggu keputusan Sofyan.
- **2026-10-16**: @raka.tekno 6 karusel terbit (run #36–#41) — counter 35→41; @fya.n9 2 karusel (NVIDIA RTX Spark; timing hike Fed). HTTP 500 `instagram-cli` tetap false negative, SOP feed check dipertahankan.
- **2026-10-16**: API-UJIKOM — audit statis repo `SofyanEkaFebriyanto/api-ujikom` vs 3 PDF modul selesai; wording 403 middleware role (IsAdmin/IsPetugas/IsPeminjam) diselaraskan spek; commit `dad2cac` dipush ke `main`. Lihat [[100 Projects/API-UJIKOM]].
- **2026-10-17**: @raka.tekno 6 karusel terbit (run #42–#47: roundup, Anthropic RUU AI, EU AI Act RFI, Microsoft MAI-Base-2, GitHub Copilot retire, DeepSeek V4.1) — counter 41→47; body cron diperbaiki ke antislop + antislop-copywriting. @fya.n9 3 karusel (akuisisi BYAN Rp26,1T; systemd v262.1 + AI canary; Meta Muse Spark Open).
- **2026-10-17**: Kenfa — revisi UI antislop 9 file (token accent-dark, kontras, copy, link mati, empty state) dipush ke branch `muse-agent` commit `b32ff6a` atas nama Noir (pengecualian eksplisit); rating stars product-reviews masih pending (di luar scope).
- **2026-10-17**: API-UJIKOM — keputusan Sofyan: JANGAN pasang Filament, repo tetap murni REST API sesuai PDF; drill weekend Pra Ujikom siap (Drill A Sabtu, Drill B Minggu). Lihat [[100 Projects/API-UJIKOM]].
- **2026-10-17**: Adobe Stock — batch review #1: 12 file direview (3 diterima, 9 ditolak; atribusi shared account belum pasti); produksi pause, recheck limit Senin 19 Okt 08:00. Lihat [[100 Projects/Adobe Stock]].
- **2026-10-18**: @raka.tekno 6 karusel terbit (run #48–#53: OpenCode breach, roundup 17–18 Okt, FTC vs OpenAI/Anthropic, Replit cabut dari Anthropic, Claude pecahkan kriptografi NSA 25 tahun, Anthropic junior dev 27%→9%) — counter 47→53. Sofyan komplain watermark badge "moda.app" → script `~/workspace/tools/moda-dewatermark.py` dipakai mulai #53; koreksi record: akun Moda = plan FREE (sefy@sefy.my.id), bukan paid — menunggu konfirmasi langganan Pro Sofyan.
- **2026-10-18**: @fya.n9 3 karusel (emas minggu 19–23 Okt; World Bank revisi proyeksi RI 2026 4,7%→5,2%; Jusuf Hamka + konsorsium Rp5T borong saham + Danantara).
- **2026-10-18**: domain baru sofyan.bond, sofyan.cyou, noirstudio.bond, noirstudio.cyou — semua konek Cloudflare; konektor Cloudflare (custom.cloudflare) menunggu token dari Sofyan; kartu billing Bright Data 9205 expired 10/26 (disampaikan ke Sofyan).
- **2026-10-18**: Kantor AI SaaS — Letter "The QRIS Catch" terkirim ke Sofyan: QRIS tidak bisa auto-debit langganan (jalur manual invoice/link WA dulu); harga Rp299rb tervalidasi; keputusan domain + timing waitlist menunggu Sofyan.
- **2026-10-18**: Adobe Stock — klaim batch review #2 tidak bisa diverifikasi (tidak disampaikan ke Sofyan); recheck + rekonsiliasi otomatis Senin 19 Okt 08:00. Lihat [[100 Projects/Adobe Stock]].
- **2026-10-19**: Kantor AI SaaS — landing `tim.sefy.my.id` LIVE (~01:00 WIB, deploy di STB: `/home/sofyan/kantor-landing/index.html`, systemd user sofyan python http.server :8095, ingress cloudflared, CNAME via konektor Cloudflare — DNS write pertama yang terverifikasi). Jalur GitHub Pages (mentok 2FA) dan Vercel (403 scope) ditinggalkan. Repo `SofyanEkaFebriyanto/kantor-ai-landing` dibuat manual sebagai backup source. Lihat [[100 Projects/Kantor AI]].
- **2026-10-19**: API-UJIKOM — verifikasi 5 jebakan drill di repo atas pertanyaan Sofyan: semua sudah benar (wording 403 persis PDF, commit `dad2cac` di main) — repo 100% sesuai PDF untuk Tes Praktik 22 Okt. Lihat [[100 Projects/API-UJIKOM]].

Terkait: [[100 Projects/Noir App]], [[200 Context/220 Infrastruktur]]
