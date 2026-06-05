"""
Dark theme QSS (Qt Style Sheets) for the Excel Agent desktop app.
Matches the existing Streamlit dark palette: GitHub dark (#0d1117 bg).
"""

DARK_QSS = """
/* ── Global ─────────────────────────────────────────────── */
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 9pt;
}

QMainWindow {
    background-color: #0d1117;
}

/* ── Scrollbars ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: #161b22;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background: #161b22;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #484f58; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

/* ── Buttons ──────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e6edf3;
    font-size: 9pt;
}
QPushButton:hover {
    background-color: #2d333b;
    border-color: #58a6ff;
    color: #58a6ff;
}
QPushButton:pressed {
    background-color: #1a3a5c;
    border-color: #58a6ff;
}
QPushButton:disabled {
    background-color: #161b22;
    border-color: #21262d;
    color: #484f58;
}
QPushButton#primaryBtn {
    background-color: #238636;
    border: 1px solid #238636;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #2ea043;
    border-color: #2ea043;
}

/* ── LineEdit / ComboBox ─────────────────────────────────── */
QLineEdit, QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 8px;
    color: #e6edf3;
    selection-background-color: #1a3a5c;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #58a6ff;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8b949e;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 4px;
    selection-background-color: #1a3a5c;
    outline: none;
}

/* ── TreeView (file explorer) ────────────────────────────── */
QTreeView {
    background-color: #0d1117;
    border: none;
    outline: none;
    show-decoration-selected: 0;
}
QTreeView::item {
    padding: 3px 4px;
    border-radius: 4px;
}
QTreeView::item:hover { background-color: #21262d; }
QTreeView::item:selected { background-color: #1a3a5c; color: #58a6ff; }
QTreeView::item:selected:active { background-color: #1f4068; }
QHeaderView::section {
    background-color: #161b22;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 4px 8px;
    color: #8b949e;
    font-size: 8pt;
    text-transform: uppercase;
}

/* ── TableWidget (excel viewer) ───────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    alternate-background-color: #161b22;
    gridline-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    outline: none;
    font-size: 9pt;
}
QTableWidget::item {
    padding: 4px 6px;
    border-radius: 2px;
}
QTableWidget::item:selected {
    background-color: #1f4068;
    color: #e6edf3;
}
QTableWidget::item:hover {
    background-color: #21262d;
}
/* Header row (row 0) */
QTableWidget QTableCornerButton::section {
    background-color: #161b22;
    border: none;
}
QHeaderView:section {
    background-color: #161b22;
    border: none;
    border-right: 1px solid #21262d;
    border-bottom: 1px solid #30363d;
    padding: 5px 6px;
    color: #8b949e;
    font-weight: 600;
    font-size: 8.5pt;
}
QHeaderView:section:hover {
    background-color: #21262d;
    color: #e6edf3;
}

/* ── TextEdit (chat history) ─────────────────────────────── */
QTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px;
    color: #e6edf3;
    selection-background-color: #1a3a5c;
}
QTextEdit:focus { border-color: #58a6ff; }

/* ── Labels ──────────────────────────────────────────────── */
QLabel {
    background-color: transparent;
    color: #e6edf3;
}
QLabel#muted { color: #8b949e; font-size: 8pt; }
QLabel#badge {
    background-color: rgba(88, 166, 255, 0.15);
    border: 1px solid rgba(88, 166, 255, 0.3);
    border-radius: 12px;
    padding: 3px 10px;
    color: #79b8ff;
    font-size: 8pt;
}
QLabel#toolTag {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 4px;
    padding: 4px 8px;
    color: #58a6ff;
    font-size: 8pt;
    font-family: "Cascadia Code", "Consolas", monospace;
}
QLabel#sectionTitle {
    color: #8b949e;
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}

/* ── Splitters ───────────────────────────────────────────── */
QSplitter::handle {
    background-color: #30363d;
}
QSplitter::handle:hover { background-color: #58a6ff; }

/* ── ToolTip ─────────────────────────────────────────────── */
QToolTip {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e6edf3;
    font-size: 8.5pt;
}

/* ── Menu ────────────────────────────────────────────────── */
QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 5px 20px;
    border-radius: 3px;
}
QMenu::item:selected { background-color: #21262d; color: #e6edf3; }
QMenu::separator {
    height: 1px;
    background-color: #30363d;
    margin: 4px 0;
}
"""
