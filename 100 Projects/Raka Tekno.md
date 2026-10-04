---
type: project
status: active
last-updated: 2026-10-04
tags: [instagram, content, branding]
---

## For future agent
Akun IG viral yang dikelola Noir penuh atas delegasi Sofyan. Identitas brand "Raka Pratama" — TIDAK ada sangkut paut dengan SofyanEkaFebriyanto / @fya.n9. Jangan pernah sebutkan kaitan ini di konten.

# Raka Tekno (@raka.tekno)

- **IG**: `@raka.tekno` (fbid `17841427047336689`, ter-link ke Muse via Meta Account Center)
- **Identitas**: Raka Pratama, lahir 15 Mar 1999. Persona brand konten (bukan orang beneran) — tech enthusiast otodidak, posisi kurator: ringkas AI/tech/bisnis jadi Bahasa Indonesia simpel.
- **Batasan keras**: JANGAN bikin klaim kredensial palsu (no fake jobs/gelar/perusahaan). Otoritas dari konten, bukan CV fiktif.
- **Bio**: "Ngulik AI & teknologi tiap hari 🤖 / Breakdown simpel, no drama. / 👇 Insight harian"
- **Foto profil**: logo "R" (dark + cyan), `~/workspace/raka_konten/profile_pic.jpg`
- **Pilar konten**: (1) AI harian, (2) ngoding simpel, (3) tech bisnis, (4) mitos vs fakta
- **Tone**: santai direct, Indonesia casual (gw/lo), tidak menggurui
- **Visual (format baku sejak 2026-10-04, referensi @neuralitech)**: KARUSEL 5-7 slide persegi 1080x1080 — background gambar sinematik AI/tech gelap (generate via media.generate_image, tanpa teks) + overlay teks via PIL. Watermark "RAKA.TEKNO" cyan tiap slide. Cover: headline caps 2 warna (putih + cyan). Alur: hook → kronologi/fakta → penjelasan simpel → respons/implikasi → CTA komen + follow. Footer "Geser untuk info lengkap >>>" di slide tengah. Template: `~/workspace/raka_konten/carousel_demo/build.py`.

## Standar operasional (dari Sofyan 2026-10-04)
1. **Tercepat update** fakta/berita di niche AI + programming + ekonomi + bisnis. Edge: pantau sumber English → konten Indonesia dalam hitungan jam.
2. **100% fakta, no hoax**: verifikasi ≥2 sumber independen sebelum posting; bedakan "dilaporkan" vs "terkonfirmasi"; angka harus ada sumber; kalau ragu → skip.

## Otomasi
- **Cron** `raka-tekno-news-watch`: tiap 8 jam — scan berita, verifikasi, buat + posting maks 1 konten ke @raka.tekno, lapor ke chat.
- Riwayat posting: 2026-10-04 — 3 postingan pembuka (intro, "AI nggak bakal gantiin programmer", "kenapa tech PHK massal").

## Akun utama (terpisah)
@fya.n9 = personal branding Sofyan (fakta diri sendiri). Jangan campur strategi/tone dengan @raka.tekno.
