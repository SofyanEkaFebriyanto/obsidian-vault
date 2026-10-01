---
type: project
status: active
last-updated: 2026-10-01
ai-first: true
tags: [noir, flutter, go, voice]
---

## For future agent
Asisten suara full voice-to-voice (tanpa teks sama sekali), ala JARVIS. Mode full-build: Noir yang bangun semuanya, Sofyan pantau via GitHub. Jangan auto-generate code di sini — ini BUKAN mode mentor PKL.

# Noir App

- **Konsep**: full voice-to-voice, tidak ada teks sama sekali. Wake phrase "Hey Noir" (Porcupine), fallback tap avatar.
- **Arsitektur**: Flutter Android client + Go/Gin backend (`noir-brain`), WebSocket realtime, SQLite memory. LLM via `BrainProvider` (default OpenAI-compatible streaming).
- **Avatar states**: `idle → listening → thinking → speaking → idle`. 4 file MP4 lokal (`assets/avatar/*.mp4`), di-gitignore — tidak ikut push.
- **Repo**: `SofyanEkaFebriyanto/noir-app`. Lokal: `~/workspace/noir-app/`. Goal: `goal_11476b3f12cc`.
- **Package**: `id.sefy.noir`, v1.0.0 (versionCode 1).

## Milestone (commit main)
- `5109d72` — milestone 1+2: backend Go, app Flutter, dokumen, deploy, settings long-press avatar, AndroidManifest, systemd unit STB, Go test memori.
- `b081251` — MP4 di-gitignore + dokumentasi aset.
- `582f2ee` — v1.1 full duplex: tap avatar = interupsi + server batalkan stream, continuous conversation 30 detik, perintah lokal `diam`/`stop`/`ulangi`, barge-in suara eksperimental (default mati, tanpa echo cancellation), timeout 12 detik → idle.
- `882dfcb` — scaffolding Android + README Fase 2 (14 file teks; binary PNG launcher + gradle-wrapper.jar TIDAK ikut karena konektor GitHub skip binary).
- `927bd45` — "Lengkapi scaffolding Android + build APK debug berhasil".

## Status 2026-10-01
- **APK debug BERHASIL di-build**: `noir-mobile/build/app/outputs/flutter-apk/app-debug.apk` (~157 MB). `flutter analyze` bersih, `aapt` validasi OK.
- **GitHub Release**: APK di-upload ke release `v1.0.0-debug` (pending otorisasi device flow GitHub saat itu).
- Backend compile-verified (`go build`/`go vet` OK, `/health` + WebSocket hello+history dites langsung). LLM call asli belum bisa — kredensial belum ada.

## Yang masih dibutuhkan (dari Sofyan)
- Custom `hey-noir.ppn` + Picovoice access key (wake word).
- LLM provider / model / credentials.
- Keputusan deploy backend: target awal STB H680P/Armbian via Tailscale. Spek minimum realistis: **1 vCPU, 1 GB RAM, 10 GB disk** (binary Go ~20–30 MB, LLM via API eksternal). VPS 2 CPU/2 GB/20 GB lebih dari cukup.
- Kerjaan di-PAUSE atas permintaan Sofyan ("stop aja bro", 2026-10-01) — lanjut hanya kalau dia minta.

## Gotchas build APK di VM (temuan 2026-10-01)
- Toolchain: Flutter 3.47.5 (`~/workspace/tools/flutter/`), Temurin JDK 17 (`~/workspace/tools/jdk17`), Android SDK (`~/workspace/tools/android-sdk`), platform 35/36, build-tools 35.0.0, NDK 28.2.13676358.
- **Gradle daemon tidak bisa connect** → build via `flutter build apk` gagal. Fix: `GRADLE_OPTS="-Djava.net.preferIPv4Stack=true"`.
- **Proxy blokir Gradle HttpClient** (plugins.gradle.org connection reset) → 600+ artifacts di-download manual via curl lewat proxy ke **local Maven repo** `~/workspace/tools/local-maven-repo` (+ `dl-maven.py`, recursive POM parse). `GRADLE_USER_HOME=~/workspace/tools/gradle-home`.
- **AGP 9.1.0** dari Google Maven; SDK licenses harus di-accept manual (`sdkmanager --licenses`).
- **AAR metadata**: `flutter_voice_processor` & `porcupine_flutter` declare compileSdk 31 < 36 → patch pub-cache (`compileSdk 31` → `36`). Patch ini hilang tiap `flutter pub get` ulang dari nol.
- Jangan rebuild tanpa perlu — APK yang sudah valid langsung dipakai.

READBACK_OK 2026-10-01
