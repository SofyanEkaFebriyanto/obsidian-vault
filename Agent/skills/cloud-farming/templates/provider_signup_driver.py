"""Provider signup driver — Playwright, capture every XHR, stop at the captcha gate.

Adapted from the MiniMax/M Code session (2026-10-20). Kept because it is the shape
that generalises: a real browser walk of a modern Next.js/React signup, with the
network contract captured as a side effect so the flow can later be replayed
HTTP-only (or rejected on measured evidence).

What it does:
  1. loads the provider's login page
  2. accepts the Terms consent (custom <button>, NOT an <input type=checkbox>)
  3. types the email -> Continue
  4. sets a password -> Continue   (this is where most providers gate on captcha)
  5. polls IMAP for the verification code, submits it
  6. writes cookies + account JSON for the next stage (key harvest / 9router inject)

Env:
  DOMAIN   catch-all domain for the mailbox        (default: sefy.my.id)
  PROXY    http://user:pass@host:port | socks5://host:port   (default: direct)
  HEADED   1 = headed under Xvfb, 0 = headless     (default: 1)
  IMAP_USER / IMAP_PASS / IMAP_HOST / IMAP_PORT    (or a .env next to the script)

Run:
  xvfb-run -a -s "-screen 0 1920x1080x24" python signup_driver.py

TUNING NOTES (measured, keep them):
- `await resp.body()` raised "function takes exactly 5 arguments (1 given)" on this
  Playwright build. Use `await resp.text()`.
- React controlled inputs: prefer `locator.type(text, delay=25)` over `fill()` when the
  value feeds a submit handler.
- `page.fill()` can time out with "waiting for <host>/ navigation to finish" when a
  click navigated away — wait for load, then re-query the locator.
- The Terms control on these apps is a <button class="... size-4 ..."> sibling of the
  consent text, not an <input type=checkbox>. Dispatch a real MouseEvent; React needs
  the event, and `el.click()` alone is not enough.
- Do NOT conclude "the provider's mailer is dead" when no mail arrives: if the flow is
  gated by a server-validated captcha, the code is never dispatched at all.
"""
from __future__ import annotations

import asyncio
import email
import imaplib
import json
import os
import random
import re
import string
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"


def load_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


load_env()

DOMAIN = os.environ.get("DOMAIN", "sefy.my.id")
PROXY = os.environ.get("PROXY", "")
HEADED = os.environ.get("HEADED", "1") == "1"
LOGIN_URL = os.environ.get("LOGIN_URL", "https://platform.minimax.io/login")
# Provider-specific XHR endpoints worth logging in full.
INTEREST = re.compile(r"(/v1/api/|/backend/|/oauth2/|register|sms/send|captcha|login)")
# Noise: analytics, pixels, captcha vendor scripts, media.
SKIP = re.compile(
    r"(facebook|google\.|doubleclick|bing|t\.co/|twitter|reddit|meerkat|gstatic"
    r"|googletag|file\.cdn|\.mp4|_next/image|blob:|cdn\.hailuo|/xhTt)"
)

EMAIL = "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@" + DOMAIN
PASSWORD = "Mm" + "".join(random.choices(string.ascii_letters + string.digits, k=8)) + "#7kq"


class Log:
    def __init__(self, path: Path):
        self.fh = path.open("w")

    def __call__(self, *parts) -> None:
        line = " ".join(str(p) for p in parts)
        self.fh.write(line + "\n")
        self.fh.flush()
        if not SKIP.search(line):
            print(line[:400])


async def accept_terms(page) -> str:
    """Click the Terms consent control, whatever shape the framework renders it as."""
    return await page.evaluate(
        """
        (() => {
          const all = Array.from(document.querySelectorAll('*'));
          const t = all.filter(e => /I have read and agree/i.test(e.innerText||''))
                        .filter(e => e.children.length === 0 || (e.innerText||'').length < 90).pop();
          if (!t) return 'no-text';
          let n = t.parentElement;
          for (let i = 0; i < 5 && n; i++) {
            for (const el of n.querySelectorAll('button')) {
              const r = el.getBoundingClientRect();
              const cls = String(el.className || '');
              if (r.width >= 10 && r.width <= 26 && r.height >= 10 && r.height <= 26 && /size-4/.test(cls)) {
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
                if (typeof el.click === 'function') { try { el.click(); } catch (e) {} }
                return 'clicked';
              }
            }
            n = n.parentElement;
          }
          return 'nothing';
        })()
        """
    )


