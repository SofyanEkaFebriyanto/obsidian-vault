---

kanban-plugin: board

---

## 📥 Backlog

- [ ] Pasang sync pull vault → VPS SG (on-hold atas permintaan user) @{2026-08-25}
- [ ] Review memory dump VPS Lightsail, ekstrak yang relevan jadi note proyek @{2026-08-29}
- [ ] kenfa-2.0: PDP sticky action bar (Chat/Keranjang/Beli) — prioritas konversi mobile, plan .hermes/plans/2026-08-27-adopsi-ui-mobile-shopee.md @{2026-08-30}
- [ ] kenfa-2.0: variant picker bottom sheet + mobile header search (fase lanjutan Shopee) @{2026-08-31}
- [ ] kenfa-2.0: cron hPanel `schedule:run` + queue worker produksi (butuh akses panel) — **P0 OPS: scheduler nohup mati tiap reboot (kejadian lagi 12 Sep)** @{2026-09-12}
- [ ] kenfa-2.0: pindah DNS kenfa.id ke Cloudflare proxy (cover customer ISP yang sama) — BUTUH keputusan founder @{2026-08-30}
- [ ] kenfa-2.0: putuskan performa "loading lama" (load 15-18) — upgrade paket / pindah VPS @{2026-08-30}
- [ ] kenfa-2.0: isi 5 placeholder `[LENGKAPI]` konten statis (badan hukum, lama proses, batas retur, dsb.) — butuh founder
- [ ] kenfa-2.0: masukin Biteship live key + Midtrans production key (mode testing sekarang) — keputusan founder

## 🔨 Doing

- [ ] kenfa-2.0: performa "loading lama" — root cause kandidat = shared hosting overload (load 15-18, TTFB 2-12s); butuh upgrade paket / pindah VPS @{2026-08-29}

## ✅ Done

- [x] kenfa-2.0: fix verifikasi Gmail (login Google = auto-verify akun lama) + 500 kirim-ulang (typo noreplay balik lagi → SMTP 535) + registrasi degrade-aman — commit `3fdc62c`, suite 211/714, +3 regresi, LIVE + DEPLOY.md checklist .env @{2026-09-12}

- [x] kenfa-2.0: form audit + kode pos terikat kecamatan (district_postal_codes 10237 baris, dropdown/readonly/auto) + password show/hide (form-field component) + register phone required + return-request phone tel+required — suite 211/714 hijau, build app-CzZulhLF.css, **deploy pending approval founder** @{2026-09-12}

- [x] kenfa-2.0: fix style hilang di live (deploy vite ke public/build) — aturan baru: build wajib ke 2 direktori @{2026-09-05}
- [x] kenfa-2.0: area akun dirapikan (/akun→/pesanan, tab returns dihapus) + checkout wajib pilih kurir — LIVE `a80b7dc`, 200 test hijau @{2026-09-04}
- [x] kenfa-2.0: /pengembalian jadi fitur navigasi — bottom-nav mobile 7 tab + navbar desktop + slide-in — LIVE `a3bed24`, 197 test hijau @{2026-09-04}
- [x] kenfa-2.0: pra-meeting owner — scheduler produksi restart + fix alur pengembalian (Notifiable + $steps 500) + smoke test live penuh + MEMO refresh — LIVE `16dfae3`, 196 test hijau @{2026-09-04}
- [x] kenfa-2.0: pengembalian publik SATU PINTU (kenfa.id + marketplace) — LIVE `4d9db1a`, 188 test hijau @{2026-08-29}
- [x] Vault health pass: 5/5 issue fixed (4 wanted-note + 1 orphan), log.md dikompres, hook memory-sync idempoten @{2026-08-29}
- [x] kenfa-2.0: bottom nav mobile ala Shopee 6 tab + fix SELinux :z + .htaccess deploy — LIVE, 188 test hijau @{2026-08-27}
- [x] kenfa-2.0: SMTP produksi aktif (465/smtps, QUEUE=sync) — email verify kekirim end-to-end @{2026-08-27}
- [x] Arm cron nightly consolidation + weekly maintenance @{2026-08-25}
- [x] Auto-start Pixel Agents server via user-systemd (pixel-agents.service) @{2026-08-25}
- [x] Setup calendar MCP + kanban board di vault @{2026-08-25}

%% kanban:github.com/mgmeyers/obsidian-kanban %%
