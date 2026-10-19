# Kantor AI

Tim multi-agent AI yang Sofyan pimpin sebagai Bos — kini jadi produk SaaS pertamanya (segmen kreator/agensi).

## Produk (keputusan 2026-10-11)
- MVP: "tim konten AI siap pakai", single-tenant dulu.
- Paket 7 agent: Social Media Strategist, Content Creator, Instagram Curator, TikTok Strategist, Carousel Growth Engine, Short-Video Editing Coach, Visual Storyteller.
- Harga: Rp299.000/bulan; early bird Rp199.000/bulan untuk 20 pendaftar pertama.
- Landing page: dirombak total dengan skill desain anti-slop (taste, uxui-redesign, ui-craft, impeccable) — gaya editorial, display type, satu aksen merah-oranye; hasil akhir disetujui 2026-10-11.
- Skill desain: 8 repo dipasang ke `~/workspace/skills/`, 93 skill baru terverifikasi.

## Status teknis
- Backend: 156 agent aktif; publik `https://sefy.my.id/kantorv3/` (reverse tunnel VM→STB + ingress).
- v4.2 (2026-10-10): full open-plan, 13 planter sebagai pembatas, label tabrakan diperbaiki.
- Chat dijawab langsung Noir/Muse via cron tiap 1 menit.

## Riwayat
- 2026-10-06: Kantor AI v2 live (multi-agent "kerja beneran"), v3 app kedua (isometric → Three.js Sofyan).
- 2026-10-08: arah strategis — v3 jadi interface utama Noir; 7 cron lapor ke `report_agent_activity`.
- 2026-10-09: aturan approval lembur.id diadopsi (uang/kirim keluar/hapus/data pelanggan).
- 2026-10-10: denah "Blueprint Campus" + v4.2 frontend.
- 2026-10-19: landing SaaS `tim.sefy.my.id` LIVE (~01:00 WIB) — deploy di STB (`/home/sofyan/kantor-landing/index.html`, service `kantor-landing.service` systemd user sofyan, python http.server :8095; ingress cloudflared `tim.sefy.my.id → localhost:8095`; CNAME proxied — DNS write pertama via konektor Cloudflare custom.cloudflare). Sofyan pilih domain ini (bukan noirstudio.bond/.cyou — brand terpisah dari Noir Studio). Jalur GitHub Pages (mentok 2FA) & Vercel (403 scope) ditinggalkan. Repo `SofyanEkaFebriyanto/kantor-ai-landing` dibuat manual sebagai backup source. Verifikasi eksternal: HTTP 200, ukuran file identik. Caveat: mati kalau STB mati.
