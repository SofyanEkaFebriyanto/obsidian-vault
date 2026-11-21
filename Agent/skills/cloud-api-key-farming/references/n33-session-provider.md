# n33.ai — Session-Cookie Provider (no API key) + 9Router Bridge

Worked example of a provider that hands you a **session cookie** instead of an API key, and of the
"session pool → local OpenAI-compatible adapter → 9Router" pattern that makes such a provider
usable from any OpenAI-compatible client.

## The provider

- Base: `https://n33.ai`
- Auth: **Better Auth**, email + password. There are **no API keys** — the only credential is a cookie.
- Session cookie: `__Secure-n33.session_token` (30-day, HTTP-only, Secure, SameSite=Lax)
  - send it as a raw `Cookie:` header, **not** as a Bearer token
- Free model ids (10): `n33-chat` (Claude Haiku 4.5), `n33-claude-sonnet`, `n33-claude-opus`,
  `n33-gpt` (GPT-5.6 Luna), `n33-gpt-terra`, `n33-gpt-sol`, `n33-gpt-astra` (GPT-6),
  `n33-grok` (Grok 4.5), `n33-grok-4-6`, `n33-grok-4-7`
- Pro ids = same id + `~pro` suffix (`pro-claude-fable`, `pro-gpt-sol`, …), locked until subscription

### Endpoints

| Purpose | Call |
|---|---|
| Sign up | `POST /api/auth/sign-up/email` |
| Verify email | `GET /api/auth/verify-email?token=…` → `{"status":true,"user":null}` |
| Sign in | `POST /api/auth/sign-in/email` → sets the session cookie |
| Session probe | `GET /api/auth/get-session` |
| Profile + quota | `GET /api/v1/me` → user + `energy.balance` (new account = 50) |
| Chat | `POST /api/chat/stream` (multipart/form-data) |
| Unauth probe | `GET /api/v1/me` without cookie → 200 `{"error":{"code":"UNAUTHENTICATED"}}` |

### Chat request shape

`POST /api/chat/stream` — **multipart/form-data**, not JSON:

| Field | Value |
|---|---|
| `message` | required — the user text (upstream 500s silently without it) |
| `model` | JSON string `{id, model, version, provider, modelId}` |
| `history` | JSON array of `{role:"user"|"bot", content}` |
| `webSearch` | `[]` |
| `textChatMode` | `""` |
| `attachments` | `[]` |

Response is `text/event-stream`; frames are `data: {"chunk":…,"fullText":…}`.
Errors arrive either as a non-2xx or as `{"error":"…"}` *inside* the stream — so parse the stream
body even on HTTP 200.

## Mail: Mail.tm-compatible disposable inbox

DuckMail (`https://api.duckmail.sbs`) speaks the Mail.tm Hydra API — no browser needed:

- `GET /domains?page=1` → verified domains (pick a random one)
- `POST /accounts` → create mailbox
- `POST /token` → bearer for that mailbox
- `GET /messages?page=1` → list
- `GET /messages/{id}` → body

Magic-link signup order: mailbox → sign-up → **poll mail for the `n33.ai/api/auth/verify-email?token=…`
link** (≈5 s to arrive; poll every 4 s, give up after 150 s) → GET the link → sign in with the
password. The upstream tool used passwords shaped `N33!<6 chars><4 digits>x`.

## Energy (quota) model — undocumented, recovered from the JS bundles

| Action | Call | Yield |
|---|---|---|
| Daily claim | `POST /api/v1/energy/claims` `{"kind":"daily"}` | +10, once/day |
| X profile link | `POST /api/v1/energy/claims` `{"kind":"x-connect"}` | +2, one-time |
| Availability | `GET /api/v1/energy/availability` | `{invitesLeftToday, dailyReady, postedToday}` |
| Invite code | `GET /api/v1/energy/invite-code` | 5 invites/day/account |
| X connect state | `GET /api/v1/energy/x` | `{canVerify, connected}` |
| Nudge offer | `GET /api/v1/energy/nudges` | current offer band |

**`Idempotency-Key` header is mandatory** on `POST /api/v1/energy/claims`, else
`400 {"error":{"code":"IDEMPOTENCY_KEY_REQUIRED"}}`. Any UUID works; reuse the *same* key when
retrying the same logical claim, generate a new one for a new claim.

Per-call cost: 1 energy for cheap models (chat/grok), 2 for the expensive ones (opus/astra/sol).
A 4-account pool topped up daily therefore sustains continuous use.

## The bridge pattern (session pool → 9Router)

Because there is no API key, n33 cannot be registered in 9Router directly. Run a small local
OpenAI-compatible adapter that owns the session pool:

```
n33.ai  (one session cookie per account)
   ↓  adapter :8784  (round-robin pool, SSE + non-stream)
9router :20128  ← provider node "openai-compatible" → baseUrl http://127.0.0.1:8784/v1
   ↓  POST /v1/chat/completions  {"model":"n33/n33-grok"}
```

Adapter requirements (9Router is picky):
- Support **both** plain JSON and SSE. 9Router sends `accept: text/event-stream` on *every*
  call, so implement SSE whenever that header is present (and when `stream:true`).
- 503 with a `pool_exhausted` body when no account is healthy; 502 `upstream_error` on throw.
- Non-stream responses should include the serving account and a token estimate.

Then in 9Router: one provider node (`type: openai-compatible`, `apiType: chat`, `prefix: n33`,
`baseUrl: <adapter>/v1`) and one connection per model, named `n33/<model-id>`.

**Pitfall: a connection's `provider` field must be the provider-NODE id, not the prefix.**
The node id looks like `openai-compatible-chat-<uuid>`. Passing the prefix registers nothing usable.

## Keeping the pool alive

Session cookies expire in 30 days and energy drains. A daily maintenance job that
(a) claims `daily` + `x-connect` on every account, (b) probes each session with `GET /api/v1/me`
and drops the dead ones, (c) provisions replacements up to a target count, is enough to keep the
bridge permanently up. Run it from a user-systemd timer (oneshot service + `OnCalendar` timer).

## Tooling

- Upstream: https://github.com/0xgetz/n33-bulk-9router — zero-dep Node; `src/n33.js` (client),
  `src/inbox.js` (mail), `src/provision.js` (signup), `src/pool.js` (round-robin, cooldown 60 s,
  3 failures → disable), `src/adapter.js` (the bridge), `src/connect-9router.js` (registration).
- Local deployment + the added `maintain` command: `~/Documents/project/n33-bulk-9router/`
  (`README.local.md` has the specifics; `src/maintain.js` holds the energy top-up logic).
