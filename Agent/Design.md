# Shared Agent Skills and MCP Vault

**Status:** Approved  
**Target:** `/home/sofyan/Documents/Obsidian Vault/Agent`

## Intent

Create one Obsidian vault for the user's installed skills and MCP catalog so Claude Code, Hermes, Codex, and OpenCode share one portable skill set and one logical MCP inventory.

## Goals

- Consolidate local user skills from OpenCode, Codex, Claude Code, Hermes, and `~/.agents/skills`.
- Include skill packages from actively enabled plugins, but not plugin catalog/cache entries that are not enabled.
- Copy file-backed, system-managed skill packages found under Codex's `.system` skill folder into the common set without modifying that source; native built-ins that are not portable `SKILL.md` packages remain native.
- Make each client resolve the same canonical skill package for each shared skill ID.
- Preserve losing/conflicting source variants in the vault and leave plugin/built-in features enabled.
- Make the 13 explicitly configured user-level MCP server names available in all four clients through native per-client configuration adapters.
- Keep resolved tokens, API keys, and OAuth state out of the vault.

## Non-goals and limitations

- Exporting or replacing agent-native bundled skills that are not portable `SKILL.md` packages.
- Disabling plugins or bundled features. They may continue to expose additional or duplicate native skills in the client where installed; the common migrated set remains identical.
- Rewriting skill instructions to remove client-specific tool references. Some shared skills may need a later portability pass if their source instructions reference tools unavailable elsewhere.
- Sharing authentication state or credentials between clients.
- Migrating project-specific MCP servers, unenabled plugin-cache entries, or server functionality exposed only by a built-in/plugin integration.

## Inventory and constraints

- The existing vault is `/home/sofyan/Documents/Obsidian Vault`; `Agent/` did not exist before planning.
- Current inventory across user skill folders, actively enabled plugin skill folders, and Codex `.system` file-backed skill packages is 262 unique skill IDs. 136 IDs occur in multiple sources; 108 have divergent `SKILL.md` content.
- The discovered skill-package files currently occupy about 75 MiB across those sources; the vault will hold consolidated packages and alternate variants, so its size will grow by roughly that amount. No Git commit will be made.
- The explicit user-level MCP union is 13 logical server names. Some same-name servers use different existing transports/endpoints, so the catalog represents logical parity, not byte-identical transport settings.
- The target vault is a Git repository. Do not commit changes automatically.
- Per-client configurations use different formats; no common config file can be consumed directly by all four clients.
- Existing local skill entries can shadow external skills, particularly in Hermes. Old entries must be archived and replaced/redirected before claiming a single active set.

## Approaches considered

1. **Canonical shared tree with per-client discovery links and MCP adapters (selected):** one canonical skill directory per ID; archive divergent package versions; link each client to the canonical tree. Maintain a secret-free MCP catalog and generate/merge each client's native config. This best matches the user's request while preserving rollback.
2. **Register all source trees unchanged:** preserves every installation in place, but duplicate skills can resolve differently across clients, so agents may use different contents.
3. **Copy independent sets into each client:** allows client-specific tuning, but updates drift and the clients no longer share one source.

## Design

```text
Agent/
├── .obsidian/              # separate Obsidian vault settings directory
├── Design.md
├── Implementation Plan.md
├── README.md
├── skills/                 # canonical active packages, one directory per skill ID
├── sources/                # non-canonical/conflicting package variants for recovery
└── mcp/
    ├── catalog.yaml        # logical 13-server inventory; no secret values
    └── sync.py             # validate catalog and merge native per-client settings
```

For each skill ID, select the complete package using this precedence: **Claude Code → Hermes → Codex → OpenCode → shared `~/.agents/skills`**. Within one client, prefer its user skill folder over a plugin-provided copy. Move the selected package from a user skill folder into `Agent/skills/<id>/`; copy it instead when its source is an installed plugin package, leaving the plugin untouched. Preserve each non-selected package in `Agent/sources/<client>/...`. Keep skill text and supporting files intact. Replace only skill entries in each local discovery root with links to the canonical package where needed; preserve unrelated files and agent metadata. Configure Hermes to create new skills in the canonical directory, and configure OpenCode to search it directly. Keep plugins installed and their native skills active.

The migration includes local user skill folders, enabled plugin packages, and file-backed Codex `.system` skill packages. It excludes non-file-backed agent-native bundles, plugin catalogs, and cached-but-disabled plugin packages. Native skills/plugins may remain as extra platform-specific entries; this does not alter the identical common set.

The MCP catalog contains the union of 13 active, explicitly configured user-level server names from the four clients. For an existing server such as Context7, preserve its current per-client configured transport/endpoint rather than forcing a potentially disruptive transport change. Per-client MCP configs are user-global. Keep current OAuth sessions in each client's credential store; use environment-variable references for new secret-bearing config fields. A configured server may still need separate sign-in or an environment variable in a client where it was not previously authenticated. Some currently configured servers already report connection/authentication issues; report those separately rather than treating configuration presence as a healthy connection.

The vault catalog is the source of truth for future MCP inventory changes. `sync.py` validates and applies the catalog without overwriting unrelated settings, and offers a check mode for drift. Skill edits made through discovery links update the canonical package. Make timestamped, permission-restricted local backups of configs before editing; do not place config backups or credential values in the Obsidian vault.

## Verification

- Compare the canonical ID manifest with each client's discovered common skill set, and confirm stale local entries no longer shadow canonical versions.
- Validate each native config and compare the 13 logical MCP names across all four clients.
- Report server connectivity/authentication separately from configuration presence.
- Confirm that plugin/native skills remain enabled, all non-selected package versions are recoverable, and no resolved credentials entered the vault.
- Run the migration's dry-run/check mode before applying and verify changes after application.

## Implementation calls

- Create the vault only after approval; stage and verify copies before replacing any local skill entries.
- Use timestamped local backups and a reversible manifest of created symlinks/config changes.
- Do not modify plugin installs, caches, built-in skill sets, unrelated user settings, or the repository's Git history.
