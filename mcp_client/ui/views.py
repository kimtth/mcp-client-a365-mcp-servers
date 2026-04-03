from __future__ import annotations

import html

from PySide6.QtCore import Qt, Signal as QtSignal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mcp_client.core.models import ChatMessage, ConnectionModel, SignalRegistry
from mcp_client.ui.theme import COLORS, msg_html_assistant, msg_html_tool, msg_html_user


QUICK_ACTIONS: list[tuple[str, str]] = [
    ("📧 MAIL", "List my recent unread emails"),
    ("📅 CALENDAR", "What meetings do I have today?"),
    ("💬 TEAMS", "Show my recent Teams messages"),
    ("📝 WORD", "List my recent Word documents"),
    ("📊 EXCEL", "List my recent Excel workbooks"),
    ("🎞️ POWERPOINT", "List my recent presentations"),
    ("☁️ ONEDRIVE", "List my recent OneDrive files"),
    ("📋 SP LISTS", "Show my SharePoint lists"),
    ("📁 FILES", "Search for my recent files"),
    ("🧠 KNOWLEDGE", "Search organizational knowledge"),
    ("👤 PROFILE", "Show my profile information"),
    ("🔍 SEARCH", "Search across my Microsoft 365 data"),
    ("🗄️ DATAVERSE", "List available Dataverse tables"),
    ("🤖 COPILOT", "What can you help me with?"),
]


def _build_panel(title: str, subtitle: str, object_name: str) -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
    panel.setObjectName(object_name)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)

    title_block = QVBoxLayout()
    title_block.setSpacing(2)

    title_label = QLabel(title)
    title_label.setObjectName("app_title")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("app_subtitle")

    title_block.addWidget(title_label)
    title_block.addWidget(subtitle_label)
    layout.addLayout(title_block)
    return panel, layout


class BaseView(QWidget):
    error_occurred = QtSignal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        raise NotImplementedError

    def _connect_signals(self) -> None:
        pass

    def set_controller(self, controller) -> None:
        self._controller = controller

    def refresh(self) -> None:
        pass


