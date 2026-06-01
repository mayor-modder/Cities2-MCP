from __future__ import annotations

import re
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


def _defines_shell_function(text: str, name: str) -> bool:
    function_name = re.escape(name)
    pattern = (
        rf"(?m)^[ \t]*(?:{function_name}[ \t]*\(\)[ \t]*\{{"
        rf"|function[ \t]+{function_name}(?:[ \t]*\(\))?[ \t]*\{{)"
    )
    return re.search(pattern, text) is not None


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
    title = frontmatter.get("title")
    if not title:
        raise ScenarioError("story.md frontmatter missing title")
    if "## Acceptance Criteria" not in story_text:
        raise ScenarioError("story.md missing Acceptance Criteria section")

    checks_text = checks.read_text(encoding="utf-8")
    if not _defines_shell_function(checks_text, "pre") or not _defines_shell_function(
        checks_text, "post"
    ):
        raise ScenarioError("checks.sh must define pre() and post()")

    return Scenario(
        id=scenario_id,
        title=title,
        path=scenario_dir,
        story=story,
        setup=setup,
        checks=checks,
    )
