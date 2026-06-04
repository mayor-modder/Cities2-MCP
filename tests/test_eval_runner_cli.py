from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"


class EvalRunnerCliTests(unittest.TestCase):
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
