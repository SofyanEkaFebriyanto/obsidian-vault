#!/usr/bin/env python3
"""Scan Hermes context files for threat-pattern hits before installing them.

A context file that trips the scanner is not injected as written -- Hermes
substitutes a blocked placeholder. The failure is silent: the file looks
installed and does nothing. Run this before every install.

Usage:
    python3 scan_context_files.py SOUL.md AGENTS.md prefill.json
    python3 scan_context_files.py --scope strict *.md
    python3 scan_context_files.py --dir .          # scans *.md and *.json

Exit codes:
    0  all files clean at the requested scope
    1  at least one file has findings
    2  scanner could not be imported (source tree missing)
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

SCOPES = ("all", "context", "strict")


def load_scanner(hermes_home: pathlib.Path):
    """Import scan_for_threats from the Hermes source tree."""
    src = hermes_home / "hermes-agent"
    if not src.is_dir():
        print(f"ERROR: source tree not found at {src}", file=sys.stderr)
        print("Set HERMES_HOME to your Hermes home directory.", file=sys.stderr)
        sys.exit(2)
    sys.path.insert(0, str(src))
    try:
        from tools.threat_patterns import scan_for_threats  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"ERROR: cannot import scan_for_threats: {exc}", file=sys.stderr)
        sys.exit(2)
    return scan_for_threats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files to scan")
    ap.add_argument("--dir", default=None, help="scan *.md and *.json in this directory")
    ap.add_argument("--scope", default="context", choices=SCOPES,
                    help="pattern scope (default: context -- the one that governs SOUL.md)")
    ap.add_argument("--all-scopes", action="store_true",
                    help="report every scope side by side (context decides, strict is informational)")
    args = ap.parse_args()

    hermes_home = pathlib.Path(os.environ.get("HERMES_HOME", pathlib.Path.home() / ".hermes"))
    scan_for_threats = load_scanner(hermes_home)

    targets: list[pathlib.Path] = []
    if args.dir:
        d = pathlib.Path(args.dir)
        targets += sorted(d.glob("*.md")) + sorted(d.glob("*.json"))
    targets += [pathlib.Path(p) for p in args.paths]

    if not targets:
        print("ERROR: no files given (pass paths or --dir)", file=sys.stderr)
        return 2

    failed = 0
    for path in targets:
        if not path.is_file():
            print(f"MISS  {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")

        if args.all_scopes:
            res = {s: scan_for_threats(text, scope=s) for s in SCOPES}
            verdict = "CLEAN" if not res["context"] else "BLOCKED"
            if res["context"]:
                failed += 1
            note = ""
            # strict-only hits are expected and harmless for SOUL.md
            if not res["context"] and res["strict"]:
                note = "  (strict-only hits are informational -- do not weaken wording for them)"
            print(f"{verdict:8} {path.name:22} all={res['all']} context={res['context']} "
                  f"strict={res['strict']}{note}")
        else:
            hits = scan_for_threats(text, scope=args.scope)
            if hits:
                failed += 1
                print(f"BLOCKED  {path.name:22} {','.join(hits)}")
            else:
                print(f"CLEAN    {path.name:22}")

    if failed:
        print(f"\n{failed} file(s) would be BLOCKED at scope 'context'.")
        print("Rewrite the offending phrasing to say the same thing in different words.")
        return 1

    print("\nAll files clean. Safe to install.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
