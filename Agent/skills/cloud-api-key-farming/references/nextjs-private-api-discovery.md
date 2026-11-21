# Discovering a Next.js App's Private API Surface

How to enumerate undocumented endpoints, request enums, and quota logic of a modern web app
before writing a single line of the HTTP-only farm. Applies to any Next.js / React SPA that
talks to a private `/api/...` backend.

## Step 1 — pull the JS chunks

Next.js apps list their chunks in the HTML. One request gets them all:

```bash
curl -s https://target.tld/page -o page.html
grep -oE '/_next/static/chunks/[a-zA-Z0-9._-]+\.js' page.html | sort -u > chunks.txt
wc -l < chunks.txt          # 40-80 chunks is typical
while read -r f; do
  curl -s "https://target.tld$f" -o "chunk_$(basename "$f")"
done < chunks.txt
cat chunk_*.js > all.js
```

## Step 2 — harvest endpoint strings

```bash
cat chunk_*.js | grep -oE '/api/v1/[a-zA-Z0-9/_-]+' | sort -u
```

Also grep for the base URL and the client wrapper:

```bash
cat chunk_*.js | grep -oE 'baseUrl:"[^"]*"|API_BASE_URL|axios.create\([^)]*\)'
```

The API base is often a *different host* from the frontend — see
`references/http-api-registration.md` (frontend/backend domain split).

## Step 3 — recover request enums from validation errors

The fastest way to learn a valid `kind` / `type` enum is to send a wrong one and read the
Zod error — the API often echoes the allowed values:

```
POST /api/v1/energy/claims  {"kind":"nonsense"}
→ 422 {"error":{"code":"VALIDATION_FAILED",
               "details":{"in":"body","issues":[{"path":"kind","message":"Invalid input"}]}}}
```

The generic message hides the enum, so pull the enum from the bundle instead — search for the
`kind:"..."` literals and for the zod schema that guards the endpoint:

```bash
cat chunk_*.js | grep -oE 'kind:"[a-z-]+"' | sort -u
cat chunk_*.js | grep -oE '.{200}postedToday.{250}'   # context around the UI that calls it
```

Then confirm each candidate live. Working kinds found this way included `daily` (one-time
+10) and `x-connect` (one-time +2); everything else returned `Invalid input`.

## Step 4 — find the required headers

Some endpoints demand an idempotency key. The error names it:

```
POST /api/v1/energy/claims  (no Idempotency-Key)
→ 400 {"error":{"code":"IDEMPOTENCY_KEY_REQUIRED",
               "message":"This request needs an Idempotency-Key header."}}
```

Send a UUID per logical operation; reuse it for retries of that same operation.

## Step 5 — find the quota/credit state endpoint

Look in the bundle for the page component that renders a balance, then trace its fetch:

```bash
cat chunk_*.js | grep -oiE '.{250}postedToday.{250}'      # availability flag
cat chunk_*.js | grep -oiE '.{250}balance.{250}'          # balance field
```

Endpoints like `GET /api/v1/me` usually return the whole account object (user + balance +
subscription) in one call — cheaper than hunting a dedicated balance route. Probe candidate
paths directly; a wrong path returns a structured error, not a hang:

```bash
for p in /api/v1/energy /api/v1/credits /api/v1/subscription /api/v1/me; do
  printf "%-28s " "$p"; curl -s -m 8 "https://target.tld$p" | head -c 120; echo
done
```

## Pitfalls

- **Grepping with `cat -A` / plain `grep` mangles template literals** — backticks get consumed by
  the shell and the output looks like the source is broken. Dump a line with
  `node -e "console.log(JSON.stringify(require('fs').readFileSync(f,'utf8').split('\n')[34]))"`
  and confirm with `sed -n '35p' f | od -c` when in doubt. A file that renders as `***` in a
  read tool is usually *secret-masking*, not damage — verify with `od -c` and `node --check`.
- **Unauthenticated probes leak nothing but still cost time** — a 200 with
  `{"error":{"code":"UNAUTHENTICATED"}}` means the endpoint exists and needs a session.
- **Auth-gated pages redirect to /login** — `curl` of `/account/energy` returns a 45-byte redirect
  to `https://target.tld/login?next=%2Faccount%2Fenergy`. Use the public chunks (from the landing
  page) plus a session cookie for gated pages.
- **Chunk lists are per-route** — the landing page's chunks may not contain the dashboard's
  energy code; diff two routes' chunk lists and fetch the symmetric difference.
