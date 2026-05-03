"""Internal MediaWiki retrieval API for Cities2-MCP.

This package was originally split out as wiki-mcp and is now bundled so
Cities2-MCP can be installed without git submodules.
"""

from .mcp_server import (
    Corpus,
    HybridIndex,
    text_result,
    format_doc_result,
    handle_request,
    handle_tools_call,
    read_message,
    send_message,
    debug_log,
    debug_enabled,
    __version__,
)

__all__ = [
    "Corpus",
    "HybridIndex",
    "text_result",
    "format_doc_result",
    "handle_request",
    "handle_tools_call",
    "read_message",
    "send_message",
    "debug_log",
    "debug_enabled",
    "__version__",
]
