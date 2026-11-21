# Slider CAPTCHA Solving (Baxia/NC)

## Overview
Alibaba Cloud uses Alibaba Cloud Security (baxia) slider CAPTCHA with `nc_1_n1z` handle.
The slider is inside a cross-origin iframe — standard Playwright/Selenium mouse events are blocked.

## Methods (tested: Linux+Xvfb)

### 1. Playwright Mouse API — FAILS ❌
- `page.mouse.move()` + `page.mouse.down()` + `page.mouse.move()` + `page.mouse.up()`
- Does NOT work on baxia slider inside cross-origin iframe
- The drag visually shows but the server rejects it

### 2. xdotool + uinput — WORKS ✅ (Linux only)
```
# Install
sudo dnf install xdotool            # Fedora
sudo apt install xdotool            # Debian
pip install python-uinput
sudo modprobe uinput

# Usage in Xvfb
subprocess.run(['xdotool', 'mousemove', str(x), str(y)])
subprocess.run(['xdotool', 'mousedown', '1'])
# ... drag steps ...
subprocess.run(['xdotool', 'mouseup', '1'])
```

### 3. PyAutoGUI — WORKS ✅ (Windows/Linux)
- `pyautogui.moveTo()` + `pyautogui.drag()`

### 4. JS Fallback — HELPER ❌ (not sufficient alone)
- Dispatching MouseEvent via JavaScript inside the frame
- Fails on cross-origin iframes in most cases
- Sometimes works after xdotool drag moves the handle

## Detection
- Look for `#nc_1_n1z` or `.btn_slide` in passport.alibabacloud.com frames
- Punish iframe appears when CAPTCHA triggers: `check_enter_email`
- Track width: typically ~464px drag distance

## Best Practice
1. Try Playwright mouse first (fast, sometimes works on simpler sliders)
2. Fall back to xdotool + uinput (Linux/Xvfb)
3. After xdotool drag, run JS fallback dispatch for baxia-specific handling
4. Check slider disappearance: `find_slider_handle()` returns None = solved

## farm_headless.py Specific
- Auto-slider solver is **commented out** by default (lines 1241-1243 in `handle_captcha`)
- Must uncomment `# if AUTO_CAPTCHA and solve_baxia_slider_dynamic(...)` to enable
- Then run with `--auto-captcha` flag
- The `solve_baxia_slider_dynamic()` function tries all methods in priority order
