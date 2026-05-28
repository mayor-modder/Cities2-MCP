from __future__ import annotations

import os
import sys

from cities2_mcp.mcp_server import main


def append_optional_arg(argv: list[str], flag: str, env_name: str) -> None:
    value = os.environ.get(env_name, "").strip()
    if value:
        argv.extend([flag, value])


if __name__ == "__main__":
    server_argv = [sys.argv[0]]
    append_optional_arg(server_argv, "--workspace", "CITIES2_MCP_WORKSPACE")
    append_optional_arg(server_argv, "--mods-dir", "CITIES2_MODS_DIR")
    append_optional_arg(server_argv, "--game-dir", "CITIES2_GAME_DIR")
    append_optional_arg(server_argv, "--locale-cok", "CITIES2_LOCALE_COK")
    sys.argv = server_argv
    main()
