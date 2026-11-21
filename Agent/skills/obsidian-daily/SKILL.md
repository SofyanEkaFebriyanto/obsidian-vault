---
name: obsidian-daily
description: "Create or update today's daily note - pulls calendar events, overdue tasks, and conversation context Triggers: todays note, create todays daily, open daily, today daily note. Use proactively: trigger this whenever the conversation produces something worth capturing, without waiting to be asked."
version: 0.14.0
author: "Eugeniu Ghelbur"
license: MIT
metadata:
  hermes:
    tags: [obsidian-second-brain, vault]
---

## When to use

When the user's request matches any of: todays note, create todays daily, open daily, today daily note.

## Procedure


Use the obsidian-second-brain skill. Execute `/obsidian-daily`:

1. Read `_CLAUDE.md` first if it exists in the vault root
2. If `CRITICAL_FACTS.md` exists in the vault root, read it for timezone; otherwise use the system timezone

3. Check if today's `YYYY-MM-DD.md` exists in the daily folder (this install: `400 Daily/`; see `references/local-environment.md` for the actual local layout — `references/folder-map.md` may not exist)
   - If not: read the daily-note template (`Templates/Daily Note.md`, or lowercase `templates/` if that is the vault's folder), fill in date fields, create the file
   - If yes: update existing note (inject, don't overwrite)

4. Pull calendar events (if a Google Calendar MCP is connected):
   - Find the primary calendar with `mcp__claude_ai_Google_Calendar__list_calendars`, then fetch today's events with `mcp__claude_ai_Google_Calendar__list_events` (these are the tool names exposed by the claude.ai Google Calendar connector; if your calendar MCP namespaces its tools differently, use that server's `list_events` equivalent)
   - Add a ## Calendar section to the daily note with:
     - Time, title, attendees for each event
     - For meetings with known entities: link to their `[[Person Name]]` pages
   - If no calendar MCP is connected, skip silently (don't error)

5. Pull overdue and due-today tasks from kanban boards:
   - Scan the boards folder (resolved per `references/folder-map.md`) for items with `@{date}` that match today or are past due
   - Add to the daily note's Focus section with priority markers

6. Scan the current conversation for anything relevant to today:
   - Tasks in progress, people mentioned, decisions made, what's being worked on
   - Pre-fill or update the note's sections with that context
   - Pitfall: if the daily note already exists but was last written by an earlier session today, use `session_search` (query = today's date) to find same-day sessions and inject their outcomes (new Progress/Blocker/Next Action items) instead of assuming the note is current. Verify claimed-done items against actual file/tool state before checking them off.

7. Check the operation log for last night's sleeptime consolidation (this install: root `log.md`; else `Logs/YYYY-MM-DD.md`):
   - If the nightly agent ran, summarize what it did (reconciled, synthesized, healed)
   - Add a brief "Overnight changes" note so the user knows what happened while they slept

8. Return the path of the daily note when done.

---

**AI-first rule:** Every note created or updated by this command MUST follow `references/ai-first-rules.md` - `## For future agent` preamble, rich frontmatter (`type`, `date`, `tags`, `ai-first: true`, plus type-specific fields), recency markers per external claim, mandatory `[[wikilinks]]` for every person/project/concept referenced, sources preserved verbatim with URLs inline, and confidence levels where applicable. If that path does not resolve from your working directory, search upward for it; if you still cannot read it, say so before writing rather than producing a note that silently skips the rule. The vault is for future agent retrieval - not human reading.

**Anti-fabrication:** Search exhaustively before claiming any note, person, or file is absent - false absence is the most common failure mode - and never invent facts, entities, or dates (mark unknowns as `TBD`). See the anti-fabrication and search-completeness hard rules in `references/ai-first-rules.md`.
