---
name: browser-automation-drivers
description: Build and verify browser automation drivers with Playwright.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, automation, browser, driver, mock, verification]
    related_skills: [dogfood, headless-cli-runner, cloud-api-key-farming, web-app-pentest]
---

# Browser Automation Drivers

## Overview

Write a program that drives a real page — fills a form, submits it, reads the
result — and **prove it works before pointing it at anything live**. The two
halves matter equally: a driver that is never exercised is a guess, and a
driver exercised only against a live target is unrepeatable.

This is about *owning the driver*. The moment you control the browser
programmatically, a large class of browser-era workarounds disappears — see
Rule 1.

## When to Use

- "Automate this page", "write a script that logs in and does X", "scrape N
  items", "check out N of these", "submit this form repeatedly".
- "Can this browser extension be a script?" — porting extension logic to a
  standalone driver.
- "Verify my scraper/checkout bot without hitting the live site."
- Any headless flow that ends in *reading a verdict* from the page or network.

**Don't use for:** exploratory QA of a web app you own → `dogfood`. Authorized
pentest → `web-app-pentest`. Bulk cloud account signup → `cloud-api-key-farming`.
Interactive `input()`-driven TUIs → `headless-cli-runner`.

## Rule 1 — Own the driver, then delete the browser's workarounds

A Chrome extension is trapped by the browser's security model. A driver is not.
Before porting extension code, list what the extension was *forced* to do and
check whether the driver still needs it.

| Extension forced to… | Because | Driver instead… |
|---|---|---|
| mask the value (`0000000000000000`) into the DOM | content scripts can't type into cross-origin iframes | type the real value directly into the iframe |
| monkey-patch `window.fetch` / `XMLHttpRequest` to rewrite the outgoing request | same — the field is inside a third-party iframe | let the page send what it sends |
| classify results by patching globals in the page | no other hook available | read the network stream from outside |
| `chrome.proxy.settings` for proxy rotation | extension API | `--proxy` on the browser launch |
| `declarativeNetRequest` to force a request header | extension API | set the header in the request you control |
| ship a popup/overlay UI to drive the tool | no UI surface in a script | CLI flags + JSON output |

Porting rule: **carry over the domain logic, discard the platform hacks.** The
generator, the classifier, the decision rules survive. The masking, the
monkey-patching, the dashboard, the license check do not.

## Rule 2 — Never point the driver at a live target before it passes a mock

A mock is the only way to test the branches you cannot afford to hit live:
decline paths, expired sessions, malformed responses.

1. Build a local mock page that mimics the target's **DOM** and, critically, its
   **response shapes** — the exact JSON keys the classifier reads.
2. Drive the mock's verdict from the input (e.g. card number) so one fixture
   file exercises every branch.
3. Include the *hard* surface too: if the real page puts fields in iframes, the
   mock must as well, or the iframe path is untested.
4. The driver must emit machine-readable verdicts: `hit` / `decline` /
   `unknown`, plus a decline code. `unknown` must be a distinct state — a
   timeout is never a decline.

Completion criterion: the driver returns the correct verdict against the mock
for **one success, one failure, and one ambiguous** case, and the test asserts
all three.

Design details and copy-paste mock shapes: `references/mock-page-design.md`.

## Rule 3 — Read the verdict from the network stream, and probe before you filter

Listen to responses from outside the page:

```js
page.on('response', async (res) => {
  if (!/api\.stripe\.com|payment_intents?/i.test(res.url())) return
  const body = await res.json().catch(() => null)
  const verdict = classify(body)   // your own rules
})
```

**The URL filter is a contract, and a too-narrow filter fails silently.** If
it misses the endpoint that carries the result, every attempt reports
`unknown` — and the symptom looks like "the app is broken", not "my filter is
wrong". Two habits prevent this:

- **Probe the real page first.** `scripts/probe_page_responses.mjs` dumps every
  response URL, method, status, content-type, and top-level JSON keys, plus the
  distinct URL patterns with the host normalised. Build the filter from that
  output, not from a guess.
- **Log what the filter let through.** On a `unknown` verdict, print the
  responses that were observed but not classified.

