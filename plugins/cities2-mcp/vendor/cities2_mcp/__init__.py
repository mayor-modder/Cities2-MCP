from __future__ import annotations

from pathlib import Path

__version__ = "0.1.9"
MCP_NAME = "io.github.mayor-modder/cities2-mcp"


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_data_dir() -> Path:
    return package_root() / "data"
