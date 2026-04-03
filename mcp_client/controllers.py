from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QThread, Signal

from mcp_bridge.bridge import McpService
from mcp_client.llm import OpenAIService
from mcp_client.core.models import ChatModel, ConnectionModel, SignalRegistry

log = logging.getLogger(__name__)


# ── Base controller ─────────────────────────────────────────────────


class BaseController(QObject):
    def __init__(self, signals: SignalRegistry, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._signals = signals
        self._views: list = []

    def register_view(self, view) -> None:
        if view not in self._views:
            self._views.append(view)
            view.set_controller(self)

    def notify_views(self) -> None:
        for view in self._views:
            view.refresh()

    def initialize(self) -> None:
        pass


# ── Chat controller ─────────────────────────────────────────────────


class _ChatWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, service: OpenAIService, message: str) -> None:
        super().__init__()
        self._service = service
        self._message = message

    def run(self) -> None:
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._service.chat(self._message))
            self.finished.emit(result)
        except Exception as exc:
            log.exception("Chat error")
            self.error.emit(str(exc))
        finally:
            loop.close()


class ChatController(BaseController):
    def __init__(
        self,
        signals: SignalRegistry,
        model: ChatModel,
        openai_service: OpenAIService,
    ) -> None:
        super().__init__(signals)
        self._model = model
        self._openai = openai_service
        self._worker: _ChatWorker | None = None

    def register_view(self, view) -> None:
        super().register_view(view)
        self._model.message_added.connect(view.append_message)

    def send_message(self, text: str) -> None:
        if self._model.busy:
            return

        self._model.add_message("user", text)
        self._model.busy = True

        for v in self._views:
            v.set_busy(True)

        self._worker = _ChatWorker(self._openai, text)
        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_response(self, text: str) -> None:
        self._model.add_message("assistant", text)
        self._model.busy = False
        for v in self._views:
            v.set_busy(False)

    def _on_error(self, msg: str) -> None:
        self._model.add_message("assistant", f"Error: {msg}")
        self._model.busy = False
        for v in self._views:
            v.set_busy(False)
        self._signals.error_occurred.emit("Chat Error", msg)

    def clear_history(self) -> None:
        self._model.clear()
        self._openai.clear_history()
        for v in self._views:
            v.clear_messages()


# ── Connection controller ───────────────────────────────────────────


class _DiscoveryWorker(QThread):
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, mcp_service: McpService) -> None:
        super().__init__()
        self._mcp_service = mcp_service

    def run(self) -> None:
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.progress.emit("Discovering Agent 365 MCP servers...")
            servers = loop.run_until_complete(self._mcp_service.discover())
            self.finished.emit(servers)
        except Exception as exc:
            log.exception("Discovery error")
            self.error.emit(str(exc))
        finally:
            loop.close()


class ConnectionController(BaseController):
    def __init__(
        self,
        signals: SignalRegistry,
        model: ConnectionModel,
        mcp_service: McpService,
    ) -> None:
        super().__init__(signals)
        self._model = model
        self._mcp_service = mcp_service
        self._worker: _DiscoveryWorker | None = None

    def register_view(self, view) -> None:
        super().register_view(view)
        self._model.status_changed.connect(view.update_status)

    def toggle_connection(self) -> None:
        if self._model.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self) -> None:
        self._model.status = "Connecting..."
        for v in self._views:
            v.set_connected(False)

        self._worker = _DiscoveryWorker(self._mcp_service)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_discovered)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _disconnect(self) -> None:
        self._model.connected = False
        self._model.status = "Disconnected"
        self._model.set_servers([])
        for v in self._views:
            v.set_connected(False)
            v.populate_servers(self._model)
        self._signals.connection_changed.emit(False)

    def _on_progress(self, text: str) -> None:
        self._model.status = text
        self._signals.discovery_progress.emit(text)

    def _on_discovered(self, servers) -> None:
        server_data = []
        for s in servers:
            server_data.append(
                {
                    "name": s.config.mcp_server_name,
                    "tools": [
                        {"name": t.name, "description": t.description}
                        for t in s.tools
                    ],
                }
            )

        self._model.set_servers(server_data)
        self._model.connected = True
        self._model.status = (
            f"Connected — {len(servers)} servers, {self._model.tool_count} tools"
        )

        for v in self._views:
            v.set_connected(True)
            v.populate_servers(self._model)

        self._signals.connection_changed.emit(True)
        self._signals.discovery_complete.emit(len(servers), self._model.tool_count)

    def _on_error(self, msg: str) -> None:
        self._model.connected = False
        self._model.status = f"Error: {msg}"
        for v in self._views:
            v.set_connected(False)
        self._signals.error_occurred.emit("Connection Error", msg)

    def set_server_enabled(self, server_name: str, enabled: bool) -> None:
        self._model.set_server_enabled(server_name, enabled)
        self._signals.server_selection_changed.emit(self._model.enabled_servers)

    def select_all_servers(self) -> None:
        for server in self._model.servers:
            self._model.set_server_enabled(server["name"], True)
        self._signals.server_selection_changed.emit(self._model.enabled_servers)
        for v in self._views:
            v.populate_servers(self._model)

    def deselect_all_servers(self) -> None:
        for server in self._model.servers:
            self._model.set_server_enabled(server["name"], False)
        self._signals.server_selection_changed.emit(self._model.enabled_servers)
        for v in self._views:
            v.populate_servers(self._model)
