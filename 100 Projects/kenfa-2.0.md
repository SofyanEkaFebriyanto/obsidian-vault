---
type: project
status: active
last-updated: 2026-08-30
ai-first: true
tags: [kenfa, laravel]
---

## For future agent
Proyek web live. Detail dari agent memory + sesi deploy (confidence high).

# kenfa-2.0

- Live: https://test.kenfa.id — hosting Hostinger hPanel.
- Stack: Laravel.

## Gotchas deploy
- **SSH auto-VPN**: `~/.ssh/config` block `hostinger-kenfa` pakai `ProxyCommand socat - SOCKS5:127.0.0.1:51001` (Warp wireproxy). Deploy/rsync langsung tanpa nyalain VPN manual.
- **Deploy WAJIB rsync `public/.htaccess` → `public_html/.htaccess`**: tanpa itu semua route selain `/` jadi 404 "This Page Does Not Exist" (front-controller rewrite hilang).
- **PHP CLI wajib `/opt/alt/php84/usr/bin/php`** (8.4.19). Default `php` di server = 8.3.30 → composer butuh ≥8.4.1 → artisan error "Composer detected issues". Pakai binary itu untuk semua artisan/cron live.
- **STRUKTUR REMOTE (penting)**: root Laravel = **`~/domains/test.kenfa.id/`**, webroot = **`~/domains/test.kenfa.id/public_html/`** (direktori nyata, bukan symlink). Mapping rsync:
  - `src/resources/views/` → `domains/test.kenfa.id/resources/views/`
  - `src/public/build/` → `domains/test.kenfa.id/public_html/build/`
  - `src/public/build/` → `domains/test.kenfa.id/public/build/` (WAJIB — lihat gotcha di bawah)
  - `src/public/images/` → `domains/test.kenfa.id/public_html/images/`
  - `src/public/.htaccess` → `domains/test.kenfa.id/public_html/.htaccess` (WAJIB)
  - JANGAN rsync root utuh `--delete` (pernah hapus `public_html`).
- **GOTCHA VITE BUILD — deploy build WAJIB ke DUA direktori (temuan 5 Sep, style hilang semalaman):** web server serve file ke browser dari `public_html/build`, TAPI `@vite()` di runtime baca manifest dari **`public/build`** (app dir Laravel). Kalau build baru hanya masuk `public_html/build`, HTML tetap nunjuk hash CSS **lama** (dari manifest lama di `public/build`) → file hash lama 404 di `public_html` → **CSS tidak ke-load** (JS bisa selamat kalau hash-nya kebetulan sama). Fix tiap deploy yang ubah CSS/JS: rsync `public/build` → DUA tujuan (`public_html/build` DAN `public/build`), lalu `view:clear`. Verifikasi cepat: `grep app-...css domains/.../public/build/manifest.json` harus == yang ada di `public_html/build/`, dan `curl` URL CSS dari HTML harus 200.
- **SYMLINK `public_html/storage` sering BROKEN** (pernah nyasar ke `/var/www/html/storage/app/public` yang tidak ada → gambar storage 404). Fix tiap deploy: `rm -f public_html/storage && ln -s $(pwd)/storage/app/public public_html/storage`.
- **JANGAN PERNAH rsync multi-source dengan satu dest + `--delete`** (incident 7 Sep 2026): `rsync -az --delete app/ config/ routes/ ... live/` FLATTEN semua isi ke root live DAN `--delete` menghapus apa pun di dest yang tidak ada di source — `public_html/`, `.env`, `vendor` ikut hilang, situs 404. SOP deploy: **satu source → satu dest per rsync** (`rsync -az --delete src/ live/dir/`), `git status` clean + smoke curl 3 halaman via Warp sebelum deploy.
- **`.env` live BUKAN `.env` lokal** — kredensial DB live = `u716977336_kenfa_db` / `u716977336_kenfaofficial` (user Hostinger), beda dari Docker (`kenfa`/`kenfa`, `DB_HOST=mysql`). Jangan copy `.env` lokal ke live apa adanya; susun dari nilai live (sumber tepercaya: backup).
- **Backup live bulanan** (menyelamatkan recovery 7 Sep): `tar czf ~/test-kenfa-backup-$(date +%m%d).tar.gz -C ~ domains/test.kenfa.id` — backup 26 Agu memuat `.env`, `public_html`, `storage` (341 file), `vendor`.

