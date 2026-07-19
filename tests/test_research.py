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

    def test_parse_report_rejects_compact_published_date(self) -> None:
        text = VALID_BODY.replace("published_at: 2024-10-09", "published_at: 20241009")
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            with self.assertRaisesRegex(ResearchValidationError, "published_at must be a real YYYY-MM-DD date"):
                parse_report(self.write_report(Path(tmp), text, "20241009-test-research-source.md"))

    def test_parse_report_rejects_iso_week_published_date(self) -> None:
        text = VALID_BODY.replace("published_at: 2024-10-09", "published_at: 2024-W41-3")
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            with self.assertRaisesRegex(ResearchValidationError, "published_at must be a real YYYY-MM-DD date"):
                parse_report(self.write_report(Path(tmp), text, "2024-W41-3-test-research-source.md"))

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
