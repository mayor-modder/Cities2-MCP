# Cities2 Research Corpus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separately attributed, deterministic `cities2-research` corpus generated from canonical Markdown reports while keeping raw source material ignored and preserving existing wiki retrieval behavior.

**Architecture:** Canonical reports live under `cities2-research/reports/`; a standard-library-only compiler validates their metadata and writes `cities2_mcp/research_data/`. The MCP loads the wiki plus valid research datasets, returns provenance with research results, and falls back to the wiki if a research dataset is malformed.

**Tech Stack:** Python 3.10+ standard library, `unittest`, JSONL corpus format, Markdown reports, Hatch packaging, existing Cities2-MCP plugin package sync.

## Global Constraints

- Python support remains `>=3.10`; add no runtime dependency for YAML, Markdown, or date parsing.
- `cities2-research/reports/*.md` is canonical; never hand-edit `cities2_mcp/research_data/`.
- `cities2-research/sources/` and all nested source material remain ignored, uncommitted, and unpackaged.
- Every report requires an exact `YYYY-MM-DD` `published_at` and a `publication_date_basis` of `source_metadata` or `user_confirmed`.
- Never infer publication date from file timestamps, event names, report dates, or repository history; stop for maintainer confirmation when unclear.
- Keep `cities2-docs` and `cities2-research` as separate datasets with separate attribution.
- Preserve bare `get_page("page-id")` compatibility when the page ID is unique across loaded datasets.
- Preserve paragraph-per-line Markdown style in all touched prose.
- Do not bump versions, push, open a pull request, merge, publish, or release without separate explicit authorization.

---

## File structure

- `cities2_mcp/research.py`: canonical report parser, validator, deterministic dataset builder, sync/check CLI.
- `cities2-research/README.md`: contributor workflow and metadata contract.
- `cities2-research/sources/.gitignore`: keeps the private intake directory present while ignoring its contents.
- `cities2-research/reports/2024-10-09-tapping-ecs-cities-skylines-ii.md`: first canonical research report.
- `cities2_mcp/research_data/`: generated manifest, attribution, pages, and chunks bundled with distributions.
- `tests/test_research.py`: report validation, deterministic generation, sync/check, privacy, and first-report tests.
- `tests/test_retrieval_multi_dataset.py`: cross-dataset resolution, search, provenance, and resource tests.
- `cities2_mcp/retrieval/mcp_server.py`: optional provenance propagation and unique bare-ID resolution.
- `cities2_mcp/mcp_server.py`: bundled research path, multi-dataset startup, fallback, and source status.
- `cities2_mcp/__init__.py`: public `bundled_research_data_dir()` helper.
- `tests/test_packaging.py`: default server, vendored payload, and bundled-path coverage.
- `.gitignore`, `pyproject.toml`, `README.md`, `CONTRIBUTING.md`, `cities2_mcp/plugin_metadata.py`, `integrations/openai/README.md`, `integrations/anthropic/README.md`: privacy, packaging, and user-facing documentation.
- `plugins/cities2-mcp/`: generated Antigravity payload refreshed only by `python -m cities2_mcp.plugin_packages sync`.

### Task 1: Parse and validate canonical research reports

**Files:**
- Create: `cities2_mcp/research.py`
- Create: `tests/test_research.py`

**Interfaces:**
- Produces: `ResearchValidationError(ValueError)` with `errors: tuple[str, ...]`.
- Produces: immutable `ResearchReport(path: Path, metadata: dict[str, str], body: str, sections: tuple[tuple[str, str], ...])`.
- Produces: `parse_report(path: Path) -> ResearchReport`.
- Produces: `load_reports(reports_dir: Path) -> list[ResearchReport]`.

- [ ] **Step 1: Write failing parser and validation tests**

Create `tests/test_research.py` with a reusable complete report fixture and focused tests:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cities2_mcp.research import ResearchValidationError, load_reports, parse_report


VALID_BODY = """---
schema_version: 1
title: Test Research Source
slug: test-research-source
source_type: conference_talk
source_url: https://example.com/talk
published_at: 2024-10-09
publication_date_basis: source_metadata
creators: Example Speaker
organizations: Example Studio
report_created_at: 2026-07-18
report_updated_at: 2026-07-18
---

# Test Research Source

## Executive summary

The source explains a system.

## Source context and temporal scope

This is a historical snapshot.

## Findings

The system uses data-oriented processing.

## Existing corpus overlap

The wiki covers the basic terminology.

## Implications for Cities2 modding

Mods should validate current APIs separately.

## Implications for Cities2-MCP

The report adds architectural rationale.

## Uncertainties and transcript corrections

No unresolved transcription issues remain.

## Sources

- https://example.com/talk
"""


