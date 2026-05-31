#!/usr/bin/env python3
"""Cities2-MCP — game knowledge and modding tools for Cities: Skylines II.

Combines internal wiki retrieval with Cities2 mod project workflow tools.
Transport: stdio with Content-Length framing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote

from .build_runner import BuildRunner
from .game_encyclopedia import (
    GAME_ENCYCLOPEDIA_WARNING,
    EncyclopediaConfig,
    GameEncyclopediaSource,
)
from .project_analyzer import ProjectAnalyzer
from .project_scaffold import ProjectScaffolder
from .retrieval.mcp_server import (
    Corpus,
    debug_enabled,
    debug_log,
    handle_request as retrieval_handle_request,
    read_message,
    send_message,
    text_result,
)
from .retrieval import mcp_server as retrieval_impl

__version__ = "0.1.9"
JSON = Dict[str, Any]
SERVER_NAME = "Cities2-MCP — game knowledge and modding tools for Cities: Skylines II"
SERVER_INSTRUCTIONS = (
    "Cities2-MCP gives AI assistants local access to the bundled Cities: Skylines II Wiki corpus "
    "for gameplay, systems, and modding questions. It also includes local workflow tools for CS2 "
    "mod projects: scaffolding, reading and writing project files, static analysis, building, "
    "and packaging. Use the wiki retrieval tools for game knowledge "
    "and reference lookups; use the workflow tools only inside configured local workspaces."
)
DOCS_GUARD_CODE = "DOCS_INDEX_MISSING_OR_MISCONFIGURED"
DOCS_GUARD_HEADLINE = "Cities2 docs are not available for this session"
DOCS_TOOL_NAMES = {"search", "query_reference", "get_page", "get_snippets"}
retrieval_resource_catalog = retrieval_impl.resource_catalog
retrieval_handle_resources_read = retrieval_impl.handle_resources_read


def bundled_data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def docs_guard_payload(corpus_error: Optional[str], docs_paths: Optional[Dict[str, str]]) -> JSON:
    paths = docs_paths or {}
    return {
        "ok": False,
        "code": DOCS_GUARD_CODE,
        "headline": DOCS_GUARD_HEADLINE,
        "error": corpus_error or "Corpus unavailable",
        "configured_paths": {
            "chunks": str(paths.get("chunks", "")),
            "pages": str(paths.get("pages", "")),
        },
        "next_step": (
            "STOP and ask the user whether to fix the MCP config, rebuild or restore the docs corpus, "
            "or continue without docs."
        ),
    }


def docs_guard_tool_result(corpus_error: Optional[str], docs_paths: Optional[Dict[str, str]]) -> JSON:
    return text_result(docs_guard_payload(corpus_error, docs_paths), is_error=True)


def docs_guard_rpc_error(req_id: object, corpus_error: Optional[str], docs_paths: Optional[Dict[str, str]]) -> JSON:
    payload = docs_guard_payload(corpus_error, docs_paths)
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32001,
            "message": DOCS_GUARD_HEADLINE,
            "data": payload,
        },
    }


# ---------------------------------------------------------------------------
# Workflow manager
# ---------------------------------------------------------------------------


class WorkflowManager:
    def __init__(
        self,
        workspaces: List[Path],
        mods_dir: Path,
        *,
        installed_game_version: Optional[str] = None,
        installed_game_version_source: Optional[str] = None,
        installed_steam_build_id: Optional[str] = None,
        installed_steam_build_id_source: Optional[str] = None,
    ) -> None:
        if not workspaces:
            raise ValueError("At least one workspace must be configured")
        self.workspaces = [workspace.resolve() for workspace in workspaces]
        self.workspace = self.workspaces[0]
        self.mods_dir = mods_dir.expanduser().resolve()
        self.scaffolder = ProjectScaffolder(
            self.workspace,
            additional_workspaces=self.workspaces[1:],
            installed_game_version=installed_game_version,
            installed_game_version_source=installed_game_version_source,
            installed_steam_build_id=installed_steam_build_id,
            installed_steam_build_id_source=installed_steam_build_id_source,
        )
        self.builder = BuildRunner(self.scaffolder)
        self.analyzer = ProjectAnalyzer(self.scaffolder)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_dict(value: object) -> JSON:
    return value if isinstance(value, dict) else {}


def _as_str_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(x) for x in value]


def _configured_path_value(value: object) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.startswith("${") and text.endswith("}"):
        return None
    return text


def default_mods_dir() -> Path:
    env = _configured_path_value(os.environ.get("CITIES2_MODS_DIR"))
    if env:
        return Path(env).expanduser()
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return (
                PureWindowsPath(os.path.expanduser(local_appdata)).parent
                / "LocalLow"
                / "Colossal Order"
                / "Cities Skylines II"
                / "Mods"
            )
        return (
            Path.home()
            / "AppData"
            / "LocalLow"
            / "Colossal Order"
            / "Cities Skylines II"
            / "Mods"
        )
    if sys.platform.startswith("linux"):
        return (
            Path.home()
            / ".local"
            / "share"
            / "Colossal Order"
            / "Cities Skylines II"
            / "Mods"
        )
    return (
        Path.home()
        / "Library/Application Support/Colossal Order/Cities Skylines II/Mods"
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_checkout_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_data_dir(value: str) -> Path:
    configured = Path(value).expanduser()
    if configured.exists():
        return configured
    checkout_data = source_checkout_root() / "data"
    if configured.resolve() == checkout_data.resolve():
        return bundled_data_dir()
    return configured


def installed_game_context(encyclopedia: Optional[GameEncyclopediaSource]) -> JSON:
    game_version = os.environ.get("CITIES2_GAME_VERSION", "").strip()
    steam_build_id = os.environ.get("CITIES2_STEAM_BUILD_ID", "").strip()
    context = {
        "installed_game_version": game_version or None,
        "installed_game_version_source": "CITIES2_GAME_VERSION" if game_version else None,
        "installed_steam_build_id": steam_build_id or None,
        "installed_steam_build_id_source": "CITIES2_STEAM_BUILD_ID" if steam_build_id else None,
    }

    discovery = getattr(encyclopedia, "discovery", None)
    discovered_build_id = str(getattr(discovery, "steam_build_id", "") or "").strip()
    if discovered_build_id and not steam_build_id:
        context["installed_steam_build_id"] = discovered_build_id
        context["installed_steam_build_id_source"] = "steam"
    return context


class UnavailableGameEncyclopedia:
    available = False
    entries: List[JSON] = []
    discovery = None

    def __init__(self, message: str, *, cache_status: str = "error") -> None:
        self.message = message
        self.cache_status = cache_status

    def status(self) -> JSON:
        return {
            "source": "game_encyclopedia",
            "available": False,
            "warning": self.message,
            "error": self.message,
            "cache_status": self.cache_status,
            "entry_count": 0,
        }

    def search(self, query: str, *, limit: int = 5) -> List[JSON]:
        return []

    def get_entry(self, entry_id: str) -> Optional[JSON]:
        return None


WORKFLOW_TOOL_NAMES = {
    "scaffold_project",
    "write_project_file",
    "list_project_tree",
    "build_project",
    "analyze_project",
    "package_project",
}

# ---------------------------------------------------------------------------
# Domain tools catalog
# ---------------------------------------------------------------------------


def domain_tools_catalog() -> List[JSON]:
    return [
        {
            "name": "scaffold_project",
            "description": "Scaffold a Cities: Skylines II mod project from a template.",
            "annotations": {
                "title": "Scaffold Mod Project",
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "template": {
                        "type": "string",
                        "enum": ["cities2-csharp", "cities2-ui", "cities2-hybrid"],
                    },
                    "target_dir": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "mod_id": {"type": "string"},
                            "display_name": {"type": "string"},
                            "short_description": {"type": "string"},
                            "game_version": {"type": "string"},
                            "github_url": {"type": "string"},
                            "forum_url": {"type": "string"},
                            "version": {"type": "string"},
                        },
                    },
                    "options": {
                        "type": "object",
                        "properties": {
                            "include_settings": {"type": "boolean", "default": True},
                            "include_localization": {"type": "boolean", "default": True},
                            "include_harmony": {"type": "boolean", "default": True},
                            "include_ui_pipeline": {
                                "type": ["boolean", "string"],
                                "default": "auto",
                            },
                            "include_changelog": {"type": "boolean", "default": True},
                        },
                    },
                },
                "required": ["name", "template"],
            },
        },
        {
            "name": "write_project_file",
            "description": "Write files inside a configured Cities: Skylines II mod project workspace.",
            "annotations": {
                "title": "Write Project File",
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": False,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "relative_path": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {
                        "type": "string",
                        "enum": ["create", "replace", "upsert"],
                        "default": "upsert",
                    },
                },
                "required": ["project_dir", "relative_path", "content"],
            },
        },
        {
            "name": "list_project_tree",
            "description": "List files in a configured Cities: Skylines II mod project workspace.",
            "annotations": {
                "title": "List Project Tree",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "glob": {"type": "string", "default": "**/*"},
                    "include_hidden": {"type": "boolean", "default": False},
                    "max_files": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10000,
                        "default": 2000,
                    },
                },
                "required": ["project_dir"],
            },
        },
        {
            "name": "build_project",
            "description": (
                "Build a Cities: Skylines II mod project and return normalized diagnostics. "
                "This executes trusted workspace code; do not use it for arbitrary untrusted repositories."
            ),
            "annotations": {
                "title": "Build Mod Project",
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "profile": {
                        "type": "string",
                        "enum": ["debug", "release"],
                        "default": "release",
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["ui", "dotnet", "package"],
                        },
                    },
                    "clean": {"type": "boolean", "default": False},
                    "package": {"type": "boolean", "default": False},
                    "timeout_sec": {
                        "type": "integer",
                        "minimum": 10,
                        "maximum": 3600,
                        "default": 300,
                    },
                },
                "required": ["project_dir"],
            },
        },
        {
            "name": "analyze_project",
            "description": "Run static checks for Cities: Skylines II mod project structure and lifecycle patterns.",
            "annotations": {
                "title": "Analyze Mod Project",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "profile": {
                        "type": "string",
                        "enum": ["auto", "cities2-csharp", "cities2-ui", "cities2-hybrid"],
                        "default": "auto",
                    },
                    "strict": {"type": "boolean", "default": True},
                },
                "required": ["project_dir"],
            },
        },
        {
            "name": "package_project",
            "description": "Create a zip package for a Cities: Skylines II mod project.",
            "annotations": {
                "title": "Package Mod Project",
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": False,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "package_name": {"type": "string"},
                    "exclude_globs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["project_dir"],
            },
        },
    ]


def encyclopedia_tools_catalog() -> List[JSON]:
    return [
        {
            "name": "search_encyclopedia",
                "description": "Search the local Cities: Skylines II in-game encyclopedia read from the user's installed game files.",
            "annotations": {
                    "title": "Search game encyclopedia",
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
            "name": "get_encyclopedia_entry",
                "description": "Return one local Cities: Skylines II in-game encyclopedia entry by entry_id.",
            "annotations": {
                    "title": "Get encyclopedia entry",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "properties": {"entry_id": {"type": "string"}},
                "required": ["entry_id"],
            },
        },
        {
            "name": "source_status",
            "description": "Report Cities2-MCP source availability for the wiki corpus and local game encyclopedia.",
            "annotations": {
                "title": "Check Source Status",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def extra_tools_catalog() -> List[JSON]:
    return domain_tools_catalog() + encyclopedia_tools_catalog()


PROMPT_ARGUMENTS = [
    {
        "name": "question",
        "description": "The Cities: Skylines II question or task to answer.",
        "required": True,
    }
]


PROMPT_DEFINITIONS: Dict[str, JSON] = {
    "cities2": {
            "description": "Answer Cities: Skylines II questions using both the bundled wiki corpus and the local game encyclopedia when available.",
        "tool_guidance": (
            "Use source_status() first. Search both sources when they are available: use search/query_reference/get_page "
            "for the bundled Cities: Skylines II Wiki corpus, and search_encyclopedia/get_encyclopedia_entry for the "
            "local in-game encyclopedia. Prefer the local game encyclopedia for current in-game terminology and exact "
            "mechanics, and use the wiki for broader explanations, guide context, tables, and modding background. "
            "If the sources disagree, say so plainly and identify which source says what."
        ),
    },
    "cities2-wiki": {
        "description": "Answer using only the bundled Cities: Skylines II Wiki corpus.",
        "tool_guidance": (
            "Use only the bundled wiki corpus tools: search, query_reference, get_page, and get_snippets when relevant. "
            "Do not use search_encyclopedia or get_encyclopedia_entry. Search first, fetch the most relevant full page "
            "with get_page when a snippet is not enough, then answer from the wiki material with page/source labels."
        ),
    },
    "cities2-encyclopedia": {
            "description": "Answer using only the local in-game encyclopedia read from the user's installed game files.",
        "tool_guidance": (
            "Use source_status() first and check game_encyclopedia.available. If it is unavailable, explain that the "
            "local game encyclopedia was not found and mention CITIES2_GAME_DIR or CITIES2_LOCALE_COK. If available, "
            "use search_encyclopedia, then get_encyclopedia_entry for the best entries before answering. Do not use "
            "the wiki tools unless the user explicitly asks for fallback."
        ),
    },
    "cities2-modding": {
        "description": "Answer Cities: Skylines II modding questions using docs and local mod project workflow tools.",
        "tool_guidance": (
            "Use wiki retrieval tools for modding concepts, APIs, localization, UI, project structure, and toolchain "
            "references. Use workflow tools only for explicit local project actions inside configured workspaces: "
            "scaffold_project, write_project_file, list_project_tree, build_project, analyze_project, package_project, "
            "and manual playtesting handoff steps. build_project executes trusted workspace code; do not run it for "
            "arbitrary untrusted repositories. Before writing files or running builds, make the intended local action clear."
        ),
    },
}


UPDATE_QUERY_MARKERS = (
    "latest patch",
    "latest update",
    "what's new",
    "what is new",
    "what changed",
    "patch notes",
    "new patch",
    "recent patch",
    "recent update",
    "game update",
    "known issue",
    "known issues",
    "morning dew",
)


LATEST_PATCH_GUIDANCE = (
    "\n\nLatest patch/update workflow:\n"
    "Use source_status() first. For latest/current patch questions, do not answer from the first broad search result "
    "alone. Search or fetch Main Page/news and Patches to identify the newest listed version, then fetch the exact "
    "patch-family page. When Patches indicates the latest release is in Patch 1.5.X, use get_page(\"patch-1-5-x\") "
    "and inspect the exact version section before summarizing. If a page lists newer versions than the section you "
    "first read, follow the newer version instead of stopping at older notes such as 1.5.7f1."
)


def is_update_question(question: str) -> bool:
    normalized = question.casefold()
    return any(marker in normalized for marker in UPDATE_QUERY_MARKERS)


def prompts_catalog() -> List[JSON]:
    return [
        {
            "name": name,
            "description": str(definition["description"]),
            "arguments": PROMPT_ARGUMENTS,
        }
        for name, definition in PROMPT_DEFINITIONS.items()
    ]


def prompt_text(name: str, question: str) -> str:
    definition = PROMPT_DEFINITIONS[name]
    tool_guidance = str(definition["tool_guidance"])
    if name in {"cities2", "cities2-wiki", "cities2-modding"} and is_update_question(question):
        tool_guidance += LATEST_PATCH_GUIDANCE

    return (
        f"You are answering a Cities: Skylines II request through Cities2-MCP.\n\n"
        f"Mode: /{name}\n"
        f"User question: {question}\n\n"
        f"Source workflow:\n{tool_guidance}\n\n"
        "Answer normally and synthesize the retrieved material instead of showing raw search results. "
        "Use concise source labels such as wiki, game encyclopedia, or mod project tools when they matter. "
        "If there is not enough retrieved evidence, say what is missing rather than guessing."
    )


def handle_prompts_get(req_id: object, params: JSON) -> JSON:
    name = str(params.get("name", "")).strip()
    if name not in PROMPT_DEFINITIONS:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": f"Unknown prompt: {name}"},
        }

    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        arguments = {}
    question = str(arguments.get("question", "")).strip()
    if not question:
        question = "Answer the user's Cities: Skylines II question using this source workflow."

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "description": str(PROMPT_DEFINITIONS[name]["description"]),
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": prompt_text(name, question)},
                }
            ],
        },
    }


def encyclopedia_resource_catalog(encyclopedia: Optional[GameEncyclopediaSource]) -> List[JSON]:
    if encyclopedia is None or not encyclopedia.available:
        return []
    resources: List[JSON] = []
    for entry in encyclopedia.entries:
        entry_id = str(entry.get("entry_id", "")).strip()
        if not entry_id:
            continue
        resources.append(
            {
                "uri": f"cities2encyclopedia://entry/{quote(entry_id, safe='')}",
                "name": str(entry.get("title") or entry_id),
                "description": f"game encyclopedia entry: {entry_id}",
                "mimeType": "application/json",
            }
        )
    return resources


def handle_encyclopedia_resource_read(
    req_id: object,
    uri: str,
    encyclopedia: Optional[GameEncyclopediaSource],
) -> Optional[JSON]:
    prefix = "cities2encyclopedia://entry/"
    if not uri.startswith(prefix):
        return None
    if encyclopedia is None or not encyclopedia.available:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32001, "message": GAME_ENCYCLOPEDIA_WARNING},
        }
    entry_id = unquote(uri[len(prefix) :])
    entry = encyclopedia.get_entry(entry_id)
    if entry is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32002, "message": f"Entry not found: {entry_id}"},
        }
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(entry, ensure_ascii=False, indent=2),
                }
            ]
        },
    }


# ---------------------------------------------------------------------------
# Domain tools handler
# ---------------------------------------------------------------------------


def encyclopedia_unavailable_result(encyclopedia: Optional[GameEncyclopediaSource] = None) -> JSON:
    status = encyclopedia.status() if encyclopedia is not None else {}
    message = str(status.get("error") or status.get("warning") or GAME_ENCYCLOPEDIA_WARNING)
    return text_result({"ok": False, "message": message}, is_error=True)


def handle_encyclopedia_tools(
    req_id: object,
    params: JSON,
    *,
    corpus: Optional[Corpus],
    encyclopedia: Optional[GameEncyclopediaSource],
    corpus_error: Optional[str],
    docs_paths: Optional[Dict[str, str]],
) -> Optional[JSON]:
    try:
        name = str(params.get("name", ""))
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}

        if name == "source_status":
            wiki_status = {
                "source": "wiki",
                "available": corpus is not None,
                "error": corpus_error or "",
                "configured_paths": docs_paths or {},
            }
            game_status = (
                encyclopedia.status()
                if encyclopedia is not None
                else {
                    "source": "game_encyclopedia",
                    "available": False,
                    "warning": GAME_ENCYCLOPEDIA_WARNING,
                    "cache_status": "unavailable",
                    "entry_count": 0,
                }
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": text_result({"wiki": wiki_status, "game_encyclopedia": game_status}),
            }

        if name == "search_encyclopedia":
            if encyclopedia is None or not encyclopedia.available:
                return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result(encyclopedia)}
            query = str(args.get("query", "")).strip()
            limit = max(1, min(20, int(args.get("limit", 5) or 5)))
            if not query:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": "Missing query"}, is_error=True),
                }
            results = encyclopedia.search(query, limit=limit)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": text_result({"ok": True, "query": query, "count": len(results), "results": results}),
            }

        if name == "get_encyclopedia_entry":
            if encyclopedia is None or not encyclopedia.available:
                return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result(encyclopedia)}
            entry_id = str(args.get("entry_id", "")).strip()
            entry = encyclopedia.get_entry(entry_id)
            if entry is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": text_result({"ok": False, "message": f"Entry not found: {entry_id}"}, is_error=True),
                }
            payload = dict(entry)
            payload["ok"] = True
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        return None
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": text_result({"ok": False, "error": str(exc)}, is_error=True),
        }


def handle_domain_tools(
    req_id: object,
    params: JSON,
    wm: Optional[WorkflowManager] = None,
    workflow_error: Optional[str] = None,
) -> Optional[JSON]:
    """Handle the Cities2 domain tools. Returns None for unknown tool names."""
    name = str(params.get("name", ""))
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        args = {}

    if name not in WORKFLOW_TOOL_NAMES:
        return None

    try:
        if wm is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": text_result(
                    {"ok": False, "error": workflow_error or "Workflow unavailable"},
                    is_error=True,
                ),
            }

        if name == "scaffold_project":
            payload = wm.scaffolder.scaffold_project(
                name=str(args.get("name", "")).strip(),
                template=str(args.get("template", "")).strip(),
                target_dir=str(args.get("target_dir", "")).strip() or None,
                metadata=_as_dict(args.get("metadata")),
                options=_as_dict(args.get("options")),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "write_project_file":
            payload = wm.scaffolder.write_project_file(
                project_dir=str(args.get("project_dir", "")),
                relative_path=str(args.get("relative_path", "")),
                content=str(args.get("content", "")),
                mode=str(args.get("mode", "upsert")).strip() or "upsert",
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "list_project_tree":
            payload = wm.scaffolder.list_project_tree(
                project_dir=str(args.get("project_dir", "")),
                glob=str(args.get("glob", "**/*")) or "**/*",
                include_hidden=bool(args.get("include_hidden", False)),
                max_files=int(args.get("max_files", 2000) or 2000),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "build_project":
            payload = wm.builder.build_project(
                project_dir=str(args.get("project_dir", "")),
                profile=str(args.get("profile", "release")).strip() or "release",
                steps=_as_str_list(args.get("steps")),
                clean=bool(args.get("clean", False)),
                package=bool(args.get("package", False)),
                timeout_sec=int(args.get("timeout_sec", 300) or 300),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "analyze_project":
            payload = wm.analyzer.analyze_project(
                project_dir=str(args.get("project_dir", "")),
                profile=str(args.get("profile", "auto")).strip() or "auto",
                strict=bool(args.get("strict", True)),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

        if name == "package_project":
            payload = wm.builder.package_project(
                project_dir=str(args.get("project_dir", "")),
                output_dir=str(args.get("output_dir", "")).strip() or None,
                package_name=str(args.get("package_name", "")).strip() or None,
                exclude_globs=_as_str_list(args.get("exclude_globs")),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": text_result(payload)}

    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": text_result({"ok": False, "error": str(exc)}, is_error=True),
        }

    return None


def handle_tools_call(
    req_id: object,
    params: JSON,
    corpus: Optional[Corpus],
    wm: Optional[WorkflowManager] = None,
    encyclopedia: Optional[GameEncyclopediaSource] = None,
    corpus_error: Optional[str] = None,
    workflow_error: Optional[str] = None,
    docs_paths: Optional[Dict[str, str]] = None,
) -> JSON:
    name = str(params.get("name", ""))
    if name in DOCS_TOOL_NAMES and corpus is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": docs_guard_tool_result(corpus_error, docs_paths),
        }

    encyclopedia_result = handle_encyclopedia_tools(
        req_id,
        params,
        corpus=corpus,
        encyclopedia=encyclopedia,
        corpus_error=corpus_error,
        docs_paths=docs_paths,
    )
    if encyclopedia_result is not None:
        return encyclopedia_result

    result = retrieval_handle_request(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": params,
        },
        corpus,
        corpus_error=corpus_error,
        extra_tools_catalog=extra_tools_catalog(),
        extra_tools_handler=lambda inner_req_id, inner_params: handle_domain_tools(
            inner_req_id,
            inner_params,
            wm=wm,
            workflow_error=workflow_error,
        ),
        server_name=SERVER_NAME,
        server_version=__version__,
        server_instructions=SERVER_INSTRUCTIONS,
    )
    if result is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": "No response for tools/call"},
        }
    return result


def handle_request(
    message: JSON,
    corpus: Optional[Corpus],
    wm: Optional[WorkflowManager],
    encyclopedia: Optional[GameEncyclopediaSource] = None,
    corpus_error: Optional[str] = None,
    workflow_error: Optional[str] = None,
    docs_paths: Optional[Dict[str, str]] = None,
) -> Optional[JSON]:
    if not isinstance(message, dict):
        return None

    method = str(message.get("method", ""))
    req_id = message.get("id")
    params = message.get("params")
    if not isinstance(params, dict):
        params = {}

    if method == "resources/list":
        resources: List[JSON] = []
        if corpus is not None:
            resources.extend(retrieval_resource_catalog(corpus))
        resources.extend(encyclopedia_resource_catalog(encyclopedia))
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resources}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": prompts_catalog()}}

    if method == "prompts/get":
        return handle_prompts_get(req_id, params)

    if method == "resources/read":
        uri = str(params.get("uri", "")).strip()
        encyclopedia_result = handle_encyclopedia_resource_read(req_id, uri, encyclopedia)
        if encyclopedia_result is not None:
            return encyclopedia_result
        if corpus is None:
            return docs_guard_rpc_error(req_id, corpus_error, docs_paths)
        return retrieval_handle_resources_read(req_id, params, corpus)

    if method == "tools/call":
        return handle_tools_call(
            req_id,
            params,
            corpus,
            wm,
            encyclopedia=encyclopedia,
            corpus_error=corpus_error,
            workflow_error=workflow_error,
            docs_paths=docs_paths,
        )

    return retrieval_handle_request(
        message,
        corpus,
        corpus_error=corpus_error,
        extra_tools_catalog=extra_tools_catalog(),
        extra_tools_handler=lambda inner_req_id, inner_params: handle_domain_tools(
            inner_req_id,
            inner_params,
            wm=wm,
            workflow_error=workflow_error,
        ),
        server_name=SERVER_NAME,
        server_version=__version__,
        server_instructions=SERVER_INSTRUCTIONS,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"install-agent-assets", "install-skills"}:
        from . import agent_assets

        raise SystemExit(agent_assets.main(sys.argv[2:]))

    parser = argparse.ArgumentParser(description=SERVER_NAME)
    parser.add_argument("--data-dir", default=str(bundled_data_dir()))
    parser.add_argument("--workspace", action="append", dest="workspaces")
    parser.add_argument("--mods-dir", default=str(default_mods_dir()))
    parser.add_argument("--game-dir")
    parser.add_argument("--locale-cok")
    parser.add_argument("--encyclopedia-cache-dir")
    parser.add_argument("--version", action="version", version=f"cities2-mcp {__version__}")
    args, extras = parser.parse_known_args()

    if extras:
        if "--mods-dir" in sys.argv and all(not x.startswith("-") for x in extras):
            args.mods_dir = " ".join([str(args.mods_dir), *extras]).strip()
            extras = []
    if extras and debug_enabled():
        debug_log(f"Ignoring unknown startup args from host: {extras}")

    corpus: Optional[Corpus] = None
    wm: Optional[WorkflowManager] = None
    encyclopedia: Optional[GameEncyclopediaSource] = None
    corpus_error: Optional[str] = None
    workflow_error: Optional[str] = None
    data_dir = resolve_data_dir(str(args.data_dir))
    docs_paths = {
        "chunks": str(data_dir / "index" / "chunks.jsonl"),
        "pages": str(data_dir / "index" / "pages.jsonl"),
    }
    workspace_values = [_configured_path_value(value) for value in (args.workspaces or [])]
    env_workspace = _configured_path_value(os.environ.get("CITIES2_MCP_WORKSPACE"))
    if env_workspace:
        workspace_values.append(env_workspace)
    workspace_paths = [Path(value) for value in workspace_values if value]

    try:
        corpus = Corpus([data_dir])
    except Exception as exc:
        corpus_error = str(exc)
        debug_log(f"Corpus init failed: {corpus_error}")

    try:
        encyclopedia = GameEncyclopediaSource.load(
            EncyclopediaConfig(
                game_dir=Path(args.game_dir) if args.game_dir else None,
                locale_cok=Path(args.locale_cok) if args.locale_cok else None,
                cache_dir=Path(args.encyclopedia_cache_dir) if args.encyclopedia_cache_dir else None,
            )
        )
    except Exception as exc:
        debug_log(f"Game encyclopedia init failed: {exc}")
        encyclopedia = UnavailableGameEncyclopedia(str(exc))  # type: ignore[assignment]

    if workspace_paths:
        try:
            wm = WorkflowManager(workspace_paths, Path(args.mods_dir), **installed_game_context(encyclopedia))
        except Exception as exc:
            workflow_error = str(exc)
            debug_log(f"WorkflowManager init failed: {workflow_error}")
    else:
        workflow_error = "Configure at least one --workspace to use Cities2-MCP workflow tools."

    if debug_enabled():
        if corpus is not None:
            debug_log(f"Corpus loaded from {data_dir}")
        else:
            debug_log(f"Corpus unavailable: {corpus_error}")
        if wm is not None:
            debug_log(f"Workspace={wm.workspace}")
            debug_log(f"Allowed workspaces={wm.workspaces}")
            debug_log(f"Mods dir={wm.mods_dir}")
        else:
            debug_log(f"Workflow manager unavailable: {workflow_error}")
        if encyclopedia is not None:
            try:
                encyclopedia_status = encyclopedia.status()
            except Exception as exc:
                encyclopedia_status = {"source": "game_encyclopedia", "available": False, "error": str(exc)}
            debug_log(
                "Game encyclopedia status: "
                + json.dumps(encyclopedia_status, ensure_ascii=False, sort_keys=True)
            )
        else:
            debug_log("Game encyclopedia status: unavailable (init returned None)")

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
                    resp = handle_request(
                        item,
                        corpus,
                        wm,
                        encyclopedia=encyclopedia,
                        corpus_error=corpus_error,
                        workflow_error=workflow_error,
                        docs_paths=docs_paths,
                    )
                    if resp is not None:
                        responses.append(resp)
                if responses:
                    send_message(responses)
                continue

            if not isinstance(msg, dict):
                continue
            method = str(msg.get("method", ""))
            debug_log(f"Received method={method}")
            resp = handle_request(
                msg,
                corpus,
                wm,
                encyclopedia=encyclopedia,
                corpus_error=corpus_error,
                workflow_error=workflow_error,
                docs_paths=docs_paths,
            )
            if resp is not None:
                if method == "initialize":
                    debug_log("Sending initialize response")
                send_message(resp)
    except Exception as exc:
        import traceback

        debug_log(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
