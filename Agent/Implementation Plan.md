# Shared Agent Skills and MCP Vault Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for implementation after this plan is approved. Complete tasks in order and verify before changing real user configuration.

**Goal:** Consolidate 262 discovered skill IDs and 13 logical MCP servers into `/home/sofyan/Documents/Obsidian Vault/Agent` and make the same common skill set and MCP inventory available to Claude Code, Hermes, Codex, and OpenCode.

**Architecture:** Keep canonical skill packages under `Agent/skills`, preserve non-canonical variants under `Agent/sources`, and use per-client discovery links/settings. Maintain a secret-free `Agent/mcp/catalog.yaml`; a Python synchronizer will validate it, update only managed server entries, and support dry-run/check mode.

**Tech Stack:** Python 3.11+, `unittest`, installed agent CLIs, JSON/TOML/YAML user configs. Use existing PyYAML for YAML operations; do not install dependencies without approval.

**Spec:** `Design.md`

## Global Constraints

- Target: `/home/sofyan/Documents/Obsidian Vault/Agent`.
- Skill conflict precedence: Claude Code → Hermes → Codex → OpenCode → shared `~/.agents/skills`.
- Keep plugins and agent-native bundled skills enabled; do not modify plugin installs or caches.
- The common MCP catalog contains 13 logical user-level servers; preserve each existing per-client configured transport/endpoint.
- Keep resolved tokens, API keys, and OAuth state out of the vault; do not run interactive OAuth flows.
- Make timestamped, permission-restricted local config backups before editing; preserve unrelated settings.
- Do not commit or rewrite Git history.

## Review Focus

- Duplicate skill names and package variants: the winning package follows the exact precedence above and every non-winning package stays recoverable. Test: `test_conflict_precedence_and_archive` in Task 1.
- Plugin packages: import their skill packages without moving or editing plugin files. Test: `test_plugin_source_is_copied_not_moved` in Task 1.
- Hidden/archived skill directories and disabled plugin caches: include only the explicitly inventoried file-backed Codex `.system` packages, and skip other hidden/archive/cache entries. Test: `test_includes_codex_system_and_ignores_archives_and_disabled_plugin_cache` in Task 1.
- Secrets in MCP config: catalog, dry-run output, and logs must contain no resolved credential value. Test: `test_catalog_uses_env_refs_not_secret_values` in Task 3.
- Existing MCP config and connection health: retain unrelated settings and local per-client transport differences; report configured/authenticated/connected as distinct states. Tests: `test_config_merge_preserves_unmanaged_keys` in Task 3 and the CLI checks in Task 5.

---

### Task 1: Skill inventory, conflict selection, and archive/import tool

**Files:**
- Create: `scripts/skill_sync.py`
- Create: `tests/test_skill_sync.py`
- Create: `manifest/skill-sources.json`
- Create: `README.md`
- Create: `.obsidian/` as a vault marker, without copying settings or plugin state from the parent vault.

**Interfaces:**
- `discover_sources() -> list[SkillPackage]` reads the known user skill roots, file-backed Codex `.system` skill packages, and currently enabled plugin skill roots only.
- `SkillPackage` contains `skill_id`, `source_name`, absolute `source_path`, package kind (`user`, `plugin`, or `system`), source-relative path, and SHA-256 digest.
- `plan_import(packages) -> ImportPlan` resolves one canonical package per ID using the approved precedence, records non-winning sources, and proposes reversible links.
- `ImportPlan` contains canonical package selections, archive destinations, source actions (`move` for user packages; `copy` for plugin and Codex `.system` packages), and client link actions. Never replace the Codex `.system` source entries with links.
- `apply_import(plan, target_root) -> ImportManifest` performs the staged copy/move/archive/link operations. `--dry-run` is the default; `--apply` is required to mutate source roots.

- [ ] **Step 1: Write tests** for precedence, non-winning package preservation, enabled-plugin and Codex `.system` copy semantics, archive/cache exclusion, idempotency, and dry-run non-mutation.
- [ ] **Step 2: Run tests and confirm expected failures** with `python3 -m unittest discover -s tests -p 'test_skill_sync.py' -v`.
- [ ] **Step 3: Implement** the package discovery and dry-run import planner; do not print file contents or secret-bearing config values.
- [ ] **Step 4: Run tests and confirm they pass** with `python3 -m unittest discover -s tests -p 'test_skill_sync.py' -v`.
- [ ] **Step 5: Run the dry-run against the real skill roots** and confirm it reports 262 IDs, 136 repeated IDs, 108 divergent `SKILL.md` copies, and no files changed.

### Task 2: Apply canonical skill tree and register discovery

