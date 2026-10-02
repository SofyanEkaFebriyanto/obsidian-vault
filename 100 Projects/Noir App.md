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

- **Konsep**: full voice-to-voice, tidak ada teks sama sekali. Wake phrase "Hey Noir" (Porcupine), fallback tap avatar.
- **Arsitektur**: Flutter Android client + Go/Gin backend (`noir-brain`), WebSocket realtime, SQLite memory. LLM via `BrainProvider` (default OpenAI-compatible streaming).
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

## Status 2026-10-02
- **VM reset**: Flutter SDK, Android SDK, JDK, Go, dan `.git` di `~/workspace/noir-app/` hilang. Toolchain di-install ulang + rebuild APK via subagent. Root cause Gradle daemon hang = socket loopback IPv6-mapped hang di sandbox; fix `JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"` via env var (tercatat di `~/AGENTS.md`).
- **Bug TTS (bisu)**: HP Sofyan tidak bersuara padahal backend sehat (WS test langsung: streaming token OK). Root cause: flutter_tts gagal diam-diam, kemungkinan engine TTS default HP tidak cocok dengan `id-ID`. Patch di `c06a675`.
- **APK debug rebuild**: `~/workspace/your_files/noir-app-debug.apk` (~174 MB), patch TTS terverifikasi di `kernel_blob.bin`, `aapt` valid.
- **GitHub Release**: APK baru di-upload ke release `v1.0.1-debug` (ganti release lama `v1.0.0-debug` yang masih bawa bug bisu).
- **Backend LIVE di STB** (100.84.6.21): service systemd `noir-brain` aktif, `/health` OK, WS `ws://100.84.6.21:8080/ws`. Deploy `c06a675` ke STB: `git pull && go build -o /opt/noir-brain/noir-brain ./cmd/server && sudo systemctl restart noir-brain`.

## Yang masih dibutuhkan (dari Sofyan)
- Custom `hey-noir.ppn` + Picovoice access key (wake word) — upgrade Picovoice masih dalam review.
- Test install APK baru di HP (install sebelumnya gagal "problem parsing package" — kemungkinan download corrupt; cek ukuran file 174 MB).
- Keputusan sinkronisasi persona/memori Noir ke system prompt backend (ditawarkan, belum disetujui).

## Gotchas build APK di VM (temuan 2026-10-01)
- Toolchain: Flutter 3.47.5 (`~/workspace/tools/flutter/`), Temurin JDK 17 (`~/workspace/tools/jdk17`), Android SDK (`~/workspace/tools/android-sdk`), platform 35/36, build-tools 35.0.0, NDK 28.2.13676358.
- **Gradle daemon tidak bisa connect** → build via `flutter build apk` gagal. Fix: `GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"`.
- **Proxy blokir Gradle HttpClient** (plugins.gradle.org connection reset) → 600+ artifacts di-download manual via curl lewat proxy ke **local Maven repo** `~/workspace/tools/local-maven-repo` (+ `dl-maven.py`, recursive POM parse). `GRADLE_USER_HOME=~/workspace/tools/gradle-home`.
- **AGP 9.1.0** dari Google Maven; SDK licenses harus di-accept manual (`sdkmanager --licenses`).
- **AAR metadata**: `flutter_voice_processor` & `porcupine_flutter` declare compileSdk 31 < 36 → patch pub-cache (`compileSdk 31` → `36`). Patch ini hilang tiap `flutter pub get` ulang dari nol.
- Jangan rebuild tanpa perlu — APK yang sudah valid langsung dipakai.

READBACK_OK 2026-10-01
