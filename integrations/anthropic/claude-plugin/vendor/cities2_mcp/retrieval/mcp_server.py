#!/usr/bin/env python3
"""Local wiki-corpus MCP retrieval server.

Transport: stdio with Content-Length framing.
Implements:
- initialize / ping
- tools/list
- tools/call
"""

from __future__ import annotations

__version__ = "0.1.1"

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

JSON = Dict[str, Any]
TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")
CODE_FENCE_RE = re.compile(r"```([\w+-]*)\n(.*?)\n```", re.S)
SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2024-11-05")
DEFAULT_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]
LAST_INPUT_TRANSPORT = "framed"
SHOULD_EXIT = False


def debug_enabled() -> bool:
    return os.environ.get("WIKI_MCP_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def debug_log(msg: str) -> None:
    if not debug_enabled():
        return
    path = Path(os.environ.get("WIKI_MCP_DEBUG_LOG", "/tmp/wiki-mcp-debug.log"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{now_iso()} {msg}\n")
    except Exception:
        pass


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def text_result(payload: object, *, is_error: bool = False) -> JSON:
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = str(payload)
    result: JSON = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


class HybridIndex:
    """BM25 + hashed dense score for robust local retrieval without dependencies."""

    def __init__(self, docs: List[JSON], text_key: str = "text") -> None:
        self.docs = docs
        self.text_key = text_key
        self.doc_tokens: List[List[str]] = []
        self.tf: List[Counter] = []
        self.df: Dict[str, int] = defaultdict(int)
        self.avg_len = 0.0

        for doc in docs:
            text = str(doc.get(text_key, ""))
            toks = tokenize(text)
            self.doc_tokens.append(toks)
            tf = Counter(toks)
            self.tf.append(tf)
            for t in tf:
                self.df[t] += 1

        self.n_docs = len(docs)
        self.avg_len = (sum(len(x) for x in self.doc_tokens) / self.n_docs) if self.n_docs else 0.0

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    @staticmethod
    def _hashed_vec(tokens: List[str], dim: int = 512) -> List[float]:
        vec = [0.0] * dim
        for t in tokens:
            h = hash(t)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def _dot(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def search(self, query: str, limit: int = 5, title_key: Optional[str] = "title") -> List[Tuple[float, JSON]]:
        query = (query or "").strip()
        if not query or not self.docs:
            return []

        terms = tokenize(query)
        if not terms:
            return []

        qvec = self._hashed_vec(terms)
        k1 = 1.5
        b = 0.75

        scored: List[Tuple[float, JSON]] = []
        query_lc = query.lower()
        for idx, doc in enumerate(self.docs):
            tf = self.tf[idx]
            dl = len(self.doc_tokens[idx])
            if dl == 0:
                continue

            bm25 = 0.0
            for t in terms:
                freq = tf.get(t, 0)
                if not freq:
                    continue
                bm25 += self._idf(t) * ((freq * (k1 + 1)) / (freq + k1 * (1 - b + b * dl / max(self.avg_len, 1.0))))

            if bm25 == 0.0:
                continue

            dvec = self._hashed_vec(self.doc_tokens[idx])
            dense = max(0.0, self._dot(qvec, dvec))
            score = bm25 * 0.8 + dense * 2.2

            text = str(doc.get(self.text_key, ""))
            if query_lc in text.lower():
                score += 1.5

            if title_key:
                title = str(doc.get(title_key, "")).lower()
                if any(t in title for t in terms):
                    score += 0.6

            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[: max(1, min(limit, 20))]


def _is_within_path(path: Path, root: Path) -> bool:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def markdown_sidecar_path(row: JSON) -> Optional[Path]:
    value = str(row.get("markdown_path") or row.get("_markdown_path") or "").strip()
    if not value:
        return None
    data_dir_value = str(row.get("_data_dir", "")).strip()
    if not data_dir_value:
        return None
    root = Path(data_dir_value).resolve()
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    path = (root / candidate).resolve()
    if not _is_within_path(path, root):
        return None
    return path if path.is_file() else None


def read_markdown_sidecar(row: JSON) -> str:
    path = markdown_sidecar_path(row)
    if path is None:
        return ""
    return path.read_text(encoding="utf-8")


class Corpus:
    def __init__(self, data_dirs: List[Path]) -> None:
        self.chunks: List[JSON] = []
        self.pages: Dict[str, JSON] = {}
        self.chunks_by_id: Dict[str, JSON] = {}
        self.chunks_by_page_id: Dict[str, List[JSON]] = {}
        self.reference_docs: List[JSON] = []
        self.snippets: List[JSON] = []
        self.dataset_names: List[str] = []
        self.single_dataset = len(data_dirs) == 1

        # Per-dataset indexes for fan-out search
        self._chunk_indexes: List[HybridIndex] = []
        self._ref_indexes: List[HybridIndex] = []
        self._snippet_indexes: List[HybridIndex] = []

        for data_dir in data_dirs:
            dataset_name = self._load_dataset_name(data_dir)
            self.dataset_names.append(dataset_name)
            self._load_dataset(data_dir, dataset_name)

    @staticmethod
    def _load_dataset_name(data_dir: Path) -> str:
        manifest_path = data_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                name = str(manifest.get("name", "")).strip()
                if name:
                    return name
            except Exception:
                pass
        return data_dir.name

    def _load_dataset(self, data_dir: Path, dataset_name: str) -> None:
        chunks_path = data_dir / "index" / "chunks.jsonl"
        pages_path = data_dir / "index" / "pages.jsonl"

        if not chunks_path.exists():
            raise FileNotFoundError(f"Missing chunks index: {chunks_path}")
        if not pages_path.exists():
            raise FileNotFoundError(f"Missing pages index: {pages_path}")

        dataset_chunks: List[JSON] = []
        dataset_ref_docs: List[JSON] = []
        dataset_snippets: List[JSON] = []
        dataset_pages: Dict[str, JSON] = {}

        with chunks_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    # Prefix chunk_id and page_id with dataset name
                    orig_chunk_id = str(row.get("chunk_id", ""))
                    orig_page_id = str(row.get("page_id", ""))
                    row["chunk_id"] = f"{dataset_name}:{orig_chunk_id}" if orig_chunk_id else ""
                    row["page_id"] = f"{dataset_name}:{orig_page_id}" if orig_page_id else ""
                    row["dataset"] = dataset_name
                    self.chunks.append(row)
                    dataset_chunks.append(row)
                    if row["chunk_id"]:
                        self.chunks_by_id[row["chunk_id"]] = row
                    if row["page_id"]:
                        self.chunks_by_page_id.setdefault(row["page_id"], []).append(row)

        with pages_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                orig_page_id = str(row.get("page_id", ""))
                prefixed_id = f"{dataset_name}:{orig_page_id}" if orig_page_id else ""
                row["page_id"] = prefixed_id
                row["dataset"] = dataset_name
                row["_data_dir"] = str(data_dir.resolve())
                if orig_page_id and not row.get("markdown_path"):
                    row["_markdown_path"] = str(Path("pages") / "markdown" / f"{orig_page_id}.md")
                if prefixed_id:
                    self.pages[prefixed_id] = row
                    dataset_pages[prefixed_id] = row

        for p in dataset_pages.values():
            sections = p.get("sections", []) or []
            text = "\n".join([str(p.get("title", "")), str(p.get("url", "")), *[str(x) for x in sections]])
            ref_doc = {
                "page_id": p.get("page_id"),
                "title": p.get("title"),
                "url": p.get("url"),
                "oldid": p.get("oldid"),
                "text": text,
                "sections": sections,
                "dataset": dataset_name,
            }
            self.reference_docs.append(ref_doc)
            dataset_ref_docs.append(ref_doc)

            md = self.page_markdown(str(p.get("page_id", "")))
            for idx, m in enumerate(CODE_FENCE_RE.finditer(md), start=1):
                lang = (m.group(1) or "").strip()
                code = m.group(2).strip()
                if len(code) < 8:
                    continue
                snippet = {
                    "snippet_id": f"{p.get('page_id')}#code-{idx}",
                    "page_id": p.get("page_id"),
                    "title": p.get("title"),
                    "url": p.get("url"),
                    "language": lang,
                    "text": code,
                    "dataset": dataset_name,
                }
                self.snippets.append(snippet)
                dataset_snippets.append(snippet)

        self._chunk_indexes.append(HybridIndex(dataset_chunks, text_key="text"))
        self._ref_indexes.append(HybridIndex(dataset_ref_docs, text_key="text"))
        self._snippet_indexes.append(
            HybridIndex(dataset_snippets, text_key="text") if dataset_snippets else None  # type: ignore[arg-type]
        )

    def _fan_out_search(
        self, indexes: List[Optional[HybridIndex]], query: str, limit: int, title_key: Optional[str] = "title"
    ) -> List[Tuple[float, JSON]]:
        """Search all indexes and merge results by score."""
        all_results: List[Tuple[float, JSON]] = []
        for index in indexes:
            if index is not None:
                all_results.extend(index.search(query, limit=limit, title_key=title_key))
        all_results.sort(key=lambda x: x[0], reverse=True)
        return all_results[: max(1, min(limit, 20))]

    def search_chunks(self, query: str, limit: int = 5) -> List[Tuple[float, JSON]]:
        return self._fan_out_search(self._chunk_indexes, query, limit)

    def search_references(self, query: str, limit: int = 5) -> List[Tuple[float, JSON]]:
        return self._fan_out_search(self._ref_indexes, query, limit)

    def search_snippets(self, query: str, limit: int = 3) -> List[Tuple[float, JSON]]:
        return self._fan_out_search(self._snippet_indexes, query, limit)

    @property
    def has_snippets(self) -> bool:
        return any(idx is not None for idx in self._snippet_indexes)

    def resolve_page_id(self, page_id: str) -> Optional[str]:
        """Resolve a page_id, handling single-dataset backward compatibility.

        When only one dataset is loaded, accepts both bare 'page-id' and 'dataset:page-id'.
        When multiple datasets are loaded, requires the 'dataset:page-id' format.
        """
        # Direct lookup first (works for prefixed IDs)
        if page_id in self.pages:
            return page_id

        # Single-dataset backward compat: try prefixing with the only dataset name
        if self.single_dataset and self.dataset_names:
            prefixed = f"{self.dataset_names[0]}:{page_id}"
            if prefixed in self.pages:
                return prefixed

        return None

    def page_markdown(self, page_id: str) -> str:
        row = self.pages.get(page_id)
        if row is not None:
            md = read_markdown_sidecar(row)
            if md:
                return md

        chunks = self.chunks_by_page_id.get(page_id, [])
        texts = [str(chunk.get("text", "")).strip() for chunk in chunks if str(chunk.get("text", "")).strip()]
        return "\n\n".join(texts)


def page_uri(page_id: str) -> str:
    return f"wikimcp://page/{quote(page_id, safe='')}"


def chunk_uri(chunk_id: str) -> str:
    return f"wikimcp://chunk/{quote(chunk_id, safe='')}"


def resource_catalog(corpus: Corpus) -> List[JSON]:
    resources: List[JSON] = []

    for page_id in sorted(corpus.pages.keys()):
        row = corpus.pages[page_id]
        resources.append(
            {
                "uri": page_uri(page_id),
                "name": str(row.get("title") or page_id),
                "description": f"page: {page_id}",
                "mimeType": "application/json",
            }
        )

    for chunk in corpus.chunks:
        chunk_id = str(chunk.get("chunk_id", "")).strip()
        if not chunk_id:
            continue
        title = str(chunk.get("title", "")).strip()
        section = str(chunk.get("section", "")).strip()
        label = title or chunk_id
        if section:
            label = f"{label} [{section}]"
        resources.append(
            {
                "uri": chunk_uri(chunk_id),
                "name": label,
                "description": f"chunk: {chunk_id}",
                "mimeType": "application/json",
            }
        )

    return resources


def resource_templates_catalog() -> List[JSON]:
    return [
        {
            "uriTemplate": "wikimcp://page/{page_id}",
            "name": "Wiki Page",
            "description": "Read a page payload by page_id from pages index.",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "wikimcp://chunk/{chunk_id}",
            "name": "Wiki Chunk",
            "description": "Read a chunk payload by chunk_id from chunks index.",
            "mimeType": "application/json",
        },
    ]


def handle_resources_read(req_id: object, params: JSON, corpus: Corpus) -> JSON:
    uri = str(params.get("uri", "")).strip()
    if not uri:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Missing uri"}}

    page_prefix = "wikimcp://page/"
    chunk_prefix = "wikimcp://chunk/"
    payload: Optional[JSON] = None

    if uri.startswith(page_prefix):
        page_id = unquote(uri[len(page_prefix):])
        resolved = corpus.resolve_page_id(page_id)
        if resolved is None:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32002, "message": f"Page not found: {page_id}"}}
        row = corpus.pages[resolved]

        md = corpus.page_markdown(resolved)

        payload = {
            "page_id": row.get("page_id"),
            "title": row.get("title"),
            "url": row.get("url"),
            "oldid": row.get("oldid"),
            "dataset": row.get("dataset"),
            "sections": row.get("sections", []),
            "links": row.get("links", []),
            "images": row.get("images", []),
            "markdown": md,
        }
    elif uri.startswith(chunk_prefix):
        chunk_id = unquote(uri[len(chunk_prefix):])
        row = corpus.chunks_by_id.get(chunk_id)
        if row is None:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32002, "message": f"Chunk not found: {chunk_id}"}}
        payload = row
    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unsupported resource uri: {uri}"}}

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2),
                }
            ]
        },
    }


