#!/usr/bin/env zsh
set -u

SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

LOG_FILE="${CITIES2_MCP_LAUNCH_LOG:-/tmp/cities2-mcp-launch.log}"
{
  echo "==== $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===="
  echo "PWD=$PWD"
  echo "ARGV=$0 $*"
  echo "CITIES2_MCP_DEBUG=${CITIES2_MCP_DEBUG:-}"
  echo "CITIES2_MCP_DEBUG_LOG=${CITIES2_MCP_DEBUG_LOG:-}"
  echo "CITIES2_MODS_DIR=${CITIES2_MODS_DIR:-}"
} >> "$LOG_FILE" 2>/dev/null || true

export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec "$PYTHON_BIN" -m cities2_mcp.mcp_server \
  --workspace "$REPO_ROOT"
