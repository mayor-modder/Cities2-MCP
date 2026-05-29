@echo off
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
py -3 -m cities2_mcp.mcp_server --workspace "%~dp0" %*
