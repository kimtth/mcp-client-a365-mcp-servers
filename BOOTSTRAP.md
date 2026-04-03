# Bootstrap

Create a GUI application for demonstrating interactions with Agent 365 MCP Servers.

## Architecture

```
┌─────────────────┐    stdio     ┌──────────────────┐    HTTPS + Auth     ┌─────────────────────────┐
│  PySide6 GUI    │ ◄──────────► │  MCP Proxy Bridge │ ◄────────────────► │  Agent 365 MCP Servers  │
│  (Client)       │  MCP protocol│  (Python / Rust)  │  StreamableHTTP    │  (Mail, Calendar, Word, │
└─────────────────┘              └────────┬─────────┘                     │   Teams, SharePoint...) │
                                          │                               └─────────────────────────┘
                                          │ Azure CLI
                                          │ Credential
                                          ▼
                                 ┌──────────────────┐
                                 │  Azure OpenAI    │
                                 │  (AI Foundry)    │
                                 └──────────────────┘
```

## Client

- Single GUI application built with **PySide6**.
- Interacts with servers via the Bridge layer.

## Bridge

- Intermediary between the Client and the MCP Servers.
- Converts natural language requests into MCP payloads, interacting with the LLM through `stdio`.
- Must be implemented in both **Python** and **Rust** (configurable from the Client).
  - **Note:** Do not create the Rust implementation during bootstrapping.
- Reference: See sample code in `ref\Agent365-Bridge`.

## LLM

- **Azure OpenAI** deployed on Azure AI Foundry.
- Uses the GPT-5 API specification (updated default arguments compared to prior versions).
- Authentication uses **Azure CLI credential** (no API key required).
- MCP server authentication: Refer to `ref\Set Up MCP Server Authentication - Microsoft Foundry _ Microsoft Learn.url`.

## Server

- **Agent 365 MCP Servers** — a predefined set of servers provided by Microsoft 365.
- Use **A365 CLI** if you need to get any more information of current resources in Azure.
- Predefined identities for connecting with Agent 365 Servers are specified in the project config.
- Reference: See `ref\Accessing Agent 365 MCP Servers in Postman.url`.
- https://learn.microsoft.com/en-us/microsoft-agent-365/developer/reference/cli/

## References

- [MCP (Model Context Protocol)](https://modelcontextprotocol.io)
