from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


CheckStatus = Literal["pass", "fail", "indeterminate"]
FinalStatus = Literal["pass", "fail", "indeterminate"]
Phase = Literal["pre", "post"]


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    path: Path
    story: Path
    setup: Path
    checks: Path


@dataclass(frozen=True)
class CheckRecord:
    name: str
    phase: Phase
    status: CheckStatus
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phase": self.phase,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RunMetadata:
    scenario_id: str
    scenario_version: str
    condition_id: str
    trial: int
    backend_name: str
    backend_executable: str
    repo_commit: str
    runner_version: str
    run_started_at: str
    skill_checksums: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "condition_id": self.condition_id,
            "trial": self.trial,
            "backend_name": self.backend_name,
            "backend_executable": self.backend_executable,
            "repo_commit": self.repo_commit,
            "runner_version": self.runner_version,
            "run_started_at": self.run_started_at,
            "skill_checksums": dict(sorted(self.skill_checksums.items())),
        }


@dataclass(frozen=True)
class Verdict:
    metadata: RunMetadata
    final: FinalStatus
    final_reason: str
    checks: list[CheckRecord] = field(default_factory=list)
    trace_path: str | None = None
    transcript_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "metadata": self.metadata.to_dict(),
            "final": self.final,
            "final_reason": self.final_reason,
            "checks": [record.to_dict() for record in self.checks],
            "trace_path": self.trace_path,
            "transcript_path": self.transcript_path,
        }


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    workdir: Path
    agent_home: Path
    raw_events: Path
    tool_calls: Path
    transcript: Path
    verdict: Path

    @classmethod
    def from_run_dir(cls, run_dir: Path) -> RunPaths:
        return cls(
            run_dir=run_dir,
            workdir=run_dir / "coding-agent-workdir",
            agent_home=run_dir / "coding-agent-config",
            raw_events=run_dir / "codex-events.jsonl",
            tool_calls=run_dir / "coding-agent-tool-calls.jsonl",
            transcript=run_dir / "transcript.txt",
            verdict=run_dir / "verdict.json",
        )
