.PHONY: help logs test

LOG_DIR := tools/web-research/output

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  logs   tail all MCP server session logs (set WR_LOG_LEVEL=DEBUG in .mcp.json to increase verbosity)"
	@echo "  test   run the full pytest suite"

logs:
	@ls $(LOG_DIR)/mcp-server-*.log 2>/dev/null || { echo "No log files found in $(LOG_DIR)/ (has the MCP server run yet?)"; exit 1; }
	tail -F $(LOG_DIR)/mcp-server-*.log

test:
	cd tools/web-research && uv run --group dev pytest
