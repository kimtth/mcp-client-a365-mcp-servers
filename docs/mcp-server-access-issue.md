# MCP Server Access — Issue & Resolution

## Problem

**0 of 14 MCP servers accessible** despite the Agent 365 manifest listing all 14 servers with correct scopes.

### Symptoms

- Token acquired successfully from `a365 login` or `az login`
- Gateway metadata endpoint returns 26 servers in the catalog
- But calling any manifest MCP server endpoint returns **403 Forbidden**
- Only 3 non-manifest servers worked: Planner, ProjectSophia, TaskPersonalization

### Root Cause

**The A365 CLI and Azure CLI tokens are issued for first-party app registrations** — not for the agent blueprint app. These first-party apps only have admin consent for management scopes and a few default MCP scopes:

```
AgentTools.AgentBluePrint.Create
AgentTools.AgentBluePrint.Delete
AgentTools.ListDataverseEnvironments.All
AgentTools.ListMCPServers.All
AgentTools.PublishMCPServer.All
AgentTools.UnpublishMCPServer.All
McpServers.Planner.All              ← only these 3 MCP scopes
McpServers.ProjectSophia.All
McpServers.TaskPersonalization.All
McpServersMetadata.Read.All
```

The **agent blueprint app** (`<your-blueprint-app-id>`) has OAuth2 consent for all 14 MCP scopes, but:

1. **Blueprint is an "AgenticApp" type** — Microsoft Entra blocks interactive auth flows (Device Code, Auth Code) for this application type (`AADSTS82006: The agent application does not support interactive authentication`)
2. **Inheritable permissions PATCH failed** — `a365 setup permissions mcp` succeeded at granting OAuth2 consent but failed configuring inheritable permissions because the `az login` session lacked `Application.ReadWrite.All` Graph permission for the beta inheritable-permissions API

### Why the blueprint app can't be used directly

The blueprint app is registered as a special Entra type: `microsoft.graph.agentIdentityBlueprint`. This is not a standard app registration — it's a managed identity type that:

- Cannot perform interactive (delegated) authentication
- Is designed to be called *by* the A365 platform (server-to-server), not *as* a user-facing client
- Its client credentials flow returns tokens with `roles` (app permissions), but the MCP servers require delegated `scp` claims

In other words: **the old app having all required scopes in Entra was not enough**. The missing piece was a supported delegated sign-in path that could mint a user token with those scopes in the `scp` claim. The blueprint app could hold the permissions, but it could not be used as the desktop client's interactive public client.

## Resolution

### Created a dedicated MCP Desktop Client app registration

A standard Entra app registration with:
- Public client flows enabled (for Device Code auth)
- All 14 MCP delegated permissions + `McpServersMetadata.Read.All` admin-consented
- No client secret (public client only)

### Entra Objects Added

| Object | Type | ID | Purpose |
|--------|------|----|---------|
| MCP Desktop Client | App Registration | `<your-mcp-client-id>` | Public client for Device Code auth |
| MCP Desktop Client | Service Principal | `<your-service-principal-id>` | Enterprise app backing the registration |
| OAuth2 Permission Grant | Admin consent | — | All 15 scopes consented for the service principal |

**Portal links:**
- App registration: `https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/<your-mcp-client-id>`
- API permissions: `https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/<your-mcp-client-id>`

### Scopes Consented (15 total)

All permissions are delegated, for resource `Agent 365 Tools` (`ea9ffc3e-8a23-4a7d-836d-234d7c7565c1`):

| Scope | MCP Server |
|-------|------------|
| `McpServers.Mail.All` | mcp_MailTools |
| `McpServers.Calendar.All` | mcp_CalendarTools |
| `McpServers.Word.All` | mcp_WordServer |
| `McpServers.Teams.All` | mcp_TeamsTools |
| `McpServers.OneDriveSharepoint.All` | mcp_OneDriveSharePointTools |
| `McpServers.CopilotMCP.All` | mcp_CopilotMCP |
| `McpServers.Excel.All` | mcp_ExcelServer |
| `McpServers.PowerPoint.All` | mcp_PowerPointServer |
| `McpServers.SharepointLists.All` | mcp_SharePointListsTools |
| `McpServers.Files.All` | mcp_FilesTools |
| `McpServers.Knowledge.All` | mcp_KnowledgeTools |
| `McpServers.Me.All` | mcp_MeTools |
| `McpServers.DASearch.All` | mcp_DASearchTools |
| `McpServers.Dataverse.All` | mcp_DataverseTools |
| `McpServersMetadata.Read.All` | (metadata endpoint) |

### Auth Mode Comparison

| Mode | All 14 servers? | Notes |
|------|:---:|-------|
| `device-code` | **Yes** | Interactive; uses the new MCP Desktop Client app with all 15 scopes |
| `azure-cli` | No (3 only) | Token from `az login` — first-party app only has Planner, ProjectSophia, TaskPersonalization scopes |
| `a365-cli` | No (3 only) | Same limitation as azure-cli |
| `client-secret` | No | Confidential client flow issues app-level tokens (`roles`), but MCP servers require delegated `scp` claims |
| `bearer` | Depends | Pass-through — works only if the supplied token already has the right scopes |

**Device-code is the only working path for all 14 MCP servers** because:

1. The MCP servers require **delegated** (user) tokens with `scp` claims
2. Only the MCP Desktop Client app registration has all 14 scopes consented
3. That app is a **public client** — so it needs an interactive flow (device-code)

Possible future expansions:
- **Auth-code with PKCE** on the same public client app (browser redirect instead of device code — faster UX)
- If Microsoft lifts the restriction on blueprint apps, the `a365-cli` path could work too

### Code Changes

1. **`mcp_bridge/auth.py`** — Added `DeviceCodeCredential` as a first-class auth mode with persistent MSAL token cache and `AuthenticationRecord` serialization for silent re-auth
2. **`.env`** — Changed `MCP_CLIENT_ID` from the blueprint app to the new Desktop Client; set `MCP_AUTH_MODE=device-code`; removed `MCP_CLIENT_SECRET` (not needed for public client)
3. **`ToolingManifest.json`** — Fixed scope casing: `McpServers.OneDriveSharePoint.All` → `McpServers.OneDriveSharepoint.All` (lowercase 'p' matches the actual Entra permission name)

### Verified Result

```
Token acquired successfully!
Scopes in token (15):
  McpServers.Calendar.All
  McpServers.CopilotMCP.All
  McpServers.DASearch.All
  McpServers.Dataverse.All
  McpServers.Excel.All
  McpServers.Files.All
  McpServers.Knowledge.All
  McpServers.Mail.All
  McpServers.Me.All
  McpServers.OneDriveSharepoint.All
  McpServers.PowerPoint.All
  McpServers.SharepointLists.All
  McpServers.Teams.All
  McpServers.Word.All
  McpServersMetadata.Read.All

Manifest scope coverage: 14/14
  ALL 14 MCP server scopes present!
```