## Gotchas Biteship (ongkir)
- **PAKAI LIVE KEY di produksi**: `BITESHIP_API_KEY` harus `biteship_live.…`. Test key (`biteship_test.…`) di produksi → Biteship tolak auth → `rates()` degrade jadi `[]` (kontrak "kegagalan = kosong, jangan gagalkan checkout") → UI ongkir KOSONG tanpa error visible. Top-up saldo TIDAK memperbaiki ini.
- Key JWT = 3 bagian dipisah titik (`biteship_live.HEADER.PAYLOAD.SIGNATURE`). Kalau kepotong (signature hilang) → auth gagal → ongkir kosong.
- Cek saat ongkir kosong: (1) key `biteship_live.` & lengkap, (2) `BITESHIP_ORIGIN_POSTAL_CODE=40375` & `BITESHIP_COURIERS` terisi, (3) config cache stale → `php artisan optimize:clear`.
- `dev_rates=true` (config) → pakai tarif palsu, JANGAN di produksi.

## Gotchas email (SMTP produksi)
- `smtp.hostinger.com` **port 465 + `MAIL_SCHEME=smtps`** (SSL implisit). Port 587 salah untuk setup ini.
- `MAIL_USERNAME` = **full email** (`noreply@kenfa.id`), akun dibuat di hPanel → Emails → Email Accounts.
- **`535 auth failed` = kredensial/akun hPanel salah, BUKAN config Laravel.** Cek akun email dulu sebelum ngoprek config.
- Email transaksional kenfa `implements ShouldQueue` → dengan `QUEUE_CONNECTION=database` **email nyangkut di tabel `jobs`** (worker Hostinger shared butuh cron hPanel yang belum ada). Produksi pakai **`QUEUE_CONNECTION=sync`**.

## Gotchas jaringan / DNS
- **DNS kenfa.id semua di hPanel Hostinger (bukan Cloudflare)**. Apex ALIAS → `kenfa.id.cdn.hstgr.net`, `www` CNAME → CDN, MX mx1/mx2.hostinger.com, SPF + DMARC + 3 DKIM CNAME (hostingermail-a/b/c), `ftp` A → 145.79.14.115.
- **`test.kenfa.id` & `kenfa.id` TIDAK punya AAAA record di hPanel** — IPv6 datang dari CDN Hostinger (target ALIAS punya AAAA sendiri), bukan record yang bisa dihapus. Jadi "hapus AAAA biar IPv6 mati" TIDAK bisa dilakukan dari hPanel.
- **VPN dev tidak route IPv6**: semua `curl -6`/`ping6` dari mesin dev gagal walau tujuan sehat. Uji IPv6 nyata lewat Warp SOCKS5 `127.0.0.1:51001` + `--resolve host:443:[IPv6]`.
- A/AAAA `test.kenfa.id` berotasi round-robin (IP beda tiap query) — normal, dilayani CDN hcdn.

## ISP WiFi rumah null-route CDN Hostinger (29 Agu 2026)
- Dari WiFi rumah: **kenfa.id & test.kenfa.id timeout di semua device** (laptop + 3 HP). Ganti DNS resolver juga gagal. **Data seluler & VPN BISA.** Dari jaringan lain (Warp/check-host) 200.
- Kedua domain resolve ke range yang SAMA → **ISP rumah null-route `147.93.77.0/24` + `213.210.57.0/24`** (range CDN Hostinger). Server sehat; ini BUKAN masalah website — customer di ISP lain aman.
- Opsi permanen (belum dieksekusi): pindah DNS kenfa.id ke **Cloudflare proxy** (customer resolve IP CF, CF tarik dari origin Hostinger). Konsekuensi: ganti nameserver, copy record (A/CNAME/MX/SPF/DKIM/DMARC), SSL Full(strict), 2-4 jam downtime propagasi.

## Fitur: Pengembalian Publik Satu Pintu (29 Agu 2026, LIVE `4d9db1a`)
- `/pengembalian` (publik, tanpa login) melayani 2 jalur: pembeli **kenfa.id** (verifikasi order_number+email dulu) & **marketplace** (Shopee/TikTok/Tokopedia/Lazada/WA — manual).
- Extend `order_returns`: `order_id`/`user_id` nullable + `channel`, `ticket_number`(RTN+date+seq, unique, backfill di migrasi), `access_token`(40, hidden), `external_order_number`, `customer_{name,email,phone}`, `item_description`.
- Keamanan: channel=kenfa WAJIB re-verify `canRequestReturn()` server-side (browser tak bisa bypass window 7 hari / 1-retur-aktif via channel palsu); marketplace TIDAK restore stok; status tiket gate `?token=` → 404 (bukan 403); rate limit per IP; email degrade aman.
- Blade: `return-request.blade.php` (indexable), `return-status.blade.php` (noindex). Filament OrderReturns: channel badge + ticket_number + filter channel.
- Blok "Ini website resmi Kenfa" di `return-request.blade.php` **DIHAPUS** atas permintaan founder (halaman jadi murni form).
- Commit `4d9db1a` (13 file, 878+/146-), push origin/main. Suite 188 hijau.

