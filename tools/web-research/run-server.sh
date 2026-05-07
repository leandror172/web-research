#!/usr/bin/env bash
# Entry point for the web-research MCP server.
# Claude Code spawns this via stdio transport.
#
# Env vars:
#   WR_LOG_LEVEL  — DEBUG | INFO | WARNING | ERROR  (default: WARNING)
#   WR_LOG_FILE   — absolute path to log file        (default: output/mcp-server.log)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$(dirname "${WR_LOG_FILE:-$SCRIPT_DIR/output/mcp-server.log}")"
echo "web-research MCP: logging to $LOG_DIR/mcp-server-$$.log (level: ${WR_LOG_LEVEL:-WARNING})" >&2

exec uv run python -m web_research.mcp.server
