from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .behavior import (
    knowledge_office_demand_grounded,
    local_playtest_handoff_present,
    no_unverified_build_claim,
    public_readiness_guarded,
    release_gate_held,
    review_actionable_findings_present,
    review_release_readiness_audit_present,
    review_unsupported_claims_absent,
    routes_debug_release_followups,
)
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


def _tool_exposure_unavailable(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    unavailable_patterns = (
        r"\btools?\b.{0,80}\b(not exposed|unavailable|not available|missing)\b",
        r"\b(not exposed|unavailable|not available|missing)\b.{0,80}\btools?\b",
        r"\bmcp\b.{0,80}\b(not exposed|unavailable|not available|missing)\b",
        r"\b(no|without)\b.{0,40}\b(mcp|retrieval)\b.{0,40}\btools?\b",
        r"\bdon't have access\b.{0,80}\b(source_status|search|retrieval|mcp)\b",
        r"\bdo not have access\b.{0,80}\b(source_status|search|retrieval|mcp)\b",
    )
    return any(re.search(pattern, normalized) for pattern in unavailable_patterns)


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
    if event_type == "command_execution":
        return "shell_command"
    if event_type not in ("tool_call", "function_call", "mcp_tool_call"):
        return ""
    for key in ("name", "tool", "tool_name"):
        value = nested.get(key)
        if isinstance(value, str):
            return value
    return ""


def _event_arguments_text(event: dict[str, object]) -> str:
    nested = _nested_event(event)
    command = nested.get("command")
    if isinstance(command, str):
        return command
    value = nested.get("arguments")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values())
    return ""


def _tool_argument_events(run_dir: Path) -> list[tuple[str, str]]:
    return [
        (_event_tool_name(event).lower(), _event_arguments_text(event).lower())
        for event in _raw_events(run_dir)
        if _event_tool_name(event)
    ]


def _tool_call_argument_events(run_dir: Path) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    for record in _tool_call_records(run_dir):
        name = record.get("name")
        if not isinstance(name, str):
            continue
        arguments = record.get("arguments")
        if isinstance(arguments, dict):
            text = " ".join(str(value) for value in arguments.values())
        elif isinstance(arguments, str):
            text = arguments
        else:
            text = ""
        events.append((name.lower(), text.lower()))
    return events


def _tool_call_records(run_dir: Path) -> list[dict[str, object]]:
    path = run_dir / "coding-agent-tool-calls.jsonl"
    if not path.is_file():
        return []

    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _tool_argument_texts(run_dir: Path, expected_tool: str) -> list[str]:
    expected = expected_tool.lower()
    texts = [
        text
        for tool_name, text in _tool_argument_events(run_dir)
        if _tool_name_matches(tool_name, expected)
    ]
    for record in _tool_call_records(run_dir):
        name = record.get("name")
        if not isinstance(name, str) or not _tool_name_matches(name.lower(), expected):
            continue
        arguments = record.get("arguments")
        if isinstance(arguments, dict):
            texts.append(" ".join(str(value).lower() for value in arguments.values()))
        elif isinstance(arguments, str):
            texts.append(arguments.lower())
    return texts


def _shell_command_segments(arguments: str) -> list[str]:
    normalized = re.sub(r"/+", "/", arguments.replace("\\", "/")).lower()
    return [
        segment.strip()
        for segment in re.split(r"\s*(?:;|&&|\|\||\||\r?\n)\s*", normalized)
        if segment.strip()
    ]


def _shell_tokens(segment: str) -> list[str]:
    return [
        token.strip("\"'")
        for token in re.findall(r'"[^"]*"|\'[^\']*\'|\S+', segment)
        if token.strip("\"'")
    ]


def _path_candidate_matches(text: str, candidate: str, *, allow_embedded: bool) -> bool:
    if allow_embedded:
        return bool(
            re.search(
                rf"(?<![a-z0-9_-]){re.escape(candidate)}(?![a-z0-9_./-])",
                text,
            )
        )
    return bool(
        re.search(
            rf"(?<![a-z0-9_./-]){re.escape(candidate)}(?![a-z0-9_./-])",
            text,
        )
    )


def _search_segment_reads_path(
    segment: str, expected: str, *, allow_embedded: bool
) -> bool:
    tokens = _shell_tokens(segment)
    if not tokens:
        return False

    command = Path(tokens[0]).name
    if command in ("select-string",):
        path_arguments: list[str] = []
        for index, token in enumerate(tokens[:-1]):
            if token in ("-path", "-literalpath"):
                path_arguments.append(tokens[index + 1])
        if path_arguments:
            return any(
                _path_candidate_matches(path_arg, expected, allow_embedded=allow_embedded)
                for path_arg in path_arguments
            )
        positional = [token for token in tokens[1:] if not token.startswith("-")]
        return any(
            _path_candidate_matches(token, expected, allow_embedded=allow_embedded)
            for token in positional[1:]
        )

    if command not in ("rg", "grep"):
        return False
    positional = [token for token in tokens[1:] if not token.startswith("-")]
    return any(
        _path_candidate_matches(token, expected, allow_embedded=allow_embedded)
        for token in positional[1:]
    )


