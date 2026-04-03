from __future__ import annotations

import json
import logging
from typing import Any

from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI

from mcp_bridge.bridge import McpProxyServer
from mcp_bridge.config import AppConfig

log = logging.getLogger(__name__)

_COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"
_MAX_HISTORY_CHARS = 120_000
_MAX_TOOL_RESULT_CHARS = 12_000


class OpenAIService:
    """Azure OpenAI GPT chat with MCP tool-calling loop."""

    def __init__(self, config: AppConfig, proxy: McpProxyServer) -> None:
        self._config = config
        self._proxy = proxy
        self._server_filter: set[str] | None = None
        self._messages: list[dict[str, Any]] = []
        self._client: AzureOpenAI | None = None
        self._reset_system_prompt()

    def set_server_filter(self, enabled_servers: set[str]) -> None:
        """Restrict which servers' tools are sent to the LLM."""
        all_servers = set(self._proxy.server_names())
        if enabled_servers >= all_servers:
            self._server_filter = None
        else:
            self._server_filter = set(enabled_servers)
        self._update_system_prompt()
        log.info(
            "Server filter updated: %s",
            "all" if self._server_filter is None else f"{len(enabled_servers)} servers",
        )

    def _reset_system_prompt(self) -> None:
        """Build a system prompt that reflects the tools actually available."""
        self._messages = [{"role": "system", "content": self._build_system_guidance()}]

    def _update_system_prompt(self) -> None:
        """Update the system message in-place without clearing history."""
        if self._messages and self._messages[0].get("role") == "system":
            self._messages[0]["content"] = self._build_system_guidance()
        else:
            self._messages.insert(0, {"role": "system", "content": self._build_system_guidance()})

    def _build_system_guidance(self) -> str:
        tool_names = [t["name"] for t in self._proxy.list_tools(self._server_filter)]
        if tool_names:
            tool_list = ", ".join(tool_names)
            guidance = (
                "You are a helpful assistant connected to Microsoft 365 via MCP tools. "
                "You can interact with M365 services like Mail, Calendar, Teams, Word, "
                "Excel, OneDrive, SharePoint, Planner, and more. "
                f"Currently available tools: {tool_list}. "
                "Use tools proactively when the user's request matches a tool's purpose. "
                "If you don't have a tool for a specific service, let the user know "
                "which services you CAN help with based on your available tools."
            )
        else:
            guidance = (
                "You are a helpful assistant for Microsoft 365. No MCP tools are "
                "currently connected. Tell the user to click Connect to discover "
                "available tools for Mail, Calendar, Teams, Word, Excel, and more."
            )
        return guidance

    def _get_client(self) -> AzureOpenAI:
        if self._client is not None:
            return self._client

        if not self._config.azure_openai_endpoint:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT not configured")

        if self._config.azure_openai_auth_mode != "azure-cli":
            raise RuntimeError(
                "Unsupported AZURE_OPENAI_AUTH_MODE. Only 'azure-cli' is supported."
            )

        # Entra auth via Azure CLI (requires `az login`)
        credential = AzureCliCredential()
        token_provider = get_bearer_token_provider(credential, _COGNITIVE_SCOPE)

        self._client = AzureOpenAI(
            azure_endpoint=self._config.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self._config.azure_openai_api_version,
        )
        return self._client

    def _build_tools(self) -> list[dict]:
        """Convert proxy tool defs to OpenAI function-calling format."""
        tools = []
        for t in self._proxy.list_tools(self._server_filter):
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
                    },
                }
            )
        return tools

    @staticmethod
    def _message_content_length(message: dict[str, Any]) -> int:
        content = message.get("content")
        if isinstance(content, str):
            return len(content)
        if isinstance(content, list):
            total = 0
            for item in content:
                if isinstance(item, dict):
                    total += len(str(item.get("text", "")))
                else:
                    total += len(str(item))
            return total
        return len(json.dumps(message, ensure_ascii=False, default=str))

    def _trim_history(self) -> None:
        if len(self._messages) <= 1:
            return

        trimmed = [self._messages[0]]
        retained: list[dict[str, Any]] = []
        total_chars = self._message_content_length(self._messages[0])

        for message in reversed(self._messages[1:]):
            message_size = self._message_content_length(message)
            if retained and total_chars + message_size > _MAX_HISTORY_CHARS:
                break
            retained.append(message)
            total_chars += message_size

        trimmed.extend(reversed(retained))

        dropped = len(self._messages) - len(trimmed)
        if dropped > 0:
            log.info("Trimmed %d old chat messages before Azure OpenAI request", dropped)
        self._messages = trimmed

    @staticmethod
    def _truncate_tool_result(text: str) -> str:
        if len(text) <= _MAX_TOOL_RESULT_CHARS:
            return text

        omitted = len(text) - _MAX_TOOL_RESULT_CHARS
        suffix = f"\n\n[truncated {omitted} characters from tool output]"
        return text[: _MAX_TOOL_RESULT_CHARS - len(suffix)] + suffix

    async def chat(self, user_message: str) -> str:
        """Send a user message and execute the tool-calling loop."""
        self._messages.append({"role": "user", "content": user_message})

        client = self._get_client()
        tools = self._build_tools()

        for _ in range(10):  # max tool-call rounds
            self._trim_history()
            kwargs: dict[str, Any] = {
                "model": self._config.azure_openai_deployment,
                "messages": self._messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                assistant_text = msg.content or ""
                self._messages.append({"role": "assistant", "content": assistant_text})
                return assistant_text

            self._messages.append(msg.model_dump())

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    fn_args = {}

                log.info("Tool call: %s(%s)", fn_name, fn_args)
                result = await self._proxy.call_tool(fn_name, fn_args)
                result_text = "\n".join(
                    c.get("text", "") for c in result.get("content", [])
                )
                result_text = self._truncate_tool_result(result_text)

                self._messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    }
                )

        return "Maximum tool-call rounds reached."

    def clear_history(self) -> None:
        """Reset conversation and rebuild the system prompt."""
        self._reset_system_prompt()
