#!/usr/bin/env python3
"""Compatibility wrapper for clone-based Cities2-MCP installs."""

from __future__ import annotations

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parents[1])
if _root not in sys.path:
    sys.path.insert(0, _root)

from cities2_mcp.mcp_server import main


if __name__ == "__main__":
    main()
