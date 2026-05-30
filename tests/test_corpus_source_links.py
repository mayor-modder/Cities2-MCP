from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cities2_mcp.retrieval import mcp_server as retrieval_server
from cities2_mcp.retrieval.mcp_server import Corpus

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "cities2_mcp" / "data"
SOURCE_PREFIX = "Source: https://cs2.paradoxwikis.com/"
OLD_SOURCE_HOST = "https://cities2.paradoxwikis.com/"


class CorpusSourceLinkTests(unittest.TestCase):
    def test_corpus_uses_current_wiki_host(self) -> None:
        matches: list[str] = []
        for path in CORPUS.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json", ".jsonl"}:
                if OLD_SOURCE_HOST in path.read_text(encoding="utf-8"):
                    matches.append(str(path.relative_to(ROOT)))
        self.assertEqual(matches, [])

    def test_public_corpus_does_not_include_page_sidecar_dirs(self) -> None:
        self.assertFalse((CORPUS / "pages").exists())

    def test_page_index_urls_use_current_wiki_host(self) -> None:
        broken: list[str] = []
        for line_number, line in enumerate((CORPUS / "index" / "pages.jsonl").read_text(encoding="utf-8").splitlines(), start=1):
            payload = json.loads(line)
            if not str(payload.get("url", "")).startswith("https://cs2.paradoxwikis.com/"):
                broken.append(f"data/index/pages.jsonl:{line_number}")
        self.assertEqual(broken, [])

    def test_public_corpus_does_not_include_private_build_paths(self) -> None:
        private_markers = [
            "source_file",
            "markdown_path",
            "json_path",
            "C:\\Users\\matt",
            "Downloads\\cs2wiki",
            "OneDrive\\Documents",
        ]
        broken: list[str] = []
        for path in CORPUS.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json", ".jsonl"}:
                text = path.read_text(encoding="utf-8")
                if any(marker in text for marker in private_markers):
                    broken.append(str(path.relative_to(ROOT)))
        self.assertEqual(broken, [])

    def test_chunk_source_links_have_following_blank_line(self) -> None:
        broken: list[str] = []
        chunks_path = CORPUS / "index" / "chunks.jsonl"
        for line_number, line in enumerate(chunks_path.read_text(encoding="utf-8").splitlines(), start=1):
            payload = json.loads(line)
            text = str(payload.get("text", ""))
            source_index = text.find(SOURCE_PREFIX)
            if source_index == -1:
                continue
            line_end = text.find("\n", source_index)
            if line_end == -1 or text[line_end : line_end + 2] != "\n\n":
                broken.append(f"{chunks_path.relative_to(ROOT)}:{line_number}")
        self.assertEqual(broken, [])

    def test_corpus_attribution_includes_license_and_media_notice(self) -> None:
        attribution = (CORPUS / "ATTRIBUTION.md").read_text(encoding="utf-8")
        attribution_words = " ".join(attribution.split())
        required = [
            "https://cs2.paradoxwikis.com/",
            "https://central.paradoxwikis.com/Copyrights",
            "Creative Commons Attribution-ShareAlike 3.0 Unported",
            "https://creativecommons.org/licenses/by-sa/3.0/",
            "Non-text media",
            "images and screenshots",
            "used referentially to identify the game, source wiki, and related companies",
            "not developed by, affiliated with, sponsored by, endorsed by, reviewed by, or approved by",
            "Paradox Interactive",
            "Iceflake Studios",
            "Colossal Order",
            "Paradox-owned source material notice",
            "## Changes",
        ]
        missing = [value for value in required if value not in attribution and value not in attribution_words]
        self.assertEqual(missing, [])
        self.assertNotIn("Copyright (c) 2014 Paradox Interactive AB", attribution)

    def test_public_corpus_loads_without_private_markdown_paths(self) -> None:
        corpus = Corpus([CORPUS])

        self.assertGreater(len(corpus.pages), 0)
        self.assertGreater(len(corpus.chunks), 0)

    def test_get_page_reconstructs_markdown_from_chunks_without_page_sidecars(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-mcp-agent-corpus-") as tmp:
            data_dir = Path(tmp)
            (data_dir / "index").mkdir()
            (data_dir / "manifest.json").write_text(
                json.dumps({"name": "agent-corpus"}),
                encoding="utf-8",
            )
            (data_dir / "index" / "pages.jsonl").write_text(
                json.dumps(
                    {
                        "page_id": "roads",
                        "title": "Roads",
                        "url": "https://cs2.paradoxwikis.com/Roads",
                        "sections": ["Overview"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (data_dir / "index" / "chunks.jsonl").write_text(
                json.dumps(
                    {
                        "chunk_id": "roads#1",
                        "page_id": "roads",
                        "title": "Roads",
                        "section": "Overview",
                        "text": "# Roads\n\nSource: https://cs2.paradoxwikis.com/Roads\n\nRoads move traffic.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            corpus = Corpus([data_dir])
            response = retrieval_server.handle_tools_call(
                1,
                {"name": "get_page", "arguments": {"page_id": "roads"}},
                corpus,
            )
            payload = json.loads(response["result"]["content"][0]["text"])

        self.assertIn("Roads move traffic.", payload["markdown"])


if __name__ == "__main__":
    unittest.main()
