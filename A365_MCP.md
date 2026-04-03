# Agent 365 MCP Servers & Tools

61 tools live-discovered across 6 servers. Tool definitions for the remaining 8 servers sourced from the [Work IQ MCP reference docs](https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview) (preview). 3 servers (PowerPoint, Files, DASearch) have no public reference yet.

> **Scope**: Each server requires the corresponding `McpServers.<Name>.All` delegated permission on the MCP Desktop Client app registration.

---

## mcp_CalendarTools — 13 tools

| Tool | Description |
|------|-------------|
| **ListEvents** | Retrieve a list of calendar events for the user matching given criteria (date range, title, attendees). Returns master events only (not expanded recurrences). |
| **ListCalendarView** | Retrieve events from a user's calendar view with recurring events expanded into individual instances. |
| **CreateEvent** | Create a new calendar event. Attendees can be provided as names or emails (names resolved automatically). |
| **UpdateEvent** | Update an existing calendar event. Add or remove attendees by name or email. |
| **DeleteEventById** | Delete a calendar event by ID. |
| **FindMeetingTimes** | Find meeting times that work for all attendees based on availability. |
| **AcceptEvent** | Accept a calendar event invitation, optionally with a comment. |
| **TentativelyAcceptEvent** | Tentatively accept a calendar event invitation, optionally with a comment. |
| **DeclineEvent** | Decline a calendar event invitation, optionally with a comment. |
| **CancelEvent** | Cancel a calendar event (organizer only). Sends cancellation notifications to all attendees. |
| **ForwardEvent** | Forward a calendar event to other recipients (names or emails). |
| **GetUserDateAndTimeZoneSettings** | Get a user's timezone, date format, time format, working hours, and language preferences. |
| **GetRooms** | Get all meeting rooms defined in the tenant (names and email addresses). |

---

## mcp_ExcelServer — 4 tools

| Tool | Description |
|------|-------------|
| **CreateWorkbook** | Create a new Excel workbook in the user's OneDrive root from CSV content. |
| **GetDocumentContent** | Fetch raw Excel workbook (XLSX) content from OneDrive/SharePoint via sharing URL. |
| **CreateComment** | Create a new comment in a workbook at a specified cell (A1 notation). |
| **ReplyToComment** | Reply to an existing comment in a workbook. |

---

## mcp_KnowledgeTools — 5 tools

| Tool | Description |
|------|-------------|
| **configure_federated_knowledge** | Register a new federated knowledge configuration. |
| **delete_federated_knowledge** | Remove a federated knowledge configuration. |
| **ingest_federated_knowledge** | Trigger (re)ingestion of a federated knowledge configuration. |
| **query_federated_knowledge** | Query content across federated knowledge configurations. |
| **retrieve_federated_knowledge** | List all federated knowledge configurations. |

---

## mcp_MailTools — 22 tools

| Tool | Description |
|------|-------------|
| **SearchMessagesQueryParameters** | Search emails using OData query parameters. Preferred over SearchMessages for performance. |
| **SearchMessages** | Full-text search across messages (slower, last resort). |
| **GetMessage** | Get a message by ID from the user's mailbox. |
| **CreateDraftMessage** | Create a draft email without sending. Recipients can be names or emails. |
| **UpdateDraft** | Update a draft's recipients, subject, body, and attachments. |
| **SendDraftMessage** | Send an existing draft by ID. |
| **SendEmailWithAttachments** | Create and send an email with optional attachments in one step. |
| **UpdateMessage** | Update a message's mutable properties (subject, body, categories, importance). |
| **FlagEmail** | Flag, complete, or clear a flag on an email message. |
| **DeleteMessage** | Delete a message from the user's mailbox. |
| **ReplyToMessage** | Reply to a message. Creates a draft by default; set `sendImmediately=true` to send at once. |
| **ReplyAllToMessage** | Reply-all to a message. Creates a draft by default; set `sendImmediately=true` to send at once. |
| **ReplyWithFullThread** | Reply preserving the full quoted thread. Optionally re-attach original files. |
| **ReplyAllWithFullThread** | Reply-all preserving the full quoted thread. Optionally re-attach original files. |
| **ForwardMessage** | Forward a message with optional comment and new attachments. |
| **ForwardMessageWithFullThread** | Forward a message preserving the full quoted thread. |
| **GetAttachments** | Get attachment metadata (ID, name, size, type) from a message. |
| **DownloadAttachment** | Download attachment content as base64. |
| **UploadAttachment** | Upload a file attachment under 3 MB (base64). |
| **UploadLargeAttachment** | Upload a file attachment 3–150 MB using chunked upload (base64). |
| **DeleteAttachment** | Delete an attachment from a message. |
| **AddDraftAttachments** | Add attachments (URI) to an existing draft. |

---

## mcp_SharePointListsTools — 13 tools

