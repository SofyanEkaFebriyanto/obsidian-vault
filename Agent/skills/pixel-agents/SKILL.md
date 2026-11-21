---
name: pixel-agents
description: Operate the Pixel Agents office (standalone server :3100, user-systemd pixel-agents.service) — debug agent visibility/despawn issues and hook integration with Hermes.
version: 1.0.0
---

# Pixel Agents Office Ops

Standalone server: user-systemd `pixel-agents.service` (node dist/cli.js --port 3100), repo at ~/hermes-agent-pixel/pixel-agents (server code in server/src/, docs in CLAUDE.md there). Hermes plugin `pixel_observer` (~/.hermes/plugins/pixel_observer/) POSTs lifecycle hooks to http://127.0.0.1:<port>/api/hooks/hermes with bearer token from ~/.pixel-agents/server.json.

## Debug playbook

- Health: `systemctl --user status pixel-agents.service`; discovery file ~/.pixel-agents/server.json holds {port, pid, token}.
- State on disk: ~/.pixel-agents/standalone-state.json — lists live agents + seats. Stale seat entries without matching agents = previously despawned characters.
- API needs auth; unknown paths return the SPA HTML — a 200 HTML response does NOT mean the endpoint exists.

## Key behavior: external agents despawn on session end (by design)

Hermes sessions/subagents are registered as `isExternal: true`. In server/src/agentRuntime.ts, an incoming `session_end` hook event for an external agent triggers unregisterAgent + removeAgent — the character is removed server-side immediately when its session/subagent finishes.

Consequence: users perceive "agents disappear on browser refresh". The refresh is innocent — the webview just re-reads already-pruned state. Characters only exist while their session is alive; subagents appear during delegation and despawn on completion.

To make characters persistent instead: patch the `if (agent.isExternal)` branch in `onSessionEnd` in agentRuntime.ts to use an idle timeout (e.g. remove after 30 min with no events), then rebuild the server.
