from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from mcp_bridge.auth import TokenProvider
from mcp_bridge.bridge import McpService
from mcp_bridge.config import load_config
from mcp_client.core.models import ChatModel, ConnectionModel, get_signal_registry
from mcp_client.controllers import ChatController, ConnectionController
from mcp_client.llm import OpenAIService
from mcp_client.ui.theme import build_stylesheet
from mcp_client.ui.views import ChatView, ConnectionView, MainWindow

log = logging.getLogger(__name__)


class McpClientApp:
    """Singleton application bootstrap and DI container."""

    _instance: McpClientApp | None = None

    def __new__(cls) -> McpClientApp:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._qt_app: QApplication | None = None
        self._signals = get_signal_registry()

    def run(self) -> int:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(name)s] %(message)s",
            stream=sys.stderr,
        )
        # Suppress noisy HTTP-level polling logs from azure SDK (device code 400s are normal)
        logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
        logging.getLogger("azure.identity").setLevel(logging.WARNING)

        self._qt_app = QApplication(sys.argv)
        self._qt_app.setStyleSheet(build_stylesheet())

        # Config & services
        config = load_config()
        log.info("Endpoint: %s", config.mcp_platform_endpoint)
        log.info("Servers in manifest: %d", len(config.manifest.mcp_servers))
        log.info("MCP auth mode: %s", config.mcp_auth_mode)
        log.info("Azure OpenAI auth mode: %s", config.azure_openai_auth_mode)

        token_provider = TokenProvider(config)
        mcp_service = McpService(config, token_provider)
        openai_service = OpenAIService(config, mcp_service.proxy)

        # Wire device-code callback to emit Qt signal (thread-safe via signal)
        token_provider._device_code_callback = lambda uri, code: (
            self._signals.device_code_prompt.emit(uri, code)
        )

        # Models
        chat_model = ChatModel()
        connection_model = ConnectionModel()

        # Views
        chat_view = ChatView(self._signals)
        connection_view = ConnectionView(self._signals)

        # Controllers
        chat_ctrl = ChatController(self._signals, chat_model, openai_service)
        chat_ctrl.register_view(chat_view)
        self._signals.quick_action_triggered.connect(chat_ctrl.send_message)

        conn_ctrl = ConnectionController(self._signals, connection_model, mcp_service)
        conn_ctrl.register_view(connection_view)

        # When server selection changes, update which tools the LLM sees
        self._signals.server_selection_changed.connect(openai_service.set_server_filter)

        # Main window
        window = MainWindow(self._signals, chat_view, connection_view)
        window.show()

        return self._qt_app.exec()
