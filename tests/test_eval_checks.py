from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class EvalCheckToolTests(unittest.TestCase):
    def test_tool_and_transcript_checks_pass_and_fail(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "cities2-knowledge").mkdir(parents=True)

            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "source_status", "arguments": {}}) + "\n",
                encoding="utf-8",
            )
            (run_dir / "transcript.txt").write_text(
                "Office demand depends on educated workers.\nSources: wiki corpus.\n",
                encoding="utf-8",
            )

            called = run_check(
                "tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            not_called = run_check(
                "not-tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            contains = run_check(
                "transcript-contains",
                ["office demand"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            missing = run_check(
                "transcript-contains",
                ["zoning taxes"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )

            self.assertEqual("pass", called.status)
            self.assertEqual("fail", not_called.status)
            self.assertEqual("pass", contains.status)
            self.assertEqual("fail", missing.status)

    def test_skill_not_visible_fails_when_visible_skill_contains_needle(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "superpowers-debugging").mkdir(parents=True)

            record = run_check(
                "skill-not-visible",
                ["superpowers"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="no-skill",
                phase="pre",
            )

            self.assertEqual("fail", record.status)

    def test_check_tool_main_cli_errors_and_default_phase(self) -> None:
        from evals.runner import check_tool

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            missing_status = check_tool.main([])

        self.assertEqual(2, missing_status)
        self.assertIn("missing check name", stderr.getvalue())

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            env = {
                "EVAL_RUN_DIR": str(run_dir),
                "EVAL_WORKDIR": str(workdir),
                "EVAL_AGENT_HOME": str(agent_home),
                "EVAL_CONDITION": "no-skill",
            }

            stdout = io.StringIO()
            with patch.dict(os.environ, env, clear=True):
                with contextlib.redirect_stdout(stdout):
                    status = check_tool.main(["agent-home-contained"])

            data = json.loads(stdout.getvalue())
            self.assertEqual(0, status)
            self.assertEqual("pass", data["status"])
            self.assertEqual("post", data["phase"])

            stderr = io.StringIO()
            env["EVAL_CHECK_PHASE"] = "during"
            with patch.dict(os.environ, env, clear=True):
                with contextlib.redirect_stderr(stderr):
                    invalid_status = check_tool.main(["agent-home-contained"])

            self.assertEqual(2, invalid_status)
            self.assertIn("invalid EVAL_CHECK_PHASE: during", stderr.getvalue())

    @unittest.skipUnless(shutil.which("bash"), "bash is required for checks.sh")
    def test_run_checks_phase_collects_records_from_checks_sh(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text(
                "pre() {\n"
                "    python -m evals.runner.check_tool agent-home-contained\n"
                "}\n"
                "post() { :; }\n",
                encoding="utf-8",
            )

            records = run_checks_phase(
                checks,
                "pre",
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="no-skill",
                repo_root=ROOT,
            )

            self.assertEqual(1, len(records))
            self.assertEqual("agent-home-contained", records[0].name)
            self.assertEqual("pass", records[0].status)

    def test_read_records_requires_declared_fields(self) -> None:
        from evals.runner.checks import _read_records

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            sink = Path(tmp) / "post-checks.jsonl"
            sink.write_text(
                json.dumps(
                    {
                        "name": "missing-detail",
                        "phase": "post",
                        "status": "pass",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(KeyError):
                _read_records(sink)

    def test_read_records_rejects_malformed_jsonl_records(self) -> None:
        from evals.runner.checks import _read_records

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            sink = Path(tmp) / "post-checks.jsonl"
            sink.write_text("{not-json}\n", encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                _read_records(sink)

            sink.write_text('"not-an-object"\n', encoding="utf-8")

            with self.assertRaises(TypeError):
                _read_records(sink)

    def test_source_command_drive_fallback_uses_current_shell(self) -> None:
        from evals.runner.checks import _source_command

        command = _source_command(Path("Z:/evals/checks.sh"), wsl=False)

        self.assertTrue(command.startswith("{ "), command)
        self.assertTrue(command.endswith("; }"), command)
        self.assertNotRegex(command, r"^\(")


if __name__ == "__main__":
    unittest.main()
