# NoirOS

OS Android sendiri Sofyan — base PixelExperience, di-rebrand jadi NoirOS, ditambah fitur yang bantu task sehari-harinya. Target device: OPPO A31 (CPH2015 / codename internal OP4C7D, MT6765).

## Status
- **v1 = GSI-based** (modifikasi PE 12.1 yang sudah jalan di HP) — jalur build dari source (LineageOS/PE dari nol) BELUM diputuskan Sofyan (ditawarkan 21:00 WIB 27 Nov 2026).
- **Image v1 SELESAI + terverifikasi independen 27 Nov 23:58 WIB** — BELUM di-flash, menunggu persetujuan eksplisit Sofyan + backup dulu.
- **Recovery v1 = OrangeFox** (keputusan Sofyan 28 Nov 00:02 WIB). Rencana nanti: recovery + kernel sendiri, full Noir (proyek terpisah setelah v1 stabil).

## Image v1 (27 Nov 2026)
- `noiros-system.img` 5.435.817.984 byte (pas ukuran partisi system mmcblk0p37, 5,06 GiB, single-slot), md5 `67308667c91e16f043af09e45abf0d0e`, `e2fsck -n` clean, ruang kosong ~1,69 GB. Image asli tidak berubah (md5 `bd7abd371143272632bb6404b45776a6`).
- Branding build.prop: brand/manufacturer Noir, model "NoirOS A31", name NoirOS, display id `NoirOS-12.1-20261127`, key `org.pixelexperience.*` → `org.noiros.*`, 0 sisa pixelexperience. Fingerprint UTUH (GMS/Play Integrity bergantung padanya).
- APK Noir Assistant sebagai system app di `/system/priv-app/NoirAssistant/` + privapp-permissions xml.
- Boot animation baru: hitam + teks emas NoirOS, 721 KB.
- Audio fix v1.3 TIDAK dibakar ke image (file di /vendor) — v1 = system.img + modul Magisk.
- Laporan: `~/workspace/scratch/noiros/gsi-build/NOIROS-MOD-REPORT.md`. Inspeksi GSI: `~/workspace/scratch/noiros/gsi-build/GSI-INSPECTION.md`.

## Noir Assistant (pilar pertama)
- Spek v1 SELESAI 27 Nov 15:24 WIB (PDF). Arsitektur Hybrid (provisional — butuh konfirmasi skema token + scope data dari Sofyan; endpoint noir-brain tanpa auth masih P0 terbuka): online ke noir-brain di STB kalau ada koneksi, fallback offline di HP + outbox.
- Invokasi: bubble mengambang ~56dp (drag/snap/tap/long-press). Avatar: sprite pixel Noir yang sudah ada (48x99, 28 warna). Quick capture v1: ide konten + jurnal trading + note bebas (task PKL TIDAK masuk).
- APK tahap 4 SELESAI dikompilasi 27 Nov 21:38 WIB: native Kotlin (AGP 9.1.0 + Kotlin 2.2.21, tanpa AndroidX, hanya stdlib), `app-debug.apk` 2.658.436 byte, md5 `a1d174d9cd005cc0fcf3caa9db38ac5b`, package `id.noirstudio.assistant.debug`. Isi: foreground service, bubble, overlay chat (status selalu Offline), QS tile, FullscreenWatcher.
- Uji perangkat 27 Nov 23:37–23:55 WIB: Skenario 1 LULUS 3/3 (overlay di Telegram, Chrome, YouTube; tutup via ✕ + Back). Skenario 2 sebagian lulus (seret+snap, fade idle alpha 0,55, menu long-press, panggil lagi via QS tile). Drag-to-dismiss BELUM terbukti (4x gagal, dugaan gestur Back sistem). Bug kecil: posisi tersimpan = pra-snap. Bubble dibiarkan NYALA di HP. Laporan: `~/workspace/scratch/noiros/noir-assistant-app/TEST-REPORT-2026-11-27.md`.

## Audio GSI PE 12 — v1.3 SUKSES (27 Nov 2026)
- Bug: volume tidak berfungsi, semua app volumenya full.
- Hipotesis HAL audio vendor 4.0 terlalu tua TERBUKTI SALAH (stock + BloomOS sama-sama HAL 4.0, VINTF GSI lolos). v1.0/v1.1/v1.2 gagal (Max 0, error VolumeCurve 58x).
- Akar masalah: satu include hilang (`hearing_aid_audio_policy_configuration.xml`) merusak parsing SELURUH `audio_policy_configuration.xml`, APM fallback ke default Max 0.
- v1.3 = v1.2 minus satu baris include itu. SUKSES ~19:05: MUSIC Max 15, RING/ALARM/SYSTEM Max 7, error XInclude 0, VolumeCurve 0. Sofyan konfirmasi 21:00: "volume udah aman" — thread DITUTUP.

