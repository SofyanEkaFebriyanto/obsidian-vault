# Cloudflare Email Routing → IMAP Readback

Validated 2026-09-27 against `sefy.my.id` (Cloudflare Email Routing → one Gmail catch-all)
while debugging a "no verification email arrived" farm failure. Every trap below produced a
false negative that looked exactly like a broken catch-all.

---

## 1. THE TRAP: the `To:` header is preserved, but the IMAP search index is not

Cloudflare Email Routing delivers to the destination account. Gmail files the message under
the **authenticated/routed identity** and builds its search index from that — not from the
raw `To:` header, which routing leaves fully intact.

Observed, both messages delivered successfully to `[Gmail]/All Mail`:

```
uid 894 | From: intunericetern@gmail.com | To: catchall9430ab83@sefy.my.id | Subject: CATCHALL TEST ...
uid 896 | From: intunericetern@gmail.com | To: caff403f45@sefy.my.id     | Subject: CA-PROBE-...
```

But searching for them returns **nothing**:

```python
m.uid("search", None, "TO", "caff403f45")      # -> [b'']   zero hits
m.uid("search", None, "TO", "sefy.my.id")      # -> 621 hits  (domain substring works)
```

The header is right there in the message. The index just isn't keyed to it.

**Rule: search by domain substring, never by the exact random local-part.**

```python
typ, data = m.uid("search", None, "TO", "my.id")   # or whatever the catch-all domain is
ids = data[0].split()
```

If you need per-address precision, match the address against the **raw headers of the last N
messages** (see §3), not against the search index. `xyris_creator.py` and the other IMAP-based
farm scripts searching `TO:<generated-address>` are fragile for exactly this reason.

Corollary: an address that *is* the routing destination identity (a fixed alias like
`sefy@sefy.my.id`) IS searchable, because the index and the header agree. Fixed aliases work;
random local-parts do not.

## 2. THE TRAP: the "Missing email from" notice is a LOOP GUARD, not a delivery failure

Cloudflare posts this into **Spam** when the sender address equals the routing destination:

```
From:   noreply@email.cloudflare.net
Subject: Cloudflare Email Routing: Missing email from
         intunericetern@gmail.com to caff403f45@sefy.my.id?
```

Both probe emails that produced this notice were **also delivered normally to All Mail**.

This notice is spam-loop protection (Gmail would otherwise bounce a message forever between
the forwarder and itself). Reading it as "Cloudflare rejected my mail" — or as "my catch-all
is misconfigured" — sends you debugging a working setup. Check `[Gmail]/All Mail` before
concluding anything.

## 3. imaplib gotchas (Python 3.14) — all hit live in this session

**Folder names containing spaces must be quoted *inside* the string you pass:**

```python
m.select("[Gmail]/All Mail")          # BAD [b'Could not parse command']
m.select('"[Gmail]/All Mail"')        # OK - 756 messages
```

**Unquoted multi-word search args fail the same way.** imaplib does not quote for you:

```python
m.uid("search", None, "SUBJECT", "Verify your email to start using the Token Harbor")
# BAD [b'Could not parse command']
```

Prefer args that need no quoting (`TO <domain>`), or quote them yourself. `X-GM-EXT` with a
JSON payload also returned `BAD` under 3.14's imaplib — the domain-substring `TO` search above
is the reliable substitute, not the JSON search.

**Do not scan the whole mailbox.** Fetching all 756 messages with one `UID FETCH` each blew
past 300s. Tail-scanning the last ~12 UIDs took 9s:

```python
typ, data = m.uid("search", None, "ALL")
for uid in data[0].split()[-12:]:
    typ, raw = m.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (DATE FROM TO SUBJECT)])")
```

`BODY.PEEK` avoids setting `\Seen` on everything you scan — without it a diagnostic sweep
marks hundreds of messages read and destroys your unread-count triage.

## 4. Catch-all smoke test (run this before blaming anyone)

Send from the routing destination Gmail to a random address on the catch-all domain, then look
in **All Mail** (not Inbox — routed mail can land outside it) by domain substring:

```python
typ, data = m.uid("search", None, "TO", "my.id")
```

Lands within seconds ⇒ catch-all good, and any missing provider mail is the provider's fault.
Does not land ⇒ the routing rule is the problem; check the Cloudflare dashboard's routing
rules and that the catch-all action is "Send to an email" (default state is **Drop**).

Always separate the two verdicts explicitly in your report: *is my mail path working* and *is
the provider's mailer alive* (see `provider-mailer-diagnosis.md` §1). Conflating them sends
the next session down the wrong path.
