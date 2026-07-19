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
