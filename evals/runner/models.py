from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    path: Path
    story: Path
    setup: Path
    checks: Path
