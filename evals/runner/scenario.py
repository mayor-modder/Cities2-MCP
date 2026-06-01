from __future__ import annotations

from pathlib import Path

from evals.runner.models import Scenario


class ScenarioError(RuntimeError):
    """Raised when a scenario directory is not runnable."""


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def load_scenario(path: Path) -> Scenario:
    scenario_dir = path.resolve()
    story = scenario_dir / "story.md"
    setup = scenario_dir / "setup.sh"
    checks = scenario_dir / "checks.sh"
    for required in (story, setup, checks):
        if not required.is_file():
            raise ScenarioError(f"missing required scenario file: {required.name}")

    story_text = story.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(story_text)
    scenario_id = frontmatter.get("id")
    if not scenario_id:
        raise ScenarioError("story.md frontmatter missing id")
    if "## Acceptance Criteria" not in story_text:
        raise ScenarioError("story.md missing Acceptance Criteria section")

    checks_text = checks.read_text(encoding="utf-8")
    if "pre()" not in checks_text or "post()" not in checks_text:
        raise ScenarioError("checks.sh must define pre() and post()")

    return Scenario(
        id=scenario_id,
        title=frontmatter.get("title", scenario_id),
        path=scenario_dir,
        story=story,
        setup=setup,
        checks=checks,
    )
