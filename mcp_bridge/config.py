from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ── Data types ──────────────────────────────────────────────────────


@dataclass
class MCPServerConfig:
    mcp_server_name: str
    mcp_server_unique_name: str | None = None
    url: str | None = None
    scope: str | None = None
    audience: str | None = None


@dataclass
class ToolingManifest:
    tenant_id: str | None = None
    agentic_app_id: str | None = None
    agent_blueprint_id: str | None = None
    mcp_platform_endpoint: str | None = None
    mcp_platform_auth_scope: str | None = None
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)


@dataclass
class AppConfig:
    # MCP / Agent identity
    mcp_tenant_id: str | None = None
    mcp_client_id: str | None = None
    mcp_client_secret: str | None = None
    agentic_app_id: str | None = None
    agent_blueprint_id: str | None = None
    mcp_bearer_token: str | None = None

    # MCP platform
    mcp_platform_endpoint: str = "https://agent365.svc.cloud.microsoft"
    mcp_platform_auth_scope: str = "ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/.default"
    mcp_auth_mode: str = "auto"

    # Azure OpenAI
    azure_openai_endpoint: str | None = None
    azure_openai_auth_mode: str = "azure-cli"
    azure_openai_deployment: str = "gpt-5.4-mini"
    azure_openai_api_version: str = "2025-04-01-preview"

    # Runtime
    bridge_type: str = "python"
    manifest: ToolingManifest = field(default_factory=ToolingManifest)


@dataclass
class DiscoveredTool:
    name: str
    description: str
    input_schema: dict
    server_name: str


@dataclass
class ResolvedServer:
    config: MCPServerConfig
    url: str
    tools: list[DiscoveredTool] = field(default_factory=list)


# ── Loader ──────────────────────────────────────────────────────────

_DEFAULT_ENDPOINT = "https://agent365.svc.cloud.microsoft"
_DEFAULT_AUTH_SCOPE = "ea9ffc3e-8a23-4a7d-836d-234d7c7565c1/.default"


def _find_project_root() -> Path:
    """Walk up from CWD looking for ToolingManifest.json, fall back to CWD."""
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        if (parent / "ToolingManifest.json").exists():
            return parent
    return cwd


def _load_manifest(manifest_path: Path | None = None) -> ToolingManifest:
    if manifest_path is None:
        manifest_path = _find_project_root() / "ToolingManifest.json"
    if not manifest_path.exists():
        return ToolingManifest()

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    servers = [
        MCPServerConfig(
            mcp_server_name=s["mcpServerName"],
            mcp_server_unique_name=s.get("mcpServerUniqueName"),
            url=s.get("url"),
            scope=s.get("scope"),
            audience=s.get("audience"),
        )
        for s in raw.get("mcpServers", [])
    ]

    return ToolingManifest(
        tenant_id=raw.get("tenantId"),
        agentic_app_id=raw.get("agenticAppId"),
        agent_blueprint_id=raw.get("agentBlueprintId"),
        mcp_platform_endpoint=raw.get("mcpPlatformEndpoint"),
        mcp_platform_auth_scope=raw.get("mcpPlatformAuthScope"),
        mcp_servers=servers,
    )


def load_config(manifest_path: Path | None = None) -> AppConfig:
    project_root = _find_project_root()
    load_dotenv(project_root / ".env")

    manifest = _load_manifest(manifest_path)

    mcp_tenant_id = (
        os.getenv("MCP_TENANT_ID")
        or os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID")
        or os.getenv("AZURE_TENANT_ID")
        or manifest.tenant_id
    )
    mcp_client_id = (
        os.getenv("MCP_CLIENT_ID")
        or os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")
        or os.getenv("AZURE_CLIENT_ID")
    )
    mcp_client_secret = (
        os.getenv("MCP_CLIENT_SECRET")
        or os.getenv("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET")
        or os.getenv("AZURE_CLIENT_SECRET")
    )

    mcp_bearer_token = os.getenv("MCP_BEARER_TOKEN") or os.getenv("BEARER_TOKEN") or None

    return AppConfig(
        mcp_tenant_id=mcp_tenant_id,
        mcp_client_id=mcp_client_id,
        mcp_client_secret=mcp_client_secret,
        agentic_app_id=os.getenv("AGENTIC_APP_ID") or manifest.agentic_app_id,
        agent_blueprint_id=manifest.agent_blueprint_id,
        mcp_bearer_token=mcp_bearer_token,
        mcp_platform_endpoint=(
            os.getenv("MCP_PLATFORM_ENDPOINT")
            or manifest.mcp_platform_endpoint
            or _DEFAULT_ENDPOINT
        ),
        mcp_platform_auth_scope=(
            os.getenv("MCP_PLATFORM_AUTH_SCOPE")
            or manifest.mcp_platform_auth_scope
            or _DEFAULT_AUTH_SCOPE
        ),
        mcp_auth_mode=os.getenv("MCP_AUTH_MODE", "auto"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_auth_mode=os.getenv("AZURE_OPENAI_AUTH_MODE", "azure-cli"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-mini"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        bridge_type=os.getenv("BRIDGE_TYPE", "python"),
        manifest=manifest,
    )
