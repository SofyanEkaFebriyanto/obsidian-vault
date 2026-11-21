---
name: obsidian-vault-ops
description: Operate the Obsidian vault as agent second-brain — obsidian-second-brain plugin layout, Python health/lint helpers, vault conventions, and gotchas.
---

# Obsidian Vault Ops

Covers the installed third-party plugin (eugeniughelbur/obsidian-second-brain)
and the operational vault structure. The base file-level `obsidian` skill
(bundled) covers read/write/search of notes; this skill covers the plugin tooling.

## Installed layout (Hermes build)
- Skills: `~/.hermes/skills/obsidian-second-brain/` — subdirs `vault/`, `meta/`,
  `research/`, `thinking/` each contain `<command>/SKILL.md` (~46 commands:
  obsidian-save, obsidian-find, obsidian-daily, obsidian-health, research, ...).
- Shared specs/helpers referenced by those skills live at the INSTALL ROOT:
  `references/` and `scripts/` directly under `obsidian-second-brain/`.
  That root path is load-bearing — skills resolve spec files relative to it.
  Update via: clone repo → `bash scripts/build.sh --platform hermes` → copy
  `dist/hermes/skills|references|scripts` into the install root.

## Python helpers
Run from the install root, never bare (`scripts/` must resolve there):
```
uv run --directory ~/.hermes/skills/obsidian-second-brain python scripts/<name>.py --path "<vault>"
```
Key scripts: `vault_health.py --path <vault> [--json]`,
`link_graph.py --path <v> --lint`, `freshness_lint.py --path <v> --json`,
`triage_links.py --path <v>`.
Requires `uv` (~/.local/bin/uv).

## Vault path
`OBSIDIAN_VAULT_PATH` in `~/.hermes/.env`. Fallback `~/Documents/Obsidian Vault`.

## Vault conventions (Karpathy LLM Wiki / OKM pattern)
Folder structure in use (adapted from creativeagentic.id Mac-mini/VPS tutorial,
local machine as primary instead of Mac mini):
- `000 Index.md` dashboard · `00 Inbox.md` capture
- `100 Projects/` · `200 Context/` (incl. `210 hermes-agent/index.md` MOC)
- `300 Decisions/` · `400 Daily/templates/` · `500 Resources/`
- Every section has a `000 * Index.md`; notes carry frontmatter
  (type/status/date/tags) so health check stays clean.

Rules: raw sources immutable, synthesis into atomic notes + wikilinks,
no secrets in notes, read-back before claiming a write succeeded,
capture jobs output [SILENT] when nothing of value.
Optional one-way sync model: local primary → VPS pull (never push), not yet armed.

## Plugin troubleshooting pattern
When a Hermes plugin "doesn't work", check in order: (1) is it in config.yaml `plugins.enabled`; (2) is the server/port actually up (`curl http://127.0.0.1:<port>`); (3) plugin load lines in `~/.hermes/logs/agent.log` (`grep -i <name>`); (4) plugins only load at process start — a session started before enabling will never pick it up; restart fixes it. Example: pixel-office (port 8113, `/state` endpoint shows live agents).

## Session lessons (2026-08-25)
- Always pass the vault path explicitly to vault_health.py (`--path "<vault>"`); running it with `.` from the wrong cwd silently scans the skills directory instead (57 false notes).
- Before ticking a Next Action checkbox as done, grep the actual file — a daily note said "fix minor" was pending while an earlier summary implied it was applied; half of it wasn't.
- Bulk-fill empty notes from agent memory in one pass: write project notes with frontmatter (type/status/last-updated/ai-first), mark unverified details TBD instead of inventing, then update all index files so nothing stays orphaned.
- When a session changes local tooling (e.g. pixel-office → pixel-agents bridge swap), update daily note + Hermes MOC + Resources Index in the same pass, and log to log.md.

## Pixel office / pixel_observer
Final stack: bridge github.com/aiunlocked1412/hermes-agent-pixel (hermes-pixel-office disabled). Server = fork Pixel Agents at ~/hermes-agent-pixel/pixel-agents, run `node dist/cli.js --port 3100`, UI http://127.0.0.1:3100, discovery ~/.pixel-agents/server.json. Plugin pixel_observer enabled with allow-tool-override; takes effect next Hermes session. Server has no auto-start yet (candidate: user-systemd). Upstream pixel-agents alone does NOT support Hermes — only Claude Code.

