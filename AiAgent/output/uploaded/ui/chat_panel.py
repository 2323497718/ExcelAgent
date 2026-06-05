"""
Right panel: Agent chat interface.
Displays conversation history, handles user input, shows tool execution results.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QTextCursor, QColor, QFont, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel,
    QSizePolicy, QSpacerItem,
)


class ChatPanel(QWidget):
    """
    Right panel — Agent chat UI.

    Signals
    -------
    message_sent(str text) : emitted when user presses Enter or clicks Send
    """

    message_sent = Signal(str)

    # ────────────────────────────────────────────────────────────
    #  Color constants (matching dark theme)
    # ────────────────────────────────────────────────────────────
    COLOR_BG       = "#0d1117"
    COLOR_CARD     = "#161b22"
    COLOR_BORDER   = "#21262d"
    COLOR_TEXT     = "#e6edf3"
    COLOR_MUTED    = "#8b949e"
    COLOR_ACCENT   = "#58a6ff"
    COLOR_GREEN    = "#3fb950"
    COLOR_RED      = "#f85149"
    COLOR_YELLOW   = "#d29922"
    COLOR_TOOL_BG  = "#0d1117"
    COLOR_TOOL_TAG = "#58a6ff"
    COLOR_USER_BG  = "#1a3a5c"
    COLOR_USER_BDR = "#2a5f8f"
    COLOR_AI_BG   = "#1c2128"
    COLOR_AI_BDR  = "#30363d"

    # ────────────────────────────────────────────────────────────
    #  Init
    # ────────────────────────────────────────────────────────────

    def __init__(self, parent=None):
        super().__init__(parent)
        self._context_file = ""
        self._thinking_visible = False
        self._thinking_cursor_pos = -1
        self._setup_ui()

    # ────────────────────────────────────────────────────────────
    #  UI Setup
    # ────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Header ──────────────────────────────────────────────
        header = QHBoxLayout()
        lbl = QLabel("🤖 Excel 智能体")
        lbl.setStyleSheet("font-size: 11pt; font-weight: 700;")
        header.addWidget(lbl)
        header.addStretch()

        self.lbl_status = QLabel("● 就绪")
        self.lbl_status.setStyleSheet(f"color: {self.COLOR_GREEN}; font-size: 8pt;")
        header.addWidget(self.lbl_status)

        layout.addLayout(header)

        # ── Context badge ────────────────────────────────────────
        self.lbl_context = QLabel("")
        self.lbl_context.setObjectName("badge")
        self.lbl_context.setStyleSheet(
            f"background:{self.COLOR_CARD}; border:1px solid {self.COLOR_BORDER};"
            f"border-radius:12px; padding:3px 10px; color:{self.COLOR_ACCENT}; font-size:8pt;"
        )
        self.lbl_context.setVisible(False)
        layout.addWidget(self.lbl_context)

        # ── Chat area ────────────────────────────────────────────
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setUndoRedoEnabled(False)
        self.chat.setAcceptRichText(True)
        layout.addWidget(self.chat, 1)

        # ── Thinking indicator ───────────────────────────────────
        self.lbl_thinking = QLabel()
        self.lbl_thinking.setStyleSheet(
            f"color:{self.COLOR_MUTED}; font-size:8pt; padding:4px;"
            f"background:{self.COLOR_CARD}; border:1px solid {self.COLOR_BORDER};"
            f"border-radius:6px;"
        )
        self.lbl_thinking.setVisible(False)
        self._thinking_timer = QTimer(self)
        self._thinking_timer.timeout.connect(self._animate_thinking)
        self._thinking_frame = 0
        layout.addWidget(self.lbl_thinking)

        # ── Input row ────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("向智能体描述你的需求…")
        self.input_box.setMinimumHeight(36)
        self.input_box.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_box, 1)

        self.btn_send = QPushButton("发送")
        self.btn_send.setObjectName("primaryBtn")
        self.btn_send.setMinimumWidth(60)
        self.btn_send.setMinimumHeight(36)
        self.btn_send.clicked.connect(self._on_send)
        input_row.addWidget(self.btn_send)

        layout.addLayout(input_row)

        # ── Bottom bar ──────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self.btn_clear = QPushButton("🗑 清空对话")
        self.btn_clear.setMinimumHeight(28)
        self.btn_clear.clicked.connect(self.clear)
        bottom.addWidget(self.btn_clear)

        bottom.addStretch()

        self.lbl_hint = QLabel("提示：直接告诉智能体你想做什么")
        self.lbl_hint.setObjectName("muted")
        bottom.addWidget(self.lbl_hint)

        layout.addLayout(bottom)

    # ────────────────────────────────────────────────────────────
    #  Public API
    # ────────────────────────────────────────────────────────────

    def set_context_file(self, path: str):
        """Show the currently open file as a context badge."""
        self._context_file = path
        if path:
            import os
            name = os.path.basename(path)
            self.lbl_context.setText(f"📎 {name}")
            self.lbl_context.setVisible(True)
        else:
            self.lbl_context.setVisible(False)

    def append_user(self, text: str):
        self._append_bubble("user", text)

    def append_assistant(self, text: str):
        self._stop_thinking()
        self._append_bubble("assistant", text)

    def append_tool(self, tool_name: str, result: str):
        self._stop_thinking()
        self._append_tool_block(tool_name, result)

    def set_thinking(self, active: bool):
        if active:
            self._start_thinking()
        else:
            self._stop_thinking()

    def set_status(self, text: str, color: str = None):
        color = color or self.COLOR_MUTED
        self.lbl_status.setStyleSheet(f"color:{color}; font-size:8pt;")
        self.lbl_status.setText(text)

    def clear(self):
        self.chat.clear()
        self.lbl_context.setVisible(False)
        self._context_file = ""
        self._stop_thinking()

    # ────────────────────────────────────────────────────────────
    #  Private helpers
    # ────────────────────────────────────────────────────────────

    def _on_send(self):
        text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()
        self.message_sent.emit(text)

    def _append_html(self, html: str):
        cursor = self.chat.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        self.chat.setTextCursor(cursor)
        self.chat.ensureCursorVisible()

    def _append_bubble(self, role: str, text: str):
        """Append a chat bubble (user=blue right, assistant=dark left)."""
        if role == "user":
            bg     = self.COLOR_USER_BG
            border = self.COLOR_USER_BDR
            align  = "right"
            label  = "👤 用户"
            color  = self.COLOR_TEXT
        else:
            bg     = self.COLOR_AI_BG
            border = self.COLOR_AI_BDR
            align  = "left"
            label  = "🤖 智能体"
            color  = self.COLOR_TEXT

        # Escape HTML
        escaped = (text
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\n", "<br>"))

        html = f"""
        <div style="display:flex; justify-content:{align}; margin:4px 0;">
          <div style="
            max-width:80%;
            background:{bg};
            border:1px solid {border};
            border-radius:12px;
            padding:8px 12px;
            font-size:9pt;
            color:{color};
            line-height:1.5;
          ">
            <div style="font-size:7.5pt; color:{self.COLOR_MUTED}; margin-bottom:4px;">{label}</div>
            <div>{escaped}</div>
          </div>
        </div>
        """
        self._append_html(html)

    def _append_tool_block(self, tool_name: str, result: str):
        """Append a monospace tool result block."""
        escaped = (result
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\n", "<br>"))

        html = f"""
        <div style="
          margin:4px 0 4px 20px;
          background:{self.COLOR_TOOL_BG};
          border:1px solid {self.COLOR_BORDER};
          border-left:3px solid {self.COLOR_TOOL_TAG};
          border-radius:4px;
          padding:6px 10px;
          font-size:8pt;
        ">
          <div style="color:{self.COLOR_TOOL_TAG}; font-weight:600; margin-bottom:4px; font-family:monospace;">
            🔧 {tool_name}
          </div>
          <div style="color:{self.COLOR_MUTED}; font-family:monospace; white-space:pre-wrap; word-break:break-all;">
            {escaped}
          </div>
        </div>
        """
        self._append_html(html)

    def _start_thinking(self):
        if self._thinking_visible:
            return
        self._thinking_visible = True
        self._thinking_frame = 0
        self.lbl_thinking.setText("🤔 智能体思考中…")
        self.lbl_thinking.setVisible(True)
        self._thinking_timer.start(400)

    def _stop_thinking(self):
        self._thinking_timer.stop()
        self._thinking_visible = False
        self.lbl_thinking.setVisible(False)

    def _animate_thinking(self):
        dots = "." * ((self._thinking_frame % 4) + 1)
        spaces = " " * (3 - (self._thinking_frame % 4))
        self.lbl_thinking.setText(f"🤔 智能体思考中{dots}{spaces}")
        self._thinking_frame += 1
