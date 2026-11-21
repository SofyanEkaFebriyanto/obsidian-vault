# nodriver API Differences vs Playwright/Camoufox

nodriver (used by bluk-cf) has a different API than Playwright/Camoufox. Key pitfalls:

## Attributes
- Playwright: `element.get_attribute("src")`
- nodriver: `element.attrs.get("src", "")`
- **`get_attribute` does NOT exist** on nodriver Elements — silent failure (returns None)

## iframe Evaluation
- Playwright: `iframe.evaluate("...")`
- nodriver: **NO `evaluate` on Elements** — use `page.evaluate()` with `querySelector()`
```python
iframe_rect = await page.evaluate("""() => {
    const iframe = document.querySelector('iframe[src*="domain.com"]');
    return iframe.getBoundingClientRect();
}""")
```

## select_all / query_selector_all
- Both `page.select_all("iframe")` and `page.query_selector_all("iframe")` work
- Returns list of nodriver Element objects

## mouse_click (OS-level)
- `page.mouse_click(x, y)` sends OS-level mouse click (bypasses iframe sandbox)
- This is the **only** way to interact with cross-origin Turnstile iframes

## Python Version
- nodriver has a non-UTF-8 byte in `cdp/network.py` → SyntaxError on Python 3.14
- Must use Python 3.10-3.13