def handle_initialize(
    req_id: object,
    params: JSON,
    server_name: str = "wiki-mcp",
    server_version: Optional[str] = None,
    server_instructions: Optional[str] = None,
) -> JSON:
    requested = params.get("protocolVersion")
    requested_str = str(requested).strip() if requested is not None else ""
    # Use the requested version if we recognise it, otherwise fall back to
    # our newest supported version so unknown future versions still connect.
    if requested_str in SUPPORTED_PROTOCOL_VERSIONS:
        protocol_version = requested_str
    else:
        protocol_version = SUPPORTED_PROTOCOL_VERSIONS[0]
    debug_log(f"initialize req_id={req_id!r} requested_protocol={requested!r} selected_protocol={protocol_version!r}")
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": protocol_version,
            "serverInfo": {"name": server_name, "version": server_version if server_version is not None else __version__},
            "capabilities": {
                "experimental": {},
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "instructions": (
                server_instructions
                if server_instructions is not None
                else "Local wiki corpus search server."
            ),
        },
    }


def tools_catalog() -> List[JSON]:
    return [
        {
            "name": "search",
            "description": "Search the bundled Cities: Skylines II Wiki corpus for gameplay, systems, and modding information.",
            "annotations": {
                "title": "Search Wiki Corpus",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_page",
            "description": "Return a full page from the bundled Cities: Skylines II Wiki corpus by page_id.",
            "annotations": {
                "title": "Get Wiki Page",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {"page_id": {"type": "string"}},
                "required": ["page_id"],
            },
        },
        {
            "name": "query_reference",
            "description": "Search page-level Cities: Skylines II Wiki references: titles, sections, URLs, and links.",
            "annotations": {
                "title": "Query Wiki References",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_snippets",
            "description": "Retrieve Cities: Skylines II modding code snippets extracted from the bundled wiki corpus.",
            "annotations": {
                "title": "Get Modding Snippets",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 3},
                },
                "required": ["query"],
            },
        },
    ]


