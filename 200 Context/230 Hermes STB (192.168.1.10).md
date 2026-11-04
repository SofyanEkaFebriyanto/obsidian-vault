---
type: context
status: active
last-updated: 2026-11-05
author: by hermes stb
tags: [infrastruktur, hermes, home-server, caddy]
---

## For future agent
STB H680P yang sama dengan entry lama di [[200 Context/220 Infrastruktur|Infrastruktur]] (konfirmasi Sofyan 2026-11-05: mesin yang sama, baru reinstall ke Armbian). Stack lama Ubuntu 26.04/CasaOS/Docker sudah pensiun; konfigurasi aktif sekarang ada di note ini.

# Hermes STB (192.168.1.10)

## Identitas & spek (audit 2026-11-05)
- **Mesin**: HG680P (STB), Armbian OS 26.11.0 noble (Ubuntu 24.04 LTS), kernel 6.12.111-ophub aarch64. User `stb`.
- **Spek**: 4x ARM Cortex-A53 (~1.5 GHz), RAM 1.8 GiB (no swap), eMMC 6.0G sistem.
- **HDD**: 500GB via enclosure USB Initio INIC-1618L (`13fd:0840`). Model HGST HTS545050A7E380, `/dev/sda1` ext4 LABEL `DATA`, mount `/mnt`, kapasitas bersih ~458G (435G kosong). UUID `3f3d4c98-1e4a-470b-b610-648637b480e7`.
- **Jaringan**: eth0 static `192.168.1.10/24`, gateway `192.168.1.1`. ED25519 host key `SHA256:uIsfwF349yy6CiRmWhJqUN+dH1rQPXFFNm3AnZInU5M`.
- **Hermes**: gateway Hermes jalan di sini (Python 3.14 tool, Node 26). RAM Hermes ~300MB — sisa headroom kecil.

## HDD layout (/mnt)
- `www/` root website statis, `projects/` git clone (vault copy di `projects/obsidian-vault`), `data/`, `backups/`, `media/`, `apps/`, `cache/` (pip/npm/uv), `logs/`, `bin/` (binary user-space), `caddy/`.
- Symlink hemat eMMC: `~/projects` → `/mnt/projects`, `~/www` → `/mnt/www`.

## Web hosting (Caddy)
- Caddy v2.11.7 static arm64 di `/mnt/bin/caddy`, user-systemd `caddy.service` (enabled + linger), serve `/mnt/www` di `:8080`, ~10MB RAM, verified `curl /health` → `ok` di localhost dan `192.168.1.10:8080`.
- Bukan system service; port 80 belum diambil (butuh root). Tunnel/domain Cloudflare masih rencana — domain kandidat: sefy.my.id, sefy.web.id, sefy.biz.id, noirstudio.web.id, sofyan.bond, sofyan.cyou, noirstudio.bond, noirstudio.cyou (tambah 1 subdomain saja).

## Optimasi eMMC (2026-11-05)
- Awalnya 94% (388M kosong). Cache pip/npm/uv dipindah ke `/mnt/cache`; stale venv Hermes dipindah ke `/mnt/apps/hermes-env-backup/` (backup, belum hapus permanen).
- Hasil: **87%, 825M kosong** (~437M terbebas). `apt clean` masih pending — skrip `~/CLEAN_ROOT.sh` + `~/SET_STATIC_IP.sh` + `~/SETUP_ROOT.sh` di-run manual oleh user via sudo.

## Gotcha USB enclosure
- Bridge `13fd:0840` kadang enumerate tanpa disk (`/dev/sda` hilang, error -71 / "Cannot enable. Maybe the USB cable is bad?") — gejala power/kabel marginal di board ARM. Solusi: kabel pendek bagus, port lain, hub powered. Spin-up "tiitt" + "krek krek" = normal HDD 2.5".
- Cek urutan: `lsusb` → `lsblk` + `ls /dev/sd*` → `dmesg | tail -40` + `blkid`.

Terkait: [[200 Context/220 Infrastruktur|Infrastruktur]], [[400 Daily/2026-11-05|Daily 2026-11-05]]