**Files:**
- Modify: `scripts/skill_sync.py`
- Modify: `manifest/skill-sources.json`
- Modify global settings: OpenCode, Codex, Claude Code, and Hermes user-level skill discovery settings/roots.
- Create: local timestamped backups of any settings file before modification; keep backups outside the vault.

**Interfaces:**
- Consume `ImportPlan` and `apply_import()` from Task 1.
- Produce `Agent/skills/<id>/SKILL.md`, preserved variants under `Agent/sources/`, and a reversible link/config manifest.

- [ ] **Step 1: Add tests** that a repeated apply is idempotent, only skill entries are linked, and unrelated entries/files remain untouched.
- [ ] **Step 2: Run tests and verify failure** with `python3 -m unittest discover -s tests -p 'test_skill_sync.py' -v`.
- [ ] **Step 3: Implement per-client registration:** symlink user skill entries to canonical packages where required; leave Codex `.system` entries untouched; add the canonical path to OpenCode; set Hermes external/create skill paths; preserve Codex and Claude config metadata.
- [ ] **Step 4: Re-run tests** with `python3 -m unittest discover -s tests -p 'test_skill_sync.py' -v` and verify all links resolve inside `Agent/skills`.
- [ ] **Step 5: Show and review the real-root dry-run**, then apply only after confirming every source path and backup destination.

### Task 3: Secret-free MCP catalog and safe synchronizer

**Files:**
- Create: `mcp/catalog.yaml`
- Create: `mcp/sync.py`
- Create: `tests/test_mcp_sync.py`
- Modify: `README.md`

**Interfaces:**
- `load_catalog(path) -> Catalog` validates unique names, supported transports, per-client overrides, and environment-variable references.
- `plan_sync(catalog, client_configs) -> SyncPlan` computes managed additions/updates without changing unrelated settings or replacing existing auth state.
- `apply_sync(plan, dry_run=True)` writes only managed MCP entries; default is dry-run. `--check` reports inventory drift without writing.
- A `CatalogServer` has a logical name and a per-client adapter definition; secret-bearing values are represented only as environment-variable references.

- [ ] **Step 1: Write tests** for the 13-server union, per-client overrides (including existing Context7 differences), unmanaged-key preservation, dry-run behavior, and secret-value exclusion.
- [ ] **Step 2: Run tests and verify failure** with `python3 -m unittest discover -s tests -p 'test_mcp_sync.py' -v`.
- [ ] **Step 3: Implement catalog parsing and native adapters** for OpenCode JSON/JSONC, Codex TOML, Claude Code JSON, and Hermes YAML. Keep secrets only in existing client stores or environment references; do not log them.
- [ ] **Step 4: Run tests** with `python3 -m unittest discover -s tests -p 'test_mcp_sync.py' -v` and validate config serialization by parsing generated temporary configs with native parsers/CLIs.
- [ ] **Step 5: Populate the catalog from the 13 configured user-level MCP definitions** using secret-redacted fields; retain current client-specific transports even when a connection is currently unhealthy; mark any server that needs client-local sign-in or environment setup.

### Task 4: Apply MCP settings and complete shared-vault documentation

**Files:**
- Modify: `mcp/catalog.yaml`, only if dry-run review finds a correction.
- Modify: the four clients' user-global MCP settings.
- Modify: `README.md` with commands for future catalog edits, sync, drift check, backups, and rollback.

- [ ] **Step 1: Run `mcp/sync.py --check` and save a redacted dry-run report**; expected server-name set is identical across all four clients.
- [ ] **Step 2: Back up each affected user config locally** with restrictive permissions, then run `mcp/sync.py --apply`.
- [ ] **Step 3: Validate each config** with its parser/CLI and confirm all 13 logical server names are present without changing unrelated settings.
- [ ] **Step 4: Confirm required credentials remain client-local**; do not launch OAuth automatically. Mark unauthenticated servers as configured but awaiting the user's login/env setup.

### Task 5: End-to-end verification and handoff

**Files:**
- Modify: `README.md`
- Create: `manifest/verification.json` with IDs/names/status only; no skill bodies, credentials, or raw configs.

- [ ] **Step 1: Run all unit tests** with `python3 -m unittest discover -s tests -v`.
- [ ] **Step 1a: Verify vault recognition** by confirming `Agent/.obsidian/` exists and opening the directory as its own Obsidian vault does not alter parent-vault settings.
- [ ] **Step 2: Verify skill discovery** in each client; confirm the 262-ID common set, no stale local shadowing, and recoverable source variants.
- [ ] **Step 3: Verify MCP inventory** using native config/list/get commands; compare configured names separately from connection/authentication status.
- [ ] **Step 4: Run the secret scan** against `Agent/` and verify no resolved credentials or copied config backups are present.
- [ ] **Step 5: Report** totals, client-specific extra native/plugin skills, MCP connection/authentication blockers, backup paths, and rollback steps. Do not commit.
