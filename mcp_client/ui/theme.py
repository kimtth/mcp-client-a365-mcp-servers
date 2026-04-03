"""
Agent 365 MCP Client — Theme & Style System

Aesthetic: Industrial Precision Console — Light Edition
Swiss engineering clarity on a clean, bright canvas.
Cool greys, deep navy text, amber accents, monospace authority.
"""

from __future__ import annotations

# ── Color palette ───────────────────────────────────────────────────

COLORS = {
    # Base tones (light)
    "bg_deep":        "#f0f1f4",
    "bg_primary":     "#ffffff",
    "bg_surface":     "#f6f7f9",
    "bg_elevated":    "#ebedf2",
    "bg_hover":       "#e2e5ec",

    # Borders & dividers
    "border_subtle":  "#d8dbe3",
    "border_medium":  "#c0c4d0",
    "border_active":  "#d48a00",

    # Text
    "text_primary":   "#1a1e2e",
    "text_secondary": "#4a5068",
    "text_muted":     "#8891a5",
    "text_accent":    "#d48a00",

    # Accent: Amber (darkened slightly for legibility on white)
    "accent":         "#d48a00",
    "accent_dim":     "#d48a0030",
    "accent_glow":    "rgba(212, 138, 0, 0.10)",
    "accent_bright":  "#e89c00",

    # Semantic
    "success":        "#0b8a5e",
    "success_dim":    "#0b8a5e18",
    "error":          "#d43050",
    "error_dim":      "#d4305018",
    "warning":        "#c07800",
    "info":           "#2468c0",
    "info_dim":       "#2468c018",

    # Chat roles
    "role_user":      "#2468c0",
    "role_assistant": "#0b8a5e",
    "role_tool":      "#d48a00",
    "role_system":    "#4a5068",

    # Server status
    "server_online":  "#0b8a5e",
    "server_offline": "#8891a5",
}

# ── Typography ──────────────────────────────────────────────────────

FONTS = {
    "mono":     "'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",
    "display":  "'DM Sans', 'Segoe UI', 'Inter', sans-serif",
    "body":     "'DM Sans', 'Segoe UI', sans-serif",

    "size_xs":  "10px",
    "size_sm":  "11px",
    "size_base": "12px",
    "size_md":  "13px",
    "size_lg":  "16px",
    "size_xl":  "20px",
    "size_2xl": "28px",
}


# ── Master stylesheet ───────────────────────────────────────────────

