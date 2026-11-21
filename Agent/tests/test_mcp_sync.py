import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "mcp/sync.py"


class McpTests(unittest.TestCase):
    def test_local_controls_and_catalog_updates(self):
        m = self.load()
        original = {'mcpServers': {'db': {'disabled': True, 'command': 'old', 'env': {'MYSQL_HOST': 'old', 'TOKEN': 'private'}}}}
        merged = m.merge_servers(original, 'claude', {'db': {'command': 'new', 'env': {'MYSQL_HOST': 'new', 'TOKEN': '${TOKEN}'}}})
        self.assertTrue(merged['mcpServers']['db']['disabled'])
        self.assertEqual(merged['mcpServers']['db']['env']['MYSQL_HOST'], 'new')
        self.assertEqual(merged['mcpServers']['db']['env']['TOKEN'], 'private')

    def test_removed_managed_server_leaves_unmanaged_server(self):
        m = self.load()
        merged = m.merge_servers({'mcpServers': {'old': {}, 'personal': {}}}, 'claude', {}, previously_managed=['old'])
        self.assertEqual(set(merged['mcpServers']), {'personal'})

    def test_catalog_rejects_literal_secrets_and_codex_aliases(self):
        m = self.load()
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'catalog.yaml'
            p.write_text('servers:\n  test:\n    default:\n      command: server\n      env:\n        API_TOKEN: literal-secret\n')
            with self.assertRaises(ValueError): m.load_catalog(p)
        with self.assertRaises(ValueError):
            m.adapt({'command': 'server', 'env': {'SERVER_TOKEN': {'env': 'SHARED_TOKEN'}}}, 'codex')

    def load(self):
        self.assertTrue(SCRIPT.exists(), "MCP synchronizer must exist")
        spec = importlib.util.spec_from_file_location("mcp_sync", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_catalog_uses_env_refs_not_secret_values(self):
        m = self.load()
        result = m.sanitize_server({"command": "server", "args": [],
                                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "fixture-secret", "MYSQL_PASS": "db-fixture-secret", "MYSQL_PORT": "3306"}})
        self.assertNotIn("fixture-secret", json.dumps(result))
        self.assertNotIn("db-fixture-secret", json.dumps(result))
        self.assertEqual(result["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"], {"env": "GITHUB_PERSONAL_ACCESS_TOKEN"})
        self.assertEqual(result["env"]["MYSQL_PORT"], "3306")

    def test_config_merge_preserves_unmanaged_keys(self):
        m = self.load()
        original = {"model": "custom", "mcpServers": {"github": {"command": "old", "env": {"TOKEN": "keep-private"}}}}
        merged = m.merge_servers(original, "claude", {"github": {"command": "new", "args": [], "env": {"TOKEN": "${TOKEN}"}}})
        self.assertEqual(merged["model"], "custom")
        self.assertEqual(merged["mcpServers"]["github"]["env"]["TOKEN"], "keep-private")
        self.assertEqual(original["mcpServers"]["github"]["command"], "old")

    def test_native_adapters_keep_transport_and_environment_references(self):
        m = self.load()
        server = {"command": "node", "args": ["server.js"], "env": {"TOKEN": {"env": "TOKEN"}}}
        self.assertEqual(m.adapt(server, "opencode")["environment"]["TOKEN"], "{env:TOKEN}")
        self.assertEqual(m.adapt(server, "codex")["env_vars"], ["TOKEN"])
        self.assertEqual(m.adapt({"url": "https://example.test/mcp"}, "claude")["type"], "http")

    def test_toml_merge_preserves_unrelated_sections(self):
        m = self.load()
        import tomllib
        text = '# keep comment\nmodel = "custom"\n[mcp_servers.old]\ncommand="old"\n[projects."/test"]\ntrust_level="trusted"\n'
        rendered = m.update_toml(text, {"old": {"command": "new", "args": ["--test"]}})
        parsed = tomllib.loads(rendered)
        self.assertEqual(parsed["projects"]["/test"]["trust_level"], "trusted")
        self.assertEqual(parsed["mcp_servers"]["old"]["command"], "new")
        self.assertIn("# keep comment", rendered)


if __name__ == "__main__":
    unittest.main()