Also normalise the body before matching: it may be a JSON object, a JSON
string, a URL-encoded form body, or `FormData`. One shape check ("is it
JSON?") decides which parser to use.

## Rule 4 — Fill by surface, in order, and report which surface worked

```
1. plain DOM inputs   (id / name / autocomplete / data-* / placeholder)
2. iframe fields      (frameLocator — works cross-origin)
3. visible-input sweep (last resort: every visible text-like input, in order)
```

Log the surface that filled the form (`filled 3 plain DOM fields` vs
`filled 3 iframe fields`). That log line is how you later prove the hard path
was exercised, and it is the first thing to check when a real page "does
nothing" — the driver probably filled a different surface than the one that
matters.

Treat "3 of 3 fields filled" as the success criterion, not "no exception".

## Rule 5 — Use the system Chrome; don't download a browser

`playwright` downloads ~150 MB of browsers on first use. On a metered or
restricted link that is a bad first step. Use `playwright-core` plus the
browser already on the machine:

```js
const { chromium } = await import('playwright-core')
const browser = await chromium.launch({
  executablePath: '/usr/bin/google-chrome',   // or /usr/bin/chromium
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
})
```

Check what exists first: `which google-chrome chromium chromium-browser
google-chrome-stable`. Keep the path in a flag (`--chrome`) so the driver is
portable. Only fall back to `playwright install` when no system browser is
present.

## Procedure

1. **Read the target.** Locate the form, the submit control, and the endpoint
   whose response carries the verdict. Prefer reading source you have over
   blind exploration.
2. **Probe the response contract** with `scripts/probe_page_responses.mjs`.
   Record the URL patterns, content-types, and JSON keys you will classify on.
3. **Write the classifier as a pure function** over a parsed JSON body —
   `classify(body) → {status, code}`. Pure functions are unit-testable without
   a browser, and that is where most of the real logic lives.
4. **Write the generator as a pure function** too. Both are trivially covered
   by unit tests that need no browser at all.
5. **Build the mock** (Rule 2) and the fixture file that drives every branch.
6. **Write the driver** — fill (Rule 4), submit, wait for a verdict, emit a
   machine-readable result line, exit with a meaningful code.
7. **Test against the mock**, then the unit tests, then (only if the user has a
   test-mode URL) the live target.
8. **Report honestly** which surfaces were exercised: mock only, or mock plus
   live test-mode.

## Pitfalls

- **A too-narrow response filter produces `unknown` for every attempt** and
  reads as "the app is broken". Probe first; log unclassified responses.
- **`window.XMLHttpRequest = () => {...}` is not a constructor.** Arrow
  functions have no `prototype` and are not constructible, so `new
  XMLHttpRequest()` throws `TypeError: f is not a constructor`. If you
  inherited that patch, replace it with a `function` + `PatchedXHR.prototype =
  originalXHR.prototype` + static-constants copy. Verify with a 3-line
  `node -e` repro instead of reasoning about it.
- **`page.evaluate(fn, arg)` passes one object.** Destructure it in the
  signature (`({ card, expiry }) => …`). Reaching for `arguments[0]` inside the
  browser-side function works by accident and breaks on the next refactor.
- **`iframe.contentDocument` is `null` cross-origin.** Use `frameLocator`. In
  your *mock*, the parent also cannot read the child — relay values with
  `postMessage`.
- **The form re-renders between attempts.** Detect it by counting the field
  selector, and reload the page when it drops to zero. Otherwise attempt 2
  silently fills a detached node.
- **`page.frames()` includes the main frame.** Skip it when sweeping frames.
- **`fill()` vs `type()`** — some masked inputs reject `fill()`; fall back to
  `type()` with a delay, or press-and-hold per character.
- **A page that needs the tab focused won't submit headless.** If the click
  registers but nothing happens, check for focus-dependent UI before suspecting
  the driver.
- **Start mock servers with the tracked background-process API**, not
  `nohup … &` inside a foreground shell — a foreground call that forks a
  background job will be killed with the shell, and you will debug a server
  that was never really up.
- **Never report "verified" against a live target you never reached.** Say
  exactly which surface ran: mock only, or mock plus live.
- **Don't inherit a dead constant.** A backend URL defined in three places and
  referenced in none is a trap; grep the identifier and confirm ≥2 hits
  (definition + use) before you wire anything to it.

## Verification

- Unit-test the pure functions (generator, classifier, extractor) with no
  browser. These should be the majority of your assertions.
- End-to-end test against the mock: assert the verdict **and** the surface
  (`filled 3 iframe fields`), not just the exit code.
- Assert on the count and print it: `pass: 31  fail: 0`.
- Give the driver meaningful exit codes (`0` = success found, `2` = completed
  with no success, `1` = setup error) so it composes in a pipeline.
- State the verification scope in the final report: which branches are covered
  by a mock, and which (if any) were exercised live.

## Support files

- `references/mock-page-design.md` — building a mock that faithfully exercises
  a driver: the verdict contract, response-shape fidelity, driving verdicts
  from the fixture, the iframe technique, and the dead-session path.
- `references/extension-to-driver-port.md` — worked example of porting a
  8149-line Chrome extension to a standalone driver: what was carried over,
  what was deleted, how to index a huge file, and the audit findings that
  generalise.
- `references/stripe-checkout-gotchas.md` — live-run gotchas when pointing a
  driver at a real Stripe checkout: the `#fidn...` URL fragment is required
  (stripping it → "This link is incomplete", no card form), the UA must be
  overridden or the card fields are mounted (form-wait times out), and
  synthetic BIN-generated cards returning `status:unknown` is normal (3DS /
  verification), not a bug. Covers `--timeout` double-duty budgeting.
- `scripts/probe_page_responses.mjs` — dump every response a page produces
  (URL, method, status, content-type, top-level JSON keys) plus the distinct
  normalised URL patterns. Build your classifier's URL filter from this output
  instead of guessing.
