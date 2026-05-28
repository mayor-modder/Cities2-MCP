from __future__ import annotations

import sys
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR_ROOT))

from cities2_mcp.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    main()