def format_doc_result(score: float, doc: JSON) -> JSON:
    text = str(doc.get("text", "")).strip()
    return {
        "score": round(score, 4),
        "chunk_id": doc.get("chunk_id"),
        "page_id": doc.get("page_id"),
        "title": doc.get("title"),
        "section": doc.get("section"),
        "url": doc.get("url"),
        "dataset": doc.get("dataset"),
        "snippet": text[:900] + ("..." if len(text) > 900 else ""),
    }


def _as_dict(value: object) -> JSON:
    return value if isinstance(value, dict) else {}


def _as_str_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(x) for x in value]


def handle_tools_call(
    req_id: object,
    params: JSON,
    corpus: Optional[Corpus],
    corpus_error: Optional[str] = None,
) -> JSON:
    name = str(params.get("name", ""))
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}

    try:
        if name == "search":
            if corpus is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "error": corpus_error or "Corpus unavailable"}, is_error=True),
                }
            q = str(args.get("query", "")).strip()
            limit = max(1, min(20, int(args.get("limit", 5) or 5)))
            if not q:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": "Missing query"}, is_error=True),
                }
            matches = corpus.search_chunks(q, limit=limit)
            payload = {
                "ok": True,
                "query": q,
                "count": len(matches),
                "results": [format_doc_result(s, d) for s, d in matches],
            }
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "get_page":
            if corpus is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "error": corpus_error or "Corpus unavailable"}, is_error=True),
                }
            page_id = str(args.get("page_id", "")).strip()
            resolved = corpus.resolve_page_id(page_id)
            if resolved is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": f"Page not found: {page_id}"}, is_error=True),
                }
            row = corpus.pages[resolved]
            md = corpus.page_markdown(resolved)
            payload = {
                "ok": True,
                "page_id": row.get("page_id"),
                "title": row.get("title"),
                "url": row.get("url"),
                "oldid": row.get("oldid"),
                "dataset": row.get("dataset"),
                "sections": row.get("sections", []),
                "links": row.get("links", []),
                "images": row.get("images", []),
                "markdown": md,
            }
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "query_reference":
            if corpus is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "error": corpus_error or "Corpus unavailable"}, is_error=True),
                }
            q = str(args.get("query", "")).strip()
            limit = max(1, min(20, int(args.get("limit", 5) or 5)))
            if not q:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": "Missing query"}, is_error=True),
                }
            matches = corpus.search_references(q, limit=limit)
            payload = {
                "ok": True,
                "query": q,
                "count": len(matches),
                "results": [
                    {
                        "score": round(s, 4),
                        "page_id": d.get("page_id"),
                        "title": d.get("title"),
                        "url": d.get("url"),
                        "oldid": d.get("oldid"),
                        "dataset": d.get("dataset"),
                        "sections": d.get("sections", []),
                    }
                    for s, d in matches
                ],
            }
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "get_snippets":
            if corpus is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "error": corpus_error or "Corpus unavailable"}, is_error=True),
                }
            q = str(args.get("query", "")).strip()
            limit = max(1, min(20, int(args.get("limit", 3) or 3)))
            if not q:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": "Missing query"}, is_error=True),
                }
            if not corpus.has_snippets:
                payload = {"ok": False, "message": "No snippets extracted from markdown"}
            else:
                matches = corpus.search_snippets(q, limit=limit)
                payload = {
                    "ok": True,
                    "query": q,
                    "count": len(matches),
                    "results": [
                        {
                            "score": round(s, 4),
                            "snippet_id": d.get("snippet_id"),
                            "page_id": d.get("page_id"),
                            "title": d.get("title"),
                            "url": d.get("url"),
                            "language": d.get("language"),
                            "dataset": d.get("dataset"),
                            "code": d.get("text"),
                        }
                        for s, d in matches
                    ],
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        return None
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": text_result({"ok": False, "error": str(exc)}, is_error=True),
        }


