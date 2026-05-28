from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from unittest import mock

from cities2_mcp import bundled_data_dir
from cities2_mcp import mcp_server

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeProc:
    def __init__(self) -> None:
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()

    def terminate(self) -> None:
        return None

    def wait(self, timeout: int | None = None) -> int:
        return 0

    def kill(self) -> None:
        return None


class PortabilityTests(unittest.TestCase):
    def test_smoke_script_uses_active_interpreter(self) -> None:
        module = load_module("smoke_mcp_portability", ROOT / "tests" / "smoke_mcp.py")
        fake_proc = _FakeProc()

        with mock.patch.object(module.subprocess, "Popen", return_value=fake_proc) as popen_mock:
            with mock.patch.object(module, "rpc_ndjson", side_effect=RuntimeError("stop")):
                with mock.patch.object(sys, "argv", ["smoke_mcp.py"]):
                    with self.assertRaisesRegex(RuntimeError, "stop"):
                        module.main()

        argv = popen_mock.call_args.args[0]
        self.assertEqual(argv[0], sys.executable)

    def test_cli_uses_active_interpreter(self) -> None:
        module = load_module("workbench_cli_portability", ROOT / "scripts" / "workbench_cli.py")
        fake_proc = _FakeProc()
        rpc_responses = [
            {"result": {}},
            {"result": {"tools": [{"name": "search"}]}},
        ]

        with mock.patch.object(module.subprocess, "Popen", return_value=fake_proc) as popen_mock:
            with mock.patch.object(module, "rpc", side_effect=rpc_responses):
                with mock.patch.object(module, "notify", return_value=None):
                    with mock.patch.object(sys, "argv", ["workbench_cli.py", "list-tools"]):
                        with mock.patch("sys.stdout", new=io.StringIO()):
                            rc = module.main()

        argv = popen_mock.call_args.args[0]
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(rc, 0)

    def test_cli_uses_current_data_dir(self) -> None:
        module = load_module("workbench_cli_data_dir", ROOT / "scripts" / "workbench_cli.py")
        fake_proc = _FakeProc()
        rpc_responses = [
            {"result": {}},
            {"result": {"tools": [{"name": "search"}]}}
        ]

        with mock.patch.object(module.subprocess, "Popen", return_value=fake_proc) as popen_mock:
            with mock.patch.object(module, "rpc", side_effect=rpc_responses):
                with mock.patch.object(module, "notify", return_value=None):
                    with mock.patch.object(sys, "argv", ["workbench_cli.py", "list-tools"]):
                        with mock.patch("sys.stdout", new=io.StringIO()):
                            module.main()

        argv = [str(item) for item in popen_mock.call_args.args[0]]
        self.assertIn(str(ROOT / "data"), argv)
        self.assertNotIn(str(ROOT / "data" / "cities2-docs"), argv)
        self.assertTrue(bundled_data_dir().exists())

    def test_cli_examples_map_to_current_tool_names(self) -> None:
        module = load_module("workbench_cli_tool_mapping", ROOT / "scripts" / "workbench_cli.py")

        scaffold = module.tool_call_from_args(
            SimpleNamespace(
                cmd="scaffold",
                name="My Mod",
                template="cities2-csharp",
                target_dir=None,
                metadata="{}",
                options="{}",
            )
        )
        analyze = module.tool_call_from_args(
            SimpleNamespace(
                cmd="analyze",
                project_dir="mods/my-mod",
                profile="auto",
                strict=True,
            )
        )
        build = module.tool_call_from_args(
            SimpleNamespace(
                cmd="build",
                project_dir="mods/my-mod",
                profile="release",
                steps="ui,dotnet",
                clean=False,
                package=False,
                timeout_sec=300,
            )
        )

        self.assertEqual(scaffold["name"], "scaffold_project")
        self.assertEqual(analyze["name"], "analyze_project")
        self.assertEqual(build["name"], "build_project")
        self.assertEqual(build["arguments"]["steps"], ["ui", "dotnet"])

    def test_default_mods_dir_uses_windows_locallow_path(self) -> None:
        expected = PureWindowsPath(r"C:\Users\Test\AppData\LocalLow\Colossal Order\Cities Skylines II\Mods")

        with mock.patch.dict(mcp_server.os.environ, {"LOCALAPPDATA": r"C:\Users\Test\AppData\Local"}, clear=True):
            with mock.patch.object(mcp_server.os, "name", "nt"):
                actual = mcp_server.default_mods_dir()

        self.assertEqual(actual, expected)

    def test_repo_examples_do_not_contain_machine_specific_paths(self) -> None:
        old_tokens = [
            "cs2-wiki",
            "cs2wiki://",
            "cs2-modding-workbench",
            "CS2_MODS_DIR",
            "cs2-csharp",
            "cs2-ui",
            "cs2-hybrid",
            "/Users/matt/",
            "/usr/bin/python3",
        ]
        targets = [
            ROOT / "mcp.config.example.json",
            ROOT / "README.md",
            ROOT / "scripts" / "mcp_launch_wrapper.sh",
            ROOT / "scripts" / "workbench_cli.py",
            ROOT / "cities2_mcp" / "mcp_server.py",
        ]
        for path in targets:
            text = path.read_text(encoding="utf-8")
            for token in old_tokens:
                self.assertNotIn(token, text, f"{path}: {token}")
        self.assertIn("data/index/chunks.jsonl", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_public_docs_avoid_scraping_language(self) -> None:
        for path in (ROOT / "README.md", ROOT / "INSTALL.md"):
            self.assertNotIn("scrap", path.read_text(encoding="utf-8").lower())

    def test_public_name_uses_cities2_mcp_label(self) -> None:
        label = "Cities2-MCP — game knowledge and modding tools for Cities: Skylines II"
        server_text = (ROOT / "cities2_mcp" / "mcp_server.py").read_text(encoding="utf-8")
        example_config = (ROOT / "mcp.config.example.json").read_text(encoding="utf-8")
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn(label, server_text)
        self.assertNotIn("Cities2 Modding Workbench", server_text)
        self.assertIn('"cities2-mcp"', example_config)
        self.assertNotIn('"cities2-modding-workbench"', example_config)
        self.assertIn("Current name:** `cities2-mcp`", install_text)
        self.assertIn("cities2-modding-workbench", install_text)

    def test_mcp_initialize_describes_full_public_scope(self) -> None:
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-11-25"},
            },
            corpus=None,
            wm=None,
        )

        instructions = response["result"]["instructions"]
        self.assertIn("Cities: Skylines II Wiki corpus", instructions)
        self.assertIn("gameplay", instructions)
        self.assertIn("mod projects", instructions)
        self.assertNotIn("Generic MediaWiki", instructions)

    def test_tool_descriptions_identify_wiki_and_mod_workflow_scope(self) -> None:
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

        tools = {tool["name"]: tool["description"] for tool in response["result"]["tools"]}
        self.assertIn("Cities: Skylines II Wiki corpus", tools["search"])
        self.assertIn("gameplay", tools["search"])
        self.assertIn("Cities: Skylines II Wiki", tools["get_page"])
        self.assertIn("Cities: Skylines II mod project", tools["scaffold_project"])
        self.assertIn("Cities: Skylines II mod project", tools["build_project"])
        for description in tools.values():
            self.assertNotIn("MediaWiki", description)

    def test_docs_disclose_optional_mod_build_prerequisites(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (install_text, readme_text):
            self.assertIn("optional", text.lower())
            self.assertIn("Microsoft.NETCore.App", text)
            self.assertIn("6.", text)
            self.assertIn("dotnet --list-runtimes", text)

    def test_public_docs_describe_skills_as_slash_commands_not_mcp_prompts(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (install_text, readme_text):
            self.assertIn("slash commands", text.lower())
            self.assertIn("cities2-knowledge", text)
            self.assertIn("cities2-modding", text)
            self.assertNotIn("MCP prompt templates", text)
            self.assertNotIn("MCP Prompts", text)
            self.assertNotIn("prompts/list", text)
            self.assertNotIn("cities2-wiki", text)
            self.assertNotIn("cities2-encyclopedia", text)

    def test_docs_include_current_claude_desktop_plugin_marketplace_path(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (install_text, readme_text):
            self.assertIn("Cowork", text)
            self.assertIn("Code", text)
            self.assertIn("Customize", text)
            self.assertIn("Personal plugins", text)
            self.assertIn("Create Plugin", text)
            self.assertIn("Add marketplace", text)
            self.assertIn("mayor-modder/Cities2-MCP", text)

    def test_agent_skills_are_packaged_and_documented(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        skill_names = ["cities2-knowledge", "cities2-modding"]

        for skill_name in skill_names:
            skill_dir = ROOT / "skills" / skill_name
            skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            metadata_text = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")

            self.assertIn(f"name: {skill_name}", skill_text)
            self.assertIn("description:", skill_text)
            self.assertIn("Use automatically", skill_text)
            self.assertIn("metadata:", skill_text)
            self.assertIn("short-description:", skill_text)
            self.assertIn("Source", skill_text)
            self.assertNotIn("TODO", skill_text)
            self.assertIn("cities2-mcp", metadata_text)
            self.assertIn(f"${skill_name}", metadata_text)
            self.assertIn(skill_name, readme_text)
            self.assertIn(skill_name, install_text)

        self.assertIn("## 5. Install Agent Skills", install_text)
        self.assertIn("compact source notes", readme_text)
        self.assertIn("compact source notes", install_text)
        self.assertIn("patch", (ROOT / "skills" / "cities2-knowledge" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("%USERPROFILE%\\.codex\\skills", install_text)
        self.assertIn("Copy-Item -Recurse -Force", install_text)
        self.assertIn("~/.codex/skills", install_text)
        self.assertIn("New Codex sessions should list", install_text)

    def test_docs_do_not_advertise_unimplemented_workspace_escape_flag(self) -> None:
        for path in (ROOT / "README.md", ROOT / "INSTALL.md"):
            self.assertNotIn("--allow-any-workspace", path.read_text(encoding="utf-8"))

    def test_install_guide_explains_workspace_allowlist_for_mod_repos(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("WORKSPACE_ROOTS", install_text)
        self.assertIn("trusted parent folder", install_text)
        self.assertIn("Path must stay inside configured workspaces", install_text)
        self.assertIn("Add that mod repo", install_text)
        self.assertNotIn("// Add more", install_text)

    def test_install_guide_avoids_runtime_specific_question_tool_names(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertNotIn("AskUserQuestion", install_text)

    def test_install_guide_uses_current_claude_code_mcp_locations(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("~/.claude.json", install_text)
        self.assertIn(".mcp.json", install_text)
        self.assertNotIn(".claude/settings.local.json", install_text)
        self.assertIn("here-string", install_text)
        self.assertIn("claude mcp add-json cities2-mcp $json --scope user", install_text)

    def test_install_guide_points_claude_desktop_to_in_app_config(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("edit `claude_desktop_config.json` directly", install_text)
        self.assertIn("Settings > Developer > Edit Config", install_text)
        self.assertIn("Claude Desktop", install_text)

    def test_install_guide_distinguishes_claude_surfaces_before_install(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("Claude Desktop app MCP settings", install_text)
        self.assertIn("Claude Code MCP settings", install_text)
        self.assertIn("ask the user which Claude surface", install_text)
        self.assertNotIn("Claude Desktop chat app", install_text)

    def test_readme_direct_cli_examples_stay_inside_default_workspace(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("/path/to/project", readme_text)
        self.assertIn("mods/my-mod", readme_text)

    def test_install_guide_uses_smoke_test_for_verification(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("<PYTHON_PATH> tests/smoke_mcp.py", install_text)
        self.assertIn("scripts/workbench_cli.py list-tools", install_text)
        self.assertNotIn("< NUL", install_text)
        self.assertNotIn("< /dev/null", install_text)

    def test_install_guide_lists_expected_public_tools_and_stale_config_cleanup(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        expected_tools = [
            "search",
            "get_page",
            "query_reference",
            "get_snippets",
            "scaffold_project",
            "write_project_file",
            "list_project_tree",
            "build_project",
            "analyze_project",
            "package_project",
            "launch_cities2",
        ]

        for tool_name in expected_tools:
            self.assertIn(f"`{tool_name}`", install_text)
        for stale_token in (
            "InfoLoom",
            "save analysis",
            "live city data",
            "city recovery",
            "dataexport",
            "saveinvestigator",
        ):
            self.assertIn(stale_token, install_text)

    def test_retrieval_layer_is_internal_not_a_submodule(self) -> None:
        server_text = (ROOT / "cities2_mcp" / "mcp_server.py").read_text(encoding="utf-8")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertFalse((ROOT / ".gitmodules").exists())
        self.assertTrue((ROOT / "cities2_mcp" / "retrieval" / "mcp_server.py").exists())
        self.assertFalse((ROOT / "cities2_mcp" / "retrieval" / "LICENSE.wiki-mcp").exists())
        self.assertIn("wiki-mcp contributors", notices)
        self.assertFalse((ROOT / "vendor" / "wiki-mcp").exists())
        self.assertNotIn("vendor/wiki-mcp", server_text)
        self.assertNotIn("wiki_mcp_server", server_text)


if __name__ == "__main__":
    unittest.main()
