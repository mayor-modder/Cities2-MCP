from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


REQUIRED_FIELDS = (
    "schema_version",
    "title",
    "slug",
    "source_type",
    "source_url",
    "published_at",
    "publication_date_basis",
    "creators",
    "organizations",
    "report_created_at",
    "report_updated_at",
)
OPTIONAL_FIELDS = ("event", "game_version", "unity_version", "entities_version")
ALLOWED_FIELDS = frozenset((*REQUIRED_FIELDS, *OPTIONAL_FIELDS))
REQUIRED_SECTIONS = (
    "Executive summary",
    "Source context and temporal scope",
    "Findings",
    "Existing corpus overlap",
    "Implications for Cities2 modding",
    "Implications for Cities2-MCP",
    "Uncertainties and transcript corrections",
    "Sources",
)
DATE_BASES = frozenset(("source_metadata", "user_confirmed"))
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECTION_RE = re.compile(r"^## ([^\n]+)\n", re.MULTILINE)


class ResearchValidationError(ValueError):
    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


@dataclass(frozen=True)
class ResearchReport:
    path: Path
    metadata: dict[str, str]
    body: str
    sections: tuple[tuple[str, str], ...]


def _parse_front_matter(path: Path, text: str) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, text, [f"{path}: report must start with --- front matter"]
    try:
        closing = lines.index("---", 1)
    except ValueError:
        return {}, text, [f"{path}: front matter is missing its closing ---"]

    metadata: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing], start=2):
        if ":" not in line:
            errors.append(f"{path}:{line_number}: metadata must use key: value")
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key in metadata:
            errors.append(f"{path}:{line_number}: duplicate metadata field: {key}")
        elif key not in ALLOWED_FIELDS:
            errors.append(f"{path}:{line_number}: unknown metadata field: {key}")
        else:
            metadata[key] = value
    body = "\n".join(lines[closing + 1 :]).strip() + "\n"
    return metadata, body, errors


def _parse_sections(path: Path, body: str) -> tuple[tuple[tuple[str, str], ...], list[str]]:
    matches = list(SECTION_RE.finditer(body))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append((match.group(1).strip(), body[start:end].strip()))
    names = tuple(name for name, _text in sections)
    errors = [f"{path}: missing required section: {name}" for name in REQUIRED_SECTIONS if name not in names]
    if not errors and names != REQUIRED_SECTIONS:
        errors.append(f"{path}: required sections must appear in the documented order")
    return tuple(sections), errors


def _validate_metadata(path: Path, metadata: dict[str, str]) -> list[str]:
    errors = [f"{path}: missing required metadata field: {field}" for field in REQUIRED_FIELDS if not metadata.get(field)]
    if "published_at" not in metadata:
        errors.append(f"{path}: confirm the publication date with the maintainer before syncing research")
    for field in ("published_at", "report_created_at", "report_updated_at"):
        value = metadata.get(field)
        if value:
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append(f"{path}: {field} must be a real YYYY-MM-DD date")
    if metadata.get("schema_version") not in (None, "1"):
        errors.append(f"{path}: unsupported schema_version: {metadata['schema_version']}")
    if metadata.get("publication_date_basis") not in (None, *DATE_BASES):
        errors.append(f"{path}: publication_date_basis must be source_metadata or user_confirmed")
    source_url = metadata.get("source_url", "")
    if source_url and urlparse(source_url).scheme not in {"http", "https"}:
        errors.append(f"{path}: source_url must use http:// or https://")
    slug = metadata.get("slug", "")
    if slug and not SLUG_RE.fullmatch(slug):
        errors.append(f"{path}: slug must use lowercase letters, numbers, and hyphens")
    if metadata.get("published_at") and slug:
        expected = f"{metadata['published_at']}-{slug}.md"
        if path.name != expected:
            errors.append(f"{path}: filename must be {expected}")
    return errors


def parse_report(path: Path) -> ResearchReport:
    text = path.read_text(encoding="utf-8")
    metadata, body, errors = _parse_front_matter(path, text)
    errors.extend(_validate_metadata(path, metadata))
    sections, section_errors = _parse_sections(path, body)
    errors.extend(section_errors)
    if errors:
        raise ResearchValidationError(errors)
    return ResearchReport(path=path, metadata=metadata, body=body, sections=sections)


def load_reports(reports_dir: Path) -> list[ResearchReport]:
    reports: list[ResearchReport] = []
    errors: list[str] = []
    seen_slugs: set[str] = set()
    for path in sorted(reports_dir.glob("*.md"), key=lambda item: item.name):
        try:
            report = parse_report(path)
        except ResearchValidationError as exc:
            errors.extend(exc.errors)
            continue
        slug = report.metadata["slug"]
        if slug in seen_slugs:
            errors.append(f"{path}: duplicate slug: {slug}")
        else:
            seen_slugs.add(slug)
            reports.append(report)
    if errors:
        raise ResearchValidationError(errors)
    return reports
