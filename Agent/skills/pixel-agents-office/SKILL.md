---
name: pixel-agents-office
description: "Operate & debug the Pixel Agents office (standalone server on :3100) with the Hermes pixel_observer plugin — architecture, event flow, and debugging when characters don't appear or vanish. Trigger: pixel agents, office kosong, karakter hilang, :3100, pixel_observer, HermesBridge."
version: 1.0.0
---

# Pixel Agents Office + Hermes Integration

## Architecture
- Standalone server: `~/hermes-agent-pixel/pixel-agents` (Node/Fastify), run as user-systemd unit `pixel-agents.service` (`node dist/cli.js --port 3100`, enabled+linger).
- Discovery/auth for hooks: `~/.pixel-agents/server.json` ({port, token}). Events POST to `/api/hooks/hermes` with Bearer token.
- Hermes side: plugin `pixel_observer` in `~/.hermes/plugins/` — registers lifecycle hooks (on_session_start, pre/post_tool_call, subagent_start/stop, ...) and POSTs each as JSON via a FIFO daemon thread. Stdlib-only, non-blocking.
- Server side: `HermesBridge` (server/src/hermesBridge.ts) turns events into AgentStateStore entries → WS broadcast → webview characters.
- Subagent model: each delegate_task child = independent session rendered as a "teammate" character via the `subagent_start` hook (teamName 'Hermes', leadAgentId = parent).

## Debugging: office empty / characters vanish

Debug order:
1. `journalctl --user -u pixel-agents.service --since "30 min ago"` — look for `[Pixel Agents] Hermes:` lines proving events arrive, plus `subagent_start`/`Removing teammate` lines.
2. If events arrive but characters vanish seconds after appearing, grep logs for `Removing teammate ... (source: team-config)`.

### Known bug (fixed 2026-08-25): team-config culling
`scanTeamConfigsForRemovals()` in `server/src/fileWatcher.ts` periodically removes teammates whose Claude team config is missing. The Claude TeamProvider reads `~/.claude/teams/<teamName>/config.json`; a Hermes teammate with `teamName: 'Hermes'` has no such file → provider returns null ("dissolved") → all Hermes characters culled ~seconds after spawn.

Fix: skip non-Claude providers in that scanner:
```ts
if (agent.providerId && agent.providerId !== 'claude') continue;
```
(Also present in the stale-JSONL despawn scanner further down the same file.)

## Rebuild & restart (slow build!)
```
cd ~/hermes-agent-pixel/pixel-agents && npm run build   # takes ~5-8 min (tsc+eslint+esbuild+vite)
systemctl --user restart pixel-agents.service
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3100/   # expect 200
```
Note: `dist/cli.mjs` does not exist — bundle is `dist/cli.js`.

## Verifying changes (ad-hoc pattern)
Don't re-implement the function under test in your fixture — transcription drift causes false failures. Instead: regex-extract the real function from TS source, strip types with the repo's own esbuild (`node_modules/.bin/esbuild --loader=ts`), then execute it against fixtures. Ready-made script: `scripts/verify-teammate-guard.mjs` (run `node <skill_dir>/scripts/verify-teammate-guard.mjs`; exit 0 = guard verified).
Fixture expectations must match the guard's SCOPE, not just "nothing removed": the providerId guard only protects non-Claude agents. A dissolved-team scan still culls a stale Claude teammate (correct behavior) — assert per-agent survival, e.g. "Hermes ids spared" AND "claude id culled", or the verification false-FAILs even when the patch is right.

## Pitfalls
- POSTing to the hook endpoint without `Content-Type: application/json` → Fastify 415 Unsupported Media Type (curl -d defaults to form-urlencoded).
- esbuild normalizes quotes: grep compiled bundles quote-agnostically (`['"]claude['"]`) or you'll false-FAIL.
- Plugin/server code changes only take effect after rebuild + service restart.
