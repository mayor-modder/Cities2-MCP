from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import unquote, urlparse


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
DRIVE_PATH_RE = re.compile(r"(?i)(?:^|[^a-z0-9])(?:[a-z]:(?:/|[^/\s]))")
POSIX_PRIVATE_PATH_RE = re.compile(r"(?i)/(?:users|home|root|mnt/[a-z]|var/folders|tmp)/")
UNC_PATH_RE = re.compile(r"(?<!:)//[^/\s]+/[^/\s]+")
ABSOLUTE_PATH_RE = re.compile(r"(?<![:/\w])/(?!/)[^/\s]+(?:/[^/\s]+)*")
RELATIVE_PATH_RE = re.compile(r"(?:^|[^a-z0-9])(?:\.\.?/)+(?:[^/\s]+/)*[^/\s]+", re.IGNORECASE)
HTTP_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>()\"']+")
HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
MAX_PATH_DECODE_PASSES = 8
MAX_PATH_DECODE_CHARS = 1_000_000
SPECIAL_USE_DNS_SUFFIXES = (
    "local",
    "localhost",
    "localdomain",
    "internal",
    "home.arpa",
    "test",
    "invalid",
    "example",
    "onion",
    "alt",
)
GENERATED_PATHS = (
    Path("manifest.json"),
    Path("ATTRIBUTION.md"),
    Path("index/pages.jsonl"),
    Path("index/chunks.jsonl"),
)


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
    if source_url and not _is_public_http_url(source_url):
        errors.append(f"{path}: source_url must be an absolute http:// or https:// URL with a hostname")
    slug = metadata.get("slug", "")
    if slug and not SLUG_RE.fullmatch(slug):
        errors.append(f"{path}: slug must use lowercase letters, numbers, and hyphens")
    if metadata.get("published_at") and slug:
        expected = f"{metadata['published_at']}-{slug}.md"
        if path.name != expected:
            errors.append(f"{path}: filename must be {expected}")
    return errors


def _decode_path_text(value: str) -> tuple[str, bool]:
    decoded = value
    if "%" not in decoded:
        return decoded.replace("\\", "/"), False
    if len(decoded) > MAX_PATH_DECODE_CHARS:
        return decoded.replace("\\", "/"), True
    for _attempt in range(MAX_PATH_DECODE_PASSES):
        unquoted = unquote(decoded)
        if len(unquoted) > MAX_PATH_DECODE_CHARS:
            return decoded.replace("\\", "/"), True
        if unquoted == decoded:
            return decoded.replace("\\", "/"), False
        decoded = unquoted
    has_residual_encoding = unquote(decoded) != decoded
    return decoded.replace("\\", "/"), has_residual_encoding


def _decoded_path_text(value: str) -> str:
    return _decode_path_text(value)[0]


def _contains_local_path(value: str) -> bool:
    normalized, has_residual_encoding = _decode_path_text(value)
    non_url_text = HTTP_URL_RE.sub("", normalized)
    lowered = normalized.lower()
    return any(
        (
            has_residual_encoding,
            DRIVE_PATH_RE.search(normalized),
            POSIX_PRIVATE_PATH_RE.search(normalized),
            UNC_PATH_RE.search(normalized),
            ABSOLUTE_PATH_RE.search(non_url_text),
            RELATIVE_PATH_RE.search(normalized),
            "file://" in lowered,
            "file:/" in lowered,
            "~/" in normalized,
            "cities2-research/sources/" in lowered,
            "onedrive/documents/" in lowered,
        )
    )


def _is_public_http_url(value: str) -> bool:
    decoded_value = _decoded_path_text(value)
    if (
        _contains_local_path(value)
        or "\\" in value
        or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in decoded_value)
    ):
        return False
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        _port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and value.lower().startswith(f"{parsed.scheme}://")
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and _is_public_hostname(hostname)
    )


def _is_public_hostname(hostname: Optional[str]) -> bool:
    if not hostname:
        return False
    candidate = hostname.rstrip(".")
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        try:
            ascii_hostname = candidate.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        if len(ascii_hostname) > 253 or "." not in ascii_hostname:
            return False
        lowered_hostname = ascii_hostname.lower()
        if any(
            lowered_hostname == suffix or lowered_hostname.endswith(f".{suffix}")
            for suffix in SPECIAL_USE_DNS_SUFFIXES
        ):
            return False
        labels = ascii_hostname.split(".")
        return all(HOST_LABEL_RE.fullmatch(label) for label in labels) and not labels[-1].isdigit()
    return address.is_global


def _validate_emitted_content(path: Path, metadata: dict[str, str], body: str) -> list[str]:
    errors = [
        f"{path}: {field} contains local or private path material"
        for field, value in metadata.items()
        if _contains_local_path(value)
    ]
    if _contains_local_path(body):
        errors.append(f"{path}: report body contains local or private path material")
    return errors


def parse_report(path: Path) -> ResearchReport:
    text = path.read_text(encoding="utf-8")
    metadata, body, errors = _parse_front_matter(path, text)
    errors.extend(_validate_metadata(path, metadata))
    errors.extend(_validate_emitted_content(path, metadata, body))
    sections, section_errors = _parse_sections(path, body)
    errors.extend(section_errors)
    if errors:
        raise ResearchValidationError(errors)
    return ResearchReport(path=path, metadata=metadata, body=body, sections=sections)


