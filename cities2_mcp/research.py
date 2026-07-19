from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
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
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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
            if not DATE_RE.fullmatch(value):
                errors.append(f"{path}: {field} must be a real YYYY-MM-DD date")
                continue
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


MAX_CHUNK_CHARS = 4000
CHUNK_OVERLAP_CHARS = 400
PROVENANCE_FIELDS = (
    "published_at",
    "publication_date_basis",
    "source_type",
    "creators",
    "organizations",
    "report_created_at",
    "report_updated_at",
)


def _json_line(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _split_section(text: str, limit: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            tail = current[-overlap:].split("\n\n", 1)[-1] if overlap else ""
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _provenance(metadata: dict[str, str]) -> dict[str, str]:
    return {field: metadata[field] for field in PROVENANCE_FIELDS}


def _report_digest(reports: list[ResearchReport]) -> str:
    digest = hashlib.sha256()
    for report in reports:
        digest.update(report.path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(report.path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_dataset(reports_dir: Path) -> dict[Path, bytes]:
    reports = load_reports(reports_dir)
    pages: list[dict[str, object]] = []
    chunks: list[dict[str, object]] = []
    for report in reports:
        metadata = report.metadata
        slug = metadata["slug"]
        page = {
            "page_id": slug,
            "dataset": "cities2-research",
            "title": metadata["title"],
            "url": metadata["source_url"],
            "sections": [name for name, _text in report.sections],
            "links": [metadata["source_url"]],
            "char_count": len(report.body),
            "word_count": len(report.body.split()),
            **_provenance(metadata),
        }
        pages.append(page)
        chunk_number = 0
        for section_name, section_text in report.sections:
            for part in _split_section(section_text):
                chunk_number += 1
                preamble = (
                    f"# {metadata['title']}\n\n"
                    f"Source: {metadata['source_url']}\n\n"
                    f"Published: {metadata['published_at']}\n\n"
                    f"Temporal context: Research summary of a source published on {metadata['published_at']}; "
                    "verify current API and patch details separately.\n\n"
                    f"## {section_name}\n\n"
                )
                chunks.append(
                    {
                        "chunk_id": f"{slug}#{chunk_number}",
                        "page_id": slug,
                        "dataset": "cities2-research",
                        "title": metadata["title"],
                        "url": metadata["source_url"],
                        "section": section_name,
                        "text": preamble + part,
                        **_provenance(metadata),
                    }
                )

    attribution_lines = [
        "# Cities2 research corpus attribution",
        "",
        "This dataset contains original research summaries and analysis. Complete source media and transcripts are not redistributed.",
        "",
        "## Sources",
        "",
    ]
    attribution_lines.extend(
        f"- {report.metadata['title']} ({report.metadata['published_at']}): {report.metadata['source_url']}"
        for report in reports
    )
    attribution_lines.extend(
        [
            "",
            "Original report prose follows the repository license. Linked source material remains subject to its original source terms.",
            "",
        ]
    )
    manifest = {
        "name": "cities2-research",
        "dataset": "cities2-research",
        "source": "Curated Cities: Skylines II research reports",
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "report_count": len(reports),
        "content_sha256": _report_digest(reports),
        "license": "MIT",
        "paths": {"pages_jsonl": "index/pages.jsonl", "chunks_jsonl": "index/chunks.jsonl"},
        "attribution": "ATTRIBUTION.md",
    }
    return {
        Path("manifest.json"): json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        Path("ATTRIBUTION.md"): "\n".join(attribution_lines).encode("utf-8"),
        Path("index/pages.jsonl"): b"".join(_json_line(page) for page in pages),
        Path("index/chunks.jsonl"): b"".join(_json_line(chunk) for chunk in chunks),
    }


def sync_dataset(reports_dir: Path, output_dir: Path) -> tuple[Path, ...]:
    expected = build_dataset(reports_dir)
    changed: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for relative, content in expected.items():
        target = output_dir / relative
        current = target.read_bytes() if target.is_file() else None
        if current == content:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, target)
        changed.append(target)
    expected_paths = {output_dir / relative for relative in expected}
    for existing in sorted(path for path in output_dir.rglob("*") if path.is_file()):
        if existing not in expected_paths:
            existing.unlink()
            changed.append(existing)
    return tuple(changed)


def check_dataset(reports_dir: Path, output_dir: Path) -> tuple[Path, ...]:
    expected = build_dataset(reports_dir)
    stale: list[Path] = []
    for relative, content in expected.items():
        target = output_dir / relative
        if not target.is_file() or target.read_bytes() != content:
            stale.append(target)
    expected_paths = {output_dir / relative for relative in expected}
    stale.extend(
        path for path in sorted(output_dir.rglob("*")) if path.is_file() and path not in expected_paths
    )
    return tuple(stale)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Cities2 research corpus")
    parser.add_argument("command", choices=("sync", "check"))
    parser.add_argument("--reports-dir", type=Path, default=_repo_root() / "cities2-research" / "reports")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "research_data")
    args = parser.parse_args(argv)
    try:
        if args.command == "sync":
            changed = sync_dataset(args.reports_dir, args.output_dir)
            for path in changed:
                print(path)
            return 0
        stale = check_dataset(args.reports_dir, args.output_dir)
    except ResearchValidationError as exc:
        print(str(exc))
        return 1
    if stale:
        print("Stale Cities2 research dataset:")
        for path in stale:
            print(path)
        print("Run: python -m cities2_mcp.research sync")
        return 1
    print("Cities2 research dataset is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
