from __future__ import annotations

from pathlib import Path

from ._version import __version__ as __version__

MCP_NAME = "io.github.mayor-modder/cities2-mcp"


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_data_dir() -> Path:
    return package_root() / "data"


def bundled_research_data_dir() -> Path:
    return package_root() / "research_data"
