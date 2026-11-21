# Local vault environment (sofyan's Fedora machine)

Session-specific facts discovered 2026-08-25. `references/folder-map.md` does NOT exist in this install — resolve folders by inspection:

- Vault path: `/home/sofyan/Documents/Obsidian Vault` (env `OBSIDIAN_VAULT_PATH` in `~/.hermes/.env`)
- Structure: Obsidian-style hybrid — `400 Daily/YYYY-MM-DD.md`, `100 Projects/`, `200 Context/`, `300 Decisions/`, `500 Resources/`, `boards/Board.md` (kanban), root `log.md` for operation log entries
- Daily template lives at `400 Daily/templates/`
- No `_CLAUDE.md`, no Google Calendar MCP connected → skip Calendar section silently

## Vault automation state (as of 2026-08-25)
- Cron nightly consolidation 02:30 WIB + weekly maintenance Senin 03:00 (deliver local)
- Kanban format: `kanban-plugin: board` frontmatter, NO `## For future agent` heading, items carry `@{YYYY-MM-DD}` dates

## Related infra on this machine
- Pixel Agents office server auto-starts via user-systemd `pixel-agents.service` (:3100); plugin `pixel_observer`. Not part of the vault, but daily-note decisions often reference it.
- User preferences embedded here: sync vault→VPS is ON HOLD at user request; user prefers user-systemd units over system services.