def build_stylesheet() -> str:
    c = COLORS
    f = FONTS
    return f"""
/* ═══ Global Reset ═══ */

* {{
    margin: 0;
    padding: 0;
    outline: none;
}}

QMainWindow {{
    background-color: {c['bg_deep']};
}}

QWidget {{
    background-color: transparent;
    color: {c['text_primary']};
    font-family: {f['body']};
    font-size: {f['size_base']};
}}

/* ═══ Scroll bars ═══ */

QScrollBar:vertical {{
    background: {c['bg_primary']};
    width: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {c['border_medium']};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background: {c['bg_primary']};
    height: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_medium']};
    min-width: 30px;
    border-radius: 3px;
}}

/* ═══ Panels ═══ */

QFrame#chat_panel, QFrame#sidebar_panel {{
    background-color: {c['bg_primary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 8px;
}}

/* ═══ Chat Messages ═══ */

QTextBrowser#messages_browser {{
    background-color: {c['bg_primary']};
    border: none;
    padding: 16px;
    font-family: {f['body']};
    font-size: {f['size_md']};
    color: {c['text_primary']};
    selection-background-color: {c['accent_dim']};
}}

/* ═══ Input Area ═══ */

QFrame#input_frame {{
    background-color: {c['bg_surface']};
    border: 1px solid {c['border_subtle']};
    border-radius: 12px;
    padding: 4px;
}}
QFrame#input_frame:focus-within {{
    border-color: {c['accent']};
}}

QLineEdit#message_input {{
    background-color: transparent;
    border: none;
    padding: 10px 14px;
    font-family: {f['mono']};
    font-size: {f['size_md']};
    color: {c['text_primary']};
    selection-background-color: {c['accent_dim']};
}}
QLineEdit#message_input::placeholder {{
    color: {c['text_muted']};
}}

/* ═══ Buttons ═══ */

QPushButton {{
    background-color: {c['bg_elevated']};
    color: {c['text_secondary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 6px;
    padding: 6px 14px;
    font-family: {f['body']};
    font-size: {f['size_sm']};
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background-color: {c['bg_hover']};
    color: {c['text_primary']};
    border-color: {c['border_medium']};
}}

QPushButton#send_btn {{
    background-color: {c['accent']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 700;
    min-width: 70px;
}}
QPushButton#send_btn:hover {{
    background-color: {c['accent_bright']};
}}
QPushButton#send_btn:disabled {{
    background-color: {c['bg_elevated']};
    color: {c['text_muted']};
}}

QPushButton#connect_btn {{
    background-color: transparent;
    color: {c['accent']};
    border: 1px solid {c['accent']};
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 700;
    font-family: {f['mono']};
    font-size: {f['size_sm']};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QPushButton#connect_btn:hover {{
    background-color: {c['accent_glow']};
}}

QPushButton#clear_btn {{
    background-color: transparent;
    border: 1px solid {c['border_subtle']};
    color: {c['text_muted']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {f['size_sm']};
}}
QPushButton#clear_btn:hover {{
    border-color: {c['error']};
    color: {c['error']};
}}

/* ═══ Quick Action Badges ═══ */

QPushButton[quickAction="true"] {{
    background-color: {c['bg_surface']};
    color: {c['text_secondary']};
    border: 1px solid {c['border_subtle']};
    border-radius: 10px;
    padding: 2px 8px;
    font-family: {f['body']};
    font-size: {f['size_xs']};
    font-weight: 500;
    margin: 1px;
}}
QPushButton[quickAction="true"]:hover {{
    background-color: {c['accent_glow']};
    color: {c['accent']};
    border-color: {c['accent']};
}}

/* ═══ Section Headers ═══ */

QLabel[sectionHeader="true"] {{
    font-family: {f['mono']};
    font-size: {f['size_xs']};
    font-weight: 700;
    color: {c['text_muted']};
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 8px 4px 4px 4px;
}}

QLabel#app_title {{
    font-family: {f['mono']};
    font-size: {f['size_lg']};
    font-weight: 700;
    color: {c['text_primary']};
    letter-spacing: 1px;
}}

QLabel#app_subtitle {{
    font-family: {f['mono']};
    font-size: {f['size_xs']};
    color: {c['accent']};
    letter-spacing: 2px;
}}

/* ═══ Tree Widget (Server List) ═══ */

QTreeWidget {{
    background-color: {c['bg_primary']};
    border: none;
    font-family: {f['mono']};
    font-size: {f['size_sm']};
    color: {c['text_secondary']};
    outline: none;
}}
QTreeWidget::item {{
    padding: 4px 6px;
    border: none;
}}
QTreeWidget::item:hover {{
    background-color: {c['bg_hover']};
}}
QTreeWidget::item:selected {{
    background-color: {c['accent_glow']};
    color: {c['accent']};
}}
QTreeWidget::branch {{
    background: transparent;
}}
QHeaderView::section {{
    background-color: {c['bg_surface']};
    color: {c['text_muted']};
    font-family: {f['mono']};
    font-size: {f['size_xs']};
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {c['border_subtle']};
}}

/* ═══ Status Indicator ═══ */

QLabel#status_label {{
    font-family: {f['mono']};
    font-size: {f['size_sm']};
    color: {c['text_secondary']};
    padding: 4px 8px;
}}

QLabel#tools_count {{
    font-family: {f['mono']};
    font-size: {f['size_2xl']};
    font-weight: 700;
    color: {c['text_primary']};
}}

QLabel#tools_unit {{
    font-family: {f['mono']};
    font-size: {f['size_xs']};
    color: {c['text_muted']};
    letter-spacing: 2px;
}}

/* ═══ Splitter ═══ */

QSplitter::handle {{
    background-color: {c['border_subtle']};
    width: 1px;
}}
QSplitter::handle:hover {{
    background-color: {c['accent']};
}}

/* ═══ Status Bar ═══ */

QStatusBar {{
    background-color: {c['bg_deep']};
    color: {c['text_muted']};
    font-family: {f['mono']};
    font-size: {f['size_xs']};
    border-top: 1px solid {c['border_subtle']};
    padding: 2px 8px;
}}

/* ═══ Message Box ═══ */

QMessageBox {{
    background-color: {c['bg_surface']};
}}
QMessageBox QLabel {{
    color: {c['text_primary']};
    font-size: {f['size_md']};
}}
QMessageBox QPushButton {{
    min-width: 80px;
}}
"""


# ── Chat message HTML templates ─────────────────────────────────────

def msg_html_user(text: str) -> str:
    c = COLORS
    return (
        f'<div style="margin: 8px 0; padding: 10px 14px; '
        f'background: {c["info_dim"]}; border-radius: 8px; '
        f'border-left: 3px solid {c["role_user"]};">'
        f'<span style="font-family: monospace; font-size: 10px; '
        f'color: {c["role_user"]}; letter-spacing: 1px;">YOU</span>'
        f'<p style="margin: 4px 0 0 0; color: {c["text_primary"]}; '
        f'font-size: 13px; line-height: 1.5;">{text}</p></div>'
    )


def msg_html_assistant(text: str) -> str:
    c = COLORS
    return (
        f'<div style="margin: 8px 0; padding: 10px 14px; '
        f'background: {c["success_dim"]}; border-radius: 8px; '
        f'border-left: 3px solid {c["role_assistant"]};">'
        f'<span style="font-family: monospace; font-size: 10px; '
        f'color: {c["role_assistant"]}; letter-spacing: 1px;">AGENT 365</span>'
        f'<p style="margin: 4px 0 0 0; color: {c["text_primary"]}; '
        f'font-size: 13px; line-height: 1.5;">{text}</p></div>'
    )


def msg_html_tool(tool_name: str, text: str) -> str:
    c = COLORS
    return (
        f'<div style="margin: 6px 0; padding: 8px 12px; '
        f'background: {c["bg_surface"]}; border-radius: 6px; '
        f'border-left: 3px solid {c["role_tool"]};">'
        f'<span style="font-family: monospace; font-size: 10px; '
        f'color: {c["role_tool"]}; letter-spacing: 1px;">'
        f'\u26A1 {tool_name.upper()}</span>'
        f'<pre style="margin: 4px 0 0 0; color: {c["text_secondary"]}; '
        f'font-family: monospace; font-size: 11px; white-space: pre-wrap; '
        f'line-height: 1.4;">{text}</pre></div>'
    )
