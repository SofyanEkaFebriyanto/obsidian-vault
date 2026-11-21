# Provider Farmability Triage

Method + measured results from a 2026-09-27 sweep of ~25 free-tier / OpenAI-compatible AI
providers. Use the ladder to decide *whether to build a pipeline at all* before writing any
farm script.

---

## The ladder (cheap → expensive, stop as soon as it fails)

**Step 1 — is the backend alive?** Probe the model catalogue unauthenticated.

```bash
curl -s -o /dev/null -w '%{http_code}' --max-time 12 https://provider.example/v1/models
```

| Code | Meaning |
|------|---------|
| `200` | Public catalogue — endpoint healthy, auth needed only for inference |
| `401` | Healthy, auth required — normal for most providers |
| `404` | Wrong path. The API is likely on a **different domain**; find it in the JS bundle before writing it off |
| `000` | Dead host / DNS / blocked — recheck, don't conclude yet |

A `401` is a *healthy* signal, not a failure. Don't treat "needs a key" as "needs farming".

**Step 2 — is the signup form scriptable?** Scrape the markers:

```bash
curl -s -L 'https://provider.example/register' \
  | grep -oiE '(csrf|_token|turnstile|recaptcha|hcaptcha|password|name="email"|github|google|apple|card|验证码)' \
  | sort -u
```

- `csrf`/`_token` only → HTTP-automatable (Laravel/Blade shape, see
  `provider-mailer-diagnosis.md` §3)
- `github`/`google`/`apple` and **no** password field → OAuth-only, not farmable
- `验证码` / `phone` → phone verification, not farmable
- `fingerprint` field (Chutes) → paste-a-key auth, no account model

**CRITICAL — the grep above CANNOT detect a captcha. It only produces false positives.**
Every Next.js/cloudflare-flavored page ships a `turnstile` script tag whether or not a widget
is present, so `grep -oiE 'turnstile'` matches on ~every SPA. A grep hit means *nothing*.
The same applies to "captcha" appearing in marketing copy or a bundle filename.

Confirm with a real browser before naming a captcha blocker. See §5 below.

**Step 3 — POST it.** Real CSRF + cookies, `allow_redirects=False`. A `302` to a
`/verify-email`-shaped path means the account exists and only mail gates the rest — proceed to
the mailer control ladder. `403 Request Forbidden` / `405 Method Not Allowed` on a POST that
the form itself advertises usually means the endpoint is not the real one.

**Step 4 — can this provider even send mail?** If tokens are email-gated, run
`provider-mailer-diagnosis.md` §1 before building anything.

## Measured results, 2026-09-27

### Genuinely usable without accounts

| Provider | Endpoint | Evidence |
|----------|----------|----------|
| **Pollinations** | `POST https://text.pollinations.ai/openai`, body `{"model":"openai-fast","messages":[...]}` | **200 with a real completion, zero auth, no signup, no captcha.** OpenAI-compatible. Best free option found. |
| **OVH AI Endpoints** | `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/models` | `200` unauthenticated; `POST /v1/chat/completions` → `422` (alive, needs a body). Signup page carries a Laravel `_token`. **Signup itself unvalidated.** |

Pollinations notes:
- `GET /v1/models` and the other catalogue endpoints are public, no auth.
- For a persistent key: `enter.pollinations.ai` is better-auth, but
  `POST /api/auth/sign-up/email` → `400 {"code":"EMAIL_PASSWORD_SIGN_UP_DISABLED"}`.
  Google/GitHub/Apple only. **Use the keyless path.**
- Raw publishable `pk_` keys are legacy and capped at ~1 pollen/IP/hour.

### Alive but not farmable

| Provider | Blocker (measured) |
|----------|-------------------|
| OpenRouter | OAuth-only signup (Google/GitHub); `/api/auth/csrf` → 404; catalogue `200` |
| NanoGPT | NextAuth `csrfToken` obtainable, but `POST /api/auth/callback/credentials` → 302 `?csrf=true` then `?error=CredentialsSignin` |
| Mistral | ZITADEL/WorkOS at `v2.auth.mistral.ai`; OIDC discovery has `registration_endpoint: null`; login page exposes only an `email` input, no signup link |
| Chutes | Catalogue `200`, inference `429`; login is a 32-char fingerprint paste, no email form |
| CometAPI | **OAuth-only** — `/console/login` and `/console/register` both redirect to login. Buttons: Continue with Google / GitHub / LinkedIn / Microsoft, plus an `Invitation Code` field. **No email field, no password field, no sitekey.** (An earlier pass wrongly recorded "Turnstile on the form" — that was a grep artifact, see §5.) |
| APIMart | Login/register render client-side with no email or password input present; OAuth buttons only |
| 302.AI | **AliyunCaptcha**, not Turnstile — loads `https://o.alicdn.com/captcha-frontend/aliyunCaptcha/AliyunCaptcha.js`. A Cloudflare solver is irrelevant here; needs a separate Aliyun path. |
| SiliconFlow | phone + AliyunCaptcha; `account.siliconflow.cn/zh/register` redirects to `/zh/login` |
| Cerebras | signup POST → `405 Method Not Allowed` |
| SambaNova | signin POST → `403 Request Forbidden` |
| Glama, Requesty, Nitro | auth routes `404` / `405` |
| Cloudflare Workers AI, GitHub Models, Nvidia, Groq, HF, Nebius, Turing, AtlasCloud | require real identity, phone, or OAuth |

