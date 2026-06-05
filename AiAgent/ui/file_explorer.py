"""
Left panel: file explorer with folder tree + search filter.
Emits file_selected(path: str) when user double-clicks an Excel file.
"""

import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTreeView, QLabel,
    QFileDialog, QMenu, QFileSystemModel,
)


class FileExplorer(QWidget):
    """Left sidebar — browse folders and select Excel files."""

    # Emitted when user opens a file (double-click or Enter)
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_path = ""
        self._filter_exts = [".xlsx", ".xlsm", ".xls"]

        self._setup_ui()
        self._setup_model()

    # ── UI Setup ────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        title = QLabel("文件浏览器")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Open folder button
        self.btn_open_folder = QPushButton("📂  打开文件夹")
        self.btn_open_folder.setMinimumHeight(32)
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        layout.addWidget(self.btn_open_folder)

        # Search bar
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  搜索文件…")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box)

        # Current path label
        self.path_label = QLabel()
        self.path_label.setObjectName("muted")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(20)
        self.path_label.setMaximumHeight(36)
        layout.addWidget(self.path_label)

        # Tree view
        self.tree = QTreeView()
        self.tree.setHeaderHidden(False)
        self.tree.setAnimated(False)
        self.tree.setIndentation(16)
        self.tree.setSortingEnabled(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.tree, 1)

        # Status bar
        self.status_label = QLabel()
        self.status_label.setObjectName("muted")
        self.status_label.setMinimumHeight(18)
        layout.addWidget(self.status_label)

    def _setup_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.tree.setModel(self.model)
        self._apply_filter("")

    # ── Filter helpers ──────────────────────────────────────────

    def _apply_filter(self, search_text: str):
        """Set name filters so only Excel files + matching folders are visible."""
        if search_text:
            pattern = f"*{search_text}*"
        else:
            pattern = "*"
        filters = [f"{pattern}{ext}" for ext in self._filter_exts]
        self.model.setNameFilters(filters)
        self.model.setNameFilterDisables(False)

    def _on_search_changed(self, text: str):
        self._apply_filter(text)
        self._update_status()

    # ── Folder open ─────────────────────────────────────────────

    def _on_open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择 Excel 文件夹",
            self._root_path or os.path.expanduser("~"),
        )
        if folder:
            self.set_root_folder(folder)

    def set_root_folder(self, path: str):
        """Programmatically set the root folder (e.g. from main window)."""
        self._root_path = path
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))
        self.path_label.setText(path)
        self._update_status()

    # ── File selection ───────────────────────────────────────────

    def _on_double_click(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path) and self._is_excel(path):
            self.file_selected.emit(path)

    def _on_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        path = self.model.filePath(index)
        if not os.path.isfile(path):
            return

        menu = QMenu(self)
        act_open = QAction("打开文件", self)
        act_open.triggered.connect(lambda: self.file_selected.emit(path))
        menu.addAction(act_open)

        act_copy = QAction("复制路径", self)
        act_copy.triggered.connect(lambda: self._copy_path(path))
        menu.addAction(act_copy)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _copy_path(self, path: str):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().clipboard().setText(path)

    def _is_excel(self, path: str) -> bool:
        return any(path.lower().endswith(ext) for ext in self._filter_exts)

    def _update_status(self):
        if not self._root_path:
            self.status_label.setText("")
            return
        count = 0
        it = self.model.index(self._root_path)
        for i in range(self.model.rowCount(it)):
            child = it.child(i, 0)
            if self._is_excel(self.model.filePath(child)):
                count += 1
        self.status_label.setText(f"  {count} 个 Excel 文件")