## Health-check gotchas
- Run `vault_health.py` with an absolute `--path` to the VAULT directory, not `.` — if cwd happens to be the skills install root it scans SKILL.md files too and reports their format-example wikilinks (`[[X]]`, `[[note A]]`) as Wanted Notes. Those hits are noise, not vault problems.
- Before ticking a `[ ]` Next Action as done in a daily note, grep the vault to verify the fix was actually applied — prior sessions can claim fixes they never made (happened 2026-08-25: "fix [[00 Inbox]] link" was checked off but the link wasn't there).
- A wikilink written as a format example in an index (e.g. `[[YYYY-MM-DD judul]]`)
  registers as a wanted note. Use HTML comments for format examples.
- Orphan reports for inbox/dashboard notes are normal; link from 000 Index if noisy.
- Operation log convention: append `## [date] op | counts` to `log.md` unless a
  `Logs/` folder exists. `log.md` itself must carry frontmatter (type/status/tags)
  or the health check flags it as missing-frontmatter.
- A format-example wikilink in an index that is NOT already wrapped in an HTML
  comment (e.g. `<!-- format: [[X]] -->`) registers as a Wanted Note — wrap all
  format examples in comments.
- New raw dumps (memory pulls, transcripts, SSH captures) belong in
  `500 Resources/`, not the vault root; give them full frontmatter
  (type: resource, status, source, pulled, tags) and link them from the
  Resources Index plus any relevant MOC (e.g. Hermes Agent MOC "remote
  instances" section). Replace placeholder wikilinks like `[[Hermes]]` with
  real path-qualified links so no wanted-notes appear.
- Proven pull-remote-memory pattern (2026-08-25): ssh with `-o
  StrictHostKeyChecking=accept-new`, cat `~/.hermes/memories/{MEMORY,USER}.md`
  plus each `~/.hermes/profiles/<name>/memories/`, write one note per source
  group into `500 Resources/`, then update Context MOCs with the infra facts
  learned (nodes, ports, keys) — dump notes stay immutable raw sources;
  synthesis goes into the MOCs.

## Templates
- `templates/daily-note.md` — daily note with provenance + READBACK_OK footer.

## Session lessons (2026-08-29)
- `triage_links.py` needs `ANTHROPIC_API_KEY` (prints `set ANTHROPIC_API_KEY` and exits). The other three helpers are stdlib-only and always runnable.
- `freshness_lint.py` FRESH-3 fires on any `word:word` token it reads as a typed pointer (`schedule:run`, `custom:Local`, `custom:9router`). Two clean fixes: wrap the token in inline code (backticks are stripped before the check), or add `freshness: snapshot` to the frontmatter of raw-dump notes — that exempts the whole file, which is correct for immutable memory/transcript dumps. Do NOT invent a `.freshness.json` just to silence one token.
- The memory→vault sync hook fires on EVERY `memory` tool call, so `log.md` grows one identical `auto | memory→vault mirror updated` line per call (90+ lines by day 5). Fixed by making `~/.hermes/agent-hooks/memory-vault-sync.py` idempotent per day: build `marker = f"- {today} auto | ..."` and only append when `marker not in log.read_text()`. Verify by piping two fake payloads into the hook and confirming the grep count stays flat.
- Wanted-notes that name a **skill or a file outside the vault** (`[[kenfa-ceo]]`, `[[plan]]`) should become inline code, not new notes — creating stub notes for them pollutes the graph. Wanted-notes that name a real concept with an existing MOC (`[[Hermes Agent]]`) get repointed to the path-qualified target (`[[200 Context/210 hermes-agent/index|Hermes Agent]]`).
- Keep `000 Index.md`'s "Daily hari ini" link pointing at the newest daily; a stale link there is invisible to the health check but wrong for a human entry point. Linking `boards/Board` from the index also clears its permanent orphan status.
