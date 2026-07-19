from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cities2_mcp.retrieval import mcp_server
from cities2_mcp.retrieval.mcp_server import Corpus


ROOT = Path(__file__).resolve().parents[1]


def write_dataset(
    root: Path,
    name: str,
    page_id: str,
    title: str,
    text: str,
    *,
    directory_name: str | None = None,
    **extra: str,
) -> Path:
    data_dir = root / (directory_name or name)
    (data_dir / "index").mkdir(parents=True)
    manifest = {
        "name": name,
        "dataset": name,
        "page_count": 1,
        "chunk_count": 1,
        "paths": {"pages_jsonl": "index/pages.jsonl", "chunks_jsonl": "index/chunks.jsonl"},
    }
    if name == "cities2-research":
        manifest["report_count"] = 1
    (data_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    page = {"page_id": page_id, "title": title, "url": f"https://example.com/{page_id}", "sections": ["Overview"], **extra}
    chunk = {"chunk_id": f"{page_id}#1", "page_id": page_id, "title": title, "url": page["url"], "section": "Overview", "text": text, **extra}
    (data_dir / "index" / "pages.jsonl").write_text(json.dumps(page) + "\n", encoding="utf-8")
    (data_dir / "index" / "chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
    return data_dir


class MultiDatasetRetrievalTests(unittest.TestCase):
    def test_bundled_search_returns_research_for_exact_title_and_report_topics(self) -> None:
        corpus = Corpus([ROOT / "cities2_mcp" / "data", ROOT / "cities2_mcp" / "research_data"])
        queries = (
            "Tapping the Entity Component System for Cities Skylines II",
            "lazy GUID based asset loading reverse prefab dependencies",
        )
        for query in queries:
            with self.subTest(query=query):
                response = mcp_server.handle_tools_call(
                    1,
                    {"name": "search", "arguments": {"query": query, "limit": 5}},
                    corpus,
                )
                results = json.loads(response["result"]["content"][0]["text"])["results"]
                self.assertIn("cities2-research", [result["dataset"] for result in results])

    def test_bundled_query_reference_routes_exact_title_and_report_topics_to_research(self) -> None:
        corpus = Corpus([ROOT / "cities2_mcp" / "data", ROOT / "cities2_mcp" / "research_data"])
        queries = (
            "Tapping the Entity Component System for Cities Skylines II",
            "lazy GUID based asset loading reverse prefab dependencies",
        )
        for query in queries:
            with self.subTest(query=query):
                response = mcp_server.handle_tools_call(
                    1,
                    {
                        "name": "query_reference",
                        "arguments": {"query": query, "limit": 5},
                    },
                    corpus,
                )
                results = json.loads(response["result"]["content"][0]["text"])["results"]
                research_results = [result for result in results if result["dataset"] == "cities2-research"]
                self.assertTrue(research_results)
                self.assertEqual(research_results[0]["published_at"], "2024-10-09")
                if query == queries[0]:
                    self.assertEqual(results[0]["dataset"], "cities2-research")

    def test_query_reference_indexes_topics_from_late_chunks_with_bounded_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            data_dir = write_dataset(
                root,
                "cities2-research",
                "long-report",
                "Long report",
                "filler " * 3000,
            )
            chunks_path = data_dir / "index" / "chunks.jsonl"
            first_chunk = json.loads(chunks_path.read_text(encoding="utf-8"))
            late_chunk = {
                **first_chunk,
                "chunk_id": "long-report#2",
                "section": "Late finding",
                "text": "xylophonic quasar sentinel",
            }
            chunks_path.write_text(
                json.dumps(first_chunk) + "\n" + json.dumps(late_chunk) + "\n",
                encoding="utf-8",
            )
            manifest_path = data_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunk_count"] = 2
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            corpus = Corpus([data_dir])

        self.assertLessEqual(
            len(mcp_server.bounded_unique_chunk_text(corpus.chunks)),
            mcp_server.REFERENCE_CONTENT_CHARS,
        )
        response = mcp_server.handle_tools_call(
            1,
            {"name": "query_reference", "arguments": {"query": "xylophonic quasar sentinel", "limit": 5}},
            corpus,
        )
        results = json.loads(response["result"]["content"][0]["text"])["results"]
        self.assertEqual(results[0]["page_id"], "cities2-research:long-report")

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

    def test_missing_and_malformed_manifests_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            for label in ("missing", "malformed"):
                data_dir = write_dataset(root, f"dataset-{label}", "page", "Page", "body")
                manifest = data_dir / "manifest.json"
                if label == "missing":
                    manifest.unlink()
                else:
                    manifest.write_text("{broken", encoding="utf-8")
                with self.subTest(label=label), self.assertRaisesRegex(ValueError, "manifest"):
                    Corpus([data_dir])

    def test_manifest_identity_and_declared_counts_are_validated(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            cases = (
                ("identity", {"dataset": "wrong-dataset"}, "manifest name and dataset must match exactly"),
                (
                    "padded-dataset",
                    {"dataset": " cities2-research "},
                    "manifest name and dataset must match exactly",
                ),
                ("pages", {"page_count": 2, "report_count": 2}, "page_count declares 2 but loaded 1"),
                ("chunks", {"chunk_count": 2}, "chunk_count declares 2 but loaded 1"),
                (
                    "invalid-report-count",
                    {"report_count": "bogus"},
                    "report_count must be a positive integer",
                ),
                (
                    "mismatched-report-count",
                    {"report_count": 2},
                    "report_count must equal page_count",
                ),
                (
                    "empty-research",
                    {"report_count": 0, "page_count": 0, "chunk_count": 0},
                    "report_count must be a positive integer",
                ),
            )
            for label, updates, expected_error in cases:
                data_dir = write_dataset(
                    root,
                    "cities2-research",
                    "page",
                    "Page",
                    "body",
                    directory_name=label,
                )
                manifest_path = data_dir / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest.update(updates)
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.subTest(label=label), self.assertRaisesRegex(ValueError, expected_error):
                    Corpus([data_dir])

    def test_duplicate_dataset_names_are_rejected_before_records_can_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            first = write_dataset(
                root,
                "cities2-research",
                "shared",
                "First",
                "first body",
                directory_name="first",
            )
            second = write_dataset(
                root,
                "cities2-research",
                "shared",
                "Second",
                "second body",
                directory_name="second",
            )
            with self.assertRaisesRegex(ValueError, "duplicate dataset name: cities2-research"):
                Corpus([first, second])

    def test_duplicate_qualified_page_and_chunk_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            for record_type in ("page", "chunk"):
                data_dir = write_dataset(
                    root,
                    f"duplicate-{record_type}",
                    "shared",
                    "Shared",
                    "body",
                )
                manifest_path = data_dir / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                index_path = data_dir / "index" / f"{record_type}s.jsonl"
                first_line = index_path.read_text(encoding="utf-8").splitlines()[0]
                index_path.write_text(first_line + "\n" + first_line + "\n", encoding="utf-8")
                manifest[f"{record_type}_count"] = 2
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.subTest(record_type=record_type), self.assertRaisesRegex(
                    ValueError, f"duplicate qualified {record_type}_id"
                ):
                    Corpus([data_dir])

    def test_non_string_or_blank_page_and_chunk_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            record_fields = (
                ("page", "pages", "page_id"),
                ("chunk", "chunks", "chunk_id"),
                ("chunk-page", "chunks", "page_id"),
            )
            invalid_values = (
                ("null", None),
                ("numeric", 7),
                ("blank", "   "),
                ("padded", " shared "),
                ("qualified", "other:shared"),
            )
            for record_label, index_name, field in record_fields:
                for value_label, invalid_value in invalid_values:
                    data_dir = write_dataset(
                        root,
                        f"invalid-{record_label}-{value_label}",
                        "shared",
                        "Shared",
                        "body",
                    )
                    index_path = data_dir / "index" / f"{index_name}.jsonl"
                    record = json.loads(index_path.read_text(encoding="utf-8"))
                    record[field] = invalid_value
                    index_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
                    with self.subTest(record=record_label, value=value_label), self.assertRaisesRegex(
                        ValueError, f"{field} is required and must be a canonical nonempty string"
                    ):
                        Corpus([data_dir])

    def test_research_name_collision_is_reported_without_disabling_wiki(self) -> None:
        from cities2_mcp.mcp_server import load_corpus_sources

        with tempfile.TemporaryDirectory(prefix="cities2-multi-") as tmp:
            root = Path(tmp)
            wiki = write_dataset(root, "cities2-docs", "wiki", "Wiki", "wiki body", directory_name="wiki")
            collision = write_dataset(
                root,
                "cities2-docs",
                "research",
                "Wrong research identity",
                "research body",
                directory_name="research",
            )
            corpus, wiki_error, statuses = load_corpus_sources(wiki, [collision])

        self.assertIsNotNone(corpus)
        self.assertIsNone(wiki_error)
        self.assertEqual(corpus.dataset_names, ["cities2-docs"])
        self.assertFalse(statuses[0]["available"])
        self.assertIn("duplicate dataset name: cities2-docs", statuses[0]["error"])