class ChatView(BaseView):
    def __init__(self, signals: SignalRegistry, parent=None) -> None:
        self._signals = signals
        super().__init__(parent)

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        panel, panel_layout = _build_panel(
            "AGENT 365 // CHAT CONSOLE",
            "MULTI-SERVICE M365 TOOL ORCHESTRATION",
            "chat_panel",
        )

        intro = QLabel(
            "A precision console for Microsoft 365 operations. Use direct prompts or fire a service chip to issue a command sequence."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(
            f"color: {COLORS['text_secondary']}; line-height: 1.45; padding-bottom: 4px;"
        )
        panel_layout.addWidget(intro)

        chips_header = QLabel("QUICK ACTION BUS")
        chips_header.setProperty("sectionHeader", True)
        panel_layout.addWidget(chips_header)

        chips_grid = QGridLayout()
        chips_grid.setHorizontalSpacing(6)
        chips_grid.setVerticalSpacing(6)
        self._quick_action_buttons: list[tuple[QPushButton, str]] = []
        for index, (label, prompt) in enumerate(QUICK_ACTIONS):
            button = QPushButton(label)
            button.setProperty("quickAction", True)
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(prompt)
            button.setFixedHeight(24)
            self._quick_action_buttons.append((button, prompt))
            chips_grid.addWidget(button, index // 7, index % 7)
        panel_layout.addLayout(chips_grid)

        feed_header = QLabel("LIVE EXCHANGE")
        feed_header.setProperty("sectionHeader", True)
        panel_layout.addWidget(feed_header)

        self._messages_browser = QTextBrowser()
        self._messages_browser.setObjectName("messages_browser")
        self._messages_browser.setOpenExternalLinks(True)
        self._messages_browser.setPlaceholderText("Conversation feed will appear here.")
        panel_layout.addWidget(self._messages_browser, 1)

        self._typing_status = QLabel()
        self._typing_status.setObjectName("status_label")
        self._typing_status.setTextFormat(Qt.RichText)
        self._typing_status.setText(self._status_html("READY", COLORS["success"]))
        panel_layout.addWidget(self._typing_status)

        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        self._message_input = QLineEdit()
        self._message_input.setObjectName("message_input")
        self._message_input.setPlaceholderText(
            'Type a message... (e.g. "List my recent emails")'
        )

        self._clear_btn = QPushButton("PURGE")
        self._clear_btn.setObjectName("clear_btn")
        self._clear_btn.setCursor(Qt.PointingHandCursor)

        self._send_btn = QPushButton("EXECUTE")
        self._send_btn.setObjectName("send_btn")
        self._send_btn.setCursor(Qt.PointingHandCursor)

        input_layout.addWidget(self._message_input, 1)
        input_layout.addWidget(self._clear_btn)
        input_layout.addWidget(self._send_btn)
        panel_layout.addWidget(input_frame)

        root.addWidget(panel)

    def _connect_signals(self) -> None:
        self._send_btn.clicked.connect(self._on_send)
        self._clear_btn.clicked.connect(self._on_clear)
        self._message_input.returnPressed.connect(self._on_send)
        for button, prompt in self._quick_action_buttons:
            button.clicked.connect(
                lambda _checked=False, p=prompt: self._signals.quick_action_triggered.emit(p)
            )

    def _status_html(self, label: str, color: str) -> str:
        return (
            f'<span style="font-family: monospace; font-size: 11px; color: {color}; '
            f'letter-spacing: 1px; font-weight: 700;">[{label}]</span>'
        )

    def _on_send(self) -> None:
        text = self._message_input.text().strip()
        if text and self._controller:
            self._message_input.clear()
            self._controller.send_message(text)

    def _on_clear(self) -> None:
        if self._controller:
            self._controller.clear_history()

    def append_message(self, msg: ChatMessage) -> None:
        safe = html.escape(msg.content).replace("\n", "<br>")
        if msg.role == "user":
            self._messages_browser.append(msg_html_user(safe))
        elif msg.role == "assistant":
            self._messages_browser.append(msg_html_assistant(safe))
        elif msg.role == "tool":
            label = html.escape(msg.tool_name) if msg.tool_name else "tool"
            self._messages_browser.append(msg_html_tool(label, safe))
        else:
            self._messages_browser.append(msg_html_assistant(safe))

        scrollbar = self._messages_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_busy(self, busy: bool) -> None:
        self._send_btn.setEnabled(not busy)
        self._message_input.setEnabled(not busy)
        if busy:
            self._typing_status.setText(self._status_html("PROCESSING", COLORS["warning"]))
            self._message_input.setPlaceholderText("Agent is executing tools...")
        else:
            self._typing_status.setText(self._status_html("READY", COLORS["success"]))
            self._message_input.setPlaceholderText(
                'Type a message... (e.g. "List my recent emails")'
            )

    def clear_messages(self) -> None:
        self._messages_browser.clear()
        self._typing_status.setText(self._status_html("READY", COLORS["success"]))


class DeviceCodeDialog(QDialog):
    """Modal dialog shown during device-code authentication."""

    def __init__(self, verification_uri: str, user_code: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sign In Required")
        self.setFixedSize(420, 200)
        self.setStyleSheet(
            f"background: {COLORS['bg_surface']}; color: {COLORS['text_primary']};"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("DEVICE CODE AUTHENTICATION")
        header.setStyleSheet(
            f"color: {COLORS['accent']}; font-weight: 700; font-size: 12px; "
            "letter-spacing: 2px;"
        )
        layout.addWidget(header)

        info = QLabel(
            "A browser window has been opened.\n"
            "Enter the code below to complete sign-in:"
        )
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        code_label = QLabel(user_code)
        code_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-family: 'JetBrains Mono', monospace; "
            f"font-size: 24px; font-weight: 700; background: {COLORS['bg_elevated']}; "
            "padding: 8px 16px; letter-spacing: 4px;"
        )
        code_label.setAlignment(Qt.AlignCenter)
        code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(code_label)

        hint = QLabel(f'<a href="{verification_uri}" style="color: {COLORS["accent"]};">{verification_uri}</a>')
        hint.setOpenExternalLinks(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 11px;")
        layout.addWidget(hint)


class ConnectionView(BaseView):
    def __init__(self, signals: SignalRegistry, parent=None) -> None:
        self._signals = signals
        self._device_code_dialog: DeviceCodeDialog | None = None
        super().__init__(parent)

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        panel, panel_layout = _build_panel(
            "SERVICE MATRIX",
            "DISCOVERY / STATUS / TOOL INVENTORY",
            "sidebar_panel",
        )

        status_row = QHBoxLayout()
        status_row.setSpacing(10)

        self._status_label = QLabel()
        self._status_label.setObjectName("status_label")
        self._status_label.setTextFormat(Qt.RichText)
        self.update_status("Disconnected")

        self._connect_btn = QPushButton("LINK")
        self._connect_btn.setObjectName("connect_btn")
        self._connect_btn.setCursor(Qt.PointingHandCursor)

        status_row.addWidget(self._status_label, 1)
        status_row.addWidget(self._connect_btn)
        panel_layout.addLayout(status_row)

        metrics_header = QLabel("DISCOVERY METRICS")
        metrics_header.setProperty("sectionHeader", True)
        panel_layout.addWidget(metrics_header)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(24)

        tools_box = QVBoxLayout()
        self._tools_count = QLabel("0")
        self._tools_count.setObjectName("tools_count")
        tools_unit = QLabel("TOOLS")
        tools_unit.setObjectName("tools_unit")
        tools_box.addWidget(self._tools_count)
        tools_box.addWidget(tools_unit)

        servers_box = QVBoxLayout()
        self._servers_count = QLabel("0")
        self._servers_count.setObjectName("tools_count")
        servers_unit = QLabel("SERVERS")
        servers_unit.setObjectName("tools_unit")
        servers_box.addWidget(self._servers_count)
        servers_box.addWidget(servers_unit)

        metrics_row.addLayout(tools_box)
        metrics_row.addLayout(servers_box)
        metrics_row.addStretch(1)
        panel_layout.addLayout(metrics_row)

        inventory_header = QLabel("SERVER INVENTORY")
        inventory_header.setProperty("sectionHeader", True)
        panel_layout.addWidget(inventory_header)

        sel_row = QHBoxLayout()
        sel_row.setSpacing(6)
        self._select_all_btn = QPushButton("SELECT ALL")
        self._select_all_btn.setObjectName("clear_btn")
        self._deselect_all_btn = QPushButton("DESELECT ALL")
        self._deselect_all_btn.setObjectName("clear_btn")
        sel_row.addWidget(self._select_all_btn)
        sel_row.addWidget(self._deselect_all_btn)
        sel_row.addStretch(1)
        panel_layout.addLayout(sel_row)

        self._servers_tree = QTreeWidget()
        self._servers_tree.setObjectName("servers_tree")
        self._servers_tree.setColumnCount(2)
        self._servers_tree.setHeaderLabels(["NODE", "TOOL"])
        self._servers_tree.setRootIsDecorated(True)
        self._servers_tree.header().setStretchLastSection(True)
        self._servers_tree.header().setMinimumSectionSize(160)
        panel_layout.addWidget(self._servers_tree, 1)

        root.addWidget(panel)

    def _connect_signals(self) -> None:
        self._connect_btn.clicked.connect(self._on_connect)
        self._signals.device_code_prompt.connect(self._show_device_code_dialog)
        self._signals.connection_changed.connect(self._dismiss_device_code_dialog)
        self._signals.error_occurred.connect(self._dismiss_device_code_dialog)
        self._servers_tree.itemChanged.connect(self._on_server_check_changed)
        self._select_all_btn.clicked.connect(self._on_select_all)
        self._deselect_all_btn.clicked.connect(self._on_deselect_all)

    def _on_select_all(self) -> None:
        if self._controller:
            self._controller.select_all_servers()

    def _on_deselect_all(self) -> None:
        if self._controller:
            self._controller.deselect_all_servers()

    def _on_server_check_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or item.parent() is not None:
            return
        server_name = item.text(0)
        enabled = item.checkState(0) == Qt.Checked
        if self._controller:
            self._controller.set_server_enabled(server_name, enabled)

    def _show_device_code_dialog(self, verification_uri: str, user_code: str) -> None:
        self._dismiss_device_code_dialog()
        self._device_code_dialog = DeviceCodeDialog(verification_uri, user_code, self.window())
        self._device_code_dialog.show()

    def _dismiss_device_code_dialog(self, *_args) -> None:
        if self._device_code_dialog:
            self._device_code_dialog.close()
            self._device_code_dialog = None

    def _on_connect(self) -> None:
        if self._controller:
            self._controller.toggle_connection()

    def update_status(self, status: str) -> None:
        normalized = status.lower()
        if normalized.startswith("connected"):
            color = COLORS["success"]
            tone = "ONLINE"
        elif normalized.startswith("error"):
            color = COLORS["error"]
            tone = "FAULT"
        elif "connecting" in normalized or "discovering" in normalized:
            color = COLORS["warning"]
            tone = "SYNC"
        else:
            color = COLORS["text_secondary"]
            tone = "IDLE"

        self._status_label.setText(
            f'<span style="color:{color}; font-family: monospace; font-size: 11px; '
            f'font-weight:700; letter-spacing:1px;">[{tone}]</span> '
            f'<span style="color:{COLORS["text_secondary"]};">{html.escape(status)}</span>'
        )

    def set_connected(self, connected: bool) -> None:
        self._connect_btn.setText("UNLINK" if connected else "LINK")

    def populate_servers(self, model: ConnectionModel) -> None:
        self._servers_tree.blockSignals(True)
        self._servers_tree.clear()
        self._tools_count.setText(str(model.tool_count))
        self._servers_count.setText(str(len(model.servers)))

        enabled = model.enabled_servers
        for server_info in model.servers:
            tool_count = len(server_info.get("tools", []))
            server_item = QTreeWidgetItem([server_info["name"], f"{tool_count} tools"])
            server_item.setFlags(server_item.flags() | Qt.ItemIsUserCheckable)
            server_item.setCheckState(
                0, Qt.Checked if server_info["name"] in enabled else Qt.Unchecked
            )
            for tool in server_info.get("tools", []):
                tool_name = tool if isinstance(tool, str) else tool.get("name", "")
                tool_desc = "" if isinstance(tool, str) else tool.get("description", "")
                QTreeWidgetItem(server_item, [tool_name, tool_desc])
            self._servers_tree.addTopLevelItem(server_item)

        self._servers_tree.collapseAll()
        self._servers_tree.resizeColumnToContents(0)
        self._servers_tree.blockSignals(False)


class MainWindow(QMainWindow):
    def __init__(
        self,
        signals: SignalRegistry,
        chat_view: ChatView,
        connection_view: ConnectionView,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._signals = signals
        self.chat_view = chat_view
        self.connection_view = connection_view
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Agent 365 MCP Client")
        self.resize(1440, 920)
        self.setMinimumSize(1180, 760)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(16)

        masthead = QFrame()
        masthead.setObjectName("sidebar_panel")
        masthead_layout = QHBoxLayout(masthead)
        masthead_layout.setContentsMargins(18, 14, 18, 14)
        masthead_layout.setSpacing(18)

        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title = QLabel("AGENT 365")
        title.setObjectName("app_title")
        subtitle = QLabel("MCP ORCHESTRATION DESK // INDUSTRIAL CONSOLE")
        subtitle.setObjectName("app_subtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        masthead_layout.addLayout(title_block)
        masthead_layout.addStretch(1)

        right_meta = QLabel("14 TARGET SERVICES // AZURE OPENAI + MCP")
        right_meta.setObjectName("status_label")
        masthead_layout.addWidget(right_meta)
        root.addWidget(masthead)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("main_splitter")
        splitter.setHandleWidth(14)
        splitter.addWidget(self.chat_view)
        splitter.addWidget(self.connection_view)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([800, 580])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self._signals.error_occurred.connect(self._show_error)

    def _show_error(self, title: str, message: str) -> None:
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(f"{title}: {message}", 10000)
        QMessageBox.critical(self, title, message)
