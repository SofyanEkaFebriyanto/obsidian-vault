---
name: headless-cli-runner
description: Drive interactive input()-driven TUI/CLI tools non-interactively from an automated context (pipelines, background, cron) — monkeypatch the input sink, auto-answer prompts, patch validation/compatibility in-memory, and diagnose prompt loops without drowning in progress-bar logs.
---

# Headless CLI Runner

Run interactive, menu-driven command-line tools (build wizards, setup
assistants, `input()`-loop TUIs) without a human at the keyboard.

## When to use
- A tool only exposes an interactive `input()` menu but you must run it in a
  pipeline, background process, or cron job.
- The tool hard-aborts on validation/compatibility you can't (or shouldn't)
  fix in the source repo.
- You need to auto-answer N prompts and capture the artifact it produces.

## Core technique
1. **Find the input sink.** Most TUIs funnel through one helper. Search for
   `request_input`, `input(`, `def request_input`. Note whether the tool calls
   bare `input()` or a classmethod wrapper (e.g. `self.u.request_input(...)`) —
   you must patch BOTH.
2. **Monkeypatch the sink.** At the top of your driver script:
   ```python
   import builtins
   def _auto(prompt="Press Enter to continue..."):
       p = (prompt or "").lower()
       if "build efi for uefi" in p:  return "yes"
       if "force load" in p:          return "no"
       if "select a " in p or "select your " in p:  return "1"
       if "scan for wifi profiles" in p:  return "no"
       return ""   # default = Enter / proceed
   builtins.input = _auto
   utils.Utils.request_input = staticmethod(lambda prompt="": _auto(prompt))
   ```
   Match on **substring of the lowercased prompt**, never exact equality —
   prompts drift across versions. Return `""` for "Press Enter to continue"
   style prompts (they just want any input).
3. **Patch data/checks in-memory, not the repo.** If the tool rejects input:
   - Strip invalid/artifact keys from the loaded data dict before the tool reads it.
   - Inject required stub keys the validator demands.
   - **Compatibility checks recompute from device IDs.** Pre-setting a
     `Compatibility` result gets overwritten — spoof the *device ID* to a
     known-supported one instead so the check passes naturally.
4. **Loop-guard + separate answer log.** Tools that reject an answer re-prompt
   in an infinite `while True`. A blank default (`""`) is often treated as
   "invalid" → infinite loop. Mitigate:
   - Log every `PROMPT -> ANSWER (n=N)` to a tiny file (`/tmp/x_answers.log`).
   - If the same prompt recurs > 8 times and your answer was `""`, return a
     safe non-empty default (`"no"` / `"1"`) to escape the loop.
   - Diagnose WHICH prompt loops by reading that small file — NOT the main log.

## Pitfalls
- **Do NOT grep the main log.** Downloaders rewrite the line with `\r` + ANSI;
  the file balloons to 100k+ lines and `grep`/python line-iteration **times
  out**. Log answers to a separate small file instead.
- **Pyright false positive** on `staticmethod` reassignment of an instance
  method — ignore it; runtime is fine.
- **Tool may block at the END** on a final `request_input()` (e.g. "Press Enter
  to continue" + open folder). That is NOT a build failure — verify the
  artifact independently, then `pkill -f <driver>`.
- Monkeypatching `builtins.input` only catches `input()`; if the tool wraps it
  in a classmethod, patch that too or prompts still block.
- Keep the repo untouched: all fixes are in your driver, in-memory.

## Verification
Verify the produced artifact directly (parse the generated `config.plist`,
assert output files/paths exist on disk), not the tool's stdout. A clean exit
code is not required if the tool ends on a blocking `request_input()`.

## Reference
- `references/opencore-simplify-headless.md` — full worked example (Hackintosh
  EFI builder): iGPU spoof, eMMC limitation, WiFi-profile prompt loop,
  loop-guard logging.
