from __future__ import annotations

import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from cities2_mcp.agent_assets import install_agent_assets
from cities2_mcp import mcp_server

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)


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
            self.assertEqual(len(tools["result"]["tools"]), 13)
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
        self.assertEqual(len(tools), 13)
        self.assertNotIn("launch_cities2", {tool["name"] for tool in tools})
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
        self.assertEqual(plugin["displayName"], "Cities2 MCP and Modding Toolkit")
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
        self.assertIn("doesn't send any data to the cloud", privacy_text)
        self.assertIn("does not collect telemetry, phone home, or send data to its authors", privacy_text)
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
                self.assertEqual(len(tools["result"]["tools"]), 13)
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
        self.assertEqual(plugin["interface"]["displayName"], "Cities2 MCP and Modding Toolkit")
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

    def test_codex_plugin_launcher_ignores_bad_plugin_root_when_self_root_is_valid(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-empty-codex-cache-") as tmp:
            empty_cache = Path(tmp) / "empty-cache"
            empty_cache.mkdir()

            result = subprocess.run(
                [
                    "node",
                    str(plugin_root / "bin" / "cities2-mcp-launcher.js"),
                    "--version",
                ],
                cwd=ROOT,
                env={**os.environ, "PLUGIN_ROOT": str(empty_cache)},
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.9")

    def test_codex_plugin_launcher_handles_stripped_vendor_package_cache(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-stripped-codex-cache-") as tmp:
            staged_root = Path(tmp) / "cities2-mcp" / "0.1.9"
            shutil.copytree(plugin_root, staged_root)
            (staged_root / "vendor" / "run_server.py").unlink()
            for init_file in (staged_root / "vendor").rglob("__init__.py"):
                init_file.unlink()

            result = subprocess.run(
                [
                    "node",
                    str(staged_root / "bin" / "cities2-mcp-launcher.js"),
                    "--version",
                ],
                cwd=ROOT,
                env={**os.environ, "PLUGIN_ROOT": str(Path(tmp) / "empty-final-cache")},
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
                self.assertEqual(len(tools["result"]["tools"]), 13)
                self.assertTrue(status["wiki"]["available"])
                self.assertEqual(scaffold["game_version"], "1.5.*")
                self.assertIn("game_version_source", scaffold)
            finally:
                self._stop_proc(proc)

    def test_codex_plugin_package_is_antigravity_plugin(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        plugin = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
        plugin_mcp = json.loads((plugin_root / "mcp_config.json").read_text(encoding="utf-8"))

        self.assertEqual(plugin["name"], "cities2-mcp")
        self.assertEqual(plugin["version"], "0.1.9")
        self.assertEqual(plugin_mcp["mcpServers"]["cities2-mcp"]["command"], "node")
        self.assertIn("-e", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        self.assertIn("--", plugin_mcp["mcpServers"]["cities2-mcp"]["args"])
        bootstrap = plugin_mcp["mcpServers"]["cities2-mcp"]["args"][1]
        self.assertIn("antigravity-cli", bootstrap)
        self.assertIn("bin','cities2-mcp-launcher.js", bootstrap)
        self.assertIn("CITIES2_MCP_ALLOW_WORKSPACE_PLUGIN_ROOTS", bootstrap)
        self.assertLess(bootstrap.index("antigravity-cli"), bootstrap.index(".agents"))
        self.assertFalse((ROOT / "plugin.json").exists())
        self.assertFalse((ROOT / "mcp_config.json").exists())
        self.assertFalse((ROOT / "start_mcp.bat").exists())
        self.assertFalse((ROOT / "bin" / "cities2-mcp-launcher.js").exists())
        self.assertTrue((plugin_root / "bin" / "cities2-mcp-launcher.js").exists())
        for skill_name in SKILL_NAMES:
            self.assertTrue((plugin_root / "skills" / skill_name / "SKILL.md").exists())

    def test_antigravity_is_not_a_generated_package_payload(self) -> None:
        self.assertFalse((ROOT / "integrations" / "google").exists())
        self.assertFalse((ROOT / "gemini-extension.json").exists())

    def test_antigravity_plugin_mcp_config_launches_from_workspace_cwd(self) -> None:
        plugin_root = ROOT / "plugins" / "cities2-mcp"
        plugin_mcp = json.loads((plugin_root / "mcp_config.json").read_text(encoding="utf-8"))
        server = plugin_mcp["mcpServers"]["cities2-mcp"]
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-root-antigravity-workspace-") as tmp:
            workspace = Path(tmp)
            result = subprocess.run(
                [server["command"], *server["args"], "--version"],
                cwd=workspace,
                env={**os.environ, "CITIES2_MCP_PLUGIN_ROOT": str(plugin_root)},
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.9")

    def test_antigravity_mcp_config_prefers_installed_plugin_over_workspace_shadow(self) -> None:
        plugin_mcp = json.loads((ROOT / "plugins" / "cities2-mcp" / "mcp_config.json").read_text(encoding="utf-8"))
        server = plugin_mcp["mcpServers"]["cities2-mcp"]
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-antigravity-precedence-") as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            userprofile = root / "home"
            shadow = workspace / ".agents" / "plugins" / "cities2-mcp" / "bin"
            installed = userprofile / ".gemini" / "config" / "plugins" / "cities2-mcp" / "bin"
            shadow.mkdir(parents=True)
            installed.mkdir(parents=True)
            shadow_launcher = shadow / "cities2-mcp-launcher.js"
            installed_launcher = installed / "cities2-mcp-launcher.js"
            shadow_launcher.write_text("console.log('evil workspace plugin');\n", encoding="utf-8")
            installed_launcher.write_text("console.log('good installed plugin');\n", encoding="utf-8")

            env = dict(os.environ)
            env.pop("CITIES2_MCP_PLUGIN_ROOT", None)
            env.pop("ANTIGRAVITY_PLUGIN_ROOT", None)
            env.pop("CITIES2_MCP_ALLOW_WORKSPACE_PLUGIN_ROOTS", None)
            env["USERPROFILE"] = str(userprofile)
            env["HOME"] = str(userprofile)
            result = subprocess.run(
                [server["command"], *server["args"], "--version"],
                cwd=workspace,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertEqual(result.stdout.strip(), "good installed plugin")

    def test_plugin_package_check_detects_stale_payload(self) -> None:
        from cities2_mcp import plugin_packages

        with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            package_root = Path("plugins") / "cities2-mcp"

            plugin_packages.sync_packages(root, package_roots=(package_root,))
            stale_skill = root / package_root / "skills" / "cities2-knowledge" / "SKILL.md"
            stale_skill.write_text("stale\n", encoding="utf-8")

            stale = plugin_packages.check_packages(root, package_roots=(package_root,))

            self.assertIn(stale_skill, stale)

    def test_repo_metadata_in_sync(self) -> None:
        from cities2_mcp import plugin_packages

        self.assertEqual(plugin_packages.check_packages(ROOT), ())

    def test_check_detects_and_sync_restores_each_metadata_file(self) -> None:
        from cities2_mcp import plugin_packages

        flattened = [
            rel
            for entries in plugin_packages.METADATA_FILES.values()
            for rel, _builder in entries
        ]
        self.assertEqual(len(flattened), 10)  # guards the spec's "10 metadata files"
        self.assertEqual(len(set(flattened)), 10)  # no duplicate registrations

        for package_rel, entries in plugin_packages.METADATA_FILES.items():
            for rel, _builder in entries:
                with self.subTest(metadata=str(rel)):
                    with tempfile.TemporaryDirectory(prefix="cities2-mcp-meta-drift-") as tmp:
                        root = Path(tmp)
                        self._write_plugin_sync_fixture(root)
                        plugin_packages.sync_packages(root, package_roots=(package_rel,))

                        target = root / rel
                        self.assertTrue(target.is_file())
                        target.write_text("DRIFT\n", encoding="utf-8")

                        stale = plugin_packages.check_packages(root, package_roots=(package_rel,))
                        self.assertIn(target, stale)

                        restored = plugin_packages.sync_packages(root, package_roots=(package_rel,))
                        self.assertIn(target, restored)
                        self.assertEqual(
                            plugin_packages.check_packages(root, package_roots=(package_rel,)), ()
                        )

    def test_plugin_package_check_output_explains_generated_artifact_sync(self) -> None:
        from cities2_mcp import plugin_packages

        with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            plugin_packages.sync_packages(root)
            stale_metadata = root / "plugins" / "cities2-mcp" / ".codex-plugin" / "plugin.json"
            stale_metadata.write_text("{}\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = plugin_packages.main(["check", "--repo-root", str(root)])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 1)
            self.assertIn("generated artifacts differ from canonical sources", output)
            self.assertIn("Canonical sources: skills/, cities2_mcp/, and cities2_mcp.plugin_metadata", output)
            self.assertIn(
                "Generated copies: integrations/anthropic/claude-plugin/ and plugins/cities2-mcp/",
                output,
            )
            self.assertIn("python -m cities2_mcp.plugin_packages sync", output)
            self.assertIn(str(stale_metadata), output)

    def test_plugin_package_sync_updates_stale_payload(self) -> None:
        from cities2_mcp import plugin_packages

        with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            package_root = Path("plugins") / "cities2-mcp"
            stale_skill = root / package_root / "skills" / "cities2-knowledge" / "SKILL.md"
            stale_skill.parent.mkdir(parents=True, exist_ok=True)
            stale_skill.write_text("stale\n", encoding="utf-8")

            changed = plugin_packages.sync_packages(root, package_roots=(package_root,))
            stale = plugin_packages.check_packages(root, package_roots=(package_root,))

            self.assertIn(stale_skill, changed)
            self.assertEqual(stale, ())
            self.assertEqual(stale_skill.read_text(encoding="utf-8"), "canonical cities2-knowledge\n")

    def test_metadata_builders_are_deterministic(self) -> None:
        from cities2_mcp import plugin_metadata as meta

        builders = (
            meta.claude_plugin_json,
            meta.claude_mcp_json,
            meta.claude_readme_md,
            meta.claude_marketplace_json,
            meta.codex_plugin_json,
            meta.codex_mcp_json,
            meta.codex_readme_md,
            meta.codex_marketplace_json,
            meta.antigravity_plugin_json,
            meta.antigravity_mcp_config_json,
        )
        for builder in builders:
            self.assertEqual(builder(), builder(), builder.__name__)

    def test_generated_metadata_is_valid_and_canonical(self) -> None:
        import cities2_mcp
        from cities2_mcp import plugin_metadata as meta

        json_builders = {
            "claude_plugin_json": meta.claude_plugin_json,
            "claude_mcp_json": meta.claude_mcp_json,
            "claude_marketplace_json": meta.claude_marketplace_json,
            "codex_plugin_json": meta.codex_plugin_json,
            "codex_mcp_json": meta.codex_mcp_json,
            "codex_marketplace_json": meta.codex_marketplace_json,
            "antigravity_plugin_json": meta.antigravity_plugin_json,
            "antigravity_mcp_config_json": meta.antigravity_mcp_config_json,
        }
        parsed = {}
        for label, builder in json_builders.items():
            text = builder()
            self.assertTrue(text.endswith("\n"), label)
            parsed[label] = json.loads(text)  # raises on invalid JSON

        version = cities2_mcp.__version__
        self.assertEqual(parsed["claude_plugin_json"]["version"], version)
        self.assertEqual(parsed["codex_plugin_json"]["version"], version)
        self.assertEqual(parsed["antigravity_plugin_json"]["version"], version)
        self.assertEqual(parsed["claude_marketplace_json"]["plugins"][0]["version"], version)
        for label in (
            "claude_mcp_json",
            "codex_mcp_json",
            "antigravity_mcp_config_json",
            "codex_marketplace_json",
        ):
            self.assertNotIn("version", parsed[label])

        for label in (
            "claude_plugin_json",
            "codex_plugin_json",
            "antigravity_plugin_json",
            "claude_marketplace_json",
            "codex_marketplace_json",
        ):
            self.assertEqual(parsed[label]["name"], meta.NAME, label)

        self.assertEqual(parsed["claude_plugin_json"]["author"], meta.AUTHOR)
        self.assertEqual(parsed["codex_plugin_json"]["author"], meta.AUTHOR)
        self.assertEqual(parsed["claude_marketplace_json"]["owner"], meta.AUTHOR)
        self.assertEqual(parsed["claude_plugin_json"]["keywords"], meta.KEYWORDS)
        self.assertEqual(parsed["codex_plugin_json"]["keywords"], meta.KEYWORDS)
        self.assertEqual(parsed["claude_plugin_json"]["repository"], meta.REPO_URL)
        self.assertEqual(parsed["codex_plugin_json"]["repository"], meta.REPO_URL)
        self.assertEqual(
            parsed["codex_plugin_json"]["interface"]["privacyPolicyURL"], meta.PRIVACY_URL
        )

        for readme in (meta.claude_readme_md(), meta.codex_readme_md()):
            self.assertIn("Generated by cities2_mcp.plugin_packages", readme)
            for name in meta.SKILL_NAMES:
                self.assertIn(name, readme)
        self.assertIn(
            "claude plugin validate integrations/anthropic/claude-plugin --strict",
            meta.claude_readme_md(),
        )

    @staticmethod
    def _write_plugin_sync_fixture(root: Path) -> None:
        for skill_name in SKILL_NAMES:
            skill_dir = root / "skills" / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(f"canonical {skill_name}\n", encoding="utf-8")
            (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
            (skill_dir / "agents" / "openai.yaml").write_text(f"name: {skill_name}\n", encoding="utf-8")

        package_dir = root / "cities2_mcp"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text("__version__ = '0.1.9'\n", encoding="utf-8")
        (package_dir / "mcp_server.py").write_text("print('server')\n", encoding="utf-8")
        (package_dir / "data").mkdir(parents=True, exist_ok=True)
        (package_dir / "data" / "manifest.json").write_text("{}\n", encoding="utf-8")

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