def handle_request(
    message: JSON,
    corpus: Optional[Corpus],
    corpus_error: Optional[str] = None,
    extra_tools_catalog: Optional[List[JSON]] = None,
    extra_tools_handler=None,
    server_name: str = "wiki-mcp",
    server_version: Optional[str] = None,
    server_instructions: Optional[str] = None,
) -> Optional[JSON]:
    global SHOULD_EXIT
    if not isinstance(message, dict):
        return None

    method = str(message.get("method", ""))
    req_id = message.get("id")
    params = message.get("params")
    if not isinstance(params, dict):
        params = {}

    if method == "notifications/initialized":
        return None
    if method == "exit":
        SHOULD_EXIT = True
        return None
    if method == "initialize":
        return handle_initialize(req_id, params, server_name=server_name, server_version=server_version, server_instructions=server_instructions)
    if method == "shutdown":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}}
    if method == "resources/list":
        if corpus is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32001, "message": corpus_error or "Corpus unavailable"},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resource_catalog(corpus)}}
    if method == "resources/templates/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resourceTemplates": resource_templates_catalog()}}
    if method == "resources/read":
        if corpus is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32001, "message": corpus_error or "Corpus unavailable"},
            }
        return handle_resources_read(req_id, params, corpus)
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_catalog() + (extra_tools_catalog or [])}}
    if method == "tools/call":
        result = handle_tools_call(req_id, params, corpus, corpus_error=corpus_error)
        if result is not None:
            return result
        if extra_tools_handler is not None:
            result = extra_tools_handler(req_id, params)
            if result is not None:
                return result
        name = params.get("name", "")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": f"Unknown tool: {name}"},
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if req_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def read_message() -> Optional[object]:
    """Read one stdio message.

    Supports both MCP Content-Length framing and newline-delimited JSON.
    """

    def read_content_length_payload(first_line: bytes) -> Optional[object]:
        content_length: Optional[int] = None
        line = first_line
        while True:
            if line in (b"\r\n", b"\n"):
                break

            header = line.decode("utf-8", errors="replace").strip()
            if header.lower().startswith("content-length:"):
                try:
                    content_length = int(header.split(":", 1)[1].strip())
                except ValueError:
                    return None

            line = sys.stdin.buffer.readline()
            if not line:
                return None

        if content_length is None:
            return None

        payload = sys.stdin.buffer.read(content_length)
        if not payload:
            return None
        return json.loads(payload.decode("utf-8"))

    def read_json_lines(first_line: bytes) -> Optional[object]:
        payload = bytearray(first_line)
        while True:
            text = payload.decode("utf-8", errors="replace").strip()
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            payload.extend(line)

    def looks_like_header_line(line: bytes) -> bool:
        return re.match(rb"^[A-Za-z][A-Za-z0-9-]*\s*:", line) is not None

    while True:
        first_line = sys.stdin.buffer.readline()
        if not first_line:
            return None
        if first_line in (b"\r\n", b"\n"):
            continue

        stripped = first_line.lstrip(b"\xef\xbb\xbf\x1e \t")
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            global LAST_INPUT_TRANSPORT
            LAST_INPUT_TRANSPORT = "ndjson"
            debug_log("Detected ndjson input transport")
            return read_json_lines(stripped)

        if looks_like_header_line(first_line):
            LAST_INPUT_TRANSPORT = "framed"
            debug_log("Detected framed input transport")
            return read_content_length_payload(first_line)

        LAST_INPUT_TRANSPORT = "ndjson"
        debug_log("Detected ndjson-ish input transport")
        return read_json_lines(first_line)


