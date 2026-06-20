from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClaudeCleanRoomAdapterTests(unittest.TestCase):
    def test_prepare_claude_home_installs_only_declared_skill_and_mcp_config(self) -> None:
        from evals.runner.claude_adapter import prepare_claude_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
            root = Path(tmp)
            claude_home = root / "coding-agent-config"
            workspace = root / "coding-agent-workdir"

            config = prepare_claude_home(
                repo_root=ROOT,
                claude_home=claude_home,
                workspace=workspace,
                skills=("cities2-knowledge",),
            )

            self.assertTrue(config.mcp_config.is_file())
            self.assertIsNotNone(config.plugin_dir)
            assert config.plugin_dir is not None
            self.assertTrue(
                (config.plugin_dir / "skills" / "cities2-knowledge" / "SKILL.md").is_file()
            )
            self.assertFalse(
                (config.plugin_dir / "skills" / "cities2-mod-debugging").exists()
            )
            mcp = json.loads(config.mcp_config.read_text(encoding="utf-8"))
            server = mcp["mcpServers"]["cities2-mcp"]
            self.assertIn("cities2_mcp.mcp_server", server["args"])
            self.assertIn(str(workspace.resolve()), server["args"])
            self.assertEqual(str(ROOT.resolve()), server["env"]["PYTHONPATH"])

    def test_no_skill_condition_has_no_plugin_dir(self) -> None:
        from evals.runner.claude_adapter import prepare_claude_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
            root = Path(tmp)
            config = prepare_claude_home(
                repo_root=ROOT,
                claude_home=root / "coding-agent-config",
                workspace=root / "coding-agent-workdir",
                skills=(),
            )

            self.assertTrue(config.mcp_config.is_file())
            self.assertIsNone(config.plugin_dir)

    def test_prepare_claude_home_rejects_path_like_skill_name(self) -> None:
        from evals.runner.claude_adapter import ClaudeAdapterError, prepare_claude_home

        skill_names = (
            "cities2-knowledge/../cities2-mod-debugging",
            "cities2-knowledge\\..\\cities2-mod-debugging",
            "/cities2-knowledge",
            "C:\\cities2-knowledge",
        )
        for skill_name in skill_names:
            with self.subTest(skill_name=skill_name):
                with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
                    root = Path(tmp)
                    with self.assertRaisesRegex(
                        ClaudeAdapterError,
                        f"invalid skill name: {re.escape(skill_name)}",
                    ):
                        prepare_claude_home(
                            repo_root=ROOT,
                            claude_home=root / "coding-agent-config",
                            workspace=root / "coding-agent-workdir",
                            skills=(skill_name,),
                        )

    def test_minimal_claude_env_forwards_only_explicit_api_auth(self) -> None:
        from evals.runner.claude_adapter import minimal_claude_env

        original = os.environ.get("ANTHROPIC_API_KEY")
        original_appdata = os.environ.get("APPDATA")
        os.environ["ANTHROPIC_API_KEY"] = "unit-test-anthropic-secret"
        os.environ["APPDATA"] = "unit-test-appdata"
        try:
            with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
                root = Path(tmp)
                env = minimal_claude_env(
                    claude_home=root / "coding-agent-config",
                    repo_root=ROOT,
                    include_auth=True,
                )
        finally:
            if original is None:
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = original
            if original_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = original_appdata

        self.assertEqual("unit-test-anthropic-secret", env["ANTHROPIC_API_KEY"])
        self.assertEqual("unit-test-appdata", env["APPDATA"])
        self.assertEqual(str(ROOT.resolve()), env["PYTHONPATH"])
        self.assertTrue(Path(env["CLAUDE_CONFIG_DIR"]).is_absolute())
        self.assertNotIn("OPENAI_API_KEY", env)

    def test_seed_claude_auth_copies_host_oauth_credentials(self) -> None:
        from evals.runner.claude_adapter import seed_claude_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
            root = Path(tmp)
            claude_home = root / "coding-agent-config"
            host_claude_home = root / "host-claude"
            claude_home.mkdir()
            host_claude_home.mkdir()
            (host_claude_home / ".credentials.json").write_text(
                '{"claudeAiOauth": {"accessToken": "fake-token"}}\n',
                encoding="utf-8",
            )

            seed_claude_auth(
                claude_home=claude_home,
                env={"PATH": "placeholder"},
                host_claude_home=host_claude_home,
            )

            self.assertEqual(
                '{"claudeAiOauth": {"accessToken": "fake-token"}}\n',
                (claude_home / ".credentials.json").read_text(encoding="utf-8"),
            )

    def test_seed_claude_auth_reports_missing_oauth_credentials(self) -> None:
        from evals.runner.claude_adapter import ClaudeAdapterError, seed_claude_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
            root = Path(tmp)
            claude_home = root / "coding-agent-config"
            host_claude_home = root / "host-claude"
            claude_home.mkdir()
            host_claude_home.mkdir()

            with self.assertRaisesRegex(
                ClaudeAdapterError,
                "ANTHROPIC_API_KEY or local Claude OAuth credentials are required",
            ):
                seed_claude_auth(
                    claude_home=claude_home,
                    env={"PATH": "placeholder"},
                    host_claude_home=host_claude_home,
                )

    def test_seed_claude_auth_does_not_copy_oauth_when_api_key_is_present(self) -> None:
        from evals.runner.claude_adapter import seed_claude_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-claude-") as tmp:
            root = Path(tmp)
            claude_home = root / "coding-agent-config"
            host_claude_home = root / "host-claude"
            claude_home.mkdir()
            host_claude_home.mkdir()

            seed_claude_auth(
                claude_home=claude_home,
                env={"PATH": "placeholder", "ANTHROPIC_API_KEY": "fake-api-key"},
                host_claude_home=host_claude_home,
            )

            self.assertFalse((claude_home / ".credentials.json").exists())

    def test_build_claude_print_command_uses_stream_json_and_clean_room_inputs(self) -> None:
        from evals.runner.claude_adapter import build_claude_print_command

        command = build_claude_print_command(
            claude_command="claude",
            workdir=Path("work"),
            prompt="Prompt",
            mcp_config=Path("mcp.json"),
            plugin_dir=Path("plugin"),
        )

        self.assertEqual("claude", command[0])
        self.assertIn("-p", command)
        self.assertNotIn("--bare", command)
        self.assertIn("--verbose", command)
        self.assertIn("--output-format", command)
        self.assertIn("stream-json", command)
        self.assertIn("--permission-mode", command)
        self.assertIn("bypassPermissions", command)
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--mcp-config", command)
        self.assertEqual("mcp.json", Path(command[command.index("--mcp-config") + 1]).name)
        self.assertIn("--plugin-dir", command)
        self.assertEqual("plugin", Path(command[command.index("--plugin-dir") + 1]).name)
        self.assertEqual("work", Path(command[command.index("--add-dir") + 1]).name)
        self.assertEqual("Prompt", command[-1])


if __name__ == "__main__":
    unittest.main()