def load_reports(reports_dir: Path) -> list[ResearchReport]:
    reports: list[ResearchReport] = []
    errors: list[str] = []
    seen_slugs: set[str] = set()
    paths = sorted(reports_dir.glob("*.md"), key=lambda item: item.name) if reports_dir.is_dir() else []
    if not paths:
        raise ResearchValidationError(
            [f"{reports_dir}: reports directory must contain at least one Markdown report"]
        )
    for path in paths:
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
    if limit < 1:
        raise ValueError("chunk limit must be positive")
    overlap = max(0, min(overlap, limit - 1))
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_oversized_paragraph(paragraph, limit, overlap))
            continue
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            available_overlap = max(0, limit - len(paragraph) - 2)
            tail_size = min(overlap, available_overlap)
            tail = current[-tail_size:].lstrip() if tail_size else ""
            current = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _split_oversized_paragraph(text: str, limit: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        hard_end = min(len(text), start + limit)
        end = hard_end
        if hard_end < len(text):
            whitespace = max(
                text.rfind(" ", start + max(1, limit // 2), hard_end),
                text.rfind("\n", start, hard_end),
            )
            if whitespace > start:
                end = whitespace
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = max(start + 1, end - overlap)
        while next_start < end and text[next_start].isspace():
            next_start += 1
        start = next_start
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
            preamble = (
                f"# {metadata['title']}\n\n"
                f"Source: {metadata['source_url']}\n\n"
                f"Published: {metadata['published_at']}\n\n"
                f"Temporal context: Research summary of a source published on {metadata['published_at']}; "
                "verify current API and patch details separately.\n\n"
                f"## {section_name}\n\n"
            )
            content_limit = MAX_CHUNK_CHARS - len(preamble)
            if content_limit < 1:
                raise ResearchValidationError(
                    [f"{report.path}: generated chunk preamble exceeds the {MAX_CHUNK_CHARS}-character limit"]
                )
            for part in _split_section(section_text, limit=content_limit):
                chunk_number += 1
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


def _paths_overlap(first: Path, second: Path) -> bool:
    first_resolved = first.resolve()
    second_resolved = second.resolve()
    return (
        first_resolved == second_resolved
        or first_resolved in second_resolved.parents
        or second_resolved in first_resolved.parents
    )


def _owned_generated_file(relative: Path) -> bool:
    return relative in GENERATED_PATHS or (
        len(relative.parts) == 2
        and relative.parts[0] == "index"
        and relative.suffix in {".json", ".jsonl"}
    )


def _validate_existing_output(output_dir: Path) -> list[Path]:
    if output_dir.is_symlink():
        raise ResearchValidationError(
            [f"{output_dir}: research output path must be a directory, not a file or symlink"]
        )
    if not output_dir.exists():
        return []
    if not output_dir.is_dir():
        raise ResearchValidationError(
            [f"{output_dir}: research output path must be a directory, not a file or symlink"]
        )

    entries = list(output_dir.rglob("*"))
    if not entries:
        return []
    if any(entry.is_symlink() for entry in entries):
        raise ResearchValidationError([f"{output_dir}: research output directory must not contain symlinks"])

    files = sorted(entry for entry in entries if entry.is_file())
    manifest_path = output_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ResearchValidationError(
            [f"{output_dir}: nonempty output directory is not a recognized cities2-research dataset"]
        ) from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("name") != "cities2-research"
        or manifest.get("dataset") != "cities2-research"
    ):
        raise ResearchValidationError(
            [f"{output_dir}: nonempty output directory is not a recognized cities2-research dataset"]
        )

    for entry in entries:
        relative = entry.relative_to(output_dir)
        if entry.is_dir() and relative != Path("index"):
            raise ResearchValidationError(
                [f"{output_dir}: unrecognized directory in research output directory: {relative}"]
            )
        if entry.is_file() and not _owned_generated_file(relative):
            raise ResearchValidationError(
                [f"{output_dir}: unrecognized file in research output directory: {relative}"]
            )
    return files


def _write_staged_dataset(stage_dir: Path, expected: dict[Path, bytes]) -> None:
    for relative, content in expected.items():
        target = stage_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def sync_dataset(reports_dir: Path, output_dir: Path) -> tuple[Path, ...]:
    if _paths_overlap(reports_dir, output_dir):
        raise ResearchValidationError(
            [f"{reports_dir}: reports and output directories must not overlap: {output_dir}"]
        )
    expected = build_dataset(reports_dir)
    existing_files = _validate_existing_output(output_dir)
    expected_paths = {output_dir / relative for relative in expected}
    changed = [
        output_dir / relative
        for relative, content in expected.items()
        if not (output_dir / relative).is_file() or (output_dir / relative).read_bytes() != content
    ]
    changed.extend(path for path in existing_files if path not in expected_paths)
    if not changed:
        return ()

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    backup_dir: Optional[Path] = None
    existing_moved = False
    installed = False
    try:
        _write_staged_dataset(stage_dir, expected)
        if output_dir.exists():
            backup_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.backup-", dir=output_dir.parent))
            backup_dir.rmdir()
            os.replace(output_dir, backup_dir)
            existing_moved = True
        try:
            os.replace(stage_dir, output_dir)
            installed = True
        except Exception as swap_error:
            if existing_moved and backup_dir is not None and backup_dir.exists() and not output_dir.exists():
                try:
                    os.replace(backup_dir, output_dir)
                    existing_moved = False
                except Exception as rollback_error:
                    raise RuntimeError(
                        f"Research dataset swap failed and rollback also failed: {rollback_error}"
                    ) from swap_error
            raise
        if backup_dir is not None and backup_dir.exists():
            shutil.rmtree(backup_dir)
            existing_moved = False
    finally:
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
        if backup_dir is not None and backup_dir.exists():
            backup_is_disposable = installed or (
                not existing_moved and backup_dir.is_dir() and not any(backup_dir.iterdir())
            )
            if backup_is_disposable:
                shutil.rmtree(backup_dir)
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
