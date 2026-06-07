from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .conditions import condition_skills
from .models import CheckRecord, CheckStatus, Phase


RUNTIME_EVIDENCE_TERMS = (
    "modding.log",
    "player.log",
    "unity log",
    "playset",
    "installed package",
    "package layout",
    "localhost:9444",
    "ui debugger",
)
REQUEST_EVIDENCE_TERMS = (
    "collect",
    "send",
    "provide",
    "share",
    "check",
    "capture",
    "gather",
    "attach",
)
HANDOFF_TERMS = ("collect", "send", "reproduce", "playtest", "next step")
UNVERIFIED_FIX_CLAIMS = (
    "this is fixed",
    "fixed now",
    "verified fixed",
    "root cause is",
    "definitely",
)
UNVERIFIED_CLAIM_NEGATIONS = (
    "cannot verify the root cause",
    "can't verify the root cause",
    "cannot confirm the root cause",
    "can't confirm the root cause",
    "root cause is unverified",
    "root cause is still unverified",
)
EDIT_TOOL_NAMES = ("apply_patch", "write", "edit", "shell_command")
SHELL_EDIT_MARKERS = (
    ">",
    ">>",
    "set-content",
    "out-file",
    "add-content",
    "new-item",
    "remove-item",
    "move-item",
    "copy-item",
    "del ",
    "rm ",
    "mkdir ",
)


# Debugging behavior checks are deterministic smoke signals for the baseline
# scenario; they intentionally avoid general NLP or shell parsing.
def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _tool_names(run_dir: Path) -> list[str]:
    path = run_dir / "coding-agent-tool-calls.jsonl"
    if not path.is_file():
        return []

    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(record["name"])
    return names


def _tool_name_matches(actual: str, expected: str) -> bool:
    return actual == expected or actual.endswith(f"__{expected}")


def _transcript_text(run_dir: Path) -> str:
    transcript = run_dir / "transcript.txt"
    return transcript.read_text(encoding="utf-8") if transcript.is_file() else ""


def _raw_events(run_dir: Path) -> list[dict[str, object]]:
    path = run_dir / "codex-events.jsonl"
    if not path.is_file():
        return []

    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _nested_event(event: dict[str, object]) -> dict[str, object]:
    msg = event.get("msg")
    if isinstance(msg, dict):
        return msg
    item = event.get("item")
    if isinstance(item, dict):
        return item
    return event


def _event_text(event: dict[str, object]) -> str:
    nested = _nested_event(event)
    parts = [
        value
        for key in ("message", "text", "content")
        if isinstance((value := nested.get(key)), str)
    ]
    return " ".join(parts)


def _assistant_event_text(event: dict[str, object]) -> str:
    nested = _nested_event(event)
    event_type = nested.get("type")
    role = nested.get("role")
    if event_type in ("agent_message", "assistant_message") or role == "assistant":
        return _event_text(event)
    return ""


def _event_tool_name(event: dict[str, object]) -> str:
    nested = _nested_event(event)
    event_type = nested.get("type")
    if event_type not in ("tool_call", "function_call"):
        return ""
    for key in ("name", "tool_name"):
        value = nested.get(key)
        if isinstance(value, str):
            return value
    return ""


def _event_arguments_text(event: dict[str, object]) -> str:
    nested = _nested_event(event)
    value = nested.get("arguments")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values())
    return ""


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower_text = text.lower()
    return any(needle.lower() in lower_text for needle in needles)


def _contains_all(text: str, needles: list[str]) -> bool:
    lower_text = text.lower()
    return bool(needles) and all(needle.lower() in lower_text for needle in needles)


def _contains_any_arg(text: str, needles: list[str]) -> bool:
    lower_text = text.lower()
    return bool(needles) and any(needle.lower() in lower_text for needle in needles)


def _requests_runtime_evidence(text: str) -> bool:
    return _has_any(text, REQUEST_EVIDENCE_TERMS) and _has_any(
        text, RUNTIME_EVIDENCE_TERMS
    )


def _has_unverified_fix_claim(text: str) -> bool:
    lower_text = text.lower()
    for negation in UNVERIFIED_CLAIM_NEGATIONS:
        lower_text = lower_text.replace(negation, "")
    return _has_any(lower_text, UNVERIFIED_FIX_CLAIMS)


def _is_edit_tool_call(event: dict[str, object]) -> bool:
    tool_name = _event_tool_name(event).lower()
    if not tool_name:
        return False
    if tool_name == "shell_command":
        return _has_any(_event_arguments_text(event), SHELL_EDIT_MARKERS)
    return any(edit_name in tool_name for edit_name in EDIT_TOOL_NAMES)


def _skill_dirs(agent_home: Path) -> list[str]:
    skills = agent_home / "skills"
    if not skills.is_dir():
        return []
    return sorted(child.name for child in skills.iterdir() if child.is_dir())


def _record(name: str, phase: Phase, status: CheckStatus, detail: str) -> CheckRecord:
    return CheckRecord(name=name, phase=phase, status=status, detail=detail)


