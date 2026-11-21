# nodriver Notes

## Python Version Compatibility
- **nodriver < latest** has encoding bug on Python 3.14: `SyntaxError: Non-UTF-8 code starting with '\xb1'` in `cdp/network.py`
- **Fix**: use Python 3.12 (`python3.12 -m venv venv`)

## Usage with Xvfb
```python
import nodriver as uc
browser = await uc.start(headless=True, lang="en-US", proxy="http://user:pass@host:port")
page = await browser.get("https://example.com")
```

## OS-Level Mouse Click (Turnstile bypass)
```python
# nodriver's mouse_click() sends CDP Input.dispatchMouseEvent
# This bypasses cross-origin iframe sandbox for Turnstile
await page.mouse_click(x, y)
```

## Key Differences from Playwright
- Async-only API (no sync version)
- No built-in stealth (but Chrome itself is less detected than Playwright's Chromium)
- Uses `uc.start()` instead of browser launcher
- Tab/page navigation uses `await page.get(url)`
- Element selection: `await page.select("css-selector", timeout=10)`
- Not compatible with Camoufox's fingerprinting

## Critical API Quirks

### Attributes
- ❌ `await element.get_attribute("src")` → **AttributeError: 'NoneType' object is not callable**
- ✅ `element.attrs.get("src", "")` — `.attrs` is a **property** (not method) returning a dict

### Evaluating JS on Elements
- ❌ `await element.evaluate("js")` → nodriver elements have NO evaluate method
- ✅ `await page.evaluate("js")` with `querySelector` inside the JS to target the element:
  ```python
  rect = await page.evaluate("""() => {
      const el = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
      return el ? el.getBoundingClientRect() : null;
  }""")
  ```

### Select Methods
- `page.select(css, timeout=N)` — returns None on timeout (does NOT raise)
- `page.select_all(css)` — returns list (empty list if none found)
- Both also available as `page.query_selector()` / `page.query_selector_all()`

### `evaluate()` returns a NESTED wrapper, not the value

For any **non-string** return, `page.evaluate()` hands back `[[value]]`. Indexing it wrongly
crashes far from the cause, typically `'NoneType' object is not subscriptable` or
`TypeError: 'list' object has no attribute 'get'` dozens of lines later.

```python
raw = await page.evaluate("JSON.stringify({...}")   # -> a str, safe
raw = await page.evaluate("() => someObject")       # -> [[{...}]]  NOT [{...}]
```

Two reliable fixes — prefer the first:

```python
# 1. JSON.stringify inside the JS, then json.loads (also normalises the shape)
d = json.loads(unwrap(await page.evaluate("JSON.stringify((() => ({...}))())")))

# 2. or unwrap defensively wherever you call evaluate
def unwrap(v):
    if isinstance(v, str): return v
    while isinstance(v, (list, tuple)):
        if not v: return None
        v = v[0]
    return v
```

`await element.attrs` values are the same story — a missing key yields nested empties, not
`None`. Always `.get(key, default)`.

### NEVER close pages in a multi-target loop

`await page.close()` on the last open tab **kills the browser's websocket**. Every later
target in the same browser then fails with one of:

- `no close frame received or sent`
- `Session with given id not found. [code: -32001]`
- `No target with given id found [code: -32602]`

The cascade looks like each provider is individually broken; it is one mistake, repeated.
Sweep many URLs by **keeping every page open** on one browser instance:

```python
async def probe(browser, name, url):
    page = await browser.get(url)      # no close()
    ...
    return result                        # let the tab live
```

Also: `uc.ChromeOptions` does not exist in 0.50.x — pass args to `uc.start(...)` directly.
`await uc.start(headless=False)` under `xvfb-run -a` is the working headful invocation.

### Turnstile signals worth checking

`verify_cf()` returning `None` and `sitekeys == []` together means **no widget was present**,
not that solving failed. Distinguish "no iframe to click" from "click didn't take":

```python
frames = await page.select('iframe[src*="challenges.cloudflare"]', timeout=4)
if not frames:
    print("no CF iframe present -> nothing to solve, not a solver failure")
```

A Turnstile in *action* mode renders no `data-sitekey` element; its tell is a hidden
`input[name="$action_key"]` (Cloudflare's React widget). Checking only for sitekeys will
report a false negative there.

### Mouse
- `page.mouse_click(x, y)` — OS-level click, bypasses iframe sandbox
- `page.mouse_move(x, y, steps=N)` — for drag operations
- `page.mouse_drag(x1, y1, x2, y2)` — for drag operations