### Takeaway

Free tiers that are actually *self-serve* are rare in 2026. Most now sit behind Turnstile,
OAuth-only, or phone verification. When a sweep comes back mostly negative, the honest
deliverable is the two or three that work plus a named blocker per rejected provider — not a
list of speculative pipelines.

## Reporting convention for a triage sweep

State the verdict per provider in one line with the measured code. Name the blocker and stop.
Do not pad a negative result with "you could try a browser automation approach" when the
evidence says OAuth-only or phone-gated — that is noise dressed as an option.

Also separate **"recon of the signup form"** from **"a signup that completed."** A browser
sweep that only reads the DOM proves the flow's *shape* (which fields, which captcha, which
OAuth wall). It does not prove an account can be created. Say which one you actually did.

---

## 5. Step 5 — confirm captcha claims in a real browser (not grep)

`curl | grep turnstile` is a coin flip that always lands on "yes". Sweep the page in Chrome
and read the DOM. Ground truth from a 24-provider sweep (2026-09-27), where
`sitekeys=[]` and `cfFrames=0` for **all but 2** targets:

```python
PROBE = r"""JSON.stringify((() => {
  const sitekeys = [...new Set([...document.querySelectorAll('[data-sitekey]')]
      .map(e => e.getAttribute('data-sitekey')).filter(Boolean))];
  const cfFrames = [...document.querySelectorAll('iframe')].map(f => f.src)
      .filter(s => s && s.includes('challenges.cloudflare'));
  const names = [...document.querySelectorAll('input')].map(i => (i.name||'').toLowerCase());
  const buttons = [...document.querySelectorAll('button,a[role=button]')]
      .map(b => b.innerText.trim().toLowerCase()).filter(Boolean);
  return {
    sitekeys, cfFrames,
    hasEmail:     names.some(n => /email|user|login/.test(n)),
    hasPassword:  names.some(n => n.includes('pass')),
    hasPhone:     names.some(n => /phone|mobile|tel/.test(n)),
    hasCaptchaField: names.some(n => /captcha|verify/.test(n)),
    social: [...new Set(buttons.filter(t =>
        /google|github|apple|microsoft|linkedin|discord|facebook/.test(t)))],
    // other engines load their own script host -- name them explicitly
    other: [...new Set([...document.querySelectorAll('script[src]')]
        .map(s => s.src).filter(s => /geetest|aliyun|recaptcha|hcaptcha/.test(s)))]
  };
})())"""
```

`page.evaluate` returns **`[[value]]`** for non-string returns — index `[0][1]` or it will
crash downstream with `'NoneType' object is not subscriptable`. Wrap it:

```python
def unwrap(v):
    if isinstance(v, str): return v
    while isinstance(v, (list, tuple)):
        if not v: return None
        v = v[0]
    return v
```

**Do not `page.close()` inside a multi-target loop.** Closing the last tab tears down the
browser websocket; every subsequent target dies with
`no close frame received or sent` / `Session with given id not found`. Leave pages open and
drive one browser across the whole sweep.

Signal that actually identifies the engine:
- `input[name="cf-turnstile-response"]` or a `data-sitekey` element → Cloudflare Turnstile
- `input[name="$action_key"]` → Turnstile in **action** mode (React widget, not a bare div)
- `script[src*="o.alicdn.com"]` / `AliyunCaptcha.js` → Aliyun, out of scope for `verify_cf()`
- `script[src*="geetest"]`, `.g-recaptcha`, `.h-captcha` → respective engines

**`await page.verify_cf()` is sitekey-agnostic** — it works on any Turnstile deployment, so a
Cloudflare-farm harness is portable across providers in principle. Its practical reach is
simply much narrower than grep suggests, because most providers no longer put a Turnstile
widget on the signup form at all. Portability of the solver ≠ prevalence of the target.
