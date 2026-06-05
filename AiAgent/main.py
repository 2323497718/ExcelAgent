"""
Entry point for the Excel Agent desktop app.

Usage:
    python main.py

Requirements (install via pip):
    pip install -r requirements.txt

The app requires PySide6, openpyxl, and the langchain packages listed
in requirements.txt.
"""

import sys


def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
