#!/usr/bin/env python3
"""
LocalSheet — A fully offline, self-contained desktop spreadsheet application.
Run with: python app.py
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.themes import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LocalSheet")
    app.setOrganizationName("LocalSheet")

    # Apply light theme by default
    apply_theme(app, dark=False)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()