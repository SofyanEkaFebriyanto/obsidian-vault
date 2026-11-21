---
name: linux-desktop-performance
description: "Triage and cleanup slow Linux desktop performance."
version: 0.1.0
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [linux, performance, desktop, systemd, docker, memory, cpu]
    related_skills: [systematic-debugging]
---

# Linux Desktop Performance

## Overview

Local Linux workstations slow down because they carry too many concurrent CPU or memory-heavy components: desktop shell, browsers and browser automation, multiple Docker stacks, background services, and indexing jobs.

This skill captures a repeatable triage-to-cleanup workflow with low-risk actions that can be done quickly and safely.

## When to Use

- User says laptop/desktop is heavy, slow, or laggy
- High load average on a small-core CPU
- Swap is active despite moderate RAM
- Chrome has many internal processes despite few tabs
- Multiple Docker containers running on a workstation
- KDE/Plasma services consuming CPU
- krunner/baloo spamming logs or consuming resources

## Principles

1. Start with evidence, not hunches.
2. Prefer stopping/relieving load over blind fixes.
3. Kill/restart the heaviest offenders first.
4. Do not delete data, uninstall packages, or drop containers the user might need.
5. If a service is clearly unusable, stop it first; ask before disabling permanently.

## Triage Workflow

### Step 1: System Snapshot

Collect evidence in parallel:

```bash
uptime
free -h
swapon --show
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -20
ps -eo pid,pcpu,pmem,comm --sort=-pmem | head -20
systemctl list-units --type=service --state=running --no-pager
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
```

Look for:
- Load average above core count for sustained periods
- Swap usage > 0 while free RAM is small
- Single browser with high CPU across multiple internal processes
- Multiple Docker containers, especially idle databases
- Background services with repeated errors

### Step 2: Quick Wins

Apply in this order:

1. **Browser / Chrome**
   - Chrome renderers + GPU + network service can total >100% CPU even with one tab.
   - If browser automation was used recently, expect orphaned renderer sessions.
   - Normal quit preferred; only `pkill chrome` when user asks for aggressive cleanup or confirms no active browsing.

2. **Non-critical systemd services**
   - Typical non-essential: `bluetooth.service`, `cups.service`, `ModemManager.service`, `avahi-daemon.service`, geoclue agents, discovery notifiers.
   - Stop first, disable later after confirming no regression.

3. **Idle Docker containers**
   - Keep the project the user is actively working on.
   - Stop other stacks: secondary databases, queues, schedulers, phpmyadmin instances, test containers.

4. **Broken desktop components**
   - `krunner` often spams errors when configured terminal/launcher is missing.
   - Kill the process; investigate KDE runner config if it respawns and continues spamming.

### Step 3: Swap and Memory Pressure

If swap is active after Step 2:

- Identify the biggest memory consumers from the snapshot.
- Restarting heavy processes often drops swap quickly.
- If swap remains high, advise closing or suspending unused apps.
- Do not tune vm.swappiness or add zswap without explicit user direction.

### Step 4: Validate

Re-run snapshot and compare:

```bash
free -h
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -10
uptime
```

Load should drop and free RAM should rise. If not, continue cleanup only after user approval.

## Hardware-Specific Notes

- **Intel N100 / 8GB-class machines**: 4 E-cores plus 8GB RAM is enough for desktop + 1 local DB + 1 browser tab. Multi-Docker + Chrome + KDE easily saturates both. Triage Docker count first.
- **KDE Plasma + Wayland**: `kwin_wayland`, `plasmashell`, and KDE services are normal background load. Do not assume they are the problem until Chrome and Docker are reduced.

## Pitfalls

- Chrome main process CPU is not the full story; renderers and GPU process can dominate.
- `docker stats --no-stream` shows point-in-time usage, not pressure. Use swap and `free -h` for pressure.
- Stopping services without checking importance can surprise users with implicit dependencies.
- Aggressive `pkill chrome` is acceptable only when the user explicitly asks for cleanup or is not actively browsing.

## Disk Space Cleanup

### When to Use

- User says disk is full or nearly full
- `df -h /` shows >80% used
- User says "beresin disk" / "disk mau penuh"

### Triage Order

Run these in parallel to map the problem:

```bash
df -h /
du -sh ~/Documents/* ~/Downloads/* ~/Games/* 2>/dev/null | sort -rh | head -20
du -sh ~/.cache/* 2>/dev/null | sort -rh | head -15
du -sh ~/.local/share/* 2>/dev/null | sort -rh | head -15
docker system df 2>/dev/null
```

### Safe Reclaim (no confirmation needed)

These are always safe — all rebuild/re-download automatically:

```bash
# Trash
rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/info/*

# Package manager cache
sudo dnf clean all

# Python / Go / Node build caches
rm -rf ~/.cache/pip ~/.cache/go-build ~/.cache/uv ~/.cache/node-gyp ~/.cache/appstream ~/.cache/libdnf5

# Docker build cache (keeps active images/containers intact)
docker builder prune -f

# Dangling Docker images + unused volumes
docker image prune -f && docker volume prune -f

# Browser automation caches (camoufox, playwright, puppeteer, electron)
rm -rf ~/.cache/camoufox ~/.cache/ms-playwright ~/.cache/ms-playwright-mcp ~/.cache/ms-playwright-go ~/.cache/puppeteer ~/.cache/electron

# Chrome cache
rm -rf ~/.cache/google-chrome
```

Typical yield: 8–15GB on a dev machine with Docker + browser automation.

### Needs Confirmation Before Deleting

Present these to the user grouped by category:

- Docker images not currently running (list with `docker images` vs `docker ps`)
- `~/Downloads/` ISOs, installer .exe, .tar.gz for already-installed apps
- `~/Games/` — specific game folders
- `~/.local/share/bottles/` — Wine bottles (MT5, Windows apps)
- `~/.local/share/flatpak` — unneeded flatpak apps
- `~/Documents/flas/` or backup dirs with archived Windows executables

### Docker Image Removal Pitfall

`docker rmi` fails if a **stopped container** still references the image.
Always `docker ps -a` first, then `docker rm <stopped_container>` before `docker rmi`.

```bash
# Check what's stopped
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Remove stopped container first
docker rm <container_name>

# Then remove image
docker rmi <image_name>
```

### User Preference

- User says "hapus aja semua yang aman" → be decisive, execute all clearly-safe items without asking per-item
- Ask once, grouped by risk category, for anything that could lose data
- Keep going without stopping to explain each step — say "continue" signals they want action, not narration

## References

- `references/n100-fedora-kde-notes.md` — session-specific observations for N100 + Fedora KDE + Docker + Chrome automation cleanup
- `references/disk-cleanup-hogs.md` — common space hogs on Fedora + Docker + browser-automation dev machines