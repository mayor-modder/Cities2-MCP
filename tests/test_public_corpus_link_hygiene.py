from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES_JSONL = ROOT / "cities2_mcp" / "data" / "index" / "pages.jsonl"
CHUNKS_JSONL = ROOT / "cities2_mcp" / "data" / "index" / "chunks.jsonl"
INTERNAL_HOST = "cs2.paradoxwikis.com"
MEDIA_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico")


def link_problem(link: str) -> str | None:
    parsed = urlparse(link)
    path = unquote(parsed.path)
    lower_path = path.lower()
    internal = not parsed.netloc or parsed.netloc.lower() == INTERNAL_HOST

    if "/file:" in lower_path or "/image:" in lower_path or lower_path.startswith(("file:", "image:")):
        return "media namespace"
    if lower_path.endswith(MEDIA_EXTENSIONS):
        return "media file extension"
    if not internal:
        return None
    if any(ord(ch) > 127 for ch in path):
        return "non-English internal page path"
    if lower_path.endswith("/lang") or "/lang/" in lower_path:
        return "language maintenance page"
    if any(namespace in lower_path for namespace in ("/special:", "/template:", "/talk:")):
        return "MediaWiki maintenance namespace"

    query = parse_qs(parsed.query)
    query_values = [unquote(value) for values in query.values() for value in values]
    lower_query_values = [value.lower() for value in query_values]
    if any(value.endswith(MEDIA_EXTENSIONS) for value in lower_query_values):
        return "media query target"
    if any(value.startswith(("special:", "template:", "file:", "image:")) for value in lower_query_values):
        return "MediaWiki maintenance query target"
    if any(value.endswith("/lang") or "/lang/" in value for value in lower_query_values):
        return "language maintenance query target"
    if any(any(ord(ch) > 127 for ch in value) for value in query_values):
        return "non-English internal query target"
    if "action" in query or "veaction" in query:
        return "MediaWiki edit/action link"
    return None


class PublicCorpusLinkHygieneTests(unittest.TestCase):
    def test_page_index_links_exclude_media_admin_and_language_clutter(self) -> None:
        broken: list[str] = []
        for line_number, line in enumerate(PAGES_JSONL.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            for link in row.get("links") or []:
                problem = link_problem(str(link))
                if problem:
                    broken.append(f"{PAGES_JSONL.relative_to(ROOT)}:{line_number} {problem}: {link}")

        self.assertEqual(broken, [])

    def test_chunk_text_excludes_wiki_image_embed_markup(self) -> None:
        broken: list[str] = []
        blocked = ("![", "/thumb.php?f=", "/File:", "File:", "/Image:", "Image:")
        for line_number, line in enumerate(CHUNKS_JSONL.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            text = str(row.get("text", ""))
            if any(token in text for token in blocked):
                broken.append(f"{CHUNKS_JSONL.relative_to(ROOT)}:{line_number}")

        self.assertEqual(broken, [])

    def test_public_corpus_excludes_common_wiki_formatting_artifacts(self) -> None:
        broken: list[str] = []
        blocked = (
            "[edit|edit source]",
            "[edit | edit source]",
            "\u200b",
            "\u200c",
            "\u200d",
            "\ufeff",
            "\u00a0",
            "ContinueDismiss",
            "YouTube might collect personal data",
        )
        for path in (PAGES_JSONL, CHUNKS_JSONL):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if any(token in line for token in blocked):
                    broken.append(f"{path.relative_to(ROOT)}:{line_number}")

        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