## Bank Jago — deteksi root (27 Nov 2026, DITUNDA Sofyan)
- DenyList saja tidak cukup (tes 19:26–19:37 gagal). Akar: Zygisk MATI → DenyList tidak bekerja. Modul Magisk terpasang 19:36: Noir ZRAM A31 v1.0 + Shamiko v1.2.5-414 + PlayIntegrityFork v19.
- Zygisk bawaan dinyalakan 19:45: tes 15 detik 0 event (menipu), tes 60 detik 2 event — masih deteksi. Foto Sofyan 19:48: "Rooted device alert", hard-block, minta factory reset.
- Akar: injeksi Zygisk bawaan RUSAK di GSI ini (libzygisk.so native bridge API v2 tidak kompatibel v3; 0 modul ter-inject). Build props bersih (release-keys, ro.debuggable=0, ro.secure=1, type user, verifiedbootstate green, flash.locked=1, vbmeta locked).
- Zygisk Next v1.5.3 terinstall 19:53 + reboot. HP sempat hilang dari USB (s/d 19:57); login TikTok 19:56–19:58 @whykenapa15 dari Oppo CPH2015 — BELUM dikonfirmasi Sofyan itu dia atau bukan.
- 21:00 Sofyan: Jago "nanti aja" — DITUNDA, jangan di-nudge. Verifikasi injeksi Zygisk Next + tes 60 detik masih menunggu. noirzram v1.1 (service.sh + `setenforce 1`) standby.

## TikTok force close — RAM habis, ZRAM jalan (27 Nov 2026)
- Bukan crash/root: TikTok dibunuh sistem ~7 detik setelah dibuka (signal 9). HP 4GB, free cuma 113MB, Swap 0; GMS ~745MB.
- Modul Magisk Noir ZRAM A31 v1.0 terpasang 19:36: zram 2GB lz4, swappiness 100. Swap 2047MB, terpakai 232MB saat TikTok jalan, TikTok hidup 25 detik+.

## Bahan & file
- GSI: `PixelExperience_Plus_arm64-ab-vndklite-12.1-20221118-UNOFFICIAL.img.xz` (1.429.630.628 byte) — download lokal utuh; upload ke Drive GAGAL 3x (HTTP 500, putus menit 14–17). Sesi GSI ditutup Sofyan 27 Nov ("yaudah kalo gitu gapapa, sampe sini aja").
- BloomOS 1.0 OP4C7D = LineageOS Android 9 (SDK 28), patch Jan 2022, eng/test-keys/permissive — BUKAN base rebrand; referensi device tree + vendor blob + konfigurasi audio. File di Drive sofyanofg (folder "BloomOS OP4C7D") + lokal `~/workspace/scratch/bloomos/`.
- Stock ROM CPH2015: `CPH2015PUEX_11_OTA_0370_all_sJAwjCFSpw7p.ozip`, 2.613.968.616 byte, MD5 `56c56a4fb8c7041fc83c544cf4d21f73`, build A.37 (10 Jun 2020), Android 9 / ColorOS 6.1.2. Lokal `~/workspace/scratch/noiros/`; upload Drive gagal 2x.
- Drive: akun pindah campus (15GB, sisa ~950MB) → sofyanofg@gmail.com (400GB). Pola terbukti: upload multipart CLI >1GB putus konsisten lewat proxy ini.
- Build machine = InstaBox (keputusan Sofyan). Mesin `noirrouter-dev` (4 vCPU/8GB/20GB) tidak cukup buat full build AOSP/PE (~200GB + ≥16GB RAM); realistis buat build kernel / host repo+tooling / server OTA.
- Analisis BloomOS: `~/workspace/scratch/noiros/bloomos-analysis.md`. Brainstorm Noir Assistant: `~/workspace/scratch/noiros/noir-assistant-brainstorm.md`.

## Riwayat
- 2026-11-27: hari pertama NoirOS — spek Assistant v1, audio v1.3 sukses, image v1 selesai, APK tahap 4 + uji perangkat, ZRAM, Zygisk Next, Jago ditunda. Lihat [[400 Daily/Noir 2026-11-27]].
