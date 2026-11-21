# Common Disk Hogs — Fedora + Docker + Browser Automation Dev Machine

Observed on: Fedora / KDE / Intel N100 / 115GB eMMC

## Typical Layout at ~85% Full

| Path | Size | Safe to Delete? |
|------|------|-----------------|
| `~/.local/share/Trash/` | 3–5GB | Yes, always |
| `~/.cache/pip` | 300–500MB | Yes |
| `~/.cache/go-build` | 500MB–1GB | Yes |
| `~/.cache/uv` | 500MB–1GB | Yes |
| `~/.cache/node-gyp` | 50–200MB | Yes |
| `~/.cache/camoufox` | 1–2GB | Yes (re-downloads) |
| `~/.cache/ms-playwright*` | 600MB–1GB | Yes (re-downloads) |
| `~/.cache/puppeteer` | 500MB–1GB | Yes (re-downloads) |
| `~/.cache/google-chrome` | 1–2GB | Yes |
| `~/.cache/electron` | 100–300MB | Yes |
| `/var/cache/dnf` + `/var/cache/libdnf5` | 800MB–1GB | Yes (`dnf clean all`) |
| Docker build cache | 5–10GB | Yes (`docker builder prune -f`) |
| Docker stopped containers | varies | Yes after confirming not needed |
| Docker unused images | 1–3GB | Confirm first |
| `~/Downloads/*.iso` | 2–5GB | Confirm |
| `~/Downloads/*.tar.gz` (installed apps) | 200–500MB each | Confirm (usually yes) |
| `~/Documents/flas/` (Windows exes, movies) | 10–15GB | Confirm |
| `~/.local/share/bottles/` | 5–6GB | Confirm (Wine prefix) |
| `~/Games/` | varies | Confirm |

## Sequence That Works

1. Trash + caches → instant 5–10GB, zero risk
2. Docker build cache → 2–5GB
3. Docker stopped containers + orphan images → 1–3GB (check `docker ps -a` first)
4. Downloads + flas Windows binaries → ask user once, grouped

## Session Notes (2026-09-22)

- Machine: `/dev/mmcblk1p3` 115GB, started at 88% (99GB used)
- After safe cache + docker cleanup: freed ~9GB → 81%
- After docker image/container cleanup + Downloads/flas: freed further → 73% (82GB used, 31GB free)
- MT5 bottle at `~/.local/share/bottles/bottles/mt5` = 5.3GB — user keeps it
- `twopointhospital` game = 8.6GB — user to decide
- Remaining reclaimable: ~14GB if user approves Games + bottles + remaining docker images
