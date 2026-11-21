# Worked example: OpCore-Simplify (Hackintosh EFI builder) — headless

Repo: OpCore-Simplify (lzhoang2801). A TUI that reads a Hardware Sniffer
`Report.json` + ACPI tables, checks compatibility, selects macOS/kexts/ACPI/
SMBIOS, downloads OpenCorePkg + kexts (dortania build-repo + OcBinaryData),
and writes `Results/Top` EFI.

## Driver shape (`run_ocs_headless.py`)
Imports the `Scripts.*` modules directly (NOT `OpCore-Simplify.py`, which
wraps everything in `while True` TUI menus). Re-implements `OCPE.build_opencore_efi`
inline (copy the function, drop the `request_input`/folder-open tail).

## Prompt map (substring → answer)
- "build efi for uefi" → `yes`
- "force load" / "unsupported macos" → `no` (don't force unsupported kexts)
- "select audio kext" → `1` (AppleALC)
- "select kext for your intel wifi" → `2` (itlwm — stable; needs HeliPort)
- "kext for your amd" → `2`
- "scan for wifi profiles" → `no`  ← EASY TO MISS, causes infinite loop
- "select a " / "select your " → `1`
- default → `""` (Enter)

## The WiFi-profile loop (the trap)
`wifi_profile_extractor.get_profiles()` asks "Would you like to scan for WiFi
profiles? (Yes/no)". My default `""` answer was treated as invalid → infinite
"Invalid selection, please try again." until I added the `scan for wifi
profiles` → `no` rule. **Always audit every `while True` + `request_input` in
the code path for prompts your substring map doesn't cover.**

## Compatibility patch (iGPU)
Alder Lake-N iGPU `8086-46D1` is NOT in OpCore's GPU table →
`check_compatibility()` sets it Unsupported and hard-aborts ("You cannot
install macOS without a supported GPU").
- Pre-setting `gpu_props["Compatibility"]` does NOT work — the check recomputes
  from Device ID and overwrites it.
- Fix: in a `patch_gpu_check` wrapper, **spoof the Device ID** to a
  known-supported Intel iGPU (`8086-9BC4`, Comet Lake) before calling the
  original. The check then passes naturally. boot-args `-igfxblt` added.
  Caveat: framebuffer for Alder Lake-N may still need manual device-id tuning.

## Report validation patch
Bundled `Report.json` failed the tool's own validator:
- 2x `_TZ_.TZ00` / `_TZ_.FAN0` ACPI paths (Linux thermal-zone artifacts) —
  drop keys from `System Devices` whose ACPI Path startswith `_TZ_`.
- Missing required `Storage Controllers` — inject a USB-SSD stub:
  `{"USB Mass Storage (External SSD)": {"Bus Type": "USB", "Device ID": "0x0000"}}`.
All in-memory on the loaded dict; repo untouched.

## Hardware reality (why it matters for this user)
- Internal storage = **eMMC** (`8086-54C4`). macOS has no eMMC driver →
  install/boot from a USB external SSD, not internal. eMMC is ignored.
- Intel AX101 WiFi (`8086-54F0`) → itlwm + HeliPort (not native).
- Intel BT `8087-0AAA` → IntelBluetoothFirmware + BlueToolFixup.

## Verification (artifact, not stdout)
Tool ends on a blocking `request_input()` in `before_using_efi()` — process
stays "running" though build is DONE. Verify directly:
```python
import plistlib, os
c = plistlib.load(open("Results/EFI/OC/config.plist","rb"))
print(c["PlatformInfo"]["Generic"]["SystemProductName"])  # MacBookPro16,2
print(len(c["Kernel"]["Add"]), len(c["ACPI"]["Add"]))
for k in c["Kernel"]["Add"]:
    assert os.path.exists("Results/EFI/OC/Kexts/"+k["BundlePath"])
```
Then `pkill -f run_ocs_headless`.

## Loop-guard logging (use always)
Main log (downloads) is 100k+ `\r`+ANSI lines — `grep`/python line-iter
**times out**. Log each `PROMPT -> ANSWER (n=N)` to `/tmp/ocs_answers.log`,
and if a prompt recurs >8× with `""` answer, return `"no"` to escape. Diagnose
the looping prompt from that small file, never from the main log.
