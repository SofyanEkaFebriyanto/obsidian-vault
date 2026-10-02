---
type: project
status: active
last-updated: 2026-10-02
ai-first: true
tags: [noir, flutter, go, voice]
---

## For future agent
Asisten suara full voice-to-voice (tanpa teks sama sekali), ala JARVIS. Mode full-build: Noir yang bangun semuanya, Sofyan pantau via GitHub. Jangan auto-generate code di sini — ini BUKAN mode mentor PKL.

# Noir App

- **Konsep**: full voice-to-voice, tidak ada teks sama sekali. Wake word: pindah dari Porcupine ke **openWakeWord** ("hey jarvis", pre-trained, gratis, on-device) — implementasi di-PAUSE saat pivot ke web. Fallback: tap/klik avatar.
- **Arsitektur**: Go/Gin backend (`noir-brain`), WebSocket realtime, SQLite memory. LLM via `BrainProvider` (default OpenAI-compatible streaming). **Agent loop**: LLM + tool calling (`internal/agent/`) — bisa eksekusi di STB (waktu, sysinfo, exec, read/write file, service). Client: Flutter Android (pause) + **web UI** (aktif, diserve dari backend via go:embed di `/`).
- **Arsitektur audio (penting!)**: STT on-device (HP) → LLM terima/kirim TEKS → TTS on-device (HP). LLM tidak perlu "support TTS". Model bebas diganti selama API-nya OpenAI-compatible + streaming (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` di `.env`). Web: STT = Web Speech API, TTS = speechSynthesis browser. **Catatan**: Web Speech API butuh secure context — akses via `http://100.84.6.21:8080` harus didaftarkan di `chrome://flags` → "Insecure origins treated as secure".
- **Arsitektur audio (penting!)**: STT on-device (HP) → LLM terima/kirim TEKS → TTS on-device (HP). LLM tidak perlu "support TTS". Model bebas diganti selama API-nya OpenAI-compatible + streaming (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` di `.env`).
- **Model LLM**: `space-bunny` = Space Bunny Alpha (`stealth/space-bunny-alpha`, OpenRouter), stealth model rilis 23 Sep 2026, gratis selama preview, OpenAI-compatible + streaming. Catatan: reasoning tidak bisa dimatikan total → kadang terasa mikir dulu sebelum jawab.
- **Avatar states**: `idle → listening → thinking → speaking → idle`. 4 file MP4 lokal (`assets/avatar/*.mp4`), di-gitignore — tidak ikut push.
- **Repo**: `SofyanEkaFebriyanto/noir-app`. Lokal: `~/workspace/noir-app/` (+ clone git persisten di `~/workspace/noir-app-git/`). Goal: `goal_11476b3f12cc`.
- **Package**: `id.sefy.noir`, v1.0.0 (versionCode 1).

## Milestone (commit main)
- `5109d72` — milestone 1+2: backend Go, app Flutter, dokumen, deploy, settings long-press avatar, AndroidManifest, systemd unit STB, Go test memori.
- `b081251` — MP4 di-gitignore + dokumentasi aset.
- `582f2ee` — v1.1 full duplex: tap avatar = interupsi + server batalkan stream, continuous conversation 30 detik, perintah lokal `diam`/`stop`/`ulangi`, barge-in suara eksperimental (default mati, tanpa echo cancellation), timeout 12 detik → idle.
- `882dfcb` — scaffolding Android + README Fase 2.
- `835b074` — scaffolding Android lengkap: `app/build.gradle.kts` (selama ini belum ke-commit, fresh clone nggak bisa build!), launcher PNG, gradle-wrapper.jar (force-add), mode gradlew, .gitignore Flutter.
- `c06a675` — TTS anti-bisu (pilih engine Google TTS, fallback bahasa id-ID→id→en-US→en-GB, volume 1.0, snackbar error di debug build) + endpoint OpenAI-compatible (`POST /v1/chat/completions` streaming SSE, `GET /v1/models`, stateless terhadap memory store).
- `c869004` — **web UI voice** (`noir-brain/internal/api/web/`: index.html/app.js/style.css), di-embed ke binary via go:embed, diserve di `/`. Protokol WS sama dengan mobile. Avatar CSS 4 state, tap untuk bicara/interupsi.
- `4b86e5d` — **agent loop ala Hermes**: LLM + tool calling (`internal/agent/`). Tools v1: waktu, sysinfo, exec, read_file, write_file, list_dir, service_status, service_restart. Safety: denylist destruktif, blokir file kredensial, write dilarang di /etc /boot /proc /sys /dev, service allowlist (`AGENT_SERVICES`), operation log `data/agent.log`. Config: `AGENT_ENABLED` (default true), `AGENT_MAX_STEPS` (8). Test lolos (safety + mock LLM).

## Status 2026-10-02 (update sore)
- **Web UI LIVE**: `http://100.84.6.21:8080` di Chrome HP (via Tailscale). STT sempat gagal diam-diam karena HTTP bukan secure context → fix via `chrome://flags` → "Insecure origins treated as secure" → `http://100.84.6.21:8080` → relaunch. Sekarang ngobrol lancar.
- **Agent VERIFIED**: commit `4b86e5d` ter-deploy di STB. Sofyan tes voice ("cek uptime STB") — Noir pakai tool beneran dan jawab angka yang sesuai. Bukan ngarang.
- **F-12 SELESAI** (commit `368f223`): memori fakta jangka panjang — tiap percakapan selesai, LLM ekstrak fakta (preferensi, proyek, rencana) → SQLite → disuntik ke system prompt sesi berikut. `/v1/chat/completions` tetap stateless.
- **F-13 SELESAI** (commit `368f223`): "Tentang Noir" — GET/PUT/DELETE `/v1/persona` + `persona.html` (link kecil di bawah avatar). Lihat/edit/reset persona, tersimpan di STB.
- **Blueprint + PRD diupdate**: status fase, pivot web, agent v1, wake word Porcupine → openWakeWord ("hey jarvis").
- **F-12/F-13 DEPLOYED** 2026-10-02 malam via SSH (commit `368f223`, verified `/v1/persona` OK).
- **F-14 SELESAI + DEPLOYED** (2026-10-02 ~23:37, commit `cf5fbf8`): proactive ping in-app only — ticker 45 mnt, LLM mutusin sapa/diem, broadcast WS (toast + auto-speak bila idle), jam sepi 23–6 WIB. Deploy langsung oleh Noir via SSH (git pull → build → restart); verified: `/health` OK, `/v1/persona` OK, log `proactive: aktif`, `/v1/chat/completions` non-stream OK (jawab "halo").
- **GitHub tanpa kode**: SSH key `noir-vm-push` terdaftar — push langsung, tidak perlu device code lagi.
- **Picovoice MATI**: free tier ditutup total 30 Jun 2026, tidak ada tier non-komersial. Request trial Sofyan ditolak. Migrasi ke openWakeWord ("hey jarvis") dipilih, riset selesai, implementasi di-PAUSE saat pivot ke web.
- VM reset / rebuild APK / bug TTS: lihat catatan di bawah (masih valid).

## Status 2026-10-02 (pagi)
- **VM reset**: Flutter SDK, Android SDK, JDK, Go, dan `.git` di `~/workspace/noir-app/` hilang. Toolchain di-install ulang + rebuild APK via subagent. Root cause Gradle daemon hang = socket loopback IPv6-mapped hang di sandbox; fix `JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"` via env var (tercatat di `~/AGENTS.md`).
- **Bug TTS (bisu)**: HP Sofyan tidak bersuara padahal backend sehat (WS test langsung: streaming token OK). Root cause: flutter_tts gagal diam-diam, kemungkinan engine TTS default HP tidak cocok dengan `id-ID`. Patch di `c06a675`.
- **APK debug rebuild**: `~/workspace/your_files/noir-app-debug.apk` (~174 MB), patch TTS terverifikasi di `kernel_blob.bin`, `aapt` valid.
- **GitHub Release**: APK baru di-upload ke release `v1.0.1-debug` (ganti release lama `v1.0.0-debug` yang masih bawa bug bisu).
- **Backend LIVE di STB** (100.84.6.21): service systemd `noir-brain` aktif, `/health` OK, WS `ws://100.84.6.21:8080/ws`. Deploy `c06a675` ke STB: `git pull && go build -o /opt/noir-brain/noir-brain ./cmd/server && sudo systemctl restart noir-brain`.

## Yang masih dibutuhkan / berikutnya
- Deploy F-12/F-13 ke STB (git pull + build + restart).
- F-14 proactive ping — butuh keputusan pola notifikasi dari Sofyan (notifikasi browser vs pull).
- Lanjutan openWakeWord ("hey jarvis") kalau APK dilanjut lagi (working tree parsial ada di `~/workspace/noir-app/noir-mobile/`, uncommitted).
- Konektor ala Muse (Gmail/Kalender/dsb.) untuk noir-app — level berikutnya setelah STB-local solid.
- Test install APK baru di HP (kemarin gagal "problem parsing package" — kemungkinan download corrupt; cek ukuran 174 MB). Saat ini fokus web.
- Keputusan sinkronisasi persona/memori Noir ke system prompt backend (ditawarkan, belum disetujui).

## Gotchas build APK di VM (temuan 2026-10-01)
- Toolchain: Flutter 3.47.5 (`~/workspace/tools/flutter/`), Temurin JDK 17 (`~/workspace/tools/jdk17`), Android SDK (`~/workspace/tools/android-sdk`), platform 35/36, build-tools 35.0.0, NDK 28.2.13676358.
- **Gradle daemon tidak bisa connect** → build via `flutter build apk` gagal. Fix: `GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"`.
- **Proxy blokir Gradle HttpClient** (plugins.gradle.org connection reset) → 600+ artifacts di-download manual via curl lewat proxy ke **local Maven repo** `~/workspace/tools/local-maven-repo` (+ `dl-maven.py`, recursive POM parse). `GRADLE_USER_HOME=~/workspace/tools/gradle-home`.
- **AGP 9.1.0** dari Google Maven; SDK licenses harus di-accept manual (`sdkmanager --licenses`).
- **AAR metadata**: `flutter_voice_processor` & `porcupine_flutter` declare compileSdk 31 < 36 → patch pub-cache (`compileSdk 31` → `36`). Patch ini hilang tiap `flutter pub get` ulang dari nol.
- Jangan rebuild tanpa perlu — APK yang sudah valid langsung dipakai.

READBACK_OK 2026-10-01
