@echo off
py -3 "%~dp0server\mcp_server.py" --data-dir "%~dp0data" --workspace "%~dp0" %*
