# Pixel Agents + Hermes bridge — troubleshooting & verification recipes

Session-proven fixes for the Hermes↔Pixel Agents stack (fork at
~/hermes-agent-pixel/pixel-agents, server :3100, plugin pixel_observer).

## Bug: subagent characters appear then vanish (~seconds later)

**Symptom:** office shows nothing during delegate_task fan-out even though
server logs show `subagent_start`.

**Diagnosis path (2026-08-25):**
1. Server logs: `journalctl --user -u pixel-agents.service --since ... | grep -iE "subagent|error"`
2. Found: `subagent_start` fired 3x, immediately followed by
   `Removing teammate N (source: team-config)`.

**Root cause:** `scanTeamConfigsForRemovals()` in
`server/src/fileWatcher.ts` treats any teammate with a teamName as a Claude
Code team member and culls it when `~/.claude/teams/<team>/config.json`
is missing (reads as "team dissolved"). Hermes teammates have no such config.

**Fix (applied):** skip non-Claude providers inside the cull loop:
```ts
if (agent.providerId && agent.providerId !== 'claude') continue;
```

## Rebuild after server source change

```
cd ~/hermes-agent-pixel/pixel-agents && npm run build   # ~5-8 min, run background
systemctl --user restart pixel-agents.service
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3100/   # expect 200
```

## Verifying a patched exported function without re-implementing it

Re-typing the function inside a test fixture caused two false failures
(transcription drift). Proven pattern instead:

1. Regex-extract the real function body from the TypeScript source.
2. Strip types using the repo's own esbuild:
   `<repo>/node_modules/.bin/esbuild --loader=ts` (pipe source in).
3. Rewrite module-level deps into injected params (e.g. `teamProvider` → param)
   and eval via `new Function`.
4. Assert behavior on fixtures AND assert the guard string exists in the
   compiled bundle (`dist/cli.js`) so you know the running build has the fix.
5. Include a no-regression case (old correct behavior still works) and a
   fixture-strength check (prove pre-patch logic would have failed).

Keep it as an ad-hoc `/tmp/hermes-verify-*.mjs` script, print PASS/FAIL lines,
delete after run. This is ad-hoc evidence — say so explicitly; do not call it
"suite green".

## Misc quirks

- POSTing to `/api/hooks/hermes` without `Content-Type: application/json`
  returns Fastify 415 — harmless noise, but don't confuse it with auth failure.
- Auth/discovery comes from `~/.pixel-agents/server.json` ({port, token});
  plugin env overrides: `PIXEL_AGENTS_URL`, `PIXEL_AGENTS_TOKEN`.