def run_check(
    name: str,
    args: list[str],
    *,
    run_dir: Path,
    workdir: Path,
    agent_home: Path,
    condition: str,
    phase: Phase,
) -> CheckRecord:
    if name == "agent-home-contained":
        contained = _is_relative_to(agent_home, run_dir)
        status: CheckStatus = "pass" if contained else "fail"
        return _record(name, phase, status, f"agent_home={agent_home}")

    if name == "condition-skill-set":
        try:
            expected = list(condition_skills(condition))
        except ValueError:
            actual = _skill_dirs(agent_home)
            return _record(
                name,
                phase,
                "indeterminate",
                f"unknown condition={condition}; actual={actual}",
            )
        actual = _skill_dirs(agent_home)
        status = "pass" if actual == expected else "fail"
        return _record(name, phase, status, f"expected={expected}; actual={actual}")

    if name == "skill-not-visible":
        needle = args[0] if args else ""
        actual = _skill_dirs(agent_home)
        visible = any(needle in skill_name for skill_name in actual)
        status = "pass" if needle and not visible else "fail"
        return _record(name, phase, status, f"needle={needle}; actual={actual}")

    if name == "git-branch":
        expected = args[0] if args else ""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workdir,
            text=True,
            capture_output=True,
        )
        actual = result.stdout.strip()
        status = "pass" if expected and result.returncode == 0 and actual == expected else "fail"
        detail = f"expected={expected}; actual={actual}; exit={result.returncode}"
        if result.stderr.strip():
            detail += f"; stderr={result.stderr.strip()}"
        return _record(name, phase, status, detail)

    if name in ("skill-called", "tool-called"):
        expected = args[0] if args else ""
        names = _tool_names(run_dir)
        called = any(_tool_name_matches(tool_name, expected) for tool_name in names)
        status = "pass" if expected and called else "fail"
        return _record(name, phase, status, f"expected={expected}; names={names}")

    if name == "skill-not-called":
        prefix = args[0] if args else ""
        names = _tool_names(run_dir)
        called = any(tool_name.startswith(prefix) for tool_name in names)
        status = "pass" if prefix and not called else "fail"
        return _record(name, phase, status, f"prefix={prefix}; names={names}")

    if name == "not-tool-called":
        expected = args[0] if args else ""
        names = _tool_names(run_dir)
        called = any(_tool_name_matches(tool_name, expected) for tool_name in names)
        status = "pass" if expected and not called else "fail"
        return _record(name, phase, status, f"expected={expected}; names={names}")

    if name == "transcript-contains":
        needle = args[0] if args else ""
        text = _transcript_text(run_dir)
        status = "pass" if needle and needle.lower() in text.lower() else "fail"
        return _record(name, phase, status, f"needle={needle}")

    if name == "transcript-contains-all":
        text = _transcript_text(run_dir)
        status = "pass" if _contains_all(text, args) else "fail"
        return _record(name, phase, status, f"needles={args}")

    if name == "transcript-contains-any":
        text = _transcript_text(run_dir)
        status = "pass" if _contains_any_arg(text, args) else "fail"
        return _record(name, phase, status, f"needles={args}")

    if name == "transcript-not-contains-any":
        text = _transcript_text(run_dir)
        status = "pass" if args and not _contains_any_arg(text, args) else "fail"
        return _record(name, phase, status, f"needles={args}")

    if name == "requests-runtime-evidence":
        text = _transcript_text(run_dir)
        status = "pass" if _requests_runtime_evidence(text) else "fail"
        return _record(name, phase, status, "runtime evidence request present")

    if name == "no-unverified-fix-claim":
        text = _transcript_text(run_dir)
        has_claim = _has_unverified_fix_claim(text)
        status = "fail" if has_claim else "pass"
        return _record(name, phase, status, "unverified fix claim guard")

    if name == "handoff-present":
        text = _transcript_text(run_dir)
        has_handoff = _has_any(text, HANDOFF_TERMS)
        has_evidence_request = _has_any(text, RUNTIME_EVIDENCE_TERMS)
        status = "pass" if has_handoff and has_evidence_request else "fail"
        return _record(name, phase, status, "runtime evidence handoff present")

    if name == "no-edit-before-runtime-evidence":
        saw_evidence_request = False
        for event in _raw_events(run_dir):
            if _requests_runtime_evidence(_assistant_event_text(event)):
                saw_evidence_request = True
            if _is_edit_tool_call(event) and not saw_evidence_request:
                return _record(name, phase, "fail", "edit tool preceded runtime evidence request")
        return _record(name, phase, "pass", "no edit before runtime evidence request")

    return _record(name, phase, "indeterminate", f"unknown check: {name}")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("missing check name", file=sys.stderr)
        return 2

    phase = os.environ.get("EVAL_CHECK_PHASE", "post")
    if phase not in ("pre", "post"):
        print(f"invalid EVAL_CHECK_PHASE: {phase}", file=sys.stderr)
        return 2

    record = run_check(
        argv[0],
        argv[1:],
        run_dir=Path(os.environ["EVAL_RUN_DIR"]),
        workdir=Path(os.environ["EVAL_WORKDIR"]),
        agent_home=Path(os.environ["EVAL_AGENT_HOME"]),
        condition=os.environ.get("EVAL_CONDITION", ""),
        phase=phase,
    )

    line = json.dumps(record.to_dict(), sort_keys=True)
    sink = os.environ.get("EVAL_RECORD_SINK")
    if sink:
        with Path(sink).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    print(line)
    return 0 if record.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
