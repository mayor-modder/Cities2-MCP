from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cities2_mcp.agent_assets import install_agent_assets
from cities2_mcp import mcp_server

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    @staticmethod
    def _stop_proc(proc: subprocess.Popen[bytes]) -> None:
        proc.terminate()
        proc.wait(timeout=3)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()

    def test_pyproject_declares_public_package_and_entrypoint(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        project = pyproject["project"]
        self.assertEqual(project["name"], "cities2-mcp")
        self.assertEqual(project["version"], "0.1.9")
        self.assertEqual(project["scripts"]["cities2-mcp"], "cities2_mcp.mcp_server:main")

    def test_package_module_reports_version_and_bundled_data_dir(self) -> None:
        package = importlib.import_module("cities2_mcp")

        self.assertEqual(package.__version__, "0.1.9")
        data_dir = package.bundled_data_dir()
        self.assertTrue((data_dir / "index" / "chunks.jsonl").exists())
        self.assertTrue((data_dir / "index" / "pages.jsonl").exists())

    def test_server_version_flag_prints_public_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cities2_mcp.mcp_server", "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.9")

    def test_default_start_without_workspace_keeps_knowledge_tools_available(self) -> None:
        from tests.smoke_mcp import call, rpc, rpc_ndjson

        proc = subprocess.Popen(
            [sys.executable, "-m", "cities2_mcp.mcp_server"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout and proc.stderr

        try:
            init = rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
            tools = rpc(proc, 2, "tools/list", {})
            search = call(proc, 3, "search", {"query": "modding toolchain requirements", "limit": 1})
            scaffold = call(proc, 4, "scaffold_project", {"name": "No Workspace", "template": "cities2-csharp"})

            self.assertEqual(init["result"]["serverInfo"]["version"], "0.1.9")
            self.assertEqual(len(tools["result"]["tools"]), 14)
            self.assertTrue(search["ok"])
            self.assertFalse(scaffold["ok"])
            self.assertIn("--workspace", scaffold["error"])
        finally:
            self._stop_proc(proc)

    def test_default_start_with_workspace_enables_workflow_tools(self) -> None:
        from tests.smoke_mcp import call, rpc_ndjson

        with tempfile.TemporaryDirectory(prefix="cities2-mcp-package-") as tmp:
            workspace = Path(tmp)
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "cities2_mcp.mcp_server",
                    "--workspace",
                    str(workspace),
                    "--mods-dir",
                    str(workspace / "local-mods"),
                ],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin and proc.stdout and proc.stderr

            try:
                rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
                scaffold = call(proc, 2, "scaffold_project", {"name": "Packaged", "template": "cities2-csharp"})

                self.assertTrue(scaffold["ok"])
                self.assertTrue(Path(scaffold["project_dir"]).is_dir())
            finally:
                self._stop_proc(proc)

    def test_server_json_registers_pypi_package(self) -> None:
        server_json = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))

        self.assertEqual(server_json["name"], "io.github.mayor-modder/cities2-mcp")
        self.assertEqual(server_json["version"], "0.1.9")
        package = server_json["packages"][0]
        self.assertEqual(package["registryType"], "pypi")
        self.assertEqual(package["identifier"], "cities2-mcp")
        self.assertEqual(package["version"], "0.1.9")
        self.assertEqual(package["transport"]["type"], "stdio")

    def test_all_public_tools_have_directory_review_annotations(self) -> None:
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            },
            corpus=None,
            wm=None,
        )

        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 14)
        for tool in tools:
            annotations = tool.get("annotations")
            self.assertIsInstance(annotations, dict, tool["name"])
            self.assertIsInstance(annotations.get("title"), str, tool["name"])
            self.assertGreater(len(annotations["title"]), 3, tool["name"])
            for key in ("readOnlyHint", "destructiveHint", "openWorldHint"):
                self.assertIsInstance(annotations.get(key), bool, f"{tool['name']} {key}")

    def test_anthropic_distribution_artifacts_are_version_aligned(self) -> None:
        plugin = json.loads(
            (ROOT / "integrations" / "anthropic" / "claude-plugin" / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        plugin_mcp = json.loads(
            (ROOT / "integrations" / "anthropic" / "claude-plugin" / ".mcp.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        privacy_text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")

        self.assertEqual(plugin["name"], "cities2-mcp")
        self.assertEqual(plugin["displayName"], "Cities2-MCP")
        self.assertEqual(plugin["version"], "0.1.9")
        self.assertIn("trusted_workspace", plugin["userConfig"])
        self.assertNotIn("mcpServers", plugin)
        self.assertEqual(plugin_mcp["mcpServers"]["cities2-mcp"]["command"], "node")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/bin/cities2-mcp-launcher.js", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertIn("${CLAUDE_PROJECT_DIR}", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertEqual(
            plugin_mcp["mcpServers"]["cities2-mcp"]["env"]["CITIES2_MCP_WORKSPACE"],
            "${user_config.trusted_workspace}",
        )
        self.assertNotIn("uvx", json.dumps(plugin_mcp))
        self.assertEqual(marketplace["name"], "cities2-mcp")
        self.assertEqual(marketplace["plugins"][0]["source"], "./integrations/anthropic/claude-plugin")
        self.assertEqual(marketplace["plugins"][0]["version"], "0.1.9")
        self.assertIn("[PRIVACY.md](PRIVACY.md)", readme_text)
        self.assertIn("does not collect telemetry", privacy_text)
        self.assertIn("does not share data with third parties", privacy_text)
        self.assertTrue((ROOT / "integrations" / "anthropic" / "claude-plugin" / "bin" / "cities2-mcp-launcher.js").exists())
        self.assertTrue((ROOT / "integrations" / "anthropic" / "claude-plugin" / "vendor" / "run_server.py").exists())
        self.assertTrue((ROOT / "integrations" / "anthropic" / "claude-plugin" / "vendor" / "cities2_mcp" / "mcp_server.py").exists())
        legacy_desktop_extension_dir = "claude-" + "mcp" + "b"
        self.assertFalse((ROOT / "integrations" / "anthropic" / legacy_desktop_extension_dir).exists())
        for skill_name in (
            "cities2-knowledge",
            "cities2-modding",
            "cities2-mod-review",
            "cities2-mod-debugging",
            "cities2-mod-release",
        ):
            self.assertTrue(
                (
                    ROOT
                    / "integrations"
                    / "anthropic"
                    / "claude-plugin"
                    / "skills"
                    / skill_name
                    / "SKILL.md"
                ).exists()
            )

    def test_claude_plugin_vendored_launcher_reports_version(self) -> None:
        plugin_root = ROOT / "integrations" / "anthropic" / "claude-plugin"
        result = subprocess.run(
            [
                "node",
                str(plugin_root / "bin" / "cities2-mcp-launcher.js"),
                "--version",
            ],
            cwd=ROOT,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.9")

    def test_claude_plugin_vendored_launcher_serves_mcp(self) -> None:
        from tests.smoke_mcp import call, rpc, rpc_ndjson

        plugin_root = ROOT / "integrations" / "anthropic" / "claude-plugin"
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-") as tmp:
            proc = subprocess.Popen(
                [
                    "node",
                    str(plugin_root / "bin" / "cities2-mcp-launcher.js"),
                    "--workspace",
                    tmp,
                    "--mods-dir",
                    str(Path(tmp) / "mods"),
                ],
                cwd=ROOT,
                env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin and proc.stdout and proc.stderr

            try:
                init = rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
                tools = rpc(proc, 2, "tools/list", {})
                status = call(proc, 3, "source_status", {})
                scaffold = call(proc, 4, "scaffold_project", {"name": "Plugin Version", "template": "cities2-csharp"})

                self.assertEqual(init["result"]["serverInfo"]["version"], "0.1.9")
                self.assertEqual(len(tools["result"]["tools"]), 14)
                self.assertTrue(status["wiki"]["available"])
                self.assertEqual(scaffold["game_version"], "1.5.*")
                self.assertIn("game_version_source", scaffold)
            finally:
                self._stop_proc(proc)

    def test_codex_distribution_artifacts_are_version_aligned(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        plugin = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        plugin_mcp = json.loads((plugin_root / ".mcp.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))

        self.assertEqual(plugin["name"], "cities2-mcp")
        self.assertEqual(plugin["interface"]["displayName"], "Cities2-MCP")
        self.assertEqual(plugin["version"], "0.1.9")
        self.assertEqual(
            plugin["interface"]["privacyPolicyURL"],
            "https://github.com/mayor-modder/Cities2-MCP/blob/main/PRIVACY.md",
        )
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(plugin["mcpServers"], "./.mcp.json")
        self.assertEqual(plugin_mcp["mcpServers"]["cities2-mcp"]["command"], "node")
        self.assertIn("./bin/cities2-mcp-launcher.js", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertNotIn("${PLUGIN_ROOT}", "\n".join(plugin_mcp["mcpServers"]["cities2-mcp"]["args"]))
        self.assertIn("--workspace", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertIn(".", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertEqual(plugin_mcp["mcpServers"]["cities2-mcp"]["cwd"], ".")
        self.assertEqual(marketplace["name"], "cities2-mcp")
        self.assertEqual(marketplace["plugins"][0]["name"], "cities2-mcp")
        self.assertEqual(marketplace["plugins"][0]["source"]["source"], "local")
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/cities2-mcp")
        self.assertEqual(marketplace["plugins"][0]["policy"]["installation"], "AVAILABLE")
        self.assertEqual(marketplace["plugins"][0]["policy"]["authentication"], "ON_INSTALL")
        for skill_name in (
            "cities2-knowledge",
            "cities2-modding",
            "cities2-mod-review",
            "cities2-mod-debugging",
            "cities2-mod-release",
        ):
            self.assertTrue((plugin_root / "skills" / skill_name / "SKILL.md").exists())
        self.assertTrue((plugin_root / "vendor" / "cities2_mcp" / "mcp_server.py").exists())
        self.assertTrue((plugin_root / "vendor" / "cities2_mcp" / "data" / "index" / "chunks.jsonl").exists())

    def test_codex_plugin_vendored_launcher_reports_version(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        result = subprocess.run(
            [
                "node",
                str(plugin_root / "bin" / "cities2-mcp-launcher.js"),
                "--version",
            ],
            cwd=ROOT,
            env={**os.environ, "PLUGIN_ROOT": str(plugin_root)},
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.9")

    def test_codex_plugin_vendored_launcher_serves_mcp(self) -> None:
        from tests.smoke_mcp import call, rpc, rpc_ndjson

        plugin_root = ROOT / "plugins" / "cities2-mcp"
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-codex-plugin-") as tmp:
            proc = subprocess.Popen(
                [
                    "node",
                    str(plugin_root / "bin" / "cities2-mcp-launcher.js"),
                    "--workspace",
                    tmp,
                    "--mods-dir",
                    str(Path(tmp) / "mods"),
                ],
                cwd=ROOT,
                env={**os.environ, "PLUGIN_ROOT": str(plugin_root)},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin and proc.stdout and proc.stderr

            try:
                init = rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
                tools = rpc(proc, 2, "tools/list", {})
                status = call(proc, 3, "source_status", {})
                scaffold = call(proc, 4, "scaffold_project", {"name": "Codex Plugin Version", "template": "cities2-csharp"})

                self.assertEqual(init["result"]["serverInfo"]["version"], "0.1.9")
                self.assertEqual(len(tools["result"]["tools"]), 14)
                self.assertTrue(status["wiki"]["available"])
                self.assertEqual(scaffold["game_version"], "1.5.*")
                self.assertIn("game_version_source", scaffold)
            finally:
                self._stop_proc(proc)

    def test_agent_asset_installer_copies_codex_and_claude_assets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-assets-") as tmp:
            home = Path(tmp)
            (home / ".codex" / "skills" / "cities2-game-updates").mkdir(parents=True)
            (home / ".claude" / "skills" / "cities2-game-updates").mkdir(parents=True)
            (home / ".claude" / "commands").mkdir(parents=True)
            (home / ".claude" / "commands" / "cities2-game-updates.md").write_text("old\n", encoding="utf-8")

            results = install_agent_assets(["all"], home=home)

            self.assertEqual({result.client for result in results}, {"codex", "claude"})
            skill_names = (
                "cities2-knowledge",
                "cities2-modding",
                "cities2-mod-review",
                "cities2-mod-debugging",
                "cities2-mod-release",
            )
            for client_root in (home / ".codex" / "skills", home / ".claude" / "skills"):
                for skill_name in skill_names:
                    self.assertTrue((client_root / skill_name / "SKILL.md").exists())
                self.assertFalse((client_root / "cities2-game-updates").exists())
            for skill_name in skill_names:
                self.assertTrue((home / ".claude" / "commands" / f"{skill_name}.md").exists())
            self.assertFalse((home / ".claude" / "commands" / "cities2-game-updates.md").exists())

    def test_agent_asset_installer_cli_exits_without_starting_stdio_server(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-cli-assets-") as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cities2_mcp.mcp_server",
                    "install-agent-assets",
                    "--client",
                    "codex",
                    "--home",
                    tmp,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("codex: installed", result.stdout)
            self.assertTrue((Path(tmp) / ".codex" / "skills" / "cities2-knowledge" / "SKILL.md").exists())
