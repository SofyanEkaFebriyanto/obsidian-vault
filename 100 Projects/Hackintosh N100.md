---
type: project
status: active
last-updated: 2026-08-25
ai-first: true
tags: [hackintosh, n100]
---

## For future agent
Proyek Hackintosh aktif. Sumber kebenaran: hardware report aktual + sesi Hermes (confidence high untuk hardware, medium untuk roadmap). Klaim spesifik yang belum diverifikasi ditandai TBD.

# Hackintosh N100

## Target hardware
- Laptop ADVAN DNN21S-140P3-CS, Intel N100 (Alder Lake-N).
- Host OS: Fedora Linux.
- Internal eMMC tidak didukung → target install ke external HDD/SSD.

## Pendekatan
- Tooling: OpCore-Simplify untuk generate EFI awal + Dortania guide sebagai referensi.
- Workflow Sofyan: edit EFI/config langsung, validasi eksplisit struktur OpenCore, path kext & enabled state, SecureBoot setting, hindari nama generik ("NO NAME").
- Target macOS: Big Sur.

## Status
- jalan — EFI build & instalasi ke external drive.

Terkait: [[100 Projects/Proyek Aktif]], [[500 Resources/000 Resources Index]]