class ResearchReportTests(unittest.TestCase):
    def write_report(self, root: Path, text: str = VALID_BODY, name: str = "2024-10-09-test-research-source.md") -> Path:
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_parse_report_returns_metadata_and_ordered_sections(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            report = parse_report(self.write_report(Path(tmp)))

        self.assertEqual(report.metadata["published_at"], "2024-10-09")
        self.assertEqual(report.metadata["publication_date_basis"], "source_metadata")
        self.assertEqual(report.sections[0][0], "Executive summary")
        self.assertEqual(report.sections[-1][0], "Sources")

    def test_parse_report_requires_publication_date_confirmation(self) -> None:
        text = VALID_BODY.replace("published_at: 2024-10-09\n", "")
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            with self.assertRaisesRegex(ResearchValidationError, "confirm the publication date with the maintainer"):
                parse_report(self.write_report(Path(tmp), text))

    def test_parse_report_rejects_invalid_date_basis_and_filename_mismatch(self) -> None:
        text = VALID_BODY.replace("publication_date_basis: source_metadata", "publication_date_basis: guessed")
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            with self.assertRaises(ResearchValidationError) as raised:
                parse_report(self.write_report(Path(tmp), text, "2025-01-01-wrong.md"))

        message = str(raised.exception)
        self.assertIn("publication_date_basis", message)
        self.assertIn("filename must be 2024-10-09-test-research-source.md", message)

    def test_parse_report_rejects_local_source_url_and_missing_section(self) -> None:
        text = VALID_BODY.replace("https://example.com/talk", "C:\\Users\\Example\\talk.txt")
        text = text.replace("## Findings\n\nThe system uses data-oriented processing.\n\n", "")
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            with self.assertRaises(ResearchValidationError) as raised:
                parse_report(self.write_report(Path(tmp), text))

        message = str(raised.exception)
        self.assertIn("source_url must use http:// or https://", message)
        self.assertIn("missing required section: Findings", message)

    def test_load_reports_sorts_files_and_rejects_duplicate_slugs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            self.write_report(root)
            duplicate = VALID_BODY.replace("published_at: 2024-10-09", "published_at: 2024-10-10")
            self.write_report(root, duplicate, "2024-10-10-test-research-source.md")
            with self.assertRaisesRegex(ResearchValidationError, "duplicate slug: test-research-source"):
                load_reports(root)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the parser tests and verify the expected failure**

Run:

```powershell
python -m unittest tests.test_research -v
```

Expected: import failure because `cities2_mcp.research` does not exist.

- [ ] **Step 3: Implement the flat-front-matter parser and validator**

Create `cities2_mcp/research.py` with these exact constants and public types, then implement the shown validation flow:

```python
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
```

- [ ] **Step 4: Run the parser tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_research -v
```

Expected: all five tests pass.

- [ ] **Step 5: Commit the parser slice**

```powershell
git add cities2_mcp/research.py tests/test_research.py
git commit -m "feat: validate Cities2 research reports"
```

### Task 2: Generate, synchronize, and check the research dataset

**Files:**
- Modify: `cities2_mcp/research.py`
- Modify: `tests/test_research.py`

**Interfaces:**
- Consumes: `ResearchReport`, `load_reports()` from Task 1.
- Produces: `build_dataset(reports_dir: Path) -> dict[Path, bytes]` with relative output paths.
- Produces: `sync_dataset(reports_dir: Path, output_dir: Path) -> tuple[Path, ...]`.
- Produces: `check_dataset(reports_dir: Path, output_dir: Path) -> tuple[Path, ...]`.
- Produces: `main(argv: Optional[list[str]] = None) -> int` supporting `sync` and `check`.

- [ ] **Step 1: Write failing generation, determinism, and stale-check tests**

Add these methods to `ResearchReportTests`:

```python
    def test_build_dataset_is_deterministic_and_preserves_provenance(self) -> None:
        from cities2_mcp.research import build_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            self.write_report(root)
            first = build_dataset(root)
            second = build_dataset(root)

        self.assertEqual(first, second)
        pages = first[Path("index/pages.jsonl")].decode("utf-8")
        chunks = first[Path("index/chunks.jsonl")].decode("utf-8")
        manifest = first[Path("manifest.json")].decode("utf-8")
        self.assertIn('"published_at": "2024-10-09"', pages)
        self.assertIn('"publication_date_basis": "source_metadata"', chunks)
        self.assertIn('"name": "cities2-research"', manifest)

    def test_sync_and_check_detect_stale_generated_output(self) -> None:
        from cities2_mcp.research import check_dataset, sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            output = root / "output"
            reports.mkdir()
            self.write_report(reports)

            changed = sync_dataset(reports, output)
            self.assertIn(output / "manifest.json", changed)
            self.assertEqual(check_dataset(reports, output), ())

            (output / "manifest.json").write_text("{}\n", encoding="utf-8")
            self.assertEqual(check_dataset(reports, output), (output / "manifest.json",))

    def test_validation_failure_does_not_replace_existing_output(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            output = root / "output"
            reports.mkdir()
            output.mkdir()
            sentinel = output / "manifest.json"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            self.write_report(reports, VALID_BODY.replace("published_at: 2024-10-09\n", ""))

            with self.assertRaises(ResearchValidationError):
                sync_dataset(reports, output)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")
```

- [ ] **Step 2: Run the focused tests and verify the expected failures**

Run:

```powershell
python -m unittest tests.test_research -v
```

Expected: the three new tests fail because `build_dataset`, `sync_dataset`, and `check_dataset` do not exist.

- [ ] **Step 3: Implement deterministic page, chunk, manifest, and attribution generation**

Add `argparse`, `hashlib`, `json`, `os`, `tempfile`, and `Optional` to the module imports. Append the following behavior to `cities2_mcp/research.py`; keep JSON serialization at `ensure_ascii=False, sort_keys=True` with one record per line:

```python
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
```

- [ ] **Step 4: Implement atomic-after-validation sync, check, and CLI behavior**

Append these functions and module entry point:

```python
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
```

- [ ] **Step 5: Run the complete research unit tests**

Run:

```powershell
python -m unittest tests.test_research -v
```

Expected: all research tests pass without warnings.

- [ ] **Step 6: Commit the generator slice**

```powershell
git add cities2_mcp/research.py tests/test_research.py
git commit -m "feat: generate Cities2 research dataset"
```

### Task 3: Add the private intake layout and first canonical report

**Files:**
- Modify: `.gitignore`
- Create: `cities2-research/README.md`
- Create: `cities2-research/sources/.gitignore`
- Create: `cities2-research/reports/2024-10-09-tapping-ecs-cities-skylines-ii.md`
- Generate: `cities2_mcp/research_data/ATTRIBUTION.md`
- Generate: `cities2_mcp/research_data/manifest.json`
- Generate: `cities2_mcp/research_data/index/pages.jsonl`
- Generate: `cities2_mcp/research_data/index/chunks.jsonl`
- Modify: `tests/test_research.py`

**Interfaces:**
- Consumes: `python -m cities2_mcp.research sync` from Task 2.
- Produces: the first real `cities2-research` page with publication-date provenance.

- [ ] **Step 1: Write failing repository privacy and first-report tests**

Add module constants and these tests to `tests/test_research.py`:

```python
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "cities2-research" / "reports"
RESEARCH_DATA = ROOT / "cities2_mcp" / "research_data"


class BundledResearchTests(unittest.TestCase):
    def test_private_source_directory_ignores_nested_material(self) -> None:
        result = subprocess.run(
            ["git", "check-ignore", "cities2-research/sources/nested/full-transcript.txt"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((ROOT / "cities2-research" / "sources" / ".gitignore").is_file())

    def test_first_report_has_verified_publication_date(self) -> None:
        from cities2_mcp.research import parse_report

        path = REPORTS / "2024-10-09-tapping-ecs-cities-skylines-ii.md"
        report = parse_report(path)
        self.assertEqual(report.metadata["published_at"], "2024-10-09")
        self.assertEqual(report.metadata["publication_date_basis"], "source_metadata")
        self.assertEqual(report.metadata["creators"], "Damien Morello")

    def test_bundled_research_data_is_current_and_private_path_free(self) -> None:
        from cities2_mcp.research import check_dataset

        self.assertEqual(check_dataset(REPORTS, RESEARCH_DATA), ())
        private_markers = ("C:\\Users\\", "OneDrive\\Documents", "hello and welcome to my talk")
        for path in RESEARCH_DATA.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertFalse(any(marker in text for marker in private_markers), path)

    def test_bundled_research_manifest_identifies_separate_dataset(self) -> None:
        manifest = json.loads((RESEARCH_DATA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "cities2-research")
        self.assertEqual(manifest["report_count"], 1)
        self.assertGreater(manifest["chunk_count"], 1)
```

- [ ] **Step 2: Run the bundled-research tests and verify the expected failures**

Run:

```powershell
python -m unittest tests.test_research.BundledResearchTests -v
```

Expected: failures because the research directories, report, and generated dataset do not exist.

- [ ] **Step 3: Add the ignored source directory and contributor guide**

Append these patterns to the root `.gitignore`:

```gitignore

# Private research source material; only curated reports are committed.
cities2-research/sources/**
!cities2-research/sources/.gitignore
```

Create `cities2-research/sources/.gitignore`:

```gitignore
*
!.gitignore
```

Create `cities2-research/README.md` with these exact sections and rules:

```markdown
# Cities2 research

This directory holds canonical research reports used to generate the separately identified `cities2-research` MCP dataset.

## Private source intake

Put full transcripts, downloaded media, slide decks, and other private working material under `sources/`. Everything below that directory is ignored except its `.gitignore`; never force-add source material.

## Canonical reports

Commit original research summaries under `reports/`. Name each report `<published_at>-<slug>.md` and follow the metadata and section structure demonstrated by the existing reports.

`published_at` must be an exact publication date. Use `publication_date_basis: source_metadata` when supplied material or a public source establishes the date, and `publication_date_basis: user_confirmed` when the maintainer confirms a date that was otherwise unclear. Do not infer the date from local file metadata or an event name.

## Generate and verify

Run `python -m cities2_mcp.research sync` after editing reports. Review the generated `cities2_mcp/research_data/` diff, then run `python -m cities2_mcp.research check`.
```

- [ ] **Step 4: Write the first canonical report**

Create `cities2-research/reports/2024-10-09-tapping-ecs-cities-skylines-ii.md`. Use the approved metadata below and write original prose under every required section; do not copy transcript paragraphs:

```markdown
---
schema_version: 1
title: Tapping the Entity Component System for Cities: Skylines II
slug: tapping-ecs-cities-skylines-ii
source_type: conference_talk
source_url: https://www.youtube.com/watch?v=nEkIyWhvq3o
published_at: 2024-10-09
publication_date_basis: source_metadata
creators: Damien Morello
organizations: Colossal Order; Unity
report_created_at: 2026-07-18
report_updated_at: 2026-07-18
event: Unite 2024
unity_version: 2022.3
---

# Tapping the Entity Component System for Cities: Skylines II

## Executive summary

Damien Morello's Unite 2024 session explains why Cities: Skylines II combines Unity ECS, the Job System, Burst, managed systems, custom prefab authoring, and custom runtime asset infrastructure. Its strongest value for modding is not a list of public APIs but the engineering rationale behind simulation phases, prefab conversion, job dependencies, debugging, and deciding which data should remain outside ECS.

## Source context and temporal scope

The session was published on 2024-10-09 and describes Colossal Order's architecture at that time. It reports Unity 2022.3 and a codebase shaped by adopting Entities while the package was still experimental. Internal systems and package behavior described here must not be assumed to remain current or publicly accessible to mods without newer documentation or installed-assembly evidence.

## Findings

CS2 uses a small managed shell around a manually updated ECS world. Input, simulation, UI transfer, allocator cleanup, main-thread dispatch, and platform callbacks occupy deliberate positions in the frame.

Designer-facing prefabs are ScriptableObject-style objects rather than Unity GameObject prefabs. Registration converts authoring data into a compact ECS representation that may use several components. A prefab accepts one component of each type, and reverse relationships let later content declare itself as a variation or replacement without patching a central list.

The runtime asset database was designed partly to support mods. Assets from the installation, user storage, cloud storage, and subscriptions are indexed by GUID, remain lazy until used, and load minimal metadata before heavier content. Geometry and texture streaming request only required data, with budgets and graceful fallback behavior.

The team kept managed systems but moved heavy work into Burst-compiled jobs, predominantly `IJobChunk`. Explicit update phases act as synchronization points. Entity command buffers are paired with barriers because playback in the wrong phase can appear harmless before causing intermittent invalid state.

The talk cautions that not every large data structure belongs in ECS. Pathfinding and utility-flow work may use persistent native collections outside entity storage while still participating in job dependencies and Burst compilation.

UI-facing systems query and cache simulation data, then send changed values through a binding layer to the JavaScript and React UI. Debug visualization systems follow the same separation: they query data without changing the simulation and are enabled only when needed.

Profiling is presented as dependency analysis as well as timing analysis. Incorrect dependencies can stall the main thread or leave worker threads idle. Long-running pathfinding jobs also led the team to disable main-thread job stealing rather than allow a several-hundred-millisecond job to create visible stutter.

## Existing corpus overlap

The wiki corpus already explains entities, components, archetypes, queries, systems, update phases, Burst-related memory handling, and basic entity-command-buffer use. The talk overlaps those definitions but adds production rationale, scale, failure modes, and architecture boundaries that are not returned clearly by the existing pages.

The wiki's `Developer diaries` page separately indexes developer communications, including the later City Corner series, but it does not contain this conference talk or a comparable architectural synthesis.

## Implications for Cities2 modding

Mods should choose update phases from actual data dependencies instead of treating modification phases as interchangeable. Structural changes should use a barrier appropriate to the chosen phase, and job handles must describe real dependencies without unnecessary serialization.

Performance-sensitive mods should profile scheduling, allocations, and worker utilization. Burst and jobs can help only when the work is large enough to justify scheduling overhead and uses unmanaged data safely.

Mod architecture should not force every custom structure into ECS. Stable graphs, flow networks, or other specialized structures may be better stored in native collections owned by a system, with ECS used at the integration boundary.

Internal CS2 facilities mentioned in the talk are architectural evidence, not automatic API recommendations. Current wiki pages, installed assemblies, logs, and profiler evidence remain necessary for implementation decisions.

## Implications for Cities2-MCP

The toolkit should retrieve this report for questions about ECS architecture, update barriers, job scheduling, prefab conversion, runtime asset loading, UI data separation, and debugging strategy. Results must identify the `cities2-research` dataset and preserve the 2024-10-09 publication date so agents can state that the material is historically situated.

The report should complement the wiki rather than outrank current documentation automatically. When research and current sources differ, agents should identify both sources and validate current APIs independently.

## Uncertainties and transcript corrections

The supplied transcript is auto-generated and repeatedly mistranscribes technical names. Normalized terms include `EntityCommandBuffer`, `IJobChunk`, `AsyncReadManager`, `BatchRendererGroup`, Burst, and pathfinding.

The transcript's exact Entities package version is ambiguous and is therefore omitted from metadata. Screenshot-only debugging examples and the unfinished question period are not recoverable from the text transcript alone.

## Sources

- Unity, Tapping the Entity Component System for Cities: Skylines II, Unite 2024: https://www.youtube.com/watch?v=nEkIyWhvq3o
- Cities: Skylines II Wiki, ECS - Entity Component System: https://cs2.paradoxwikis.com/ECS_-_Entity_Component_System
- Cities: Skylines II Wiki, Systems: https://cs2.paradoxwikis.com/Systems
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
```

- [ ] **Step 5: Generate and inspect the separate dataset**

Run:

```powershell
python -m cities2_mcp.research sync
python -m cities2_mcp.research check
```

Expected: `sync` creates four files below `cities2_mcp/research_data/`; `check` prints `Cities2 research dataset is in sync.` and exits 0. Inspect the manifest, first page row, first chunk row, and attribution file without dumping the entire JSONL.

- [ ] **Step 6: Run privacy and first-report tests**

Run:

```powershell
python -m unittest tests.test_research -v
git status --short --ignored cities2-research
```

Expected: all tests pass; `sources/.gitignore` is visible and a representative source file would be ignored.

- [ ] **Step 7: Commit the canonical report and generated dataset**

```powershell
git add .gitignore cities2-research cities2_mcp/research_data tests/test_research.py
git commit -m "docs: add first Cities2 research report"
```

### Task 4: Preserve provenance and backward compatibility in multi-dataset retrieval

**Files:**
- Create: `tests/test_retrieval_multi_dataset.py`
- Modify: `cities2_mcp/retrieval/mcp_server.py:230-369`
- Modify: `cities2_mcp/retrieval/mcp_server.py:380-468`
- Modify: `cities2_mcp/retrieval/mcp_server.py:599-723`

**Interfaces:**
- Consumes: wiki and research JSONL records through `Corpus(data_dirs)`.
- Produces: `provenance_fields(row: JSON) -> JSON`.
- Changes: `Corpus.resolve_page_id()` accepts an unqualified ID when exactly one loaded dataset owns it.
- Changes: search, reference, page, and page-resource payloads include research provenance only when present.

- [ ] **Step 1: Write failing multi-dataset tests**

Create `tests/test_retrieval_multi_dataset.py` with a helper that writes minimal dataset directories and tests these exact behaviors:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cities2_mcp.retrieval import mcp_server
from cities2_mcp.retrieval.mcp_server import Corpus


def write_dataset(root: Path, name: str, page_id: str, title: str, text: str, **extra: str) -> Path:
    data_dir = root / name
    (data_dir / "index").mkdir(parents=True)
    (data_dir / "manifest.json").write_text(json.dumps({"name": name}), encoding="utf-8")
    page = {"page_id": page_id, "title": title, "url": f"https://example.com/{page_id}", "sections": ["Overview"], **extra}
    chunk = {"chunk_id": f"{page_id}#1", "page_id": page_id, "title": title, "url": page["url"], "section": "Overview", "text": text, **extra}
    (data_dir / "index" / "pages.jsonl").write_text(json.dumps(page) + "\n", encoding="utf-8")
    (data_dir / "index" / "chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
    return data_dir


class MultiDatasetRetrievalTests(unittest.TestCase):
    def test_unique_bare_page_id_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            wiki = write_dataset(root, "cities2-docs", "systems", "Systems", "wiki update phases")
            research = write_dataset(root, "cities2-research", "ecs-talk", "ECS Talk", "research job barriers")
            corpus = Corpus([wiki, research])

        self.assertEqual(corpus.resolve_page_id("systems"), "cities2-docs:systems")
        self.assertEqual(corpus.resolve_page_id("ecs-talk"), "cities2-research:ecs-talk")

    def test_ambiguous_bare_page_id_requires_dataset_prefix(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            wiki = write_dataset(root, "cities2-docs", "shared", "Wiki Shared", "wiki")
            research = write_dataset(root, "cities2-research", "shared", "Research Shared", "research")
            corpus = Corpus([wiki, research])

        self.assertIsNone(corpus.resolve_page_id("shared"))
        self.assertEqual(corpus.resolve_page_id("cities2-research:shared"), "cities2-research:shared")

    def test_research_search_page_reference_and_resource_preserve_provenance(self) -> None:
        provenance = {
            "published_at": "2024-10-09",
            "publication_date_basis": "source_metadata",
            "source_type": "conference_talk",
            "creators": "Damien Morello",
            "organizations": "Colossal Order; Unity",
            "report_created_at": "2026-07-18",
            "report_updated_at": "2026-07-18",
        }
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            wiki = write_dataset(root, "cities2-docs", "systems", "Systems", "wiki update phases")
            research = write_dataset(root, "cities2-research", "ecs-talk", "ECS Talk", "job barriers profiler", **provenance)
            corpus = Corpus([wiki, research])
            search = mcp_server.handle_tools_call(1, {"name": "search", "arguments": {"query": "job barriers"}}, corpus)
            page = mcp_server.handle_tools_call(2, {"name": "get_page", "arguments": {"page_id": "ecs-talk"}}, corpus)
            reference = mcp_server.handle_tools_call(3, {"name": "query_reference", "arguments": {"query": "ECS Talk"}}, corpus)
            resource = mcp_server.handle_resources_read(4, {"uri": mcp_server.page_uri("cities2-research:ecs-talk")}, corpus)

        payloads = [json.loads(item["result"]["content"][0]["text"]) for item in (search, page, reference)]
        resource_payload = json.loads(resource["result"]["contents"][0]["text"])
        self.assertEqual(payloads[0]["results"][0]["published_at"], "2024-10-09")
        self.assertEqual(payloads[1]["publication_date_basis"], "source_metadata")
        self.assertEqual(payloads[2]["results"][0]["source_type"], "conference_talk")
        self.assertEqual(resource_payload["creators"], "Damien Morello")

    def test_wiki_result_shape_does_not_add_empty_research_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            wiki = write_dataset(Path(tmp), "cities2-docs", "systems", "Systems", "wiki update phases")
            corpus = Corpus([wiki])
            response = mcp_server.handle_tools_call(1, {"name": "search", "arguments": {"query": "update phases"}}, corpus)
        result = json.loads(response["result"]["content"][0]["text"])["results"][0]
        self.assertNotIn("published_at", result)
```

- [ ] **Step 2: Run the multi-dataset tests and verify failures**

Run:

```powershell
python -m unittest tests.test_retrieval_multi_dataset -v
```

Expected: bare-ID and provenance assertions fail against current retrieval behavior.

- [ ] **Step 3: Add optional provenance propagation**

Add this helper near `format_doc_result()` and merge it into reference documents, search results, page payloads, and page resource payloads:

```python
PROVENANCE_KEYS = (
    "published_at",
    "publication_date_basis",
    "source_type",
    "creators",
    "organizations",
    "report_created_at",
    "report_updated_at",
)


def provenance_fields(row: JSON) -> JSON:
    return {key: row[key] for key in PROVENANCE_KEYS if row.get(key) not in (None, "")}
```

When building `ref_doc`, include `**provenance_fields(p)` and append present provenance values to its indexed `text` so queries for a publication date, creator, or source type can route to the report. In `format_doc_result()`, return the existing fields plus `**provenance_fields(doc)`. In `get_page`, `query_reference`, and page resources, add `**provenance_fields(row)` or `**provenance_fields(d)` after the standard fields. Do not insert keys with empty values.

- [ ] **Step 4: Restore unique bare-ID resolution**

Replace the single-dataset-only fallback in `Corpus.resolve_page_id()` with unambiguous suffix resolution:

```python
        suffix = f":{page_id}"
        matches = [candidate for candidate in self.pages if candidate.endswith(suffix)]
        if len(matches) == 1:
            return matches[0]
        return None
```

Keep direct qualified lookup first. Update the docstring to state that bare IDs work when unique and qualified IDs are required on collision.

- [ ] **Step 5: Run focused and existing retrieval tests**

Run:

```powershell
python -m unittest tests.test_retrieval_multi_dataset tests.test_corpus_source_links -v
```

Expected: all focused retrieval tests pass.

- [ ] **Step 6: Commit the retrieval slice**

```powershell
git add cities2_mcp/retrieval/mcp_server.py tests/test_retrieval_multi_dataset.py
git commit -m "feat: expose research provenance in retrieval"
```

### Task 5: Load research independently and report source status

**Files:**
- Modify: `cities2_mcp/__init__.py`
- Modify: `cities2_mcp/mcp_server.py:54-73`
- Modify: `cities2_mcp/mcp_server.py:470-550`
- Modify: `cities2_mcp/mcp_server.py:717-754`
- Modify: `cities2_mcp/mcp_server.py:890-1014`
- Modify: `cities2_mcp/mcp_server.py:1028-1106`
- Modify: `tests/test_packaging.py`
- Modify: `tests/smoke_mcp.py:179-201`

**Interfaces:**
- Produces: `bundled_research_data_dir() -> Path` from both package and server modules.
- Produces: `load_corpus_sources(wiki_dir: Path, research_dirs: list[Path]) -> tuple[Optional[Corpus], Optional[str], list[JSON]]`.
- Changes: `source_status` adds `research`, a list of dataset status objects.
- Changes: CLI accepts repeatable `--research-data-dir`; explicit values replace the bundled default.

- [ ] **Step 1: Write failing package-path and server source-status tests**

Extend `test_package_module_reports_version_and_bundled_data_dir` to assert the research manifest and indexes exist. Add a default server assertion that `source_status()["research"][0]` is available with dataset `cities2-research`, positive page/chunk counts, and configured paths.

Add this fallback test using the existing MCP smoke helpers:

```python
    def test_bad_research_dataset_keeps_wiki_available(self) -> None:
        from tests.smoke_mcp import call, rpc_ndjson

        with tempfile.TemporaryDirectory(prefix="cities2-bad-research-") as tmp:
            bad = Path(tmp) / "bad"
            bad.mkdir()
            proc = subprocess.Popen(
                [sys.executable, "-m", "cities2_mcp.mcp_server", "--research-data-dir", str(bad)],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin and proc.stdout and proc.stderr
            try:
                rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
                status = call(proc, 2, "source_status", {})
                search = call(proc, 3, "search", {"query": "modding toolchain", "limit": 1})
                self.assertTrue(status["wiki"]["available"])
                self.assertFalse(status["research"][0]["available"])
                self.assertIn("Missing chunks index", status["research"][0]["error"])
                self.assertTrue(search["ok"])
            finally:
                self._stop_proc(proc)
```

- [ ] **Step 2: Run the package tests and verify failures**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_package_module_reports_version_and_bundled_data_dir tests.test_packaging.PluginPackagingTests.test_default_start_without_workspace_keeps_knowledge_tools_available tests.test_packaging.PluginPackagingTests.test_bad_research_dataset_keeps_wiki_available -v
```

Expected: failures because the package helper, CLI option, and research status do not exist.

- [ ] **Step 3: Add bundled research paths and isolated source loading**

Add this function to `cities2_mcp/__init__.py` and mirror it in `cities2_mcp/mcp_server.py`:

```python
def bundled_research_data_dir() -> Path:
    return package_root() / "research_data"
```

In the server module use `Path(__file__).resolve().parent / "research_data"` because it already defines its local `bundled_data_dir()`.

Add this loader near `resolve_data_dir()`:

```python
def load_corpus_sources(
    wiki_dir: Path,
    research_dirs: list[Path],
) -> tuple[Optional[Corpus], Optional[str], list[JSON]]:
    try:
        wiki_corpus = Corpus([wiki_dir])
    except Exception as exc:
        return None, str(exc), [
            {
                "source": "research",
                "dataset": path.name,
                "available": False,
                "error": "Wiki corpus must load before research datasets can be combined.",
                "configured_paths": {
                    "chunks": str(path / "index" / "chunks.jsonl"),
                    "pages": str(path / "index" / "pages.jsonl"),
                },
            }
            for path in research_dirs
        ]

    valid: list[Path] = []
    statuses: list[JSON] = []
    for path in research_dirs:
        configured_paths = {
            "chunks": str(path / "index" / "chunks.jsonl"),
            "pages": str(path / "index" / "pages.jsonl"),
        }
        try:
            probe = Corpus([path])
        except Exception as exc:
            statuses.append(
                {
                    "source": "research",
                    "dataset": path.name,
                    "available": False,
                    "error": str(exc),
                    "configured_paths": configured_paths,
                    "page_count": 0,
                    "chunk_count": 0,
                }
            )
            continue
        valid.append(path)
        statuses.append(
            {
                "source": "research",
                "dataset": probe.dataset_names[0],
                "available": True,
                "error": "",
                "configured_paths": configured_paths,
                "page_count": len(probe.pages),
                "chunk_count": len(probe.chunks),
            }
        )
    if not valid:
        return wiki_corpus, None, statuses
    return Corpus([wiki_dir, *valid]), None, statuses
```

- [ ] **Step 4: Thread research status through requests and startup**

Add `research_status: Optional[list[JSON]] = None` to `handle_encyclopedia_tools`, `handle_tools_call`, and `handle_request`, pass it through every call, and add this field to the `source_status` result:

```python
"research": research_status or [],
```

Extend `wiki_status` with `dataset`, `page_count`, and `chunk_count`. Define `wiki_dataset = corpus.dataset_names[0] if corpus is not None and corpus.dataset_names else "cities2-docs"` immediately before the status dictionary, then derive counts from that name so research records are not included in wiki totals:

```python
"dataset": wiki_dataset,
"page_count": sum(1 for row in corpus.pages.values() if row.get("dataset") == wiki_dataset) if corpus else 0,
"chunk_count": sum(1 for row in corpus.chunks if row.get("dataset") == wiki_dataset) if corpus else 0,
```

Add the CLI option and resolve configured directories:

```python
parser.add_argument("--research-data-dir", action="append", dest="research_data_dirs")

research_values = args.research_data_dirs or [str(bundled_research_data_dir())]
research_dirs = [resolve_data_dir(value) for value in research_values]
corpus, corpus_error, research_status = load_corpus_sources(data_dir, research_dirs)
```

Replace the existing `Corpus([data_dir])` try/except with this call. Log every research status in debug mode. Update source-status tool text, prompt guidance, and server instructions so `search`, `query_reference`, and `get_page` are described as searching bundled wiki and research datasets, with dataset labels and temporal caution for research.

- [ ] **Step 5: Run focused server tests**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_package_module_reports_version_and_bundled_data_dir tests.test_packaging.PluginPackagingTests.test_default_start_without_workspace_keeps_knowledge_tools_available tests.test_packaging.PluginPackagingTests.test_bad_research_dataset_keeps_wiki_available -v
```

Expected: all focused tests pass and the bad-research process still answers a wiki search.

- [ ] **Step 6: Run the direct MCP smoke test against bundled sources**

Before running it, extend the status assertions and output in `tests/smoke_mcp.py`:

```python
assert status["research"][0]["available"]
assert status["research"][0]["dataset"] == "cities2-research"
print("research dataset available:", status["research"][0]["available"])
```

Run:

```powershell
python tests/smoke_mcp.py --use-bundled-data
```

Expected: initialization, wiki search, research-aware source status, and existing workflow smoke operations complete successfully.

- [ ] **Step 7: Commit the server integration slice**

```powershell
git add cities2_mcp/__init__.py cities2_mcp/mcp_server.py tests/test_packaging.py tests/smoke_mcp.py
git commit -m "feat: load bundled Cities2 research"
```

### Task 6: Package, document, synchronize, and verify the feature

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `cities2_mcp/plugin_metadata.py`
- Modify: `integrations/openai/README.md`
- Modify: `integrations/anthropic/README.md`
- Modify: `tests/test_packaging.py`
- Generate: `plugins/cities2-mcp/**`

**Interfaces:**
- Consumes: canonical `cities2_mcp/` package and generated research dataset from Tasks 1-5.
- Produces: wheel/sdist configuration and plugin payloads containing `research_data`.
- Produces: user documentation distinguishing wiki, research, and local encyclopedia sources.

- [ ] **Step 1: Write failing packaging assertions**

Update the existing vendored package tests to require:

```python
self.assertTrue((plugin_root / "vendor" / "cities2_mcp" / "research_data" / "manifest.json").exists())
self.assertTrue((plugin_root / "vendor" / "cities2_mcp" / "research_data" / "index" / "chunks.jsonl").exists())
self.assertTrue(status["research"][0]["available"])
self.assertEqual(status["research"][0]["dataset"], "cities2-research")
```

Add `pyproject.toml` assertions that `cities2-research/README.md` and `cities2-research/reports/**` are included in the sdist list, while `cities2-research/**` and `cities2-research/sources/**` are not broad include patterns.

- [ ] **Step 2: Run focused packaging tests and verify failures**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_claude_plugin_vendored_launcher_serves_mcp tests.test_packaging.PluginPackagingTests.test_codex_plugin_vendored_launcher_serves_mcp tests.test_packaging.PluginPackagingTests.test_repo_metadata_in_sync -v
```

Expected: vendor or metadata assertions fail until canonical docs are updated and plugin payloads are synchronized.

- [ ] **Step 3: Update packaging and user-facing source descriptions**

Add only `cities2-research/README.md` and `cities2-research/reports/**` to `[tool.hatch.build.targets.sdist].include`. Do not include `cities2-research/sources/**`; Hatch can otherwise collect ignored local files that happen to match a broad sdist glob.

Update `README.md` with a `Search curated research` subsection that states reports are historically situated, separately attributed, and generated from committed notes rather than raw transcripts. Update the licensing section to link `cities2_mcp/research_data/ATTRIBUTION.md` separately from the wiki corpus.

Update `CONTRIBUTING.md` with the exact commands:

```powershell
python -m cities2_mcp.research sync
python -m cities2_mcp.research check
```

State that unclear publication dates require maintainer confirmation before sync and raw source material must stay under ignored `cities2-research/sources/`.

Update the long descriptions and packaged README prose in `cities2_mcp/plugin_metadata.py`, plus both integration READMEs, so distributions say they bundle the CS2 wiki corpus and curated research reports. Preserve the distinction between those bundled sources and the locally extracted game encyclopedia.

- [ ] **Step 4: Synchronize generated plugin payloads**

Run:

```powershell
python -m cities2_mcp.plugin_packages sync
python -m cities2_mcp.plugin_packages check
```

Expected: sync updates the committed Antigravity vendor copy, including `vendor/cities2_mcp/research_data/`; check prints `Plugin package payloads are in sync.`

- [ ] **Step 5: Run research, retrieval, packaging, and full repository gates**

Run these fresh commands in order:

```powershell
python -m cities2_mcp.research check
python -m cities2_mcp.plugin_packages check
python -m unittest tests.test_research tests.test_retrieval_multi_dataset tests.test_corpus_source_links tests.test_packaging -v
python -m unittest discover -s tests -v
```

Expected: research and plugin checks exit 0; focused tests pass; the full suite reports zero failures.

- [ ] **Step 6: Inspect privacy, generated output, and diff hygiene**

Run:

```powershell
git status --short --ignored cities2-research
git diff --check
git diff --stat origin/main...HEAD
rg -n "C:\\Users\\|OneDrive\\Documents|hello and welcome to my talk" cities2-research/reports cities2_mcp/research_data plugins/cities2-mcp/vendor/cities2_mcp/research_data
```

Expected: only `sources/.gitignore` is tracked under private intake; `git diff --check` is clean; the private-marker search returns no matches; generated dataset and vendor copies are present and intentional.

- [ ] **Step 7: Commit documentation, metadata, and generated payloads**

```powershell
git add pyproject.toml README.md CONTRIBUTING.md cities2_mcp/plugin_metadata.py integrations/openai/README.md integrations/anthropic/README.md tests/test_packaging.py plugins/cities2-mcp docs/superpowers/plans/2026-07-18-cities2-research-corpus.md
git commit -m "docs: document bundled Cities2 research"
```

- [ ] **Step 8: Re-run final verification after the commit**

Run:

```powershell
python -m cities2_mcp.research check
python -m cities2_mcp.plugin_packages check
python -m unittest discover -s tests -v
git status --short --branch
```

Expected: both checks pass, the full suite reports zero failures, and the worktree is clean with `codex/cities2-research` ahead of `origin/main` only by the approved commits.