## Fitur: Mobile UI ala Shopee (30 Agus 2026, LIVE)
- Plan: `.hermes/plans/2026-08-27-adopsi-ui-mobile-shopee.md` (Fase 1–3 dieksekusi; Fase 4 grid PLP sudah `grid-cols-2`).
- **PDP sticky action bar** (mobile, `lg:hidden fixed bottom-0`): Chat CS wa.me / + Keranjang / Beli Sekarang. Harga live via `displayPrice`. Bottom-nav sitewide **disembunyikan di PDP** lewat flag `@section('pdp_action_bar')` di `layouts/app.blade.php` (`@unless(View::hasSection(...))`). Desktop PDP tidak berubah (tombol Add to Cart `hidden lg:flex`).
- **Variant picker → bottom sheet** (mobile): selector inline desktop `hidden lg:block`; sheet `lg:hidden` slide-up, konfirmasi jalankan `addToCart()`/`buyNow()` tertunda. Harga satu sumber (`v.formatted`/`displayPrice`), tidak ada re-derive manual.
- **Mobile header**: logo-K (`images/logo-k.png`, kiri) + search bar lebar langsung ketik-able (tengah, reuse `headerSearch`) + wishlist (kanan). Hamburger + logo full + ikon akun/keranjang disembunyikan di mobile (`hidden lg:flex`) — navigasi lewat bottom nav. Desktop tetap ikon search → panel.
- Test: `tests/Feature/PdpActionBarTest.php` (6 kasus). Full suite 194 passed (641 assertions). Commit `0ddb35c`.
- **GOTCHA ALPINE — tombol `<button>` bottom-nav mati (fix sore 30 Agus, commit `4f12b49`)**: Kategori (`$dispatch('toggle-mobile-menu')`) & Keranjang (`$store.cart.toggle()`) tidak memicu apa pun padahal `<a href>` jalan & Alpine hidup. Akar: `<nav>` bottom-nav tidak punya `x-data` → Alpine tidak me-bind `@click`. Fix: tambah `x-data` di `<nav>`. **Aturan Alpine v3: elemen ber-`@click`/`$store`/`$dispatch` wajib dalam subtree `x-data`.** Verifikasi headless (Playwright, viewport 390px): klik Kategori buka menu, klik Keranjang buka drawer.
- Deploy LIVE test.kenfa.id ✅ (rsync views/build/images/.htaccess, recreate symlink storage broken, cache php84). Verifikasi HTTP 200.

## Fitur: Google Login + Hapus Transfer Manual (7 Sep 2026, LIVE)
- **Google Login** (Socialite v5.31): `Auth/GoogleController`, routes `/auth/google` + `/auth/google/callback` (guest group, di atas catch-all), config `services.google` + `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI`. Akun baru = auto-verified (email dijamin Google) → `Auth::login` → ClaimGuestOrders auto-tautkan order guest. Password kolom NOT NULL → diisi string acak (cast `hashed`), tak bisa login via email. Tanpa key = tombol tampil, klik kembali dgn pesan "belum diaktifkan" (harmless). 7 test di GoogleLoginTest.
- **Transfer Manual dihapus dari checkout**: validasi server `in:midtrans,cod` (form palsu manual → 422, +1 test); enum DB `manual` dibiarkan (legacy, 0 baris); radio checkout hilang; badge/filer admin "(legacy)"; FAQ diupdate — **PageSeeder `firstOrCreate`, teks DB live harus di-fix manual** (sudah, 7 Sep).
- **INCIDENT rsync** (7 Sep): multi-source `--delete` flatten root live + hapus `public_html`/`.env`/`vendor` → 404 ~10-15 menit. Recovery dari backup 26 Agu (DB utuh, kode di git). SOP baru + gotchas di bagian Gotchas deploy di atas. Commit `6ade1f3` + `2997984`, suite 208.

## Open issue
- 🔶 **Performa mobile "loading lama"**: root cause kandidat kuat = **shared hosting overload** (load average 15-18 dari server, proses kita 0% CPU; TTFB terukur 2-12s). Bukan DNS/IPv6/blokir ISP. Solusi: upgrade paket / pindah VPS — di luar kendali kita tanpa tindakan founder.
- 🔶 **ISP WiFi rumah blokir Hostinger** (lihat bagian di atas) — akses dari rumah butuh VPN. Risiko customer di ISP yang sama; opsi Cloudflare proxy belum dieksekusi.
- 🔶 Cron hPanel `schedule:run` + queue worker produksi — BUTUH AKSES PANEL.

## Gotchas lokal (Docker)
- bind-mount `docker-compose.yml` pakai **`:z`** (shared SELinux label), BUKAN `:Z`. `:Z` = private per-container, kategori ganti tiap recreate → container kehilangan akses `/var/www/html`, artisan invisible, `serve` mati, `:8080` down. `docker restart` cuma fix sesaat.

