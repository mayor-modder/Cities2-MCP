from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from evals.runner.models import Scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"
DEBUGGING_SCENARIO = (
    ROOT / "evals" / "scenarios" / "baseline" / "cities2-debugging-runtime-no-logs"
)
REVIEW_MATRIX_SCENARIO = (
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-tsx-no-react-evidence"
)
RELEASE_MATRIX_SCENARIO = (
    ROOT
    / "evals"
    / "scenarios"
    / "matrix"
    / "cities2-mod-release-build-passed-no-playtest"
)
MODDING_MATRIX_SCENARIO = (
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-modding-workflow-safe-handoff"
)


class EvalRunnerCliTests(unittest.TestCase):
    def test_summarize_subcommand_writes_digest(self) -> None:
        from evals.runner.__main__ import main

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            verdict = root / "verdict.json"
            output = root / "digest.md"
            verdict.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "no-skill",
                            "trial": 1,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T17:00:00Z",
                            "skill_checksums": {},
                        },
                        "final": "pass",
                        "final_reason": "all checks passed",
                        "checks": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = main(["summarize", "--output", str(output), str(verdict)])

            digest = output.read_text(encoding="utf-8")

        self.assertEqual(0, status)
        self.assertEqual(f"{output}\n", stdout.getvalue())
        self.assertIn("# Eval results digest", digest)
        self.assertIn("Verdicts summarized: 1", digest)

    def test_utc_timestamp_works_without_datetime_utc_alias(self) -> None:
        from evals.runner import __main__ as runner

        utc = runner.dt.UTC
        try:
            delattr(runner.dt, "UTC")

            stamp = runner._utc_timestamp()
        finally:
            runner.dt.UTC = utc

        self.assertRegex(stamp, r"^\d{8}T\d{6}Z$")

    def test_metadata_uses_python_310_compatible_utc(self) -> None:
        from evals.runner import __main__ as runner

        scenario = Scenario(
            id="scenario-id",
            title="Scenario",
            path=ROOT,
            story=ROOT / "story.md",
            setup=ROOT / "setup.sh",
            checks=ROOT / "checks.sh",
        )
        utc = runner.dt.UTC
        try:
            delattr(runner.dt, "UTC")
            with patch("evals.runner.__main__._repo_commit", return_value="abc123"):
                metadata = runner._metadata(
                    scenario=scenario,
                    condition="no-skill",
                    trial=1,
                    backend_name="codex",
                    backend_executable="codex",
                    repo_root=ROOT,
                    skills=(),
                )
        finally:
            runner.dt.UTC = utc

        self.assertRegex(
            metadata.run_started_at,
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )

    def test_final_status_preserves_indeterminate_post_checks(self) -> None:
        from evals.runner.__main__ import _final_status
        from evals.runner.models import CheckRecord

        pre_records = [
            CheckRecord("agent-home-contained", "pre", "pass", "contained"),
        ]
        records = [
            *pre_records,
            CheckRecord(
                "required-tool-called",
                "post",
                "indeterminate",
                "tool exposure unavailable",
            ),
            CheckRecord("knowledge-office-demand-grounded", "post", "fail", "no source"),
        ]

        final, reason = _final_status(pre_records, records)

        self.assertEqual("indeterminate", final)
        self.assertIn("indeterminate", reason)

    def test_condition_skills_supports_debugging_skill_condition(self) -> None:
        from evals.runner.__main__ import _condition_skills

        self.assertEqual(
            ("cities2-mod-debugging",),
            _condition_skills("with-cities2-mod-debugging"),
        )

    def test_condition_skills_supports_all_matrix_target_conditions(self) -> None:
        from evals.runner.__main__ import _condition_skills

        expected = {
            "no-skill": (),
            "with-cities2-knowledge": ("cities2-knowledge",),
            "with-cities2-modding": ("cities2-modding",),
            "with-cities2-mod-review": ("cities2-mod-review",),
            "with-cities2-mod-debugging": ("cities2-mod-debugging",),
            "with-cities2-mod-release": ("cities2-mod-release",),
        }
        for condition, skills in expected.items():
            with self.subTest(condition=condition):
                self.assertEqual(skills, _condition_skills(condition))

    def test_mcp_error_messages_include_claude_auth_failures(self) -> None:
        from evals.runner.__main__ import _mcp_error_messages

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            raw_events = Path(tmp) / "claude-preflight-events.jsonl"
            raw_events.write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "error": "authentication_failed",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Not logged in. Please run /login",
                                }
                            ]
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            messages = _mcp_error_messages(raw_events)

        self.assertEqual(
            ["authentication_failed: Not logged in. Please run /login"],
            messages,
        )

    def test_run_setup_reports_missing_bash(self) -> None:
        from evals.runner.__main__ import _run_setup

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            with patch(
                "evals.runner.__main__.subprocess.run",
                side_effect=FileNotFoundError("bash"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "bash executable not found",
                ):
                    _run_setup(Path("setup.sh"), Path(tmp))

    def test_run_setup_translates_setup_and_workdir_for_wsl_bash(self) -> None:
        from evals.runner.__main__ import _run_setup

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            setup = root / "setup.sh"
            workdir = root / "workdir"
            setup.write_text(":", encoding="utf-8")
            workdir.mkdir()
            calls: list[list[str]] = []

            def fake_bash_path(path: Path, *, wsl: bool) -> str:
                return f"/wsl/{path.name}"

            with patch("evals.runner.__main__._is_wsl_bash", return_value=True):
                with patch("evals.runner.__main__._bash_path", side_effect=fake_bash_path):
                    with patch(
                        "evals.runner.__main__.subprocess.run",
                        return_value=type(
                            "Result",
                            (),
                            {"returncode": 0, "stdout": "", "stderr": ""},
                        )(),
                    ) as run:
                        _run_setup(setup, workdir)
                        calls.append(run.call_args.args[0])

        self.assertEqual(
            [["bash", "-lc", "cd /wsl/workdir; bash /wsl/setup.sh"]],
            calls,
        )

    def test_run_eval_passes_absolute_setup_path_without_relpath(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            scenario_dir = root / "scenario"
            scenario_dir.mkdir()
            story = scenario_dir / "story.md"
            setup = scenario_dir / "setup.sh"
            checks = scenario_dir / "checks.sh"
            story.write_text("```text\nPrompt\n```\n", encoding="utf-8")
            setup.write_text(":", encoding="utf-8")
            checks.write_text("pre() { :; }\npost() { :; }\n", encoding="utf-8")
            scenario = Scenario(
                id="scenario-id",
                title="Scenario",
                path=scenario_dir,
                story=story,
                setup=setup,
                checks=checks,
            )
            observed_setup_paths: list[Path] = []

            def record_setup_path(path: Path, workdir: Path) -> None:
                observed_setup_paths.append(path)

            with patch("evals.runner.__main__.load_scenario", return_value=scenario):
                with patch(
                    "evals.runner.__main__._utc_timestamp",
                    return_value="20260601T120000Z",
                ):
                    with patch("evals.runner.__main__.prepare_codex_home"):
                        with patch(
                            "evals.runner.__main__._run_setup",
                            side_effect=record_setup_path,
                        ):
                            with patch("evals.runner.__main__.run_checks_phase", return_value=[]):
                                with patch(
                                    "evals.runner.__main__._repo_commit",
                                    return_value="abc123",
                                ):
                                    with patch(
                                        "evals.runner.__main__.subprocess.run",
                                        return_value=type(
                                            "Result",
                                            (),
                                            {"returncode": 0, "stderr": ""},
                                        )(),
                                    ):
                                        with patch(
                                            "os.path.relpath",
                                            side_effect=ValueError("different drives"),
                                        ):
                                            run_eval(
                                                scenario_path=scenario_dir,
                                                condition="no-skill",
                                                repo_root=ROOT,
                                                results_root=root / "results",
                                                live_auth=False,
                                            )

        self.assertEqual([setup.resolve()], observed_setup_paths)

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_runner_writes_verdict_with_codex_stub(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"tool_call","name":"cities2-knowledge","arguments":{}}')
                    print('{"type":"tool_call","name":"source_status","arguments":{}}')
                    print('{"type":"tool_call","name":"search","arguments":{"query":"office demand jobs education"}}')
                    print('{"type":"agent_message","message":"Office demand grows with educated workers, enough jobs, lower office taxes, and careful zoning. Source note: wiki and game encyclopedia entries for demand and office zones."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

            self.assertEqual(verdict["metadata"]["scenario_id"], "cities2-knowledge-office-demand")
            self.assertEqual(verdict["metadata"]["condition_id"], "with-cities2-knowledge")
            self.assertEqual(verdict["final"], "pass")
            self.assertTrue(paths.raw_events.exists())
            self.assertTrue(paths.tool_calls.exists())
            self.assertTrue(paths.transcript.exists())

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_knowledge_runner_marks_missing_mcp_tools_indeterminate(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"agent_message","message":"I read the Cities2 knowledge skill, but the Cities2-MCP retrieval tools are not exposed in this clean-room Codex environment."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

        self.assertEqual("indeterminate", verdict["final"])
        self.assertIn("indeterminate", verdict["final_reason"])
        self.assertIn("codex-mcp-tool-exposure", [record["name"] for record in verdict["checks"]])
        self.assertNotIn("required-tool-called", [record["name"] for record in verdict["checks"]])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_knowledge_runner_stops_when_mcp_tool_preflight_is_unavailable(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"agent_message","message":"The Cities2-MCP retrieval tools are not exposed in this clean-room Codex environment."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))
            raw_events = paths.raw_events.read_text(encoding="utf-8")

        self.assertEqual("indeterminate", verdict["final"])
        preflight = [
            record
            for record in verdict["checks"]
            if record["name"] == "codex-mcp-tool-exposure"
        ]
        self.assertEqual(
            [
                {
                    "name": "codex-mcp-tool-exposure",
                    "phase": "pre",
                    "status": "indeterminate",
                    "detail": "expected=['source_status', 'search']; names=[]",
                }
            ],
            preflight,
        )
        self.assertEqual("", raw_events)
        self.assertNotIn("required-tool-called", [record["name"] for record in verdict["checks"]])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_debugging_baseline_stub_writes_passing_verdict(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_debugging_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"agent_message","message":"I cannot verify the root cause from source alone. Please collect Modding.log, Player.log, playset state, installed package layout, and localhost:9444 UI debugger output. Then reproduce in game and send those logs for the next step."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=DEBUGGING_SCENARIO,
                condition="with-cities2-mod-debugging",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

        self.assertEqual(
            "cities2-debugging-runtime-no-logs",
            verdict["metadata"]["scenario_id"],
        )
        self.assertEqual(
            "with-cities2-mod-debugging",
            verdict["metadata"]["condition_id"],
        )
        self.assertEqual("pass", verdict["final"])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_review_matrix_stub_exercises_harness_wiring(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_review_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    import json

                    print(json.dumps({"type":"tool_call","name":"shell_command","arguments":{"command":"Get-Content ReviewBaitMod/src/Mod.cs; Get-Content ReviewBaitMod/ui/OptionsPanel.tsx; Get-Content ReviewBaitMod/ui/theme.css; Get-Content ReviewBaitMod/README.md"}}))
                    print(json.dumps({"type":"agent_message","message":"Findings\\n\\n1. Mod.cs has only a Name property and no IMod lifecycle. Fix: implement the supported entry point, then run build/package checks.\\n2. theme.css is not imported or referenced by OptionsPanel.tsx, so it has no current effect. Fix: wire it into the UI bundle.\\n3. React loader work is a hypothesis until package or import evidence proves it. Readiness still needs a package artifact, installed package/playset smoke launch, logs, UI debugger evidence, and local playtest results."}))
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=REVIEW_MATRIX_SCENARIO,
                condition="with-cities2-mod-review",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

        self.assertEqual("cities2-mod-review-tsx-no-react-evidence", verdict["metadata"]["scenario_id"])
        self.assertEqual("with-cities2-mod-review", verdict["metadata"]["condition_id"])
        self.assertEqual("pass", verdict["final"])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_release_matrix_stub_exercises_harness_wiring(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_release_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"agent_message","message":"The packaged mod has not been locally playtested, so I advise against public upload and would not call it release-ready. Draft Paradox Mods description, unvalidated: Adds a settings panel. Before publishing, run a local packaged smoke test."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=RELEASE_MATRIX_SCENARIO,
                condition="with-cities2-mod-release",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

        self.assertEqual(
            "cities2-mod-release-build-passed-no-playtest",
            verdict["metadata"]["scenario_id"],
        )
        self.assertEqual("with-cities2-mod-release", verdict["metadata"]["condition_id"])
        self.assertEqual("pass", verdict["final"])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_modding_matrix_stub_exercises_harness_wiring(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_modding_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"tool_call","name":"shell_command","arguments":{"command":"Get-Content WorkflowHandoffMod/README.md; Get-Content WorkflowHandoffMod/src/Mod.cs; Get-Content WorkflowHandoffMod/package/package-state.txt"}}')
                    print('{"type":"agent_message","message":"I cannot confirm the build from this fixture, so keep the build status as unverified until you run it locally. For local playtesting, install a local package, launch the game, confirm the playset, and collect Modding.log plus localhost:9444 UI debugger evidence. Public upload is blocked until the packaged mod is locally playtested, so this is not public release ready; use cities2-mod-release for release readiness and cities2-mod-debugging if the UI does not appear."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=MODDING_MATRIX_SCENARIO,
                condition="with-cities2-modding",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

        self.assertEqual("cities2-modding-workflow-safe-handoff", verdict["metadata"]["scenario_id"])
        self.assertEqual("with-cities2-modding", verdict["metadata"]["condition_id"])
        self.assertEqual("pass", verdict["final"])

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_claude_backend_stub_writes_passing_verdict(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            claude_stub = root / "claude_stub.py"
            claude_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    import json

                    event = {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "mcp__cities2-mcp__source_status", "input": {}},
                                {"type": "tool_use", "name": "mcp__cities2-mcp__search", "input": {"query": "office demand jobs education"}},
                                {"type": "text", "text": "Office demand grows with educated workers, enough jobs, lower office taxes, and careful zoning. Source note: wiki and game encyclopedia entries for demand and office zones."},
                            ]
                        },
                    }
                    print(json.dumps(event))
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                backend="claude",
                claude_command=sys.executable,
                claude_args_prefix=(str(claude_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))
            tool_calls = paths.tool_calls.read_text(encoding="utf-8")

        self.assertEqual("claude", verdict["metadata"]["backend_name"])
        self.assertEqual(sys.executable, verdict["metadata"]["backend_executable"])
        self.assertEqual("with-cities2-knowledge", verdict["metadata"]["condition_id"])
        self.assertEqual("pass", verdict["final"])
        self.assertIn("mcp__cities2-mcp__source_status", tool_calls)

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_claude_backend_records_nonzero_exit(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            claude_stub = root / "claude_exit_stub.py"
            claude_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    import json
                    import sys

                    event = {
                        "type": "assistant",
                        "message": {"content": [{"type": "text", "text": "I cannot verify the root cause."}]},
                    }
                    print(json.dumps(event))
                    sys.stderr.write("claude failure\\n")
                    raise SystemExit(9)
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=DEBUGGING_SCENARIO,
                condition="with-cities2-mod-debugging",
                repo_root=ROOT,
                results_root=root / "results",
                backend="claude",
                claude_command=sys.executable,
                claude_args_prefix=(str(claude_stub),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))
            raw_events = paths.raw_events.read_text(encoding="utf-8")

        self.assertIn("claude failure", raw_events)
        self.assertIn(
            {
                "name": "claude-exit",
                "phase": "post",
                "status": "fail",
                "detail": "exit=9",
            },
            verdict["checks"],
        )

    @unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
    def test_nonzero_codex_stderr_is_appended_as_raw_text(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            codex_stub = root / "codex_stub.py"
            codex_stub.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    import sys

                    if "Eval plumbing preflight" in sys.argv[-1]:
                        print('{"type":"tool_call","name":"source_status","arguments":{}}')
                        print('{"type":"tool_call","name":"search","arguments":{"query":"office demand"}}')
                        raise SystemExit(0)

                    print('{"type":"tool_call","name":"cities2-knowledge","arguments":{}}')
                    print('{"type":"tool_call","name":"source_status","arguments":{}}')
                    print('{"type":"tool_call","name":"search","arguments":{"query":"office demand jobs education"}}')
                    print('{"type":"agent_message","message":"Office demand grows with educated workers. Source note: wiki."}')
                    sys.stderr.write("first line\\n  second line\\n")
                    raise SystemExit(7)
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(codex_stub),),
                live_auth=False,
                trial=1,
            )

            raw_events = paths.raw_events.read_text(encoding="utf-8")
            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

            self.assertTrue(raw_events.endswith("first line\n  second line\n"))
            self.assertNotIn('"type": "error"', raw_events)
            self.assertEqual(verdict["final"], "fail")
            self.assertIn(
                {
                    "name": "codex-exit",
                    "phase": "post",
                    "status": "fail",
                    "detail": "exit=7",
                },
                verdict["checks"],
            )
