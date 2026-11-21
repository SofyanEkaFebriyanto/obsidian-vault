# Alibaba Cloud Slider Solver

## How It Works
Alibaba Cloud uses baxia/NC slider CAPTCHA inside a cross-origin iframe. Playwright's mouse API can't bypass it — OS-level input is required.

## Linux (Fedora)
```bash
pkexec dnf install -y xdotool
```
- xdotool sends X11 mouse events at the OS level
- Script detects xdotool via `shutil.which("xdotool")`
- Falls back to Playwright mouse if xdotool unavailable (but won't solve)

## uinput Virtual Mouse
Alternative method requiring `modprobe uinput`:
```python
import uinput
device = uinput.Device([uinput.BTN_LEFT, uinput.ABS_X, uinput.ABS_Y])
```
Used in `farm.py` for the humanized bezier-curve drag.

## Key: Prefer xdotool over Playwright
```python
has_xdotool = shutil.which("xdotool") is not None
use_playwright = True
if has_xdotool and UINPUT_AVAILABLE and mouse:
    use_playwright = False  # xdotool path
```
