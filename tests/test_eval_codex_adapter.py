from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class CodexCleanRoomAdapterTests(unittest.TestCase):
    def test_prepare_codex_home_installs_only_declared_skill_and_mcp_config(
        self,
    ) -> None:
        from evals.runner.codex_adapter import prepare_codex_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            prepare_codex_home(
                repo_root=ROOT,
                codex_home=codex_home,
                skills=("cities2-knowledge",),
            )

            self.assertTrue(
                (codex_home / "skills" / "cities2-knowledge" / "SKILL.md").is_file()
            )
            self.assertFalse((codex_home / "skills" / "cities2-mod-debugging").exists())
            self.assertFalse((codex_home / "skills" / "superpowers").exists())

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn("[mcp_servers.cities2-mcp]", config)
            self.assertIn("cities2_mcp.mcp_server", config)

    def test_no_skill_condition_has_empty_skill_directory(self) -> None:
        from evals.runner.codex_adapter import prepare_codex_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            prepare_codex_home(repo_root=ROOT, codex_home=codex_home, skills=())

            self.assertEqual([], list((codex_home / "skills").iterdir()))

    def test_mcp_config_uses_declared_workspace(self) -> None:
        from evals.runner.codex_adapter import prepare_codex_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"
            workspace = Path(tmp) / "coding-agent-workdir"

            prepare_codex_home(
                repo_root=ROOT,
                codex_home=codex_home,
                workspace=workspace,
                skills=(),
            )

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn(json.dumps(str(workspace.resolve())), config)
            self.assertNotIn(json.dumps(str(ROOT.resolve())), config)

    def test_prepare_codex_home_rejects_path_like_skill_name(self) -> None:
        from evals.runner.codex_adapter import CodexAdapterError, prepare_codex_home

        skill_names = (
            "cities2-knowledge/../cities2-mod-debugging",
            "cities2-knowledge\\..\\cities2-mod-debugging",
            "/cities2-knowledge",
            "C:\\cities2-knowledge",
        )
        for skill_name in skill_names:
            with self.subTest(skill_name=skill_name):
                with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
                    codex_home = Path(tmp) / "coding-agent-config"

                    with self.assertRaisesRegex(
                        CodexAdapterError,
                        f"invalid skill name: {re.escape(skill_name)}",
                    ):
                        prepare_codex_home(
                            repo_root=ROOT,
                            codex_home=codex_home,
                            skills=(skill_name,),
                        )

                    self.assertFalse(
                        (codex_home / "skills" / "cities2-mod-debugging").exists()
                    )

    def test_minimal_codex_env_uses_generated_home_without_user_profile(self) -> None:
        from evals.runner.codex_adapter import minimal_codex_env

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"
            repo_root = Path(tmp) / "repo"

            env = minimal_codex_env(
                codex_home=codex_home, repo_root=repo_root, include_auth=False
            )

            self.assertEqual(str(codex_home), env["CODEX_HOME"])
            self.assertEqual(str(repo_root), env["PYTHONPATH"])
            self.assertIn("PATH", env)
            self.assertNotIn("USERPROFILE", env)
            self.assertNotIn("HOME", env)
            self.assertNotIn("OPENAI_API_KEY", env)

    def test_minimal_codex_env_can_forward_auth_without_printing_it(self) -> None:
        from evals.runner.codex_adapter import minimal_codex_env

        original = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "unit-test-secret"
        try:
            with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
                codex_home = Path(tmp) / "coding-agent-config"
                repo_root = Path(tmp) / "repo"

                env = minimal_codex_env(
                    codex_home=codex_home, repo_root=repo_root, include_auth=True
                )

                self.assertEqual("unit-test-secret", env["OPENAI_API_KEY"])
        finally:
            if original is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = original

    def test_seed_codex_auth_sends_api_key_on_stdin_not_child_env(self) -> None:
        from evals.runner.codex_adapter import seed_codex_auth

        env = {
            "CODEX_HOME": "placeholder-home",
            "OPENAI_API_KEY": "sk-test-placeholder",
            "PATH": "placeholder-path",
        }
        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            with patch("evals.runner.codex_adapter.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess(
                    args=["codex", "login", "--with-api-key"],
                    returncode=0,
                    stderr="",
                )

                seed_codex_auth(codex_home=codex_home, env=env)

        kwargs = run.call_args.kwargs
        self.assertEqual("sk-test-placeholder", kwargs["input"])
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertEqual(str(codex_home), kwargs["env"]["CODEX_HOME"])

    def test_seed_codex_auth_copies_host_oauth_when_api_key_absent(self) -> None:
        from evals.runner.codex_adapter import seed_codex_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            root = Path(tmp)
            host_codex_home = root / "host-codex"
            codex_home = root / "coding-agent-config"
            host_codex_home.mkdir()
            codex_home.mkdir()
            (host_codex_home / "auth.json").write_text(
                '{"mode":"chatgpt","placeholder":"unit-test"}\n',
                encoding="utf-8",
            )

            with patch("evals.runner.codex_adapter.subprocess.run") as run:
                seed_codex_auth(
                    codex_home=codex_home,
                    env={"PATH": "placeholder-path"},
                    host_codex_home=host_codex_home,
                )

            self.assertEqual(
                '{"mode":"chatgpt","placeholder":"unit-test"}\n',
                (codex_home / "auth.json").read_text(encoding="utf-8"),
            )
            run.assert_not_called()

    def test_seed_codex_auth_uses_configured_codex_home_as_oauth_source(self) -> None:
        from evals.runner.codex_adapter import seed_codex_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            root = Path(tmp)
            host_codex_home = root / "configured-codex-home"
            codex_home = root / "coding-agent-config"
            host_codex_home.mkdir()
            codex_home.mkdir()
            (host_codex_home / "auth.json").write_text(
                '{"mode":"chatgpt","placeholder":"configured-home"}\n',
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(host_codex_home)}):
                with patch("evals.runner.codex_adapter.subprocess.run") as run:
                    seed_codex_auth(codex_home=codex_home, env={"PATH": "placeholder"})

            self.assertEqual(
                '{"mode":"chatgpt","placeholder":"configured-home"}\n',
                (codex_home / "auth.json").read_text(encoding="utf-8"),
            )
            run.assert_not_called()

    def test_seed_codex_auth_reports_missing_local_auth_without_api_key(self) -> None:
        from evals.runner.codex_adapter import CodexAdapterError, seed_codex_auth

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            root = Path(tmp)
            host_codex_home = root / "host-codex"
            codex_home = root / "coding-agent-config"
            host_codex_home.mkdir()
            codex_home.mkdir()

            with self.assertRaisesRegex(
                CodexAdapterError,
                "OPENAI_API_KEY or local Codex auth is required for live Codex evals",
            ):
                seed_codex_auth(
                    codex_home=codex_home,
                    env={"PATH": "placeholder-path"},
                    host_codex_home=host_codex_home,
                )

            self.assertFalse((codex_home / "auth.json").exists())

    def test_seed_codex_auth_redacts_api_key_from_login_failure(self) -> None:
        from evals.runner.codex_adapter import CodexAdapterError, seed_codex_auth

        api_key = "sk-test-placeholder"
        env = {"OPENAI_API_KEY": api_key, "PATH": "placeholder-path"}
        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            with patch("evals.runner.codex_adapter.subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess(
                    args=["codex", "login", "--with-api-key"],
                    returncode=17,
                    stderr=f"login failed for {api_key}",
                )

                with self.assertRaises(CodexAdapterError) as raised:
                    seed_codex_auth(codex_home=codex_home, env=env)

        message = str(raised.exception)
        self.assertIn("codex login failed with exit 17", message)
        self.assertIn("[REDACTED]", message)
        self.assertNotIn(api_key, message)

    def test_toml_string_escapes_control_characters(self) -> None:
        from evals.runner.codex_adapter import _toml_string

        encoded = _toml_string('line 1\nline 2\t"value"\x08')

        self.assertEqual('"line 1\\nline 2\\t\\"value\\"\\b"', encoded)


if __name__ == "__main__":
    unittest.main()
