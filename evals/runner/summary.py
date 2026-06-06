from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def _load(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"verdict must be an object: {path}")
    return data


def _metadata(verdict: dict[str, object]) -> dict[object, object]:
    metadata = verdict.get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError("verdict metadata must be an object")
    return metadata


def _metadata_value(verdict: dict[str, object], name: str, default: str = "unknown") -> str:
    value = _metadata(verdict).get(name)
    return str(value) if value not in (None, "") else default


def _trial(verdict: dict[str, object]) -> int:
    value = _metadata(verdict).get("trial", 0)
    if isinstance(value, int):
        return value
    return int(str(value))


def _failed_checks(verdict: dict[str, object]) -> list[str]:
    failed: list[str] = []
    for check in verdict.get("checks", []):
        if isinstance(check, dict) and check.get("status") == "fail":
            failed.append(str(check.get("name", "unknown-check")))
    return sorted(set(failed))


def generate_digest(paths: Iterable[Path]) -> str:
    verdicts = [_load(path) for path in paths]
    rows = sorted(
        verdicts,
        key=lambda verdict: (
            _metadata_value(verdict, "backend_name"),
            _metadata_value(verdict, "scenario_id"),
            _metadata_value(verdict, "condition_id"),
            _trial(verdict),
        ),
    )
    check_counts: dict[str, Counter[str]] = defaultdict(Counter)
    backends: set[str] = set()
    commits: set[str] = set()
    checksums: set[str] = set()
    run_dates: set[str] = set()

    for verdict in rows:
        metadata = _metadata(verdict)
        backend = metadata.get("backend_name")
        if isinstance(backend, str) and backend:
            backends.add(backend)
        repo_commit = metadata.get("repo_commit")
        if isinstance(repo_commit, str) and repo_commit:
            commits.add(repo_commit)
        run_started_at = metadata.get("run_started_at")
        if isinstance(run_started_at, str) and len(run_started_at) >= 10:
            run_dates.add(run_started_at[:10])
        skill_checksums = metadata.get("skill_checksums")
        if isinstance(skill_checksums, dict):
            for value in skill_checksums.values():
                if isinstance(value, str):
                    checksums.add(value)
        for check in verdict.get("checks", []):
            if isinstance(check, dict):
                check_name = str(check.get("name", "unknown-check"))
                check_status = str(check.get("status", "unknown"))
                check_counts[check_name][check_status] += 1

    lines = [
        "# Eval results digest",
        "",
        "## Short version",
        "",
        f"Verdicts summarized: {len(rows)}",
        f"Backends: {', '.join(sorted(backends)) if backends else 'unknown'}",
        f"Run dates: {', '.join(sorted(run_dates)) if run_dates else 'unknown'}",
        "",
        "These results cover only the listed backend runs.",
        "",
        "## Run matrix",
        "",
        f"Repository commits: {', '.join(sorted(commits)) if commits else 'unknown'}",
        f"Skill checksums: {', '.join(sorted(checksums)) if checksums else 'none'}",
        "",
        "## Verdict table",
        "",
        "| Backend | Scenario | Condition | Trial | Final | Failed checks |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for verdict in rows:
        failed = ", ".join(_failed_checks(verdict)) or "none"
        lines.append(
            "| "
            f"{_metadata_value(verdict, 'backend_name')} | "
            f"{_metadata_value(verdict, 'scenario_id')} | "
            f"{_metadata_value(verdict, 'condition_id')} | "
            f"{_trial(verdict)} | "
            f"{str(verdict.get('final', 'unknown'))} | "
            f"{failed} |"
        )
    lines.extend(["", "## Failure patterns", ""])
    if check_counts:
        for check_name, counter in sorted(check_counts.items()):
            parts = [
                f"{status}={counter[status]}"
                for status in ("pass", "fail", "indeterminate")
                if counter[status]
            ]
            lines.append(f"- `{check_name}`: {'; '.join(parts)}")
    else:
        lines.append("- No check records were present.")
    lines.extend(
        [
            "",
            "## Representative behavior",
            "",
            "No raw transcripts are included in this digest.",
            "",
            "## Interpretation",
            "",
            "This digest reports deterministic verdict data and grouped check outcomes. Human interpretation should remain tied to the listed runs and should not generalize to untested clients.",
            "",
            "## Follow-up status",
            "",
            "No follow-up status was provided by the digest generator.",
            "",
            "## Privacy note",
            "",
            "Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_verdicts(paths: Iterable[Path]) -> str:
    verdicts = [_load(path) for path in paths]
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    checks: dict[str, Counter[str]] = defaultdict(Counter)
    backends: set[str] = set()
    commits: set[str] = set()
    checksums: set[str] = set()

    for verdict in verdicts:
        metadata = verdict.get("metadata")
        if not isinstance(metadata, dict):
            raise TypeError("verdict metadata must be an object")
        scenario = str(metadata.get("scenario_id", "unknown-scenario"))
        condition = str(metadata.get("condition_id", "unknown-condition"))
        final = str(verdict.get("final", "unknown"))
        counts[(scenario, condition)][final] += 1
        backend = metadata.get("backend_name")
        if isinstance(backend, str) and backend:
            backends.add(backend)
        repo_commit = metadata.get("repo_commit")
        if isinstance(repo_commit, str) and repo_commit:
            commits.add(repo_commit)
        skill_checksums = metadata.get("skill_checksums")
        if isinstance(skill_checksums, dict):
            for value in skill_checksums.values():
                if isinstance(value, str):
                    checksums.add(value)
        for check in verdict.get("checks", []):
            if isinstance(check, dict):
                check_name = str(check.get("name", "unknown-check"))
                check_status = str(check.get("status", "unknown"))
                checks[check_name][check_status] += 1

    lines = ["# Cities2 debugging runtime-no-logs baseline summary", ""]
    lines.append(f"Verdicts summarized: {len(verdicts)}")
    lines.append(f"Backends: {', '.join(sorted(backends)) if backends else 'unknown'}")
    lines.append(f"Repository commits: {', '.join(sorted(commits)) if commits else 'unknown'}")
    lines.append(f"Skill checksums: {', '.join(sorted(checksums)) if checksums else 'none'}")
    lines.append("")
    lines.append("## Final counts")
    for (scenario, condition), counter in sorted(counts.items()):
        lines.append(
            f"- {scenario} / {condition}: "
            f"pass={counter['pass']}; fail={counter['fail']}; "
            f"indeterminate={counter['indeterminate']}"
        )
    lines.append("")
    lines.append("## Check counts")
    for check_name, counter in sorted(checks.items()):
        lines.append(
            f"- {check_name}: pass={counter['pass']}; fail={counter['fail']}; "
            f"indeterminate={counter['indeterminate']}"
        )
    lines.append("")
    return "\n".join(lines)
