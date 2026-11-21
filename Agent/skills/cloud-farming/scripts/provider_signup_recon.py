#!/usr/bin/env python3
"""Batch provider signup recon via real Chrome (nodriver).

Read-only: inspects each target's signup page and classifies the flow.
Creates NO accounts. Extend TARGETS and re-run.

Requires Python 3.12 (nodriver breaks on 3.14) and a display:
    python3.12 -m venv venv
    ./venv/bin/pip install nodriver opencv-python-headless   # opencv: verify_cf template matching
    xvfb-run -a ./venv/bin/python scripts/provider_signup_recon.py

Writes /tmp/recon.json and prints a per-provider verdict block.
"""
import asyncio
import json
import sys

import nodriver as uc

# (label, url) -- the signup/login surface to inspect
TARGETS = [
    ("codecraft",    "https://codecraftapi.com/register"),
    ("deepinfra",    "https://deepinfra.com/login"),
    ("tokenharbor",  "https://tokenharbor.ai/login"),
    ("nano-gpt",     "https://nano-gpt.com/auth/signin"),
    ("cometapi",     "https://www.cometapi.com/console/register"),
    ("apimart",      "https://apimart.ai/register"),
    ("aihubmix",     "https://aihubmix.com/register"),
    ("openrouter",   "https://openrouter.ai/signup"),
    ("opencode-zen", "https://opencode.ai/zen"),
    ("kilo",         "https://kilo.ai/"),
    ("chutes",       "https://chutes.ai/login"),
    ("hyperbolic",   "https://hyperbolic.xyz/signup"),
    ("sambanova",    "https://sambanova.ai/signin"),
    ("cerebras",     "https://inference.cerebras.ai/signup"),
    ("mistral",      "https://console.mistral.ai/login"),
    ("302ai",        "https://302.ai/register"),
    ("siliconflow",  "https://account.siliconflow.cn/zh/register"),
    ("pollinations", "https://enter.pollinations.ai/signup"),
    ("nebius",       "https://studio.nebius.com/signup"),
    ("deepinfra-2",  "https://deepinfra.com/signup"),
    ("together",     "https://api.together.ai/signin"),
    ("fireworks",    "https://app.fireworks.ai/login"),
    ("novita",       "https://novita.ai/login"),
]

SLEEP = 7


def unwrap(v):
    """page.evaluate() returns [[value]] for non-string returns."""
    if isinstance(v, str):
        return v
    while isinstance(v, (list, tuple)):
        if not v:
            return None
        v = v[0]
    return v


PROBE = r"""JSON.stringify((() => {
  const sitekeys = [...new Set([...document.querySelectorAll('[data-sitekey]')]
      .map(e => e.getAttribute('data-sitekey')).filter(Boolean))];
  const cfFrames = [...document.querySelectorAll('iframe')].map(f => f.src)
      .filter(s => s && s.includes('challenges.cloudflare'));
  const names = [...document.querySelectorAll('input')].map(i => (i.name || '').toLowerCase());
  const buttons = [...document.querySelectorAll('button,a[role=button]')]
      .map(b => b.innerText.trim().toLowerCase()).filter(Boolean);
  const scripts = [...document.querySelectorAll('script[src]')].map(s => s.src);

  // Captcha engine tells -- checking for the word "turnstile" in HTML is meaningless.
  const engine = [];
  if (names.includes('cf-turnstile-response') || sitekeys.length) engine.push('turnstile');
  if (names.some(n => n.includes('$action_key'))) engine.push('turnstile:action');
  if (sitekeys.length && engine.length === 0) engine.push('turnstile:sitekey-only');
  if (scripts.some(s => /geetest/i.test(s))) engine.push('geetest');
  if (scripts.some(s => /o\.alicdn\.com|aliyuncaptcha/i.test(s))) engine.push('aliyun');
  if (document.querySelector('.g-recaptcha') || scripts.some(s => /recaptcha/i.test(s))) engine.push('recaptcha');
  if (document.querySelector('.h-captcha') || scripts.some(s => /hcaptcha/i.test(s))) engine.push('hcaptcha');

  return {
    url: location.href,
    title: document.title,
    hasEmail:        names.some(n => /email|user|login/.test(n)),
    hasPassword:     names.some(n => n.includes('pass')),
    hasPhone:        names.some(n => /phone|mobile|tel/.test(n)),
    hasCaptchaField: names.some(n => /captcha|verify/.test(n)),
    hasInviteField:  names.some(n => /invite|code|referr/.test(n)),
    csrf: !!document.querySelector(
        'input[name="_token"],input[name="csrfToken"],input[name="csrf_token"],input[name="authenticity_token"]'),
    social: [...new Set(buttons.filter(t =>
        /google|github|apple|microsoft|linkedin|discord|facebook/.test(t)))],
    sitekeys, cfFrames, engine,
    fieldNames: [...new Set(names)].slice(0, 14),
  };
})())"""


def verdict(d):
    """One-line classification from the probe result."""
    if d.get("engine"):
        return f"CAPTCHA:{'+'.join(d['engine'])}"
    if not d["hasEmail"] and not d["hasPassword"]:
        if d["social"]:
            return f"OAUTH-ONLY ({len(d['social'])} providers) -- not farmable"
        return "no form found (client-side render? wrong path?)"
    if not d["hasPassword"]:
        return "email only, no password -- likely magic-link or OTP"
    if d["hasPhone"]:
        return "email+password+PHONE -- not farmable"
    if d["hasInviteField"]:
        return "email+password but invite-gated"
    if d["csrf"]:
        return "email+password+csrf -- HTTP-automatable (Laravel/Blade)"
    return "email+password, no csrf -- possible, verify by POST"


async def probe(browser, name, url):
    try:
        page = await browser.get(url)
        await page.sleep(SLEEP)
        raw = unwrap(await page.evaluate(PROBE))
        d = json.loads(raw) if raw else {}
        d["name"] = name
        d["target"] = url
        d["ok"] = bool(d)
        d["verdict"] = verdict(d) if d else "empty DOM"
        return d
    except Exception as e:
        return {"name": name, "ok": False, "err": str(e)[:120], "target": url}


async def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/recon.json"
    browser = await uc.start(headless=False)
    out = []
    try:
        for name, url in TARGETS:
            # Do NOT page.close() here -- closing the last tab kills the
            # websocket and every later target fails with
            # "no close frame received or sent".
            d = await probe(browser, name, url)
            out.append(d)
            if d.get("ok"):
                print(f"{d['verdict']:52} {name:15} -> {d['url'][:52]}", flush=True)
                if d["sitekeys"]:
                    print(f"{'':52} sitekeys={d['sitekeys']} cfFrames={len(d['cfFrames'])}", flush=True)
                if d["social"]:
                    print(f"{'':52} social={d['social']}", flush=True)
            else:
                print(f"{'ERROR':52} {name:15} {d.get('err','')}", flush=True)
    finally:
        with open(out_path, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nwrote {out_path} ({len(out)} targets)")
        try:
            browser.stop()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
