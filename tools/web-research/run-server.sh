#!/usr/bin/env bash
# Entry point for the web-research MCP server.
# Claude Code spawns this via stdio transport.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

exec uv run python -m web_research.mcp.server