async def wait_for_code(addr: str, timeout: int = 240) -> str | None:
    """Poll IMAP for a 6-digit verification code addressed to `addr`.

    Match the bare local part as well as the full address: Cloudflare Email Routing
    rewrites the To: header, so a full-address filter silently times out.
    Scan All Mail too, not just INBOX.
    """
    user = os.environ["IMAP_USER"]
    pw = os.environ["IMAP_PASS"]
    host = os.environ.get("IMAP_HOST", "imap.gmail.com")
    port = int(os.environ.get("IMAP_PORT", "993"))
    local = addr.split("@")[0].lower()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            m = imaplib.IMAP4_SSL(host, port)
            m.login(user, pw)
            for box in ("INBOX", '"[Gmail]/All Mail"', '"[Gmail]/Spam"'):
                try:
                    if m.select(box, readonly=True)[0] != "OK":
                        continue
                except Exception:
                    continue
                status, msgs = m.search(None, "(ALL)")
                ids = msgs[0].split() if status == "OK" and msgs and msgs[0] else []
                for mid in reversed(ids[-30:]):
                    st, data = m.fetch(mid, "(RFC822)")
                    if st != "OK" or not data or not data[0]:
                        continue
                    msg = email.message_from_bytes(data[0][1])
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", "replace")
                                break
                    else:
                        body = (msg.get_payload(decode=True) or b"").decode("utf-8", "replace")
                    blob = (str(msg.get("To", "")) + " " + str(msg.get("Subject", "")) + " " + body).lower()
                    if local not in blob:
                        continue
                    codes = re.findall(r"(?<!\d)(\d{6})(?!\d)", body)
                    if codes:
                        m.store(mid, "+FLAGS", "\\Seen")
                        m.logout()
                        return codes[-1]
            m.logout()
        except Exception as exc:
            print("  [imap] err", str(exc)[:90])
        await asyncio.sleep(8)
    return None


def proxy_config(proxy: str) -> dict | None:
    if not proxy:
        return None
    m = re.match(r"(?:http|socks5)://(?:([^:]+):([^@]+)@)?([^:/]+):(\d+)", proxy)
    if not m:
        return {"server": proxy}
    cfg = {"server": f"{proxy.split('://')[0]}://{m.group(3)}:{m.group(4)}"}
    if m.group(1):
        cfg.update({"username": m.group(1), "password": m.group(2)})
    return cfg


async def main() -> None:
    log = Log(HERE / f"signup_{EMAIL.split('@')[0]}.log")
    log("EMAIL:", EMAIL, "| PROXY:", PROXY or "direct")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=not HEADED,
            proxy=proxy_config(PROXY),
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 950},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        await ctx.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            window.chrome = window.chrome || {runtime: {}};
            """
        )
        page = await ctx.new_page()

        def on_request(req):
            if INTEREST.search(req.url):
                log(f"REQ {req.method} {req.url[:250]}", "|", (req.post_data or "")[:400])

        async def on_response(resp):
            if not INTEREST.search(resp.url):
                return
            try:
                body = (await resp.text())[:1200]
            except Exception as exc:
                body = f"<err {str(exc)[:60]}>"
            log(f"RES {resp.status} {resp.url[:250]} :: {body}")

        page.on("request", on_request)
        page.on("response", on_response)

        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        log("terms:", await accept_terms(page))

        email_box = page.locator("input[type=email]")
        await email_box.click()
        await email_box.type(EMAIL, delay=25)
        await page.get_by_role("button", name="Continue", exact=True).first.click()
        await page.wait_for_timeout(9000)
        text = await page.evaluate("document.body ? document.body.innerText : ''")
        log("STEP1:", text.replace("\n", " | ")[:300])

        if await page.locator("input[type=password]").count():
            pw = page.locator("input[type=password]").first
            await pw.click()
            await pw.type(PASSWORD, delay=25)
            await accept_terms(page)
            await page.get_by_role("button", name="Continue", exact=True).first.click()
            log("=== submitted password")
            await page.wait_for_timeout(12000)
            text = await page.evaluate("document.body ? document.body.innerText : ''")
            log("STEP2:", text.replace("\n", " | ")[:600])

        code_boxes = page.locator("input[maxlength='6'], input[inputmode='numeric']")
        if await code_boxes.count():
            log("=== code step; polling IMAP")
            code = await wait_for_code(EMAIL)
            log("CODE:", code)
            if code:
                n = await code_boxes.count()
                if n == 1:
                    await code_boxes.first.fill(code)
                else:
                    for i, ch in enumerate(code[:n]):
                        await code_boxes.nth(i).fill(ch)
                for label in ("Continue", "Confirm", "Verify", "Next", "Submit"):
                    button = page.get_by_role("button", name=label, exact=True).first
                    if await button.count():
                        await button.click()
                        log("=== clicked", label)
                        break
                await page.wait_for_timeout(14000)
                text = await page.evaluate("document.body ? document.body.innerText : ''")
                log("STEP3:", text.replace("\n", " | ")[:700])

        cookies = await ctx.cookies()
        log("COOKIES:", json.dumps([c["name"] for c in cookies]))
        (HERE / f"account_{EMAIL.split('@')[0]}.json").write_text(
            json.dumps({"email": EMAIL, "password": PASSWORD, "url": page.url, "cookies": cookies}, indent=1)
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