| Tool | Description |
|------|-------------|
| **searchSitesByName** | Find SharePoint sites by name, title, or partial name. Primary site discovery tool. |
| **getSiteByPath** | Resolve a SharePoint site by exact hostname and server-relative path. |
| **listSubsites** | List child sites (subsites) for a given site. |
| **listLists** | Get all lists available on a specific SharePoint site. |
| **createList** | Create a new SharePoint list on a site. |
| **listListColumns** | List column definitions for a specific SharePoint list. |
| **createListColumn** | Create a new column in a SharePoint list. |
| **editListColumn** | Update an existing column definition on a SharePoint list. |
| **deleteListColumn** | Delete a column from a SharePoint list. |
| **listListItems** | Get items (rows/records) from a SharePoint list. |
| **createListItem** | Create a new item in a SharePoint list. |
| **updateListItem** | Update fields of an existing item in a SharePoint list. |
| **deleteListItem** | Delete an item from a SharePoint list. |

---

## mcp_WordServer — 4 tools

| Tool | Description |
|------|-------------|
| **CreateDocument** | Create a new Word document in the user's OneDrive root from HTML or plain text. |
| **GetDocumentContent** | Fetch raw Word document (DOCX) content from OneDrive/SharePoint via sharing URL. |
| **AddComment** | Add a new comment in a Word document. |
| **ReplyToComment** | Reply to an existing comment in a Word document. |

---

## mcp_TeamsTools — 25 tools

**Work IQ Teams** · Scope: `McpServers.Teams.All` · [Docs](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/teams)

### Chat tools

| Tool | Description |
|------|-------------|
| **mcp_graph_chat_addChatMember** | Add a member to a chat by user reference and optional role (member, owner). |
| **mcp_graph_chat_createChat** | Create a new Teams chat (`oneOnOne` requires exactly 2 members; group requires 3+). |
| **mcp_graph_chat_deleteChat** | Soft-delete a chat. Subject to tenant retention policies. |
| **mcp_graph_chat_deleteChatMessage** | Soft-delete a specific chat message by ID. |
| **mcp_graph_chat_getChat** | Retrieve a chat by ID (metadata: type, topic). |
| **mcp_graph_chat_getChatMessage** | Retrieve a specific message from a chat by ID. |
| **mcp_graph_chat_listChatMembers** | List participants in a chat (roles: member, owner, guest). |
| **mcp_graph_chat_listChatMessages** | List messages in a chat with optional `$top`, `$filter`, `$orderby`; paged. |
| **mcp_graph_chat_listChats** | List all chats visible to the caller with optional OData query params. |
| **mcp_graph_chat_postMessage** | Post a plain-text message to a chat. |
| **mcp_graph_chat_updateChat** | Update chat topic (group chats only). |
| **mcp_graph_chat_updateChatMessage** | Update a chat message with new plain-text content. |

### Channel and Team tools

| Tool | Description |
|------|-------------|
| **mcp_graph_teams_addChannelMember** | Add a member to a private or shared channel with optional owner role. |
| **mcp_graph_teams_createChannel** | Create a channel (standard, private, or shared) in a team. Private/shared require explicit members. |
| **mcp_graph_teams_createPrivateChannel** | Create a private channel; at least one owner must be in the members list. |
| **mcp_graph_teams_getChannel** | Retrieve a channel with optional `$select`/`$filter`. |
| **mcp_graph_teams_getTeam** | Retrieve team properties with optional `$select`/`$expand`. |
| **mcp_graph_teams_listChannelMembers** | List all members of a Teams channel (identity, roles, membership status). |
| **mcp_graph_teams_listChannelMessages** | List messages in a channel; supports `$top`, `$expand` for replies. |
| **mcp_graph_teams_listChannels** | List all channels in a team; private/shared only visible if caller is a member. |
| **mcp_graph_teams_listTeams** | List the teams a specific user has joined. |
| **mcp_graph_teams_postChannelMessage** | Post a plain-text message to a channel. |
| **mcp_graph_teams_replyToChannelMessage** | Reply to a channel message thread with plain-text content. |
| **mcp_graph_teams_updateChannel** | Update a channel's `displayName` or description. |
| **mcp_graph_teams_updateChannelMember** | Update a member's role in a private or shared channel. |

---

## mcp_OneDriveSharePointTools — 13 tools

**Work IQ OneDrive** · Scope: `McpServers.OneDriveSharePoint.All` · [Docs](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/onedrive)

All file ops limited to ≤5 MB. All operations target the authenticated user's personal OneDrive.

