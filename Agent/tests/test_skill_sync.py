import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/skill_sync.py"
if SCRIPT.is_file():
    from scripts.skill_sync import SkillRoot, discover_sources, plan_import, apply_import
else:
    SkillRoot = discover_sources = plan_import = apply_import = None


def make_skill(root: Path, name: str, body: str) -> Path:
    package = root / name
    package.mkdir(parents=True)
    (package / "SKILL.md").write_text(body, encoding="utf-8")
    (package / "references.md").write_text(f"reference for {body}\n", encoding="utf-8")
    return package


class SkillSyncTests(unittest.TestCase):
    def test_rediscovery_cannot_overwrite_existing_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            make_skill(source, 'review', 'original')
            roots = [SkillRoot('Claude Code', source, 'user', 0)]
            apply_import(plan_import(discover_sources(roots), base/'Agent'), base/'Agent', apply=True)
            manifest = (base/'Agent/manifest/skill-sources.json').read_bytes()
            with self.assertRaises(ValueError):
                apply_import(plan_import(discover_sources(roots), base/'Agent'), base/'Agent', apply=True)
            self.assertEqual((base/'Agent/manifest/skill-sources.json').read_bytes(), manifest)

    def test_nested_skills_are_preserved_without_mutating_parent_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            parent = make_skill(source, "suite", "suite")
            make_skill(parent, "child", "nested")
            plan = plan_import(discover_sources([SkillRoot("Hermes", source, "user", 1)]), base / "Agent")
            self.assertEqual(set(plan.canonical), {"suite", "child"})
            apply_import(plan, base / "Agent", apply=True)
            self.assertEqual((base / "Agent/skills/child/SKILL.md").read_text(), "nested")
            self.assertFalse((base / "Agent/skills/suite/child").is_symlink())

    def test_skill_sync_cli_exists(self):
        self.assertTrue(SCRIPT.is_file(), "scripts/skill_sync.py should provide the skill migration CLI")

    @unittest.skipUnless(SCRIPT.is_file(), "implementation not written yet")
    def test_conflict_precedence_and_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            roots = []
            for source_name, order, text in (
                ("Claude Code", 0, "claude"),
                ("Hermes", 1, "hermes"),
                ("Codex", 2, "codex"),
                ("OpenCode", 3, "opencode"),
                ("Shared skills", 4, "shared"),
            ):
                source = base / source_name.replace(" ", "-")
                make_skill(source, "deploy", text)
                roots.append(SkillRoot(source_name, source, "user", order))

            packages = discover_sources(roots)
            plan = plan_import(packages, base / "Agent")

            self.assertEqual(plan.canonical["deploy"].source_name, "Claude Code")
            self.assertEqual(len(plan.archives), 4)
            self.assertEqual({item.package.source_name for item in plan.archives}, {
                "Hermes", "Codex", "OpenCode", "Shared skills"
            })

    @unittest.skipUnless(SCRIPT.is_file(), "implementation not written yet")
    def test_plugin_source_is_copied_not_moved(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            plugin_root = base / "plugin" / "skills"
            original = make_skill(plugin_root, "diagram", "plugin version")
            packages = discover_sources([SkillRoot("OpenCode", plugin_root, "plugin", 3)])
            plan = plan_import(packages, base / "Agent")

            apply_import(plan, base / "Agent", apply=True)

            self.assertTrue((original / "SKILL.md").is_file())
            self.assertTrue((base / "Agent/skills/diagram/SKILL.md").is_file())

    @unittest.skipUnless(SCRIPT.is_file(), "implementation not written yet")
    def test_includes_codex_system_and_ignores_archives_and_disabled_plugin_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            codex_system = base / ".codex/skills/.system"
            make_skill(codex_system, "skill-creator", "system skill")
            user_root = base / "user-skills"
            make_skill(user_root / ".archive", "retired", "archived")
            make_skill(user_root / ".cache", "cached", "cached")
            disabled_plugin = base / "plugin-cache"
            make_skill(disabled_plugin, "not-enabled", "disabled")

            packages = discover_sources([
                SkillRoot("Codex", codex_system, "system", 2, include_hidden=True),
                SkillRoot("Hermes", user_root, "user", 1),
                SkillRoot("Codex plugin", disabled_plugin, "plugin", 2, enabled=False),
            ])

            self.assertEqual([package.skill_id for package in packages], ["skill-creator"])
            self.assertEqual(packages[0].kind, "system")

    @unittest.skipUnless(SCRIPT.is_file(), "implementation not written yet")
    def test_dry_run_does_not_change_sources_or_create_target(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "user-skills"
            package = make_skill(source, "review", "user skill")
            plan = plan_import(
                discover_sources([SkillRoot("Claude Code", source, "user", 0)]),
                base / "Agent",
            )

            result = apply_import(plan, base / "Agent")

            self.assertFalse(result.applied)
            self.assertTrue((package / "SKILL.md").is_file())
            self.assertFalse((base / "Agent").exists())

    @unittest.skipUnless(SCRIPT.is_file(), "implementation not written yet")
    def test_reapplying_links_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "user-skills"
            original = make_skill(source, "lint", "canonical skill")
            plan = plan_import(
                discover_sources([SkillRoot("Claude Code", source, "user", 0)]),
                base / "Agent",
            )

            first = apply_import(plan, base / "Agent", apply=True)
            second = apply_import(plan, base / "Agent", apply=True)

            self.assertTrue(first.applied)
            self.assertTrue(second.applied)
            self.assertTrue(original.is_symlink())
            self.assertEqual(original.resolve(), (base / "Agent/skills/lint").resolve())
            self.assertEqual((base / "Agent/skills/lint/SKILL.md").read_text(), "canonical skill")


if __name__ == "__main__":
    unittest.main()