def send_message(message: object) -> None:
    data = json.dumps(message, ensure_ascii=False)
    if LAST_INPUT_TRANSPORT == "ndjson":
        sys.stdout.buffer.write((data + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
        debug_log("Sent ndjson response")
        return

    payload = data.encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    debug_log("Sent framed response")


def main() -> None:
    parser = argparse.ArgumentParser(description="wiki-mcp: generic MediaWiki MCP server")
    parser.add_argument(
        "--data-dir",
        action="append",
        required=True,
        help="Path to dataset directory (repeatable: --data-dir wiki-a --data-dir wiki-b)",
    )
    parser.add_argument("--version", action="version", version=f"wiki-mcp {__version__}")
    args = parser.parse_args()

    # Flatten: each --data-dir value is a single string
    data_dirs = [Path(d) for d in args.data_dir]

    corpus: Optional[Corpus] = None
    corpus_error: Optional[str] = None

    try:
        corpus = Corpus(data_dirs)
    except Exception as exc:
        corpus_error = str(exc)
        debug_log(f"Corpus init failed: {corpus_error}")

    if debug_enabled():
        if corpus is not None:
            debug_log(
                f"Loaded datasets={corpus.dataset_names} "
                f"chunks={len(corpus.chunks)} pages={len(corpus.pages)} snippets={len(corpus.snippets)}"
            )
        else:
            debug_log(f"Corpus unavailable: {corpus_error}")

    try:
        while True:
            msg = read_message()
            if msg is None:
                debug_log("read_message returned None; exiting loop")
                break
            if isinstance(msg, list):
                responses: List[JSON] = []
                for item in msg:
                    if not isinstance(item, dict):
                        continue
                    resp = handle_request(item, corpus, corpus_error=corpus_error)
                    if resp is not None:
                        responses.append(resp)
                    if SHOULD_EXIT:
                        break
                if responses:
                    send_message(responses)
                if SHOULD_EXIT:
                    debug_log("Received exit notification; exiting loop")
                    break
                continue

            if not isinstance(msg, dict):
                continue
            method = str(msg.get("method", ""))
            debug_log(f"Received method={method}")
            resp = handle_request(msg, corpus, corpus_error=corpus_error)
            if resp is not None:
                if method == "initialize":
                    debug_log(f"Sending initialize response: {json.dumps(resp, ensure_ascii=False)}")
                send_message(resp)
            if SHOULD_EXIT:
                debug_log("Received exit notification; exiting loop")
                break
    except Exception as exc:
        debug_log(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
