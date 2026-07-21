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
REFERENCE_CONTENT_CHARS = 16000
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


def bounded_unique_chunk_text(chunks: List[JSON], limit: int = REFERENCE_CONTENT_CHARS) -> str:
    token_groups: List[List[str]] = []
    for chunk in chunks:
        value = chunk.get("text")
        text = value if isinstance(value, str) else ""
        tokens = list(dict.fromkeys(tokenize(text)))
        if tokens:
            token_groups.append(tokens)

    positions = [0] * len(token_groups)
    terms: List[str] = []
    seen_terms: set[str] = set()
    length = 0
    while any(position < len(group) for position, group in zip(positions, token_groups)):
        for index, group in enumerate(token_groups):
            if positions[index] >= len(group):
                continue
            term = group[positions[index]]
            positions[index] += 1
            if term in seen_terms:
                continue
            additional = len(term) + (1 if terms else 0)
            if length + additional > limit:
                continue
            terms.append(term)
            seen_terms.add(term)
            length += additional
    return " ".join(terms)


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
    def __init__(self, data_dirs: List[Path], *, allow_legacy_primary_manifest: bool = False) -> None:
        self.chunks: List[JSON] = []
        self.pages: Dict[str, JSON] = {}
        self.chunks_by_id: Dict[str, JSON] = {}
        self.chunks_by_page_id: Dict[str, List[JSON]] = {}
        self.reference_docs: List[JSON] = []
        self.snippets: List[JSON] = []
        self.dataset_names: List[str] = []
        self.single_dataset = len(data_dirs) == 1

        # All loaded records share one index so BM25 scores are comparable.
        self._chunk_indexes: List[HybridIndex] = []
        self._ref_indexes: List[HybridIndex] = []
        self._snippet_indexes: List[HybridIndex] = []

        seen_dataset_names: set[str] = set()
        for index, data_dir in enumerate(data_dirs):
            manifest, legacy_manifest = self._load_manifest(
                data_dir,
                allow_legacy=allow_legacy_primary_manifest and index == 0,
            )
            dataset_name = str(manifest["name"])
            if dataset_name in seen_dataset_names:
                raise ValueError(f"duplicate dataset name: {dataset_name}")
            self._load_dataset(
                data_dir,
                dataset_name,
                manifest,
                validate_declared_counts=not legacy_manifest,
            )
            seen_dataset_names.add(dataset_name)
            self.dataset_names.append(dataset_name)

        self._chunk_indexes.append(HybridIndex(self.chunks, text_key="text"))
        self._ref_indexes.append(HybridIndex(self.reference_docs, text_key="text"))
        self._snippet_indexes.append(
            HybridIndex(self.snippets, text_key="text") if self.snippets else None  # type: ignore[arg-type]
        )

    @staticmethod
    def _load_manifest(data_dir: Path, *, allow_legacy: bool = False) -> Tuple[JSON, bool]:
        manifest_path = data_dir / "manifest.json"
        if not manifest_path.is_file():
            if allow_legacy:
                return {"name": data_dir.name, "dataset": data_dir.name}, True
            raise ValueError(f"Missing dataset manifest: {manifest_path}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Invalid dataset manifest: {manifest_path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise ValueError(f"Invalid dataset manifest: {manifest_path}: top level must be an object")

        if allow_legacy and set(manifest) == {"name"}:
            legacy_name = manifest.get("name")
            if isinstance(legacy_name, str) and legacy_name.strip():
                return {"name": legacy_name.strip(), "dataset": legacy_name.strip()}, True

        name = manifest.get("name")
        dataset = manifest.get("dataset")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(dataset, str)
            or name != dataset
        ):
            raise ValueError(
                f"Invalid dataset manifest: {manifest_path}: manifest name and dataset must match exactly"
            )
        if ":" in name or any(character.isspace() for character in name):
            raise ValueError(f"Invalid dataset manifest: {manifest_path}: dataset name cannot contain spaces or ':'")
        for count_key in ("page_count", "chunk_count"):
            count = manifest.get(count_key)
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError(f"Invalid dataset manifest: {manifest_path}: {count_key} must be a non-negative integer")
        if name == "cities2-research":
            report_count = manifest.get("report_count")
            if isinstance(report_count, bool) or not isinstance(report_count, int) or report_count < 1:
                raise ValueError(
                    f"Invalid dataset manifest: {manifest_path}: report_count must be a positive integer"
                )
            if report_count != manifest["page_count"]:
                raise ValueError(
                    f"Invalid dataset manifest: {manifest_path}: report_count must equal page_count"
                )
            if manifest["chunk_count"] < 1:
                raise ValueError(
                    f"Invalid dataset manifest: {manifest_path}: cities2-research chunk_count must be positive"
                )
        paths = manifest.get("paths")
        expected_paths = {"pages_jsonl": "index/pages.jsonl", "chunks_jsonl": "index/chunks.jsonl"}
        if not isinstance(paths, dict) or any(paths.get(key) != value for key, value in expected_paths.items()):
            raise ValueError(f"Invalid dataset manifest: {manifest_path}: paths must identify the canonical JSONL indexes")
        return manifest, False

    def _load_dataset(
        self,
        data_dir: Path,
        dataset_name: str,
        manifest: JSON,
        *,
        validate_declared_counts: bool,
    ) -> None:
        chunks_path = data_dir / "index" / "chunks.jsonl"
        pages_path = data_dir / "index" / "pages.jsonl"

        if not chunks_path.exists():
            raise FileNotFoundError(f"Missing chunks index: {chunks_path}")
        if not pages_path.exists():
            raise FileNotFoundError(f"Missing pages index: {pages_path}")

        dataset_chunks: List[JSON] = []
        dataset_pages: Dict[str, JSON] = {}
        dataset_chunk_ids: set[str] = set()
        dataset_page_ids: set[str] = set()

        with chunks_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError(f"Invalid chunk record at {chunks_path}:{line_number}: expected an object")
                    # Prefix chunk_id and page_id with dataset name
                    raw_chunk_id = row.get("chunk_id")
                    raw_page_id = row.get("page_id")
                    if (
                        not isinstance(raw_chunk_id, str)
                        or not raw_chunk_id
                        or raw_chunk_id != raw_chunk_id.strip()
                        or ":" in raw_chunk_id
                    ):
                        raise ValueError(
                            f"Invalid chunk record at {chunks_path}:{line_number}: "
                            "chunk_id is required and must be a canonical nonempty string without ':'"
                        )
                    if (
                        not isinstance(raw_page_id, str)
                        or not raw_page_id
                        or raw_page_id != raw_page_id.strip()
                        or ":" in raw_page_id
                    ):
                        raise ValueError(
                            f"Invalid chunk record at {chunks_path}:{line_number}: "
                            "page_id is required and must be a canonical nonempty string without ':'"
                        )
                    orig_chunk_id = raw_chunk_id
                    orig_page_id = raw_page_id
                    declared_dataset = row.get("dataset")
                    if declared_dataset not in (None, "", dataset_name):
                        raise ValueError(
                            f"Invalid chunk record at {chunks_path}:{line_number}: "
                            "dataset does not match manifest"
                        )
                    qualified_chunk_id = f"{dataset_name}:{orig_chunk_id}"
                    qualified_page_id = f"{dataset_name}:{orig_page_id}"
                    if qualified_chunk_id in dataset_chunk_ids or qualified_chunk_id in self.chunks_by_id:
                        raise ValueError(f"duplicate qualified chunk_id: {qualified_chunk_id}")
                    dataset_chunk_ids.add(qualified_chunk_id)
                    row["chunk_id"] = qualified_chunk_id
                    row["page_id"] = qualified_page_id
                    row["dataset"] = dataset_name
                    self.chunks.append(row)
                    dataset_chunks.append(row)
                    self.chunks_by_id[row["chunk_id"]] = row
                    self.chunks_by_page_id.setdefault(row["page_id"], []).append(row)

        with pages_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"Invalid page record at {pages_path}:{line_number}: expected an object")
                raw_page_id = row.get("page_id")
                if (
                    not isinstance(raw_page_id, str)
                    or not raw_page_id
                    or raw_page_id != raw_page_id.strip()
                    or ":" in raw_page_id
                ):
                    raise ValueError(
                        f"Invalid page record at {pages_path}:{line_number}: "
                        "page_id is required and must be a canonical nonempty string without ':'"
                    )
                orig_page_id = raw_page_id
                declared_dataset = row.get("dataset")
                if declared_dataset not in (None, "", dataset_name):
                    raise ValueError(
                        f"Invalid page record at {pages_path}:{line_number}: dataset does not match manifest"
                    )
                prefixed_id = f"{dataset_name}:{orig_page_id}"
                if prefixed_id in dataset_page_ids or prefixed_id in self.pages:
                    raise ValueError(f"duplicate qualified page_id: {prefixed_id}")
                dataset_page_ids.add(prefixed_id)
                row["page_id"] = prefixed_id
                row["dataset"] = dataset_name
                row["_data_dir"] = str(data_dir.resolve())
                if orig_page_id and not row.get("markdown_path"):
                    row["_markdown_path"] = str(Path("pages") / "markdown" / f"{orig_page_id}.md")
                self.pages[prefixed_id] = row
                dataset_pages[prefixed_id] = row

        if validate_declared_counts and len(dataset_pages) != manifest["page_count"]:
            raise ValueError(
                f"Invalid dataset manifest: {data_dir / 'manifest.json'}: page_count declares {manifest['page_count']} but loaded {len(dataset_pages)}"
            )
        if validate_declared_counts and len(dataset_chunks) != manifest["chunk_count"]:
            raise ValueError(
                f"Invalid dataset manifest: {data_dir / 'manifest.json'}: chunk_count declares {manifest['chunk_count']} but loaded {len(dataset_chunks)}"
            )
        missing_pages = sorted(
            str(chunk["page_id"]) for chunk in dataset_chunks if str(chunk["page_id"]) not in dataset_pages
        )
        if missing_pages:
            raise ValueError(f"Chunk records reference missing pages: {', '.join(missing_pages[:3])}")

        for p in dataset_pages.values():
            sections = p.get("sections", []) or []
            page_content = bounded_unique_chunk_text(
                self.chunks_by_page_id.get(str(p.get("page_id", "")), [])
            )
            text = "\n".join(
                [
                    str(p.get("title", "")),
                    str(p.get("url", "")),
                    *[str(x) for x in sections],
                    *[str(value) for value in provenance_fields(p).values()],
                    page_content,
                ]
            )
            ref_doc = {
                "page_id": p.get("page_id"),
                "title": p.get("title"),
                "url": p.get("url"),
                "oldid": p.get("oldid"),
                "text": text,
                "sections": sections,
                "dataset": dataset_name,
                **provenance_fields(p),
            }
            self.reference_docs.append(ref_doc)

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

    def _fan_out_search(
        self, indexes: List[Optional[HybridIndex]], query: str, limit: int, title_key: Optional[str] = "title"
    ) -> List[Tuple[float, JSON]]:
        """Search the shared corpus index and return globally comparable scores."""
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
        """Resolve a page_id, accepting bare IDs only when they are unique across datasets.

        Qualified 'dataset:page-id' values always work. Bare 'page-id' values are accepted when exactly one loaded dataset owns them and require qualification on collision.
        """
        # Direct lookup first (works for qualified IDs)
        if page_id in self.pages:
            return page_id

        suffix = f":{page_id}"
        matches = [candidate for candidate in self.pages if candidate.endswith(suffix)]
        if len(matches) == 1:
            return matches[0]
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
            **provenance_fields(row),
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
        **provenance_fields(doc),
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
                **provenance_fields(row),
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
                        **provenance_fields(d),
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
