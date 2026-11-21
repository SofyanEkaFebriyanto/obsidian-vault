#!/usr/bin/env python3
"""Enumerate a Next.js app's hidden API endpoints from its client bundles.

Next.js consoles put every backend path inside the JS bundle, usually as
`"".concat(base, "/backend/...")`. grep on the HTML finds nothing; you need
the webpack runtime's chunk map plus every chunk file.

Usage:
    python3 extract_nextjs_endpoints.py https://platform.minimax.io/console/plan
    python3 extract_nextjs_endpoints.py <url> --out /tmp/chunks --grep '/v1/api|/backend'

Prints a sorted list of discovered path literals. Writes the downloaded chunks
to --out so you can grep them by hand.

Notes:
- Chunks are fetched from the SAME host that served the webpack runtime. A CDN
  mirror of the same build id can 404 for some chunk ids and return an XML
  NoSuchKey body that looks like JS if you do not sanity-check the payload.
- Path literals survive the `concat(base, "...")` assembly form, so a plain
  string grep is enough to recover them.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.request
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_text(url: str) -> str:
    return fetch(url).decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="/tmp/nextjs-chunks")
    ap.add_argument("--grep", default=r"^/[a-zA-Z0-9_/.-]{3,80}$")
    ap.add_argument("--max-chunks", type=int, default=120)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    html = get_text(args.url)
    base = args.url if args.url.endswith("/") else args.url + "/"

    # 1. every chunk the HTML references, plus the webpack runtime
    refs = set(re.findall(r'/_next/static/chunks/[A-Za-z0-9_.-]+\.js', html))
    refs |= set(re.findall(r'/_next/static/chunks/pages/[A-Za-z0-9_.-]+\.js', html))
    if not refs:
        print("no /_next/static/chunks references found — is this a Next.js app?", file=sys.stderr)

    # 2. the runtime's chunk map often names chunks the HTML never references
    for ref in list(refs):
        if "webpack" not in ref:
            continue
        try:
            runtime = get_text(urljoin(base, ref))
        except Exception:
            continue
        for name in re.findall(r'static/chunks/[A-Za-z0-9_.-]+\.js', runtime):
            refs.add("/_next/" + name)
        break

    # 3. download and collect path literals
    pattern = re.compile(args.grep)
    found: set[str] = set()
    for ref in sorted(refs)[: args.max_chunks]:
        url = urljoin(base, ref)
        try:
            body = fetch(url)
        except Exception as exc:
            print(f"  skip {ref}: {exc}", file=sys.stderr)
            continue
        # A CDN mirror can answer with an XML error page; do not treat it as JS.
        if body.lstrip()[:5].startswith(b"<?xml") or b"NoSuchKey" in body[:200]:
            print(f"  skip {ref}: error page, wrong bucket for this chunk id", file=sys.stderr)
            continue
        text = body.decode("utf-8", "replace")
        with open(os.path.join(args.out, os.path.basename(ref)), "w") as fh:
            fh.write(text)
        for m in re.findall(r'"(/[A-Za-z0-9_./-]{3,80})"', text):
            if pattern.match(m) and not m.endswith((".js", ".css", ".png", ".svg", ".json")):
                found.add(m)

    for path in sorted(found):
        print(path)
    print(f"\n# {len(found)} paths from {len(refs)} chunks (chunks saved in {args.out})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
