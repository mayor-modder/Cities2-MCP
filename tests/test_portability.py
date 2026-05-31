from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

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
            "/Users/Example/",
            "/usr/bin/python3",
        ]
        targets = [
            ROOT / "mcp.config.example.json",
            ROOT / "README.md",
            ROOT / "scripts" / "mcp_launch_wrapper.sh",
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

    def test_public_name_uses_human_facing_toolkit_label(self) -> None:
        label = "Cities2-MCP — game knowledge and modding tools for Cities: Skylines II"
        server_text = (ROOT / "cities2_mcp" / "mcp_server.py").read_text(encoding="utf-8")
        example_config = (ROOT / "mcp.config.example.json").read_text(encoding="utf-8")
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(label, server_text)
        self.assertIn("# Cities2 MCP and Modding Toolkit", readme_text)
        self.assertNotIn("Cities2 Modding Workbench", server_text)
        self.assertIn('"cities2-mcp"', example_config)
        self.assertNotIn('"cities2-modding-workbench"', example_config)
        self.assertNotIn("current `cities2-mcp` entry", install_text)
        self.assertNotIn("cities2-modding-workbench", install_text)

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

        self.assertIn("optional", install_text.lower())
        self.assertIn("Microsoft.NETCore.App", install_text)
        self.assertIn("6.", install_text)
        self.assertIn("dotnet --list-runtimes", install_text)
        self.assertIn("build prerequisites", readme_text.lower())
        self.assertIn("INSTALL.md", readme_text)

    def test_public_docs_describe_agent_skills_not_mcp_prompts(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (install_text, readme_text):
            self.assertIn("agent skills", text.lower())
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

        for text in (install_text,):
            self.assertIn("Cowork", text)
            self.assertIn("Code", text)
            self.assertIn("Customize", text)
            self.assertIn("Personal plugins", text)
            self.assertIn("Create Plugin", text)
            self.assertIn("Add marketplace", text)
            self.assertIn("mayor-modder/Cities2-MCP", text)
        self.assertIn("/plugin marketplace add mayor-modder/Cities2-MCP", install_text)
        self.assertIn("INSTALL.md#install-in-claude-code", readme_text)
        self.assertIn("INSTALL.md#install-in-claude-desktop", readme_text)
        self.assertIn("INSTALL.md", readme_text)

    def test_docs_include_codex_plugin_marketplace_path(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        openai_readme = (ROOT / "integrations" / "openai" / "README.md").read_text(encoding="utf-8")
        codex_plugin_readme = (ROOT / "plugins" / "cities2-mcp" / "README.md").read_text(encoding="utf-8")

        self.assertIn("codex plugin marketplace add mayor-modder/Cities2-MCP", install_text)
        self.assertIn("/skills", install_text)
        self.assertIn("INSTALL.md#install-in-codex-cli", readme_text)
        self.assertIn("INSTALL.md#install-in-the-codex-app", readme_text)
        self.assertIn("INSTALL.md", readme_text)
        self.assertNotIn(".agents/plugins/marketplace.json", readme_text)
        self.assertNotIn("plugins/cities2-mcp", readme_text)
        for skill_name in ("cities2-knowledge", "cities2-modding"):
            self.assertIn(f"$cities2-mcp:{skill_name}", install_text)
            self.assertIn(f"$cities2-mcp:{skill_name}", readme_text)
            self.assertIn(skill_name, readme_text)
        self.assertIn("allowlist", openai_readme)
        self.assertIn("template-copy fallback", codex_plugin_readme)
        self.assertNotIn("MCP workspace is the current Codex project folder", openai_readme)
        self.assertNotIn("MCP workspace is the current project folder", codex_plugin_readme)

    def test_docs_include_antigravity_install_paths(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in (install_text, readme_text):
            self.assertIn("Google Antigravity", text)
            self.assertIn("INSTALL.md#install-in-google-antigravity", text)
            self.assertIn("/cities2", text)
        self.assertIn("git clone --depth 1 https://github.com/mayor-modder/Cities2-MCP", install_text)
        self.assertIn(r"$env:USERPROFILE\.gemini\config\plugins\cities2-mcp", install_text)
        self.assertIn("plugins\\cities2-mcp", install_text)
        self.assertIn("Both apps read plugins from this folder", install_text)
        self.assertIn("plugin.json", install_text)
        self.assertIn("Move or replace that one folder before reinstalling", install_text)
        self.assertIn("replace only the existing `cities2-mcp` plugin folder", install_text)
        self.assertIn("clear the parent Antigravity `plugins` folder", install_text)
        self.assertIn("Direct URL installs are not currently supported", install_text)
        self.assertNotIn("agy plugin install https://github.com/mayor-modder/Cities2-MCP\n```", install_text)
        self.assertNotIn("rm -rf", install_text)
        self.assertNotIn("Remove-Item -Recurse -Force", install_text)
        self.assertNotIn(".agents/plugins/cities2-mcp", install_text)
        self.assertNotIn("_agents/plugins/cities2-mcp", install_text)
        self.assertNotIn("integrations/google/antigravity-plugin", install_text)
        self.assertNotIn("optional global Antigravity", install_text)

    def test_public_docs_do_not_advertise_gemini_cli_package(self) -> None:
        public_text = "\n".join(
            (
                (ROOT / "README.md").read_text(encoding="utf-8"),
                (ROOT / "INSTALL.md").read_text(encoding="utf-8"),
            )
        )

        self.assertNotIn("gemini-extension.json", public_text)
        self.assertNotIn("gemini extensions install", public_text)
        self.assertNotIn("Gemini CLI extension package", public_text)

    def test_anthropic_integration_docs_treat_plugin_as_only_documented_install_path(self) -> None:
        anthropic_readme = (ROOT / "integrations" / "anthropic" / "README.md").read_text(encoding="utf-8")
        claude_plugin_readme = (
            ROOT / "integrations" / "anthropic" / "claude-plugin" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("primary Claude package", anthropic_readme)
        self.assertIn("plugin marketplace", anthropic_readme)
        self.assertIn("/cities2-knowledge", claude_plugin_readme)
        self.assertIn("/cities2-modding", claude_plugin_readme)
        self.assertNotIn("/cities2-mcp:cities2-knowledge", claude_plugin_readme)
        self.assertNotIn("Connectors Directory", anthropic_readme)
        self.assertNotIn("correct artifact", anthropic_readme)

    def test_agent_skills_are_packaged_and_documented(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        skill_names = [
            "cities2-knowledge",
            "cities2-modding",
            "cities2-mod-review",
            "cities2-mod-debugging",
            "cities2-mod-release",
        ]

        for skill_name in skill_names:
            skill_dir = ROOT / "skills" / skill_name
            skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            metadata_text = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")

            self.assertIn(f"name: {skill_name}", skill_text)
            self.assertIn("description:", skill_text)
            self.assertIn('description: "Use when', skill_text)
            self.assertIn("metadata:", skill_text)
            self.assertIn("short-description:", skill_text)
            self.assertIn("Source", skill_text)
            self.assertNotIn("TODO", skill_text)
            self.assertIn("cities2-mcp", metadata_text)
            self.assertIn(f"${skill_name}", metadata_text)
            self.assertIn(skill_name, readme_text)
            for distributed_root in (
                ROOT / "plugins" / "cities2-mcp" / "skills",
                ROOT / "integrations" / "anthropic" / "claude-plugin" / "skills",
            ):
                distributed_text = (distributed_root / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertEqual(
                    skill_text,
                    distributed_text,
                    f"{skill_name} drifted from {distributed_root}",
                )

        self.assertFalse((ROOT / "skills" / "cities2-skill-style-review").exists())
        self.assertFalse((ROOT / "plugins" / "cities2-mcp" / "skills" / "cities2-skill-style-review").exists())
        self.assertFalse(
            (
                ROOT
                / "integrations"
                / "anthropic"
                / "claude-plugin"
                / "skills"
                / "cities2-skill-style-review"
            ).exists()
        )

        self.assertIn("compact source notes", " ".join(readme_text.split()))
        for skill_name in ("cities2-knowledge", "cities2-modding", "cities2-mod-review"):
            self.assertIn(skill_name, install_text)
        self.assertIn("patch", (ROOT / "skills" / "cities2-knowledge" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("uvx cities2-mcp install-agent-assets", install_text)
        self.assertIn("load local agent skills separately", install_text)
        legacy_skill_wording = "client supports MCP servers" + " but not plugin skills"
        self.assertNotIn(legacy_skill_wording, install_text)

    def test_modding_quality_skills_encode_review_debug_release_rules(self) -> None:
        review = (ROOT / "skills" / "cities2-mod-review" / "SKILL.md").read_text(encoding="utf-8")
        debugging = (ROOT / "skills" / "cities2-mod-debugging" / "SKILL.md").read_text(encoding="utf-8")
        release = (ROOT / "skills" / "cities2-mod-release" / "SKILL.md").read_text(encoding="utf-8")
        modding = (ROOT / "skills" / "cities2-modding" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("documented best practices", review.lower())
        self.assertIn("negative constraints", review.lower())
        self.assertIn("best practice", review.lower())
        self.assertIn("playtesting handoff", debugging.lower())
        self.assertIn("Modding.log", debugging)
        self.assertIn("localhost:9444", debugging)
        self.assertIn("after applying a fix", debugging.lower())
        self.assertIn("build or install", debugging.lower())
        self.assertIn("playtesting steps", debugging.lower())
        self.assertIn("close Cities: Skylines II", debugging)
        self.assertIn("must be closed", debugging)
        self.assertIn("successful build is not enough", release.lower())
        self.assertIn("local playtesting", release.lower())
        self.assertIn("not gameplay-verified", release.lower())
        self.assertIn("close Cities: Skylines II", release)
        self.assertIn("must be closed", modding)
        self.assertIn("local playtest artifact", modding)
        self.assertIn("Do not block packaging or installing a local", modding)
        self.assertIn("cities2-mod-review", modding)
        self.assertIn("cities2-mod-debugging", modding)
        self.assertIn("cities2-mod-release", modding)

    def test_mod_review_skill_offers_portable_multi_agent_review(self) -> None:
        skill_paths = [
            ROOT / "skills" / "cities2-mod-review" / "SKILL.md",
            ROOT / "plugins" / "cities2-mcp" / "skills" / "cities2-mod-review" / "SKILL.md",
            ROOT
            / "integrations"
            / "anthropic"
            / "claude-plugin"
            / "skills"
            / "cities2-mod-review"
            / "SKILL.md",
        ]

        for path in skill_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("Multi-Agent Review Offer", text)
            self.assertIn("command -v codex", text)
            self.assertIn("Get-Command codex", text)
            self.assertIn("claude", text)
            self.assertIn("agy", text)
            self.assertIn("Ask before running external reviewers", text)
            self.assertIn("Before opt-in, only use PATH lookup", text)
            self.assertIn("Do not run external CLI commands, including `--help`", text)
            self.assertIn("If no external reviewer is available", text)
            self.assertIn("codex review", text)
            self.assertIn("claude ultrareview", text)
            self.assertIn("agy --print", text)
            self.assertIn("file-output-first", text)
            self.assertIn("--log-file", text)
            self.assertIn("not the final review artifact", text)
            self.assertIn("Offer to remove temporary review files", text)
            self.assertIn("Do not outsource judgment", text)
            self.assertNotIn("C:\\Users\\matt", text)

    def test_docs_do_not_advertise_unimplemented_workspace_escape_flag(self) -> None:
        for path in (ROOT / "README.md", ROOT / "INSTALL.md"):
            self.assertNotIn("--allow-any-workspace", path.read_text(encoding="utf-8"))

    def test_modding_skill_describes_codex_workspace_fallback_honestly(self) -> None:
        skill_paths = [
            ROOT / "skills" / "cities2-modding" / "SKILL.md",
            ROOT / "plugins" / "cities2-mcp" / "skills" / "cities2-modding" / "SKILL.md",
            ROOT / "integrations" / "anthropic" / "claude-plugin" / "skills" / "cities2-modding" / "SKILL.md",
        ]

        for path in skill_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("plugin-bundled MCP servers", text)
            self.assertIn("installed plugin", text)
            self.assertIn("cache", text)
            self.assertIn("explicit fallback", text)
            self.assertIn("do not hand-roll", text)
            self.assertIn("npm.cmd", text)
            self.assertIn("do not", text)
            self.assertIn("try bare `npm` first", text)
            self.assertIn("Get-ChildItem", text)
            self.assertIn("package-lock.json", text)
            self.assertIn("Windows paths", text)
            self.assertIn("do not", text)
            self.assertIn("start a dev server", text)
            self.assertNotIn("Claude Code and Codex, project-scoped plugin", text)

    def test_install_guide_explains_workspace_allowlist_for_mod_repos(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("trusted workspace", install_text)
        self.assertIn("trusted parent folder", install_text)
        self.assertIn("Path must stay inside configured workspaces", install_text)
        self.assertIn("mod project folder", install_text)
        self.assertNotIn("// Add more", install_text)

    def test_install_guide_avoids_runtime_specific_question_tool_names(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertNotIn("AskUserQuestion", install_text)

    def test_install_guide_uses_current_claude_code_mcp_locations(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("/plugin marketplace add mayor-modder/Cities2-MCP", install_text)
        self.assertNotIn(".claude/settings.local.json", install_text)
        self.assertNotIn("~/.claude.json", install_text)
        self.assertNotIn(".mcp.json", install_text)
        self.assertNotIn("claude mcp add-json", install_text)

    def test_install_guide_points_claude_desktop_to_in_app_config(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("Claude desktop", install_text)
        self.assertIn("Personal plugins", install_text)
        self.assertIn("Trusted mod projects folder", install_text)
        self.assertNotIn("claude_desktop_config.json", install_text)
        self.assertNotIn("Settings > Developer > Edit Config", install_text)

    def test_install_guide_distinguishes_claude_surfaces_before_install(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("### Install in Claude Code", install_text)
        self.assertIn("### Install in Claude desktop", install_text)
        self.assertNotIn("ask the user which Claude surface", install_text)
        self.assertNotIn("Claude Desktop chat app", install_text)

    def test_readme_no_longer_duplicates_direct_cli_install_examples(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("/path/to/project", readme_text)
        self.assertNotIn("mods/my-mod", readme_text)
        self.assertNotIn("scripts/workbench_cli.py", readme_text)
        self.assertNotIn("tests/smoke_mcp.py", readme_text)

    def test_readme_links_to_separate_privacy_policy_and_omits_migration_table(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        privacy_text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")

        self.assertIn("[PRIVACY.md](PRIVACY.md)", readme_text)
        self.assertIn("does not collect telemetry", privacy_text)
        self.assertIn("configured trusted workspace paths", privacy_text)
        self.assertNotIn("## Privacy policy", readme_text)
        self.assertNotIn("## Migration From Older Tool Names", readme_text)
        self.assertNotIn("create_mod_project", readme_text)
        self.assertNotIn("launch_game_with_flags", readme_text)

    def test_install_guide_has_no_maintainer_release_or_validation_steps(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertNotIn("tests/smoke_mcp.py", install_text)
        self.assertNotIn("scripts/workbench_cli.py", install_text)
        self.assertNotIn("PLUGIN_CREATOR_SKILL", install_text)
        self.assertNotIn("claude plugin validate", install_text)
        self.assertNotIn("publish to pypi", install_text.lower())
        self.assertNotIn("mcp registry", install_text.lower())
        self.assertNotIn("release workflow", install_text.lower())
        self.assertNotIn("trusted publisher", install_text.lower())
        self.assertNotIn("testing unreleased", install_text.lower())
        self.assertNotIn("local checkout testing", install_text.lower())
        self.assertNotIn("developing this repository", install_text.lower())
        self.assertNotIn("< NUL", install_text)
        self.assertNotIn("< /dev/null", install_text)

    def test_install_guide_is_concise_and_omits_personal_legacy_cleanup(self) -> None:
        install_text = (ROOT / "INSTALL.md").read_text(encoding="utf-8")

        self.assertLess(len(install_text.splitlines()), 220)
        for stale_token in (
            "InfoLoom",
            "save analysis",
            "live city data",
            "city recovery",
            "dataexport",
            "saveinvestigator",
            "older or separate",
            "previous local tools repo",
            "manual cleanup",
        ):
            self.assertNotIn(stale_token, install_text)

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
