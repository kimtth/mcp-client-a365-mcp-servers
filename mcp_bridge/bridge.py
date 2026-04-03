from __future__ import annotations

import logging
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from mcp_bridge.auth import TokenProvider
from mcp_bridge.config import (
    AppConfig,
    DiscoveredTool,
    MCPServerConfig,
    ResolvedServer,
)
from mcp_bridge.tools_cache import CachedTool, load_tools_cache, save_tools_cache

log = logging.getLogger(__name__)

_USER_AGENT = "McpBridge-A365/1.0.0 (Python)"


# ── Schema sanitization ────────────────────────────────────────────


def sanitize_schema(schema: dict) -> dict:
    """Strip oneOf/allOf/anyOf from tool schemas for LLM compatibility."""
    result = dict(schema)

    if isinstance(result.get("allOf"), list):
        for sub in result["allOf"]:
            if isinstance(sub, dict):
                if "properties" in sub:
                    result.setdefault("properties", {}).update(sub["properties"])
                if isinstance(sub.get("required"), list):
                    existing = result.get("required", [])
                    result["required"] = list(set(existing + sub["required"]))
        del result["allOf"]
        result.setdefault("type", "object")

    for keyword in ("oneOf", "anyOf"):
        if isinstance(result.get(keyword), list):
            variants = result[keyword]
            if variants and isinstance(variants[0], dict):
                first = variants[0]
                if "properties" in first:
                    result.setdefault("properties", {}).update(first["properties"])
                if isinstance(first.get("required"), list):
                    existing = result.get("required", [])
                    result["required"] = list(set(existing + first["required"]))
            del result[keyword]
            result.setdefault("type", "object")

    if isinstance(result.get("properties"), dict):
        result["properties"] = {
            k: sanitize_schema(v) if isinstance(v, dict) else v
            for k, v in result["properties"].items()
        }

    return result


# ── Server discovery ───────────────────────────────────────────────