| Tool | Description |
|------|-------------|
| **getOnedrive** | Get OneDrive metadata, quota, and owner information. |
| **getFolderChildrenInMyOnedrive** | Enumerate up to 20 files and folders in a specified parent folder (default: root). |
| **findFileOrFolderInMyDrive** | Find a file or folder by partial or full name within the user's OneDrive. |
| **getFileOrFolderMetadataInMyOnedrive** | Get metadata of a file or folder by ID. |
| **getFileOrFolderMetadataByUrl** | Get metadata of a file or folder from a sharing URL (user must already have access). |
| **readSmallTextFileFromMyOnedrive** | Download a text file (≤5 MB) by driveItemId. |
| **createSmallTextFileInMyOnedrive** | Create/upload a text file (≤5 MB) with optional parent folder. |
| **createFolderInMyOnedrive** | Create a new folder; auto-appends numeric suffix on duplicate names. |
| **renameFileOrFolderInMyOnedrive** | Rename a file or folder with eTag concurrency control. |
| **deleteFileOrFolderInMyOnedrive** | Delete a file or folder with eTag concurrency control. |
| **moveSmallFileInMyOnedrive** | Move a file (≤5 MB) to another folder within the user's OneDrive. |
| **shareFileOrFolderInMyOnedrive** | Send a sharing invitation granting read or write access; optional email notification. |
| **setSensitivityLabelOnFileInMyOnedrive** | Apply or remove a sensitivity label on a file; requires licensing. |

---

## mcp_CopilotMCP — 1 tool

**Work IQ Copilot** · Scope: `McpServers.CopilotMCP.All` · Requires M365 Copilot license · [Docs](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/searchtools)

| Tool | Description |
|------|-------------|
| **CopilotChat** | Search and chat across the entire M365 ecosystem (SharePoint, OneDrive, email, Teams chats, files). Supports multi-turn conversations via `conversationId`, agent-specific context via `agentId`, and file grounding via `fileUris`. Use as the primary fallback when no workload-specific tool is available. |

---

## mcp_PowerPointServer — tools not yet documented

Scope: `McpServers.PowerPoint.All`

No public reference page as of April 2026. Expected to mirror `mcp_WordServer` and `mcp_ExcelServer` with tools for creating/reading presentations and adding comments. Reconnect the app to discover live tool definitions.

---

## mcp_FilesTools — tools not yet documented

Scope: `McpServers.Files.All`

No public reference page as of April 2026. Likely covers cross-drive file operations not scoped to a single OneDrive or SharePoint document library. Reconnect the app to discover live tool definitions.

---

## mcp_MeTools — 6 tools

**Work IQ User** · Scope: `McpServers.Me.All` · [Docs](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/me)

| Tool | Description |
|------|-------------|
| **mcp_graph_getMyProfile** | Get the signed-in user's own profile. Supports `$select` and `$expand`. |
| **mcp_graph_getMyManager** | Get the signed-in user's manager. |
| **mcp_graph_getUserProfile** | Get any user's profile by object ID or UPN. Supports `$select` and `$expand` (manager or directReports; one at a time). |
| **mcp_graph_getUsersManager** | Get the manager of a specified user by object ID or UPN. |
| **mcp_graph_getDirectReports** | List direct reports of a specified user by object ID or UPN. |
| **mcp_graph_listUsers** | List org users with `$select`, `$filter`, `$top`, `$orderby`, free-text `$search` (format: `"displayName:John"`). Auto-retries with `$filter` if `$search` fails. |

---

## mcp_DASearchTools — tools not yet documented

Scope: `McpServers.DASearch.All` · Requires M365 Copilot license

No public reference page as of April 2026. DASearch = Declarative Agent search — likely exposes semantic search over Copilot-indexed content scoped to Declarative Agent knowledge sources. Reconnect the app to discover live tool definitions.

---

## mcp_DataverseTools — 11 tools

**Dataverse MCP Server** · Scope: `McpServers.Dataverse.All` · Requires Power Platform / Dataverse · [Docs](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/dataverse)

| Tool | Description |
|------|-------------|
| **list_tables** | List all tables available in the connected Dataverse environment. |
| **describe_table** | Retrieve the complete T-SQL schema for a table (fields, types, relationships). |
| **read_query** | Execute SELECT statements to query Dataverse data with filters and conditions. |
| **search** | Keyword-based search across Dataverse to locate records, entities, or fields. |
| **fetch** | Retrieve complete record details by table name and record ID. |
| **create_record** | Insert a new record into a Dataverse table; returns the new record's GUID. |
| **update_record** | Update fields in an existing record by GUID. |
| **delete_record** | Delete a specific record by GUID. Supports GDPR/retention compliance. |
| **create_table** | Create a new Dataverse table with a defined schema. |
| **update_table** | Modify an existing table's schema (add columns, rename fields, update constraints). |
| **delete_table** | Permanently delete a table and all its data. Restricted to permissioned users. |

---

> **Note on the following 8 servers**: tool definitions are sourced from the [Work IQ MCP reference docs](https://learn.microsoft.com/en-us/microsoft-agent-365/tooling-servers-overview) (preview, last updated March 2026). Actual tool names returned by the live server may differ slightly. Reconnect the app to populate real-time discovery.

### License / Entitlement Requirements

Some servers are gated by M365 licensing beyond a standard E3/E5 seat:

| Server | Requires |
|--------|----------|
| mcp_CopilotMCP | Microsoft 365 Copilot license (E3/E5 + Copilot add-on) |
| mcp_DASearchTools | M365 Copilot (Declarative Agent search) |
| mcp_DataverseTools | Power Platform / Dataverse (separate from M365) |
| mcp_TeamsTools | Teams license (usually included in E3/E5, but may need separate enablement) |
