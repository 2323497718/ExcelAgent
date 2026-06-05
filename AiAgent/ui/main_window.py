"""
Main window: 3-column horizontal layout via QSplitter.
Left = FileExplorer, Center = ExcelViewer, Right = ChatPanel.
Wires all signals together and manages the AgentWorker lifecycle.
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMessageBox, QMenuBar, QMenu,
)


class MainWindow(QMainWindow):
    """
    Main window for the Excel Agent desktop app.

    Layout: [FileExplorer | ExcelViewer | ChatPanel]
    Uses a horizontal QSplitter so panels can be resized by dragging.
    """

    # API key — in production this should come from an env var or config file
    API_KEY = "sk-5588ad0c13e44635bbdddac949f1e874"

    def __init__(self):
        super().__init__()
        self._current_file = ""
        self._chat_history = []   # session conversation history
        self._worker       = None

        self._setup_ui()
        self._setup_menu()
        self._apply_styles()
        self._connect_signals()

    # ────────────────────────────────────────────────────────────
    #  UI Setup
    # ────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setWindowTitle("Excel 智能体")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        root.addWidget(splitter)

        # Lazy imports to avoid loading heavy modules at import time
        from .file_explorer import FileExplorer
        from .excel_viewer   import ExcelViewer
        from .chat_panel     import ChatPanel

        self.explorer = FileExplorer()
        self.explorer.setMinimumWidth(220)
        self.explorer.setMaximumWidth(320)

        self.viewer   = ExcelViewer()
        self.viewer.setMinimumWidth(400)

        self.chat     = ChatPanel()
        self.chat.setMinimumWidth(300)

        splitter.addWidget(self.explorer)
        splitter.addWidget(self.viewer)
        splitter.addWidget(self.chat)

        # Default widths: 250 / 550 / 400
        splitter.setSizes([250, 600, 400])
        splitter.setStretchFactor(0, 0)   # explorer fixed
        splitter.setStretchFactor(1, 1)   # viewer flexible
        splitter.setStretchFactor(2, 1)   # chat flexible

    def _setup_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # File menu
        menu_file = QMenu("文件(&F)", self)
        menubar.addMenu(menu_file)

        act_open_folder = QAction("打开文件夹…", self)
        act_open_folder.setShortcut("Ctrl+O")
        act_open_folder.triggered.connect(self._on_open_folder)
        menu_file.addAction(act_open_folder)

        menu_file.addSeparator()

        act_save = QAction("保存文件    Ctrl+S", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._on_save)
        menu_file.addAction(act_save)

        menu_file.addSeparator()
        menu_file.addAction(QAction("退出", self, triggered=self.close))

        # Edit menu
        menu_edit = QMenu("编辑(&E)", self)
        menubar.addMenu(menu_edit)
        menu_edit.addAction(QAction("清空对话", self, triggered=self._on_clear_chat))
        menu_edit.addAction(QAction("重新加载文件", self, triggered=self._on_reload_file))

        # Help menu
        menu_help = QMenu("帮助(&H)", self)
        menubar.addMenu(menu_help)
        menu_help.addAction(QAction("关于", self, triggered=self._on_about))

    def _apply_styles(self):
        from .styles import DARK_QSS
        self.setStyleSheet(DARK_QSS)

    # ────────────────────────────────────────────────────────────
    #  Signal wiring
    # ────────────────────────────────────────────────────────────

    def _connect_signals(self):
        # File explorer → viewer + context
        self.explorer.file_selected.connect(self._on_file_selected)

        # Viewer → context badge in chat
        self.viewer.file_loaded.connect(self._on_file_loaded)

        # Chat input → start agent
        self.chat.message_sent.connect(self._on_message_sent)

        # Agent worker signals → chat panel
        # (connected dynamically in _start_agent)

    # ────────────────────────────────────────────────────────────
    #  File events
    # ────────────────────────────────────────────────────────────

    def _on_file_selected(self, path: str):
        """User clicked a file in the explorer."""
        if self.viewer.is_modified():
            reply = QMessageBox.question(
                self, "未保存的更改",
                "当前文件有未保存的修改，是否先保存？",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.viewer.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self._current_file = path
        self.chat.set_context_file(path)
        self.viewer.load_file(path)

    def _on_file_loaded(self, path: str):
        self._current_file = path

    def _on_open_folder(self):
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self, "选择 Excel 文件夹",
            os.path.expanduser("~"),
        )
        if folder:
            self.explorer.set_root_folder(folder)

    def _on_save(self):
        if self.viewer.get_file_path():
            self.viewer.save_file()

    def _on_reload_file(self):
        path = self.viewer.get_file_path()
        if path:
            self.viewer.load_file(path)

    # ────────────────────────────────────────────────────────────
    #  Chat / Agent events
    # ────────────────────────────────────────────────────────────

    def _on_message_sent(self, text: str):
        self._start_agent(text)

    def _start_agent(self, user_prompt: str):
        from .agent_worker import AgentWorker

        # Kill previous worker if still running
        if self._worker and self._worker.isRunning():
            self._worker._abort = True
            self._worker.wait(2000)

        # Build history for this turn (copy, before appending current user msg)
        hist = list(self._chat_history)

        # Add user message to persistent session history
        self._chat_history.append({"role": "user", "content": user_prompt})
        hist = list(self._chat_history)

        self._worker = AgentWorker(api_key=self.API_KEY, parent=self)
        self._worker.configure(
            user_prompt=user_prompt,
            chat_history=hist,
            current_file=self._current_file,
        )

        # Wire worker → chat panel
        self._worker.user_message_ready.connect(self.chat.append_user)
        self._worker.assistant_message_ready.connect(self._on_agent_response)
        self._worker.tool_result_ready.connect(self.chat.append_tool)
        self._worker.tool_result_ready.connect(self._append_tool_to_history)
        self._worker.thinking_started.connect(lambda: self.chat.set_thinking(True))
        self._worker.thinking_finished.connect(lambda: self.chat.set_thinking(False))
        self._worker.error_occurred.connect(self._on_agent_error)
        self._worker.finished.connect(self._on_worker_finished)

        self._worker.start()

    def _on_agent_response(self, text: str):
        # Append to session history
        self._chat_history.append({"role": "assistant", "content": text})
        # Show in panel
        self.chat.append_assistant(text)

    def _on_agent_error(self, message: str):
        self.chat.set_status("● 错误", color="#f85149")
        self.chat.append_assistant(f"❌ {message}")

    def _on_worker_finished(self):
        # Tool results were already appended to _chat_history by _append_tool_to_history
        pass

    def _append_tool_to_history(self, tool_name: str, result: str):
        self._chat_history.append({"role": "tool", "tool": tool_name, "result": result})

    def _on_clear_chat(self):
        self._chat_history = []
        self.chat.clear()
        self.chat.set_status("● 就绪", color="#3fb950")

    # ────────────────────────────────────────────────────────────
    #  Help
    # ────────────────────────────────────────────────────────────

    def _on_about(self):
        QMessageBox.about(
            self, "关于",
            "<b>Excel 智能体</b><br>"
            "一个基于大语言模型的 Excel 智能助手。<br><br>"
            "支持直接编辑表格，或通过自然语言让智能体帮你修改数据。"
        )
