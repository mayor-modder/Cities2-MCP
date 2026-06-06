from __future__ import annotations

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


class EvalRunnerCliTests(unittest.TestCase):
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
                    codex_command="codex",
                    repo_root=ROOT,
                    skills=(),
                )
        finally:
            runner.dt.UTC = utc

        self.assertRegex(
            metadata.run_started_at,
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )

    def test_condition_skills_supports_debugging_skill_condition(self) -> None:
        from evals.runner.__main__ import _condition_skills

        self.assertEqual(
            ("cities2-mod-debugging",),
            _condition_skills("with-cities2-mod-debugging"),
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
                    print('{"type":"agent_message","message":"Office demand grows with educated workers. Source note: wiki."}')
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
