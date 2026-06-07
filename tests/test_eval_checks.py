from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def _write_trace(run_dir: Path, events: list[dict[str, object]]) -> None:
    (run_dir / "codex-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )


def _run_debugging_checks(
    checks: list[str],
    *,
    transcript: str = "",
    events: list[dict[str, object]] | None = None,
) -> list[object]:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        if transcript:
            (run_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
        if events is not None:
            _write_trace(run_dir, events)
        return [
            run_check(
                check,
                [],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )
            for check in checks
        ]


def _run_debugging_check(
    check: str,
    *,
    transcript: str = "",
    events: list[dict[str, object]] | None = None,
) -> object:
    return _run_debugging_checks([check], transcript=transcript, events=events)[0]


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

    def test_tool_called_accepts_mcp_server_prefix(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "cities2-mcp__source_status", "arguments": {}})
                + "\n",
                encoding="utf-8",
            )

            record = run_check(
                "tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )

        self.assertEqual("pass", record.status)

    def test_not_tool_called_rejects_mcp_server_prefix(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "cities2-mcp__source_status", "arguments": {}})
                + "\n",
                encoding="utf-8",
            )

            record = run_check(
                "not-tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )

        self.assertEqual("fail", record.status)

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

    def test_condition_skill_set_supports_debugging_skill_condition(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "cities2-mod-debugging").mkdir(parents=True)

            record = run_check(
                "condition-skill-set",
                [],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="pre",
            )

        self.assertEqual("pass", record.status)
        self.assertIn("cities2-mod-debugging", record.detail)

    def test_condition_skill_set_supports_all_matrix_target_conditions(self) -> None:
        from evals.runner.check_tool import run_check

        expected = {
            "no-skill": [],
            "with-cities2-knowledge": ["cities2-knowledge"],
            "with-cities2-modding": ["cities2-modding"],
            "with-cities2-mod-review": ["cities2-mod-review"],
            "with-cities2-mod-debugging": ["cities2-mod-debugging"],
            "with-cities2-mod-release": ["cities2-mod-release"],
        }

        for condition, skills in expected.items():
            with self.subTest(condition=condition):
                with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
                    run_dir = Path(tmp)
                    workdir = run_dir / "coding-agent-workdir"
                    agent_home = run_dir / "coding-agent-config"
                    workdir.mkdir()
                    for skill in skills:
                        (agent_home / "skills" / skill).mkdir(parents=True)

                    record = run_check(
                        "condition-skill-set",
                        [],
                        run_dir=run_dir,
                        workdir=workdir,
                        agent_home=agent_home,
                        condition=condition,
                        phase="pre",
                    )

                self.assertEqual("pass", record.status)

    def test_generic_transcript_contains_all_any_and_not_contains_any(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "transcript.txt").write_text(
                "Findings: observed files show a TSX file. "
                "There is not enough evidence to require React. "
                "The CSS file is not loaded, so it has no current effect.",
                encoding="utf-8",
            )

            contains_all = run_check(
                "transcript-contains-all",
                ["Findings", "observed", "CSS"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            contains_any = run_check(
                "transcript-contains-any",
                ["playtested package", "not enough evidence"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            not_contains_any = run_check(
                "transcript-not-contains-any",
                ["install React", "ready for upload now"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            missing_all = run_check(
                "transcript-contains-all",
                ["Findings", "playtested package"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )

        self.assertEqual("pass", contains_all.status)
        self.assertEqual("pass", contains_any.status)
        self.assertEqual("pass", not_contains_any.status)
        self.assertEqual("fail", missing_all.status)

    def test_transcript_rubric_reports_plain_english_criterion_result(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            (run_dir / "transcript.txt").write_text(
                "Findings: observed TSX file, but no package dependency evidence.",
                encoding="utf-8",
            )

            passed = run_check(
                "transcript-rubric",
                [
                    "evidence-grounded-review",
                    "Separates observed files from inferred recommendations.",
                    "all",
                    "observed",
                    "inferred",
                ],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            failed = run_check(
                "transcript-rubric",
                [
                    "react-evidence",
                    "Explains that TSX alone is not enough evidence for React.",
                    "all",
                    "TSX",
                    "React",
                ],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            any_pass = run_check(
                "transcript-rubric",
                [
                    "missing-react-proof",
                    "Names missing dependency evidence.",
                    "any",
                    "package dependency evidence",
                    "React imports",
                ],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            none_pass = run_check(
                "transcript-rubric",
                [
                    "no-release-claim",
                    "Does not claim the mod is ready to release.",
                    "none",
                    "ready to release",
                    "upload now",
                ],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            unknown_mode = run_check(
                "transcript-rubric",
                [
                    "bad-mode",
                    "Rejects unknown rubric modes.",
                    "some",
                    "observed",
                ],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )
            short_args = run_check(
                "transcript-rubric",
                ["too-short", "Missing mode and terms.", "all"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-review",
                phase="post",
            )

        self.assertEqual("fail", passed.status)
        self.assertEqual("rubric:evidence-grounded-review", passed.name)
        self.assertIn("Separates observed files", passed.detail)
        self.assertIn("missing=['inferred']", passed.detail)
        self.assertEqual("fail", failed.status)
        self.assertEqual("rubric:react-evidence", failed.name)
        self.assertIn("Explains that TSX alone", failed.detail)
        self.assertIn("missing=['React']", failed.detail)
        self.assertEqual("pass", any_pass.status)
        self.assertIn("matched=['package dependency evidence']", any_pass.detail)
        self.assertEqual("pass", none_pass.status)
        self.assertIn("mode=none", none_pass.detail)
        self.assertEqual("indeterminate", unknown_mode.status)
        self.assertIn("unknown mode=some", unknown_mode.detail)
        self.assertEqual("indeterminate", short_args.status)
        self.assertIn("usage: transcript-rubric", short_args.detail)

    def test_debugging_behavior_checks_pass_for_evidence_request_handoff(self) -> None:
        records = _run_debugging_checks(
            [
                "requests-runtime-evidence",
                "no-unverified-fix-claim",
                "handoff-present",
                "no-edit-before-runtime-evidence",
            ],
            transcript=(
                "I cannot verify the root cause from source alone. "
                "Please collect Modding.log, Player.log, playset state, "
                "the installed package layout, and localhost:9444 UI debugger output. "
                "Then reproduce in game and send those logs for the next step."
            ),
            events=[
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log before any source edit.",
                }
            ],
        )

        self.assertEqual(["pass", "pass", "pass", "pass"], [record.status for record in records])

    def test_no_unverified_fix_claim_allows_explicit_unverified_root_cause(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript=(
                "The root cause is unverified from source alone. "
                "A source edit would be a guess until runtime evidence is available."
            ),
        )

        self.assertEqual("pass", record.status)

    def test_no_unverified_fix_claim_allows_still_unverified_root_cause(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="The root cause is still unverified without logs or installed state.",
        )

        self.assertEqual("pass", record.status)

    def test_requests_runtime_evidence_fails_without_runtime_terms(self) -> None:
        record = _run_debugging_check(
            "requests-runtime-evidence",
            transcript="The source code probably has a null GameManager. Change the code.",
        )

        self.assertEqual("fail", record.status)

    def test_requests_runtime_evidence_fails_when_logs_are_dismissed(self) -> None:
        record = _run_debugging_check(
            "requests-runtime-evidence",
            transcript="I do not need Modding.log because the source code is enough.",
        )

        self.assertEqual("fail", record.status)

    def test_no_unverified_fix_claim_fails_on_fixed_claim_without_evidence(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="This is fixed. The root cause is definitely the UI update phase.",
        )

        self.assertEqual("fail", record.status)

    def test_no_unverified_fix_claim_fails_even_with_later_evidence_request(self) -> None:
        record = _run_debugging_check(
            "no-unverified-fix-claim",
            transcript="The root cause is the UI update phase. Please collect Modding.log.",
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_fails_when_write_precedes_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            transcript="I edited the code. Please collect Modding.log afterward.",
            events=[
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
                {"type": "agent_message", "message": "Please collect Modding.log afterward."},
            ],
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_allows_read_only_shell_before_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "tool_call",
                    "name": "shell_command",
                    "arguments": {"command": "git status --short"},
                },
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log.",
                },
            ],
        )

        self.assertEqual("pass", record.status)

    def test_no_edit_before_runtime_evidence_ignores_user_message_request(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "user_message",
                    "message": "Please collect Modding.log before editing.",
                },
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
            ],
        )

        self.assertEqual("fail", record.status)

    def test_no_edit_before_runtime_evidence_fails_when_logs_are_dismissed_before_edit(self) -> None:
        record = _run_debugging_check(
            "no-edit-before-runtime-evidence",
            events=[
                {
                    "type": "agent_message",
                    "message": "I do not need Modding.log before editing.",
                },
                {"type": "tool_call", "name": "apply_patch", "arguments": {}},
            ],
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

        with patch("evals.runner.checks._bash_path", return_value="Z:/evals/checks.sh"):
            command = _source_command(Path("checks.sh"), wsl=False)

        self.assertTrue(command.startswith("{ "), command)
        self.assertTrue(command.endswith("; }"), command)
        self.assertNotRegex(command, r"^\(")

    def test_run_checks_phase_reports_missing_bash_as_failed_check(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            with patch(
                "evals.runner.checks.subprocess.run",
                side_effect=FileNotFoundError("bash"),
            ):
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
        self.assertEqual("pre-checks", records[0].name)
        self.assertEqual("fail", records[0].status)
        self.assertIn("bash executable not found", records[0].detail)

    def test_run_checks_phase_records_nonzero_exit_after_check_records(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            sink = run_dir / "pre-checks.jsonl"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            def run_with_partial_record(*args: object, **kwargs: object) -> object:
                sink.write_text(
                    json.dumps(
                        {
                            "name": "first-check",
                            "phase": "pre",
                            "status": "pass",
                            "detail": "recorded before crash",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=7,
                    stdout="before crash\n",
                    stderr="script crashed\n",
                )

            with patch("evals.runner.checks._is_wsl_bash", return_value=False):
                with patch(
                    "evals.runner.checks.subprocess.run",
                    side_effect=run_with_partial_record,
                ):
                    records = run_checks_phase(
                        checks,
                        "pre",
                        run_dir=run_dir,
                        workdir=workdir,
                        agent_home=agent_home,
                        condition="no-skill",
                        repo_root=ROOT,
                    )

        self.assertEqual(
            ["first-check", "pre-checks"],
            [record.name for record in records],
        )
        self.assertEqual("pass", records[0].status)
        self.assertEqual("fail", records[1].status)
        self.assertIn("exit=7", records[1].detail)

    def test_run_checks_phase_reports_malformed_records_as_failed_check(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            checks = run_dir / "checks.sh"
            sink = run_dir / "pre-checks.jsonl"
            workdir.mkdir()
            agent_home.mkdir()
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")

            def run_with_malformed_record(*args: object, **kwargs: object) -> object:
                sink.write_text("{not-json}\n", encoding="utf-8")
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=7,
                    stdout="before crash\n",
                    stderr="script crashed\n",
                )

            with patch("evals.runner.checks._is_wsl_bash", return_value=False):
                with patch(
                    "evals.runner.checks.subprocess.run",
                    side_effect=run_with_malformed_record,
                ):
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
        self.assertEqual("pre-checks", records[0].name)
        self.assertEqual("fail", records[0].status)
        self.assertIn("invalid check record", records[0].detail)
        self.assertIn("exit=7", records[0].detail)


if __name__ == "__main__":
    unittest.main()
