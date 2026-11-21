# Agent

Pusat skill dan katalog MCP untuk Claude Code, Hermes, Codex, dan OpenCode.

## Isi

- `skills/`: 262 paket skill bersama.
- `sources/`: 161 varian sumber yang tetap disimpan.
- `manifest/skill-sources.json`: asal paket dan hash impor.
- `mcp/catalog.yaml`: 13 definisi MCP, dengan override transport per agent.

Prioritas konflik: Claude Code → Hermes → Codex → OpenCode → shared skills. Plugin dan skill bawaan tetap aktif, sehingga masing-masing agent masih bisa menyediakan tambahan native.

## Pemakaian

Edit paket di `skills/`; symlink agent menunjuk langsung ke sini. Untuk skill baru, buat folder dengan `SKILL.md`, lalu daftarkan link baru:

```sh
python3 scripts/skill_sync.py --sync-links --apply
```

Hermes membaca folder ini melalui `skills.external_dirs` dan menulis skill baru lewat `skills.create_dir`. OpenCode memakai sumber eksplisit; Claude/Codex memakai link user/shared.

Setelah mengedit katalog MCP:

```sh
python3 mcp/sync.py
python3 mcp/sync.py --apply
python3 mcp/sync.py --check
```

Perintah pertama hanya dry-run. Server yang dihapus dari katalog akan dihapus hanya jika sebelumnya terdaftar sebagai server terkelola. Server pribadi di luar katalog tetap dipertahankan. Skrip memerlukan Python 3.11+ dan PyYAML yang sudah tersedia di mesin ini.

Kredensial tidak disimpan di katalog. Server GitHub dan MySQL memerlukan `GITHUB_PERSONAL_ACCESS_TOKEN` dan `MYSQL_PASS` di environment agent yang belum memiliki kredensial lokal. OAuth tetap perlu dilakukan terpisah di masing-masing aplikasi; OpenCode menggunakan `/mcps`, Claude `/mcp`.

## Verifikasi dan batasan

16 tes migrasi/adaptor lulus. Keempat konfigurasi memuat 13 nama MCP dan check sinkronisasi tidak menemukan drift. Semua 262 paket terhubung ke folder discovery user/shared; Hermes mengiklankan 261 entri pada pemeriksaan runtime, sementara `sdlc-review` tidak diiklankan oleh filter runtime Hermes.

Lima metadata nama skill yang bentrok disamakan dengan ID folder agar tidak tersembunyi di Hermes. Satu dokumen lama mengandung kredensial yang dikenal; nilai tersebut diganti placeholder. Instruksi lainnya tidak ditulis ulang, sehingga beberapa skill masih merujuk tool khusus agent asal.

Status koneksi OpenCode saat pemeriksaan: 11 tersambung; filesystem timeout dan mysql_local keluar saat startup. Codex mencatat Context7, Figma, dan Exa sebagai belum login. Ini berbeda dari keberadaan konfigurasi.

Parser konfigurasi OpenCode pada skrip ini menerima JSON biasa; jangan menambahkan komentar/trailing comma ke file yang disinkronkan tanpa menambahkan parser JSONC. Importer awal memakai lokasi plugin yang diinventarisasi saat migrasi; gunakan `--sync-links` untuk pendaftaran skill selanjutnya, bukan mengulang impor awal.

## Backup dan pemulihan

Backup konfigurasi awal privat berada di `~/.local/state/agent-vault/backups/20261121-181445-initial/`; `paths.json` memetakan file asal. Backup tambahan dibuat saat sync mengubah konfigurasi. Direktori skill asal masih disimpan sebagai sibling tersembunyi `.nama.agent-backup` di lokasi sebelumnya.

Untuk rollback: hentikan agent, pulihkan konfigurasi dari backup yang dipilih, lalu ganti hanya symlink migrasi dengan direktori `.agent-backup` pasangannya. Jangan menimpa perubahan baru; bandingkan terlebih dahulu. Salinan plugin dan Codex `.system` tidak diubah. Tidak ada commit Git dibuat.
