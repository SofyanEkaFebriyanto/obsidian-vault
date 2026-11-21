#!/usr/bin/env python3
"""Measure per-strategy compliance rate over N samples.

Why this exists: auto_jailbreak() picks a winner from a SINGLE sample at
temperature 0.7. A strategy that complies once can score 285 and be locked in,
then refuse 6/6 times when actually used. This script replaces that one-shot
guess with a measured compliance rate.

Usage:
    python3 measure_strategies.py                 # N=6, current model
    python3 measure_strategies.py --n 10
    python3 measure_strategies.py --json out.json

Reads model/provider/api_key from ~/.hermes/config.yaml (resolving
custom_providers entries and ${ENV} refs), and loads the caller's own
prefill.json as a candidate strategy.
"""
import os
import sys
import json
import argparse
import statistics
from pathlib import Path

REAL_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

# Load ~/.hermes/.env so provider keys are visible
_envp = REAL_HOME / ".env"
if _envp.exists():
    for _line in _envp.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# Load the godmode modules via the loader (explicit namespace required —
# bare exec() at module scope loses the bindings)
_g = {}
exec(compile(open(Path(__file__).resolve().parent / "load_godmode.py").read(),
             "load_godmode.py", "exec"), _g)


def main():
    ap = argparse.ArgumentParser(description="Measure jailbreak strategy compliance rate")
    ap.add_argument("--n", type=int, default=6, help="samples per strategy (default 6)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--canary", default=None)
    ap.add_argument("--json", default=None, help="write results to this JSON path")
    args = ap.parse_args()

    model, base_url = _g["_get_current_model"]()
    model = args.model or model
    base_url = args.base_url or base_url
    api_key = _g["_get_api_key"](base_url)
    if not api_key:
        print("ERROR: no API key resolved for provider in config.yaml")
        return 1

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)

    canary = args.canary or _g["QUICK_CANARY"]
    family = _g["_detect_model_family"](model)
    strat = _g["MODEL_STRATEGIES"].get(family, _g["DEFAULT_STRATEGY"])

    print(f"model={model}  family={family}  base_url={base_url}  N={args.n}\n")

    candidates = []
    for name in strat["order"]:
        sp = strat.get("system_templates", {}).get(name)
        if name == "parseltongue":
            for lvl in range(3):
                q, lab = _g["escalate_encoding"](canary, lvl)
                candidates.append((f"parseltongue_L{lvl}_{lab}", None, _g["SUBTLE_PREFILL"], q))
        elif name == "prefill_only":
            candidates.append(("prefill_only", None, _g["STANDARD_PREFILL"], canary))
        elif sp:
            candidates.append((name, sp, None, canary))
            candidates.append((f"{name}+prefill", sp, _g["STANDARD_PREFILL"], canary))

    # the user's existing prefill is a first-class candidate
    user_prefill_path = REAL_HOME / "prefill.json"
    if user_prefill_path.exists():
        try:
            candidates.append(("user_prefill_only", None,
                               json.loads(user_prefill_path.read_text()), canary))
        except Exception as e:
            print(f"[warn] could not load {user_prefill_path}: {e}")

    results = {}
    for label, sp, pf, q in candidates:
        scores, oks, errs = [], 0, []
        for _ in range(args.n):
            msgs = _g["_build_messages"](system_prompt=sp, prefill=pf, query=q)
            content, _lat, err = _g["_test_query"](client, model, msgs)
            r = _g["_score_attempt"](content, err, canary)
            scores.append(r["score"])
            if r.get("transport_failed"):
                errs.append((r.get("error") or "transport")[:60])
            elif not r["is_refusal"] and r["score"] > 0:
                oks += 1
        rate = oks / args.n
        results[label] = {
            "comply_rate": round(rate, 3),
            "complied": oks,
            "n": args.n,
            "mean_score": round(statistics.mean(scores), 1),
            "max_score": max(scores),
            "transport_errors": errs[:2],
        }
        flag = "  <-- transport errors!" if errs else ""
        print(f"{label:34s} comply {oks}/{args.n}  rate={rate:.2f}  "
              f"mean={statistics.mean(scores):9.1f}  max={max(scores)}{flag}")

    # rank by compliance rate, then mean score; never crown a transport failure
    usable = {k: v for k, v in results.items() if not v["transport_errors"]}
    if not usable:
        print("\nABORT: every strategy hit a transport/auth error — nothing measured.")
        return 1
    best = max(usable.items(), key=lambda kv: (kv[1]["comply_rate"], kv[1]["mean_score"]))
    print(f"\nBEST: {best[0]}  rate={best[1]['comply_rate']}  mean={best[1]['mean_score']}")
    if best[1]["comply_rate"] < 1.0:
        print(f"NOTE: best strategy complies only {best[1]['comply_rate']*100:.0f}% of the time. "
              "Retry-on-refusal is required for reliability.")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"model": model, "family": family, "n": args.n, "results": results}, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
