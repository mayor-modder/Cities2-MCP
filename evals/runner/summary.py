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


def summarize_verdicts(paths: Iterable[Path]) -> str:
    verdicts = [_load(path) for path in paths]
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    checks: dict[str, Counter[str]] = defaultdict(Counter)
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
