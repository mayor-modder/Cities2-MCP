from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalTraceTests(unittest.TestCase):
    def test_normalizes_codex_tool_events_and_transcript(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            events = [
                {"type": "tool_call", "name": "source_status", "arguments": {}},
                {
                    "type": "event",
                    "msg": {
                        "type": "function_call",
                        "name": "search",
                        "arguments": {"query": "office demand jobs education"},
                    },
                },
                {
                    "type": "agent_message",
                    "message": "Office demand needs educated workers.",
                },
            ]
            raw.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            call_records = [
                json.loads(line)
                for line in calls.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                ["source_status", "search"],
                [record["name"] for record in call_records],
            )
            self.assertIn(
                "Office demand needs educated workers.",
                transcript.read_text(encoding="utf-8"),
            )

    def test_ignores_non_json_lines(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            raw.write_text("not json\n", encoding="utf-8")

            normalize_codex_events(raw, calls, transcript)

            self.assertEqual("", calls.read_text(encoding="utf-8"))
            self.assertEqual("", transcript.read_text(encoding="utf-8"))

    def test_transcript_excludes_non_assistant_message_text(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            events = [
                {"type": "user_message", "message": "User prompt copied."},
                {"type": "tool_result", "content": "Tool result copied."},
                {"type": "tool_output", "text": "Tool output copied."},
                {"type": "error", "message": "Error copied."},
                {
                    "type": "message",
                    "role": "user",
                    "content": "Role user copied.",
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": "Assistant answer kept.",
                },
                {
                    "type": "event",
                    "msg": {
                        "type": "assistant_message",
                        "message": "Nested assistant answer kept.",
                    },
                },
            ]
            raw.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            self.assertEqual(
                "Assistant answer kept.\n\nNested assistant answer kept.",
                transcript.read_text(encoding="utf-8"),
            )

    def test_tool_call_parses_json_string_arguments(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            raw.write_text(
                json.dumps(
                    {
                        "type": "tool_call",
                        "name": "search",
                        "arguments": json.dumps({"query": "office demand"}),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            call_records = [
                json.loads(line)
                for line in calls.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual({"query": "office demand"}, call_records[0]["arguments"])

    def test_tool_call_defaults_malformed_and_non_dict_arguments(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            events = [
                {"type": "tool_call", "name": "bad_json", "arguments": "not json"},
                {"type": "tool_call", "name": "list_args", "arguments": [1, 2]},
                {"type": "tool_call", "name": "json_list", "arguments": "[1, 2]"},
            ]
            raw.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            call_records = [
                json.loads(line)
                for line in calls.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([{}, {}, {}], [record["arguments"] for record in call_records])

    def test_tool_call_name_falls_back_to_tool_name(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            run_dir = Path(tmp)
            raw = run_dir / "codex-events.jsonl"
            calls = run_dir / "coding-agent-tool-calls.jsonl"
            transcript = run_dir / "transcript.txt"

            raw.write_text(
                json.dumps(
                    {
                        "type": "tool_call",
                        "name": 123,
                        "tool_name": "source_status",
                        "arguments": {},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            call_records = [
                json.loads(line)
                for line in calls.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                ["source_status"], [record["name"] for record in call_records]
            )


if __name__ == "__main__":
    unittest.main()
