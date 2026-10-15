---
type: project
status: active
last-updated: 2026-10-13
ai-first: true
tags: [income, stock, ai]
---

# Adobe Stock Contributor

- **Akun aktif** (Member ID 213662686; nama pemegang sesuai instruksi Sofyan). W-8BEN treaty-country Validated s/d 31 Desember 2029; payout PayPal.
- **Goal**: `penghasilan-dari-adobe-stock-contributor` — evaluasi mingguan tiap Senin ~09:42 WIB (mulai 19 Okt 2026): earning, download, status aset, aset terbaik, rekomendasi aksi.
- **Produksi**: target 20 gambar/hari, 5 cron (08:42 / 11:42 / 14:42 / 17:42 / 20:42 WIB), 4 gambar per run. Video generation tidak tersedia di region (403) — fokus gambar dulu.
- **Aturan upload**: upscale ke 2880×1920 (5,53MP — portal tolak <4MP); label "Created using generative AI tools" wajib; hindari logo/merek/IP, teks tertanam, wajah identifiable tanpa release; cek library sebelum retry (upload bisa delay).
- **Scope lock** (akun multi-agent): Noir hanya edit/metadata/submit file miliknya sendiri. Ledger: `goals/penghasilan-dari-adobe-stock-contributor/hidden_files/noir-file-ledger.json`.
- **Riwayat**:
  - 2026-10-13: akun selesai penuh (daftar csg8155@gmail.com, verifikasi email + SMS, W-8BEN valid, payout PayPal); batch 01–04 = 15 gambar Noir diajukan ke review (In review account-wide 37); 5 cron produksi harian dibuat.
  - 2026-10-14: batch-06 2 file (rainforest, hands typing) stuck karena tombol Submit portal disabled seharian — pulih sendiri sore hari, masuk In review; batch-07 4 file (emerald-copper abstract, jogger sunrise, solar-panel, contract signing) di-upload + submit (In review account-wide: 42). Review tab Not accepted: 16 ditolak, 6 milik Noir (quality issues) — implikasi: fokus abstract/komposisi sederhana, photorealistic manusia dihentikan sementara. Temuan teknis: bulk Select-All "Include in submission" tidak persist server-side (scope-lock multi-agent wajib toggle per file).
  - 2026-10-15: **audit portal + pivot total (atas permintaan Sofyan, berlaku mulai 16 Okt)** — skor: 1 approved (spa still life), 11 rejected, batch-08 4 file masih menunggu submit. Pembuktian: 3 file abstract generatif DITOLAK (quality + similar content, koleksi Adobe jenuh); foto orang photorealistic gagal quality (artefak kulit/wajah); yang lolos = motif batik Indonesia (4/4 ilustrasi approved adalah batik), urban farming, still life bersih. Aturan keras baru: **STOP abstract generatif, STOP foto orang photorealistic** — fokus motif batik/budaya Indonesia, urban farming, still life objek bersih; batch-09 (4 abstract) DITAHAN, tidak jadi upload (hemat kuota mingguan; limit mingguan shared antar agent, Upload button dikunci sampai reset otomatis). Evaluasi: `goals/penghasilan-dari-adobe-stock-contributor/hidden_files/APPROVAL-EVALUATION-2026-10-15.md`. Anomali: 13 file milik Noir tidak ada di tab mana pun (glitch portal vs terhapus) — perlu cek manual, ID tercatat di ledger/AGENTS.md.

Terkait: goal `penghasilan-dari-adobe-stock-contributor`, [[100 Projects/Portfolio]]
