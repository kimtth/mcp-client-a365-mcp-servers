"""Stdio MCP server for Agent 365 — usable by Claude Code, VS Code, etc."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_bridge.auth import TokenProvider
from mcp_bridge.bridge import McpService, sanitize_schema
from mcp_bridge.config import load_config

log = logging.getLogger(__name__)

_service: McpService | None = None


def _build_server() -> Server:
    server = Server("agent365-bridge")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        assert _service is not None
        return [
            Tool(
                name=t["name"],
                description=t.get("description", ""),
                inputSchema=sanitize_schema(t.get("inputSchema", {"type": "object", "properties": {}})),
            )
            for t in _service.proxy.list_tools()
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        assert _service is not None
        result = await _service.proxy.call_tool(name, arguments or {})
        return [
            TextContent(type="text", text=c.get("text", ""))
            for c in result.get("content", [])
        ]

    return server


async def _run() -> None:
    global _service

    config = load_config()
    log.info("Bridge starting — %d servers in manifest", len(config.manifest.mcp_servers))

    token_provider = TokenProvider(config)
    _service = McpService(config, token_provider)

    # Discover tools before serving (tools come from cache instantly if available)
    if _service.proxy.tool_count == 0:
        log.info("No cached tools — running live discovery...")
        await _service.discover()
    else:
        log.info("Serving %d cached tools; background discovery starting...", _service.proxy.tool_count)
        asyncio.create_task(_background_discover())

    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def _background_discover() -> None:
    """Refresh tools from live servers without blocking stdio."""
    try:
        assert _service is not None
        await _service.discover()
        log.info("Background discovery complete — %d tools live", _service.proxy.tool_count)
    except Exception as exc:
        log.warning("Background discovery failed: %s", exc)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(_run())


if __name__ == "__main__":
    main()