class ServerDiscovery:
    """Discovers tools from Agent 365 MCP servers via StreamableHTTP."""

    def __init__(self, config: AppConfig, token_provider: TokenProvider) -> None:
        self._config = config
        self._token_provider = token_provider

    async def discover_all(self) -> list[ResolvedServer]:
        manifest_configs = self._config.manifest.mcp_servers
        resolved = await self._resolve_server_configs(manifest_configs)
        if resolved:
            return resolved

        if self._config.agentic_app_id:
            gateway_configs = await self._get_from_gateway()
            gateway_names = {s.mcp_server_name for s in gateway_configs}
            manifest_names = {s.mcp_server_name for s in manifest_configs}
            if gateway_configs and gateway_names != manifest_names:
                log.warning(
                    "Manifest servers are not accessible with the current token; "
                    "falling back to %d gateway-visible servers",
                    len(gateway_configs),
                )
                resolved = await self._resolve_server_configs(gateway_configs)
                if resolved:
                    return resolved

        token_scopes = await self._token_provider.get_token_scopes()
        manifest_scopes = {s.scope for s in manifest_configs if s.scope}
        missing_scopes = sorted(manifest_scopes - token_scopes)
        if missing_scopes:
            preview = ", ".join(missing_scopes[:5])
            if len(missing_scopes) > 5:
                preview += ", ..."
            raise RuntimeError(
                "No manifest MCP servers are accessible with the current token. "
                f"Missing scopes include: {preview}"
            )

        return []

    async def _resolve_server_configs(
        self, server_configs: list[MCPServerConfig]
    ) -> list[ResolvedServer]:
        resolved: list[ResolvedServer] = []

        for sc in server_configs:
            try:
                url = self._build_server_url(sc)
                tools = await self._discover_tools(sc.mcp_server_name, url)
                resolved.append(ResolvedServer(config=sc, url=url, tools=tools))
                log.info(
                    "Discovered %d tools from %s", len(tools), sc.mcp_server_name
                )
            except Exception as exc:
                log.warning("Failed to discover %s: %s", sc.mcp_server_name, exc)

        return resolved

    async def _get_server_configs(self) -> list[MCPServerConfig]:
        # Always use the local manifest as the source of truth.
        # The gateway only returns servers the token already has scopes for,
        # which may be a subset. The manifest lists all servers the user wants.
        return self._config.manifest.mcp_servers

    async def _get_from_gateway(self) -> list[MCPServerConfig]:
        token = await self._token_provider.get_token()
        url = (
            f"{self._config.mcp_platform_endpoint}"
            f"/agents/{self._config.agentic_app_id}/mcpServers"
        )
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # API may return {mcpServers: [...]} or a bare list
        servers_raw = data.get("mcpServers", data) if isinstance(data, dict) else data

        return [
            MCPServerConfig(
                mcp_server_name=s["mcpServerName"],
                mcp_server_unique_name=s.get("mcpServerUniqueName"),
                url=s.get("url") or s.get("mcpServerUrl"),
                scope=s.get("scope"),
                audience=s.get("audience"),
            )
            for s in servers_raw
        ]

    def _build_server_url(self, config: MCPServerConfig) -> str:
        if config.url:
            return config.url
        base = self._config.mcp_platform_endpoint.rstrip("/")
        return f"{base}/agents/servers/{config.mcp_server_name}/"

    async def _discover_tools(
        self, server_name: str, server_url: str
    ) -> list[DiscoveredTool]:
        token = await self._token_provider.get_token()

        headers: dict[str, str] = {"User-Agent": _USER_AGENT}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._config.agentic_app_id:
            headers["x-ms-agentid"] = self._config.agentic_app_id

        async with streamablehttp_client(
            server_url, headers=headers
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()

                return [
                    DiscoveredTool(
                        name=t.name,
                        description=t.description or "",
                        input_schema=t.inputSchema if isinstance(t.inputSchema, dict) else {},
                        server_name=server_name,
                    )
                    for t in (result.tools or [])
                ]


# ── Tool forwarder ─────────────────────────────────────────────────


class ToolForwarder:
    """Forwards tool calls to the correct Agent 365 MCP server."""

    def __init__(
        self,
        config: AppConfig,
        token_provider: TokenProvider,
        servers: list[ResolvedServer],
    ) -> None:
        self._config = config
        self._token_provider = token_provider
        self._tool_server_map: dict[str, ResolvedServer] = {}

        for server in servers:
            for tool in server.tools:
                self._tool_server_map[tool.name] = server

    async def call_tool(
        self,
        tool_name: str,
        args: dict[str, Any],
        target_server: ResolvedServer | None = None,
    ) -> dict:
        server = target_server or self._tool_server_map.get(tool_name)
        if not server:
            return {
                "content": [
                    {"type": "text", "text": f'Error: Unknown tool "{tool_name}".'}
                ]
            }

        try:
            token = await self._token_provider.get_token()

            headers: dict[str, str] = {"User-Agent": _USER_AGENT}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if self._config.agentic_app_id:
                headers["x-ms-agentid"] = self._config.agentic_app_id

            async with streamablehttp_client(
                server.url, headers=headers
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args)

                    content = []
                    for item in result.content or []:
                        if hasattr(item, "text"):
                            content.append({"type": "text", "text": item.text})
                        else:
                            content.append({"type": "text", "text": str(item)})

                    return {"content": content}

        except Exception as exc:
            msg = f'Error calling "{tool_name}" on {server.config.mcp_server_name}: {exc}'
            log.error(msg)
            return {"content": [{"type": "text", "text": msg}]}


# ── Tool registry entry ────────────────────────────────────────────


class _ToolRegistryEntry:
    __slots__ = ("unique_name", "original_name", "server_name", "tool_def")

    def __init__(
        self,
        unique_name: str,
        original_name: str,
        server_name: str,
        tool_def: dict,
    ) -> None:
        self.unique_name = unique_name
        self.original_name = original_name
        self.server_name = server_name
        self.tool_def = tool_def


# ── Proxy server ───────────────────────────────────────────────────


class McpProxyServer:
    """Aggregates tools from multiple Agent 365 MCP servers with caching and dedup."""

    def __init__(self) -> None:
        self._registry: dict[str, _ToolRegistryEntry] = {}
        self._forwarder: ToolForwarder | None = None
        self._resolved_servers: list[ResolvedServer] = []

        cached = load_tools_cache()
        if cached:
            self._rebuild_registry_from_cache(cached)

    @property
    def tool_count(self) -> int:
        return len(self._registry)

    @property
    def forwarder(self) -> ToolForwarder | None:
        return self._forwarder

    def set_live_data(
        self, forwarder: ToolForwarder, servers: list[ResolvedServer]
    ) -> None:
        if not servers:
            log.warning(
                "Discovery returned no live servers; preserving cached tool registry"
            )
            self._forwarder = None
            self._resolved_servers = []
            return

        self._forwarder = forwarder
        self._resolved_servers = servers
        self._rebuild_registry_from_live(servers)

        fresh = [
            CachedTool(
                name=e.original_name,
                description=e.tool_def.get("description", ""),
                input_schema=e.tool_def.get("inputSchema", {}),
                server_name=e.server_name,
            )
            for e in self._registry.values()
        ]
        save_tools_cache(fresh)

    def list_tools(self, server_filter: set[str] | None = None) -> list[dict]:
        if server_filter is None:
            return [e.tool_def for e in self._registry.values()]
        return [
            e.tool_def
            for e in self._registry.values()
            if e.server_name in server_filter
        ]

    def server_names(self) -> list[str]:
        seen: dict[str, None] = {}
        for e in self._registry.values():
            seen.setdefault(e.server_name)
        return list(seen)

    async def call_tool(self, name: str, args: dict[str, Any]) -> dict:
        entry = self._registry.get(name)
        if not entry:
            return {"content": [{"type": "text", "text": f"Tool '{name}' not found."}]}

        if not self._forwarder:
            return {
                "content": [
                    {"type": "text", "text": "Bridge not connected. Run discovery first."}
                ]
            }

        target = None
        for s in self._resolved_servers:
            if s.config.mcp_server_name == entry.server_name:
                target = s
                break

        return await self._forwarder.call_tool(entry.original_name, args, target)

    def _rebuild_registry_from_cache(self, tools: list[CachedTool]) -> None:
        self._registry.clear()
        name_counts: dict[str, int] = {}
        for t in tools:
            name_counts[t.name] = name_counts.get(t.name, 0) + 1

        for t in tools:
            unique = t.name
            if name_counts.get(t.name, 0) > 1:
                unique = f"{t.name}_{t.server_name}"
            self._registry[unique] = _ToolRegistryEntry(
                unique_name=unique,
                original_name=t.name,
                server_name=t.server_name,
                tool_def={
                    "name": unique,
                    "description": t.description,
                    "inputSchema": sanitize_schema(t.input_schema),
                },
            )

    def _rebuild_registry_from_live(self, servers: list[ResolvedServer]) -> None:
        self._registry.clear()
        name_counts: dict[str, int] = {}
        for s in servers:
            for t in s.tools:
                name_counts[t.name] = name_counts.get(t.name, 0) + 1

        for s in servers:
            for t in s.tools:
                unique = t.name
                if name_counts.get(t.name, 0) > 1:
                    unique = f"{t.name}_{s.config.mcp_server_name}"
                self._registry[unique] = _ToolRegistryEntry(
                    unique_name=unique,
                    original_name=t.name,
                    server_name=s.config.mcp_server_name,
                    tool_def={
                        "name": unique,
                        "description": t.description,
                        "inputSchema": sanitize_schema(t.input_schema),
                    },
                )


# ── MCP service ────────────────────────────────────────────────────


class McpService:
    """High-level service that orchestrates discovery and wraps the proxy."""

    def __init__(self, config: AppConfig, token_provider: TokenProvider) -> None:
        self._config = config
        self._token_provider = token_provider
        self.proxy = McpProxyServer()

    async def discover(self) -> list[ResolvedServer]:
        discovery = ServerDiscovery(self._config, self._token_provider)
        servers = await discovery.discover_all()

        forwarder = ToolForwarder(self._config, self._token_provider, servers)
        self.proxy.set_live_data(forwarder, servers)

        total = self.proxy.tool_count
        log.info("Discovery complete: %d tools across %d servers", total, len(servers))
        return servers
