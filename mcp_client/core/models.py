from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject, Signal


# ── Signal registry ─────────────────────────────────────────────────


class SignalRegistry(QObject):
    """Central signal bus for cross-component communication."""

    # Chat
    message_received = Signal(str, str)       # role, content
    tool_called = Signal(str, str)            # tool_name, result_text
    quick_action_triggered = Signal(str)      # prompt text

    # Connection
    connection_changed = Signal(bool)         # connected
    discovery_progress = Signal(str)          # status text
    discovery_complete = Signal(int, int)     # server_count, tool_count
    device_code_prompt = Signal(str, str)     # verification_uri, user_code
    server_selection_changed = Signal(set)    # enabled server names

    # Errors
    error_occurred = Signal(str, str)         # title, message

    # App lifecycle
    app_closing = Signal()


_registry: SignalRegistry | None = None


def get_signal_registry() -> SignalRegistry:
    global _registry
    if _registry is None:
        _registry = SignalRegistry()
    return _registry


# ── Base model ──────────────────────────────────────────────────────


class BaseModel(QObject):
    property_changed = Signal(str, object)  # name, value
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._updated_at = datetime.now()

    def _set_property(self, name: str, old: Any, new: Any) -> bool:
        if old != new:
            self._updated_at = datetime.now()
            self.property_changed.emit(name, new)
            self.changed.emit()
            return True
        return False


# ── Chat model ──────────────────────────────────────────────────────


@dataclass
class ChatMessage:
    role: str            # "user", "assistant", "tool", "system"
    content: str
    tool_name: str = ""  # set for role="tool"


class ChatModel(BaseModel):
    message_added = Signal(object)  # ChatMessage

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._messages: list[ChatMessage] = []
        self._busy = False

    @property
    def messages(self) -> list[ChatMessage]:
        return list(self._messages)

    @property
    def busy(self) -> bool:
        return self._busy

    @busy.setter
    def busy(self, value: bool) -> None:
        if self._set_property("busy", self._busy, value):
            self._busy = value

    def add_message(self, role: str, content: str, tool_name: str = "") -> None:
        msg = ChatMessage(role=role, content=content, tool_name=tool_name)
        self._messages.append(msg)
        self.message_added.emit(msg)
        self.changed.emit()

    def clear(self) -> None:
        self._messages.clear()
        self.changed.emit()


# ── Connection model ────────────────────────────────────────────────


class ConnectionModel(BaseModel):
    """Tracks MCP server connection state and discovered tools."""

    status_changed = Signal(str)  # status text

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._connected = False
        self._status = "Disconnected"
        self._servers: list[dict] = []
        self._tool_count = 0
        self._enabled_servers: set[str] = set()

    @property
    def connected(self) -> bool:
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        if self._set_property("connected", self._connected, value):
            self._connected = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if self._set_property("status", self._status, value):
            self._status = value
            self.status_changed.emit(value)

    @property
    def servers(self) -> list[dict]:
        return list(self._servers)

    @property
    def tool_count(self) -> int:
        return self._tool_count

    def set_servers(self, servers: list[dict]) -> None:
        self._servers = servers
        self._tool_count = sum(len(s.get("tools", [])) for s in servers)
        self._enabled_servers = {s["name"] for s in servers}
        self.changed.emit()

    @property
    def enabled_servers(self) -> set[str]:
        return set(self._enabled_servers)

    def set_server_enabled(self, server_name: str, enabled: bool) -> None:
        if enabled:
            self._enabled_servers.add(server_name)
        else:
            self._enabled_servers.discard(server_name)
        self.changed.emit()
