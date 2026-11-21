import importlib.util
from pathlib import Path
import tempfile
import unittest


class RegistrationTests(unittest.TestCase):
    def test_links_add_new_packages_without_replacing_unrelated_directories(self):
        from scripts.skill_sync import register_links
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            canonical = base / "Agent/skills"
            (canonical / "review").mkdir(parents=True)
            (canonical / "review/SKILL.md").write_text("review")
            local = base / "client/skills"
            (local / "metadata").mkdir(parents=True)
            (local / "metadata/state").write_text("keep")
            register_links(canonical, [local])
            register_links(canonical, [local])
            self.assertTrue((local / "review").is_symlink())
            self.assertEqual((local / "metadata/state").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
