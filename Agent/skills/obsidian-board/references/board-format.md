# Kanban board format & local board

## Format rules (kanban exception)
- Frontmatter: `kanban-plugin: board` (with `---` fences, blank line after)
- NO `## For future agent` heading — the Obsidian Kanban plugin renders it as a phantom column
- Items: `- [ ] text @{YYYY-MM-DD}` — the `@{date}` is the only age/overdue signal
- Done items: `- [x] ~~text~~` style with date, moved under ✅ Done column
- Columns are `## Emoji Heading` sections; end file with a `%% ... %%` comment (convention: plugin credit line)

## Local board (sofyan's vault)
Path: `/home/sofyan/Documents/Obsidian Vault/boards/Board.md`
Columns: 📥 Backlog / 🔨 Doing / ✅ Done
Known backlog: sync vault→VPS SG is ON HOLD at user request — do not auto-promote it to Doing.

## Overdue flagging
Past-due = `@{date}` earlier than today. In-progress items more than a week past their date need explicit escalation, not silent leave-in-place. Never guess dwell time from column position.
