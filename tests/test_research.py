from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import quote

from cities2_mcp.research import ResearchValidationError, load_reports, parse_report


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "cities2-research" / "reports"
RESEARCH_DATA = ROOT / "cities2_mcp" / "research_data"


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
        self.assertIn("source_url must be an absolute http:// or https:// URL with a hostname", message)
        self.assertIn("missing required section: Findings", message)

    def test_parse_report_rejects_malformed_http_urls_without_a_real_hostname(self) -> None:
        source_urls = (
            "http:C:\\Users\\Example\\private.txt",
            "https:///C:/Users/Example/private.txt",
            "https://example.com/C:%5CUsers%5CExample%5Cprivate.txt",
            "https://example.com/?file=/Users/Example/private.txt",
            "https://example.com/?file=../sources/private.txt",
            "https://example.com/?file=~/private.txt",
            "https://example.com/cities2-research/sources/private.txt",
            "https://user:supersecret@example.com/talk",
            "https://.",
            "https://-",
            "https://example.com private",
            "https://localhost/private.txt",
            "https://127.0.0.1/private.txt",
            "https://printer.local/talk",
            "https://service.localhost/talk",
            "https://host.localdomain/talk",
            "https://build.internal/talk",
            "https://router.home.arpa/talk",
            "https://service.test/talk",
            "https://service.invalid/talk",
            "https://service.example/talk",
            "https://service.onion/talk",
            "https://service.alt/talk",
        )
        for source_url in source_urls:
            with self.subTest(source_url=source_url), tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
                text = VALID_BODY.replace("https://example.com/talk", source_url)
                with self.assertRaisesRegex(ResearchValidationError, "source_url must be an absolute http:// or https:// URL with a hostname"):
                    parse_report(self.write_report(Path(tmp), text))

    def test_parse_report_accepts_public_hosts_with_special_use_labels(self) -> None:
        source_urls = (
            "https://local.example.com/talk",
            "https://internal.example.com/talk",
            "https://home.arpa.example.com/talk",
        )
        for source_url in source_urls:
            with self.subTest(source_url=source_url), tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
                text = VALID_BODY.replace("https://example.com/talk", source_url)
                report = parse_report(self.write_report(Path(tmp), text))
                self.assertEqual(report.metadata["source_url"], source_url)

    def test_build_dataset_rejects_private_paths_in_emitted_metadata_or_body(self) -> None:
        from cities2_mcp.research import build_dataset

        private_values = (
            ("creators: Example Speaker", "creators: C:\\Users\\Example\\speaker.txt"),
            ("creators: Example Speaker", "creators: C:private.txt"),
            ("creators: Example Speaker", "creators: /secret"),
            ("The source explains a system.", "The source was copied from \\\\server\\share\\private.txt."),
            (
                "The source explains a system.",
                "The source was copied from cities2-research/sources/full-transcript.txt.",
            ),
            ("The source explains a system.", "The source was copied from /opt/private/full-transcript.txt."),
            ("The source explains a system.", "The source was copied from ../sources/full-transcript.txt."),
            ("creators: Example Speaker", "creators: file:///Users/Example/speaker.txt"),
        )
        for original, private_value in private_values:
            with self.subTest(private_value=private_value), tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
                root = Path(tmp)
                self.write_report(root, VALID_BODY.replace(original, private_value))
                with self.assertRaisesRegex(ResearchValidationError, "local or private path material"):
                    build_dataset(root)

    def test_build_dataset_rejects_deeply_percent_encoded_private_paths(self) -> None:
        from cities2_mcp.research import build_dataset

        cases = (
            (r"C:\Users\Example\speaker.txt", 3),
            ("../sources/full-transcript.txt", 4),
            ("/Users/Example/private.txt", 12),
        )
        for private_path, passes in cases:
            encoded = private_path
            for _pass in range(passes):
                encoded = quote(encoded, safe="")
            with self.subTest(private_path=private_path, passes=passes), tempfile.TemporaryDirectory(
                prefix="cities2-research-"
            ) as tmp:
                root = Path(tmp)
                self.write_report(root, VALID_BODY.replace("creators: Example Speaker", f"creators: {encoded}"))
                with self.assertRaisesRegex(ResearchValidationError, "local or private path material"):
                    build_dataset(root)

    def test_load_reports_sorts_files_and_rejects_duplicate_slugs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            self.write_report(root)
            duplicate = VALID_BODY.replace("published_at: 2024-10-09", "published_at: 2024-10-10")
            self.write_report(root, duplicate, "2024-10-10-test-research-source.md")
            with self.assertRaisesRegex(ResearchValidationError, "duplicate slug: test-research-source"):
                load_reports(root)

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

    def test_sync_rejects_missing_or_empty_report_directories(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            for reports in (root / "missing", root / "empty"):
                if reports.name == "empty":
                    reports.mkdir()
                output = root / f"output-{reports.name}"
                with self.subTest(reports=reports), self.assertRaisesRegex(
                    ResearchValidationError, "reports directory must contain at least one Markdown report"
                ):
                    sync_dataset(reports, output)
                self.assertFalse(output.exists())

    def test_sync_rejects_overlapping_input_and_output_paths(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            report = self.write_report(reports)
            for output in (reports, root):
                with self.subTest(output=output), self.assertRaisesRegex(
                    ResearchValidationError, "reports and output directories must not overlap"
                ):
                    sync_dataset(reports, output)
                self.assertTrue(report.is_file())

    def test_sync_prunes_only_owned_stale_generated_paths(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            output = root / "output"
            reports.mkdir()
            self.write_report(reports)
            sync_dataset(reports, output)

            stale_generated = output / "index" / "stale.jsonl"
            stale_generated.write_text("stale\n", encoding="utf-8")
            changed = sync_dataset(reports, output)
            self.assertIn(stale_generated, changed)
            self.assertFalse(stale_generated.exists())

            unrelated = output / "personal-notes.txt"
            unrelated.write_text("keep me\n", encoding="utf-8")
            with self.assertRaisesRegex(ResearchValidationError, "unrecognized file in research output directory"):
                sync_dataset(reports, output)
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep me\n")

    def test_sync_refuses_nonempty_unrecognized_output_directories(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            self.write_report(reports)

            for label, include_foreign_manifest in (("missing-manifest", False), ("foreign-manifest", True)):
                output = root / label
                output.mkdir()
                sentinel = output / "keep-me.txt"
                sentinel.write_text("do not replace\n", encoding="utf-8")
                if include_foreign_manifest:
                    (output / "manifest.json").write_text(
                        json.dumps({"name": "someone-else", "dataset": "someone-else"}),
                        encoding="utf-8",
                    )
                before = {path.name: path.read_bytes() for path in output.iterdir()}

                with self.subTest(label=label), self.assertRaisesRegex(
                    ResearchValidationError, "nonempty output directory is not a recognized cities2-research dataset"
                ):
                    sync_dataset(reports, output)

                after = {path.name: path.read_bytes() for path in output.iterdir()}
                self.assertEqual(after, before)
                self.assertEqual(list(root.glob(f".{output.name}.*")), [])

    def test_sync_rejects_a_dangling_output_symlink_without_touching_it(self) -> None:
        from cities2_mcp.research import sync_dataset

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            self.write_report(reports)
            missing_target = root / "missing-target"
            output = root / "output-link"
            try:
                output.symlink_to(missing_target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlinks are unavailable: {exc}")

            with self.assertRaisesRegex(ResearchValidationError, "directory, not a file or symlink"):
                sync_dataset(reports, output)

            self.assertTrue(output.is_symlink())
            self.assertFalse(missing_target.exists())

    def test_sync_rolls_back_the_complete_dataset_after_swap_failure(self) -> None:
        from cities2_mcp import research

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            output = root / "output"
            reports.mkdir()
            report = self.write_report(reports)
            research.sync_dataset(reports, output)
            before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            report.write_text(VALID_BODY.replace("The source explains a system.", "The source explains a changed system."), encoding="utf-8")

            real_replace = research.os.replace

            def fail_staged_swap(source: object, target: object) -> None:
                source_path = Path(source)
                target_path = Path(target)
                if source_path.name.startswith(f".{output.name}.stage-") and target_path == output:
                    raise OSError("injected staged swap failure")
                real_replace(source, target)

            with mock.patch.object(research.os, "replace", side_effect=fail_staged_swap):
                with self.assertRaisesRegex(OSError, "injected staged swap failure"):
                    research.sync_dataset(reports, output)

            after = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            self.assertEqual(after, before)
            self.assertEqual(list(root.glob(f".{output.name}.*")), [])

    def test_sync_cleans_empty_backup_after_backup_preparation_failure(self) -> None:
        from cities2_mcp import research

        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            reports = root / "reports"
            output = root / "output"
            reports.mkdir()
            report = self.write_report(reports)
            research.sync_dataset(reports, output)
            before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            report.write_text(
                VALID_BODY.replace("The source explains a system.", "The source explains a changed system."),
                encoding="utf-8",
            )

            real_rmdir = research.Path.rmdir

            def fail_backup_rmdir(path: Path) -> None:
                if path.name.startswith(f".{output.name}.backup-"):
                    raise OSError("injected backup preparation failure")
                real_rmdir(path)

            with mock.patch.object(research.Path, "rmdir", autospec=True, side_effect=fail_backup_rmdir):
                with self.assertRaisesRegex(OSError, "injected backup preparation failure"):
                    research.sync_dataset(reports, output)

            after = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
            self.assertEqual(after, before)
            self.assertEqual(list(root.glob(f".{output.name}.*")), [])

    def test_chunk_splitting_bounds_overlap_and_oversized_paragraphs(self) -> None:
        from cities2_mcp.research import _split_section

        first = ("alpha " * 13).strip()
        second = ("beta " * 10).strip()
        boundary_chunks = _split_section(f"{first}\n\n{second}", limit=100, overlap=30)
        expected_tail = first[-30:].lstrip()
        self.assertEqual(boundary_chunks, [first, f"{expected_tail}\n\n{second}"])
        self.assertTrue(all(len(chunk) <= 100 for chunk in boundary_chunks))

        text = ("alpha " * 40).strip() + "\n\n" + ("B" * 240) + "\n\n" + ("charlie " * 30).strip()
        chunks = _split_section(text, limit=100, overlap=30)

        self.assertGreater(len(chunks), 3)
        self.assertTrue(all(0 < len(chunk) <= 100 for chunk in chunks))
        self.assertTrue(any("B" * 80 in chunk for chunk in chunks))

    def test_generated_chunk_text_never_exceeds_the_documented_limit(self) -> None:
        from cities2_mcp.research import MAX_CHUNK_CHARS, build_dataset

        oversized = ("A" * 4500) + "\n\n" + ("B" * 4500)
        text = VALID_BODY.replace("The system uses data-oriented processing.", oversized)
        with tempfile.TemporaryDirectory(prefix="cities2-research-") as tmp:
            root = Path(tmp)
            self.write_report(root, text)
            built = build_dataset(root)

        chunks = [json.loads(line) for line in built[Path("index/chunks.jsonl")].decode("utf-8").splitlines()]
        findings = [chunk for chunk in chunks if chunk["section"] == "Findings"]
        self.assertGreater(len(findings), 2)
        self.assertTrue(all(len(chunk["text"]) <= MAX_CHUNK_CHARS for chunk in chunks))

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


class BundledResearchTests(unittest.TestCase):
    def test_generated_research_json_paths_are_forced_to_lf(self) -> None:
        paths = (
            "cities2_mcp/research_data/manifest.json",
            "cities2_mcp/research_data/index/pages.jsonl",
            "cities2_mcp/research_data/index/chunks.jsonl",
            "plugins/cities2-mcp/vendor/cities2_mcp/research_data/manifest.json",
            "plugins/cities2-mcp/vendor/cities2_mcp/research_data/index/pages.jsonl",
            "plugins/cities2-mcp/vendor/cities2_mcp/research_data/index/chunks.jsonl",
        )
        result = subprocess.run(
            ["git", "check-attr", "eol", "--", *paths],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout.count("eol: lf"), len(paths), result.stdout)

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

    def test_city_corner_9_11_report_has_substantive_source_coverage(self) -> None:
        report = parse_report(REPORTS / "2026-07-23-city-corner-series-9-11.md")

        self.assertEqual(report.metadata["slug"], "city-corner-series-9-11")
        self.assertEqual(report.metadata["source_type"], "developer_diary_series")
        self.assertGreater(len(report.body), 7_500)
        for number, thread_id in ((9, "1934993"), (10, "1937714"), (11, "1938630")):
            self.assertIn(f"City Corner #{number}", report.body)
            self.assertIn(thread_id, report.body)
        for detail in (
            "200+ bugs",
            "-startEditor",
            "Parent Mesh",
            "off-disk",
            "reserve enough capacity",
            "income rather than wealth",
            "Waterway Pass",
            "frosted and opaque glass",
        ):
            self.assertIn(detail, report.body)

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
        self.assertEqual(manifest["report_count"], len(list(REPORTS.glob("*.md"))))
        self.assertEqual(manifest["page_count"], manifest["report_count"])
        self.assertGreater(manifest["chunk_count"], 1)


if __name__ == "__main__":
    unittest.main()