## Gotchas Blade/Livewire (1 Sep 2026)
- **JANGAN pakai `@php($x = [...])` inline multi-line di view** — compiler Blade Livewire v4 (aktif karena Filament) merusaknya jadi raw `<?php($x = [` → `Call to undefined function php()` → 500. Pakai **block form** (`@php ... @endphp`) atau single-line. Verifikasi cepat: `Blade::compileString($tpl)` — cek apakah `@php(` masih tersisa literal. Regresi: `OrderTrackingReturnTest::test_status_page_renders_for_valid_token...`.
- **Model yang di-`notify()` wajib `use Notifiable`** — kalau trait-nya hilang, `store()` catch `Throwable` bikin kegagalan email DEGRADE DIAM-DIAM (hanya WARNING di log). Cek log `Gagal mengirim notifikasi` setelah deploy fitur yang kirim email.

## Tim agent & status (2026-08-26)
- Multi-agent flow: profiles [[200 Context/210 hermes-agent/index|Hermes Agent]] `kenfa-frontend/backend/qa/deploy` + skill CEO (`kenfa-ceo`). Founder → CEO → delegasi paralel → lapor.
- Audit produksi 2026-08-25: test 164 passed. P0: APP_DEBUG=true di .env, no auto-expire order pending, node_modules root-owned. P1: queue worker absent, /cart page, tracking guest, error pages, double-submit checkout, font Inter, migrasi foto, filter PLP.
- Filament v5.6.7 sudah aktif dengan resources lengkap — klaim "not configured" di CLAUDE.md STALE.

## Recent Activity
- [[400 Daily/2026-09-07|2026-09-07 — Google Login LIVE (Socialite v5.31, tombol /masuk+/daftar, auto-verified + claim guest order) + hapus Transfer Manual (validasi server midtrans|cod) + INCIDENT rsync multi-source `--delete` hapus public_html/.env → recovery penuh dari backup 26 Agu, situs 200 lagi. Suite 208, commit 6ade1f3+2997984]]
- [[400 Daily/2026-09-05|2026-09-05 — Nav pengembalian (7 tab + desktop) + rapikan akun (/akun→pesanan, tab returns keluar) + wajib pilih kurir + FIX style vite (public/build). LIVE `a80b7dc`, 200 test hijau]]
- [[400 Daily/2026-09-04|2026-09-04 — Pra-meeting owner: scheduler produksi di-restart (auto-expire 3 order pending), FIX 2 bug latens alur pengembalian (Notifiable + $steps 500), ongkir verified live. Suite 196 hijau, commit 16dfae3]]
- [[400 Daily/2026-08-30|2026-08-30 — Fix bottom-nav mobile: tombol Kategori/Keranjang mati (Alpine `x-data` di `<nav>`), commit `4f12b49`. Logo desktop/mobile + searchbar. Deploy ✅]]
- [[400 Daily/2026-08-30|2026-08-30 — Mobile UI Shopee-style LIVE: PDP action bar + variant bottom sheet + header logo-K/search/wishlist. Deploy test.kenfa.id ✅. Suite 194 hijau.]]
- [[400 Daily/Dev Logs/2026-08-29 - kenfa-2.0 pengembalian publik|2026-08-29 — Pengembalian publik satu pintu (kenfa.id + marketplace) LIVE `4d9db1a`. Biteship live key fix ongkir]]
- [[400 Daily/Dev Logs/2026-08-27 - kenfa-2.0 bottom-nav mobile shopee|2026-08-27 — Bottom nav mobile ala Shopee (6 tab) + fix SELinux :z + SSH VPN + .htaccess deploy. 7 test baru, 188 suite hijau, LIVE]]
- [[400 Daily/Dev Logs/2026-08-27 - kenfa-2.0 double-submit guard|2026-08-27 — Double-submit guard checkout (client+server) + deploy. 2 test baru, 180/181 suite hijau]]
- [[400 Daily/Dev Logs/2026-08-27 - kenfa-2.0 lacak guest live|2026-08-27 — Selesaikan /lacak (guest order tracking) + deploy live. 8 test baru, 178/179 suite hijau]]
- [[400 Daily/Dev Logs/2026-08-26 - kenfa-2.0 deploy p1|2026-08-26 — Deploy P0 LIVE ke test.kenfa.id + Sprint P1 sebagian (/cart, error pages, queue email). 171 tests pass. /lacak WIP]]
- [[400 Daily/Dev Logs/2026-08-26 - kenfa-2.0 sprint P0|2026-08-26 — Sprint stabilisasi P0 dieksekusi: auto-expire order, scheduler+queue containers, config produksi, build unblock. 167 tests pass]]
- [[400 Daily/Dev Logs/2026-08-25 - kenfa-2.0|2026-08-25 — Setup tim agent + audit produksi + fix Pixel Agents]]

Terkait: [[100 Projects/Proyek Aktif]]