def _shell_segment_reads_path(
    segment: str, expected: str, *, allow_embedded: bool
) -> bool:
    if not _path_candidate_matches(segment, expected, allow_embedded=allow_embedded):
        return False
    direct_read_patterns = (
        r"(^|[\s\"'])get-content(\s|$)",
        r"(^|[\s\"'])gc(\s|$)",
        r"(^|[\s\"'])cat(\s|$)",
        r"(^|[\s\"'])type(\s|$)",
    )
    search_patterns = (
        r"(^|[\s\"'])rg\s+(-n|--line-number|--files-with-matches)\b",
        r"(^|[\s\"'])select-string\b",
        r"(^|[\s\"'])grep(\s|$)",
    )
    if any(re.search(pattern, segment) for pattern in direct_read_patterns):
        return True
    if any(re.search(pattern, segment) for pattern in search_patterns):
        return _search_segment_reads_path(
            segment, expected, allow_embedded=allow_embedded
        )
    return False


def _expected_path_candidates(expected: str) -> list[str]:
    normalized = re.sub(r"/+", "/", expected.replace("\\", "/")).lower()
    candidates = [normalized]
    if "/" in normalized:
        candidates.append(normalized.split("/", 1)[1])
    return candidates


def _expected_path_candidate_rules(expected: str) -> list[tuple[str, bool]]:
    normalized = re.sub(r"/+", "/", expected.replace("\\", "/")).lower()
    if "/" not in normalized:
        return [(normalized, True)]
    rules = [(normalized, True)]
    rules.append((normalized.split("/", 1)[1], False))
    return rules


def _looks_like_file_inspection(tool_name: str, arguments: str, expected: str) -> bool:
    normalized_expected = re.sub(r"/+", "/", expected.replace("\\", "/")).lower()
    expected_paths = _expected_path_candidate_rules(expected)
    normalized_arguments = re.sub(r"/+", "/", arguments.replace("\\", "/")).lower()
    allow_embedded_path = "/" not in normalized_expected
    if not any(
        _path_candidate_matches(
            normalized_arguments,
            expected_path,
            allow_embedded=allow_embedded_path or candidate_allows_embedded,
        )
        for expected_path, candidate_allows_embedded in expected_paths
    ):
        return False
    if any(term in tool_name for term in ("read", "open", "view")):
        return True
    if "shell_command" not in tool_name:
        return False
    return any(
        _shell_segment_reads_path(segment, expected_path, allow_embedded=allow_embedded)
        for segment in _shell_command_segments(arguments)
        for expected_path, candidate_allows_embedded in expected_paths
        for allow_embedded in (allow_embedded_path or candidate_allows_embedded,)
    )


def _compact_search_query(text: str, required_terms: list[str]) -> tuple[bool, str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    full_user_question = (
        len(normalized) > 80
        or "why is my city" in normalized
        or "can i ignore" in normalized
    )
    has_required_terms = all(term.lower() in normalized for term in required_terms)
    passed = bool(normalized) and has_required_terms and not full_user_question
    detail = (
        f"query={normalized!r}; required_terms={required_terms}; "
        f"full_user_question={full_user_question}"
    )
    return passed, detail


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower_text = text.lower()
    return any(needle.lower() in lower_text for needle in needles)


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

    if name == "required-tool-called":
        expected = args[0] if args else ""
        names = _tool_names(run_dir)
        called = any(_tool_name_matches(tool_name, expected) for tool_name in names)
        if expected and called:
            return _record(name, phase, "pass", f"expected={expected}; names={names}")
        if _tool_exposure_unavailable(_transcript_text(run_dir)):
            return _record(
                name,
                phase,
                "indeterminate",
                f"tool exposure unavailable; expected={expected}; names={names}",
            )
        return _record(name, phase, "fail", f"expected={expected}; names={names}")

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

    if name == "release-gate-held":
        verdict = release_gate_held(_transcript_text(run_dir))
        status: CheckStatus = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "review-unsupported-claims-absent":
        verdict = review_unsupported_claims_absent(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "review-actionable-findings-present":
        verdict = review_actionable_findings_present(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "review-release-readiness-audit-present":
        verdict = review_release_readiness_audit_present(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "project-files-inspected":
        tool_events = _tool_argument_events(run_dir) + _tool_call_argument_events(run_dir)
        missing = [
            arg
            for arg in args
            if not any(
                _looks_like_file_inspection(tool_name, text, arg)
                for tool_name, text in tool_events
            )
        ]
        status = "fail" if missing else "pass"
        return _record(name, phase, status, f"missing={missing}; expected={args}")

    if name == "no-unverified-build-claim":
        verdict = no_unverified_build_claim(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "local-playtest-handoff-present":
        verdict = local_playtest_handoff_present(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "knowledge-office-demand-grounded":
        verdict = knowledge_office_demand_grounded(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "compact-search-query":
        required_terms = args
        candidates = _tool_argument_texts(run_dir, "search")
        matches = [_compact_search_query(candidate, required_terms) for candidate in candidates]
        passed = any(match_passed for match_passed, _detail in matches)
        detail = "candidates=[]" if not matches else " | ".join(
            match_detail for _match_passed, match_detail in matches
        )
        return _record(name, phase, "pass" if passed else "fail", detail)

    if name == "public-readiness-guarded":
        verdict = public_readiness_guarded(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

    if name == "routes-debug-release-followups":
        verdict = routes_debug_release_followups(_transcript_text(run_dir))
        status = "pass" if verdict.passed else "fail"
        return _record(name, phase, status, verdict.detail)

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
