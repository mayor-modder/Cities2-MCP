from __future__ import annotations

import json
import unittest
from pathlib import Path

from cities2_mcp import mcp_server

ROOT = Path(__file__).resolve().parents[1]


class DocsGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = mcp_server
        cls.docs_paths = {
            "chunks": r"C:\broken\data\index\chunks.jsonl",
            "pages": r"C:\broken\data\index\pages.jsonl",
        }

    def test_search_returns_blocking_error_payload_when_docs_are_unavailable(self) -> None:
        response = self.module.handle_tools_call(
            1,
            {"name": "search", "arguments": {"query": "zoning", "limit": 1}},
            corpus=None,
            wm=None,
            corpus_error=f"Missing chunks index: {self.docs_paths['chunks']}",
            workflow_error=None,
            docs_paths=self.docs_paths,
        )

        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "DOCS_INDEX_MISSING_OR_MISCONFIGURED")
        self.assertEqual(payload["headline"], "Cities2 docs are not available for this session")
        self.assertEqual(payload["configured_paths"]["chunks"], self.docs_paths["chunks"])
        self.assertIn("STOP and ask the user", payload["next_step"])

    def test_resources_list_is_empty_when_docs_are_unavailable(self) -> None:
        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}},
            corpus=None,
            wm=None,
            corpus_error=f"Missing chunks index: {self.docs_paths['chunks']}",
            workflow_error=None,
            docs_paths=self.docs_paths,
        )

        uris = {item["uri"] for item in response["result"]["resources"]}
        self.assertEqual(uris, set())

    def test_all_docs_tools_share_the_same_blocking_guard(self) -> None:
        docs_tools = [
            ("search", {"query": "zoning", "limit": 1}),
            ("query_reference", {"query": "zoning", "limit": 1}),
            ("get_page", {"page_id": "zoning"}),
            ("get_snippets", {"query": "settings file", "limit": 1}),
        ]
        expected_payload = {
            "ok": False,
            "code": "DOCS_INDEX_MISSING_OR_MISCONFIGURED",
            "headline": "Cities2 docs are not available for this session",
            "error": f"Missing chunks index: {self.docs_paths['chunks']}",
            "configured_paths": {
                "chunks": self.docs_paths["chunks"],
                "pages": self.docs_paths["pages"],
            },
            "next_step": (
                "STOP and ask the user whether to fix the MCP config, rebuild or restore the docs corpus, "
                "or continue without docs."
            ),
        }

        for name, arguments in docs_tools:
            with self.subTest(name=name):
                response = self.module.handle_tools_call(
                    3,
                    {"name": name, "arguments": arguments},
                    corpus=None,
                    wm=None,
                    corpus_error=f"Missing chunks index: {self.docs_paths['chunks']}",
                    workflow_error=None,
                    docs_paths=self.docs_paths,
                )
                payload = json.loads(response["result"]["content"][0]["text"])
                self.assertEqual(payload, expected_payload)

    def test_docs_guard_names_match_public_docs_tools(self) -> None:
        self.assertEqual(
            self.module.DOCS_TOOL_NAMES,
            {"search", "query_reference", "get_page", "get_snippets"},
        )

    def test_resources_read_uses_the_same_guard_payload(self) -> None:
        expected_payload = {
            "ok": False,
            "code": "DOCS_INDEX_MISSING_OR_MISCONFIGURED",
            "headline": "Cities2 docs are not available for this session",
            "error": f"Missing pages index: {self.docs_paths['pages']}",
            "configured_paths": {
                "chunks": self.docs_paths["chunks"],
                "pages": self.docs_paths["pages"],
            },
            "next_step": (
                "STOP and ask the user whether to fix the MCP config, rebuild or restore the docs corpus, "
                "or continue without docs."
            ),
        }

        response = self.module.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "cities2docs://page/zoning"},
            },
            corpus=None,
            wm=None,
            corpus_error=f"Missing pages index: {self.docs_paths['pages']}",
            workflow_error=None,
            docs_paths=self.docs_paths,
        )

        self.assertEqual(response["error"]["message"], expected_payload["headline"])
        self.assertEqual(response["error"]["data"], expected_payload)
