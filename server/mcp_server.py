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
from pathlib import Path
from typing import Any, Dict, List, Optional

_server_dir = str(Path(__file__).resolve().parent)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from build_runner import BuildRunner
from game_encyclopedia import (
    GAME_ENCYCLOPEDIA_WARNING,
    GameEncyclopediaSource,
)
from project_analyzer import ProjectAnalyzer
from project_scaffold import ProjectScaffolder
from retrieval import (
    Corpus,
    debug_enabled,
    debug_log,
    handle_request as retrieval_handle_request,
    read_message,
    send_message,
    text_result,
)
from retrieval import mcp_server as retrieval_impl

JSON = Dict[str, Any]
SERVER_NAME = "Cities2-MCP — game knowledge and modding tools for Cities: Skylines II"
SERVER_INSTRUCTIONS = (
    "Cities2-MCP gives AI assistants local access to the bundled Cities: Skylines II Wiki corpus "
    "for gameplay, systems, and modding questions. It also includes local workflow tools for CS2 "
    "mod projects: scaffolding, reading and writing project files, static analysis, building, "
    "packaging, and dry-run launching the game. Use the wiki retrieval tools for game knowledge "
    "and reference lookups; use the workflow tools only inside configured local workspaces."
)
DOCS_GUARD_CODE = "DOCS_INDEX_MISSING_OR_MISCONFIGURED"
DOCS_GUARD_HEADLINE = "Cities2 docs are not available for this session"
DOCS_TOOL_NAMES = {"search", "query_reference", "get_page", "get_snippets"}
retrieval_resource_catalog = retrieval_impl.resource_catalog
retrieval_handle_resources_read = retrieval_impl.handle_resources_read


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
    def __init__(self, workspaces: List[Path], mods_dir: Path) -> None:
        if not workspaces:
            raise ValueError("At least one workspace must be configured")
        self.workspaces = [workspace.resolve() for workspace in workspaces]
        self.workspace = self.workspaces[0]
        self.mods_dir = mods_dir.expanduser().resolve()
        self.scaffolder = ProjectScaffolder(self.workspace, additional_workspaces=self.workspaces[1:])
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


def default_mods_dir() -> Path:
    env = os.environ.get("CITIES2_MODS_DIR")
    if env:
        return Path(env).expanduser()
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return (
                Path(local_appdata).expanduser().parent
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


WORKFLOW_TOOL_NAMES = {
    "scaffold_project",
    "write_project_file",
    "list_project_tree",
    "build_project",
    "analyze_project",
    "package_project",
    "launch_cities2",
}

# ---------------------------------------------------------------------------
# Domain tools catalog
# ---------------------------------------------------------------------------


def domain_tools_catalog() -> List[JSON]:
    return [
        {
            "name": "scaffold_project",
            "description": "Scaffold a Cities: Skylines II mod project from a template.",
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
            "description": "Build a Cities: Skylines II mod project and return normalized diagnostics.",
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
        {
            "name": "launch_cities2",
            "description": "Launch Cities: Skylines II with platform-aware executable resolution (dry-run by default).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "executable": {"type": "string"},
                    "flags": {"type": "array", "items": {"type": "string"}},
                    "platform": {
                        "type": "string",
                        "enum": ["auto", "mac", "windows", "linux"],
                        "default": "auto",
                    },
                    "dry_run": {"type": "boolean", "default": True},
                },
            },
        },
    ]


def encyclopedia_tools_catalog() -> List[JSON]:
    return [
        {
            "name": "search_encyclopedia",
            "description": "Search the local Cities: Skylines II in-game Encyclopedia read from the user's installed game files.",
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
            "description": "Return one local Cities: Skylines II in-game Encyclopedia entry by entry_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"entry_id": {"type": "string"}},
                "required": ["entry_id"],
            },
        },
        {
            "name": "source_status",
            "description": "Report Cities2-MCP source availability for the wiki corpus and local game Encyclopedia.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def extra_tools_catalog() -> List[JSON]:
    return domain_tools_catalog() + encyclopedia_tools_catalog()


# ---------------------------------------------------------------------------
# Domain tools handler
# ---------------------------------------------------------------------------


def encyclopedia_unavailable_result() -> JSON:
    return text_result({"ok": False, "message": GAME_ENCYCLOPEDIA_WARNING}, is_error=True)


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
                return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result()}
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
                return {"jsonrpc": "2.0", "id": req_id, "result": encyclopedia_unavailable_result()}
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

        if name == "launch_cities2":
            flags = _as_str_list(args.get("flags"))
            exe_val = args.get("executable")
            executable = str(exe_val).strip() if isinstance(exe_val, str) else None
            payload = wm.builder.launch_cities2(
                executable=executable or None,
                flags=flags,
                platform=str(args.get("platform", "auto")).strip() or "auto",
                dry_run=bool(args.get("dry_run", True)),
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
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resources}}

    if method == "resources/read":
        uri = str(params.get("uri", "")).strip()
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
        server_instructions=SERVER_INSTRUCTIONS,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    root = repo_root()
    parser = argparse.ArgumentParser(description=SERVER_NAME)
    parser.add_argument("--data-dir", default=str(root / "data"))
    parser.add_argument("--workspace", action="append", dest="workspaces")
    parser.add_argument("--mods-dir", default=str(default_mods_dir()))
    args, extras = parser.parse_known_args()

    if extras:
        if "--mods-dir" in sys.argv and all(not x.startswith("-") for x in extras):
            args.mods_dir = " ".join([str(args.mods_dir), *extras]).strip()
            extras = []
    if extras and debug_enabled():
        debug_log(f"Ignoring unknown startup args from host: {extras}")

    corpus: Optional[Corpus] = None
    wm: Optional[WorkflowManager] = None
    corpus_error: Optional[str] = None
    workflow_error: Optional[str] = None
    docs_paths = {
        "chunks": str(Path(args.data_dir) / "index" / "chunks.jsonl"),
        "pages": str(Path(args.data_dir) / "index" / "pages.jsonl"),
    }
    workspace_values = args.workspaces or [str(root)]
    workspace_paths = [Path(value) for value in workspace_values]

    try:
        corpus = Corpus([Path(args.data_dir)])
    except Exception as exc:
        corpus_error = str(exc)
        debug_log(f"Corpus init failed: {corpus_error}")

    try:
        wm = WorkflowManager(workspace_paths, Path(args.mods_dir))
    except Exception as exc:
        workflow_error = str(exc)
        debug_log(f"WorkflowManager init failed: {workflow_error}")

    if debug_enabled():
        if corpus is not None:
            debug_log(f"Corpus loaded from {args.data_dir}")
        else:
            debug_log(f"Corpus unavailable: {corpus_error}")
        if wm is not None:
            debug_log(f"Workspace={wm.workspace}")
            debug_log(f"Allowed workspaces={wm.workspaces}")
            debug_log(f"Mods dir={wm.mods_dir}")
        else:
            debug_log(f"Workflow manager unavailable: {workflow_error}")

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
