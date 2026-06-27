"""
Light and dark theme stylesheets for LocalSheet — Google Sheets inspired.
"""


LIGHT_STYLE = """
    QMainWindow { background: #ffffff; }

    /* Menu bar */
    QMenuBar { background: #ffffff; border-bottom: 1px solid #e0e0e0; color: #444746; padding: 2px; }
    QMenuBar::item { padding: 4px 8px; border-radius: 2px; background: transparent; }
    QMenuBar::item:selected { background: #f1f3f4; }

    /* Toolbar */
    QToolBar { background: #ffffff; border: none; border-bottom: 1px solid #e0e0e0; spacing: 0px; padding: 2px 4px; }
    QToolBar QToolButton { padding: 4px 6px; border-radius: 2px; color: #444746; background: transparent; border: none; }
    QToolBar QToolButton:hover { background: #f1f3f4; }
    QToolBar QToolButton:checked { background: #e8f0fe; color: #1a73e8; }
    QToolBar QToolButton:pressed { background: #e8eaed; }
    QToolBar::separator { width: 1px; background: #e0e0e0; margin: 4px 4px; }

    /* Grid */
    QTableView { gridline-color: #e1e3e6; background: #ffffff; border: none; color: #202124; }
    QTableView::item { padding: 1px 2px; color: #202124; }
    QTableView::item:selected { background: #c9daf8; color: #202124; }
    QTableView::item:focus { background: #c9daf8; }

    /* Headers */
    QHeaderView { border: none; }
    QHeaderView::section { background: #f8f9fa; border: none; border-right: 1px solid #e1e3e6; border-bottom: 1px solid #e1e3e6; padding: 0px; font-weight: 400; color: #5f6368; }
    QHeaderView::section:horizontal { border-top: none; }
    QHeaderView::section:vertical { border-left: none; border-right: 1px solid #e1e3e6; border-bottom: 1px solid #e1e3e6; }
    QHeaderView::section:highlighted { background: #e8f0fe; color: #1a73e8; }

    /* Sheet tabs */
    QTabBar { background: #f8f9fa; }
    QTabBar::tab { background: #f8f9fa; border: none; border-right: 1px solid #e1e3e6; padding: 5px 14px; color: #5f6368; }
    QTabBar::tab:selected { background: #ffffff; border-bottom: 2px solid #1a73e8; color: #1a73e8; }
    QTabBar::tab:hover:!selected { background: #f1f3f4; color: #202124; }
    QTabBar::close-button { image: none; subcontrol-position: right; width: 0px; height: 0px; }

    /* Inputs */
    QLineEdit { border: 1px solid #c0c0c0; border-radius: 0px; padding: 3px 6px; background: #ffffff; color: #202124; }
    QLineEdit:focus { border: 2px solid #1a73e8; padding: 2px 5px; }

    /* Menus */
    QMenu { border: 1px solid #c0c0c0; background: #ffffff; color: #202124; padding: 4px; }
    QMenu::item { padding: 4px 24px 4px 16px; border-radius: 2px; }
    QMenu::item:selected { background: #f1f3f4; }
    QMenu::separator { height: 1px; background: #e0e0e0; margin: 4px 8px; }

    /* Buttons */
    QPushButton { border: 1px solid transparent; border-radius: 2px; padding: 4px 10px; background: transparent; color: #444746; }
    QPushButton:hover { background: #f1f3f4; }
    QPushButton:pressed { background: #e8eaed; }

    /* Combo box */
    QComboBox { border: 1px solid transparent; border-radius: 2px; padding: 2px 4px 2px 6px; background: transparent; color: #444746; }
    QComboBox:hover { background: #f1f3f4; }
    QComboBox::drop-down { border: none; width: 16px; }
    QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
    QComboBox QAbstractItemView { border: 1px solid #c0c0c0; background: #ffffff; color: #202124; selection-background-color: #e8f0fe; selection-color: #1a73e8; outline: none; }

    /* Status bar */
    QStatusBar { background: #f8f9fa; border-top: 1px solid #e1e3e6; color: #5f6368; }
    QStatusBar::item { border: none; }

    /* Misc */
    QLabel { color: #202124; }
    QCheckBox { color: #202124; }
    QRadioButton { color: #202124; }
    QGroupBox { color: #202124; border: 1px solid #e0e0e0; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
    QScrollArea { background: #ffffff; border: none; }

    /* Scrollbars */
    QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: #c0c0c0; border-radius: 3px; min-height: 30px; margin: 2px; }
    QScrollBar::handle:vertical:hover { background: #9aa0a6; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
    QScrollBar::handle:horizontal { background: #c0c0c0; border-radius: 3px; min-width: 30px; margin: 2px; }
    QScrollBar::handle:horizontal:hover { background: #9aa0a6; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

DARK_STYLE = """
    QMainWindow { background: #23252a; }

    QMenuBar { background: #23252a; border-bottom: 1px solid #3c4043; color: #c4c7c5; padding: 2px; }
    QMenuBar::item { padding: 4px 8px; border-radius: 2px; background: transparent; }
    QMenuBar::item:selected { background: #3c4043; }

    QToolBar { background: #23252a; border: none; border-bottom: 1px solid #3c4043; spacing: 0px; padding: 2px 4px; }
    QToolBar QToolButton { padding: 4px 6px; border-radius: 2px; color: #c4c7c5; background: transparent; border: none; }
    QToolBar QToolButton:hover { background: #3c4043; }
    QToolBar QToolButton:checked { background: #394457; color: #8ab4f8; }
    QToolBar QToolButton:pressed { background: #3c4043; }
    QToolBar::separator { width: 1px; background: #3c4043; margin: 4px 4px; }

    QTableView { gridline-color: #3c4043; background: #23252a; border: none; color: #e8eaed; }
    QTableView::item { padding: 1px 2px; color: #e8eaed; }
    QTableView::item:selected { background: #394457; color: #e8eaed; }
    QTableView::item:focus { background: #394457; }

    QHeaderView { border: none; }
    QHeaderView::section { background: #28292c; border: none; border-right: 1px solid #3c4043; border-bottom: 1px solid #3c4043; padding: 0px; font-weight: 400; color: #9aa0a6; }
    QHeaderView::section:vertical { border-left: none; border-right: 1px solid #3c4043; border-bottom: 1px solid #3c4043; }
    QHeaderView::section:highlighted { background: #394457; color: #8ab4f8; }

    QTabBar { background: #28292c; }
    QTabBar::tab { background: #28292c; border: none; border-right: 1px solid #3c4043; padding: 5px 14px; color: #9aa0a6; }
    QTabBar::tab:selected { background: #23252a; border-bottom: 2px solid #8ab4f8; color: #8ab4f8; }
    QTabBar::tab:hover:!selected { background: #3c4043; color: #e8eaed; }
    QTabBar::close-button { image: none; width: 0px; height: 0px; }

    QLineEdit { border: 1px solid #5f6368; border-radius: 0px; padding: 3px 6px; background: #28292c; color: #e8eaed; }
    QLineEdit:focus { border: 2px solid #8ab4f8; padding: 2px 5px; }

    QMenu { border: 1px solid #5f6368; background: #28292c; color: #e8eaed; padding: 4px; }
    QMenu::item { padding: 4px 24px 4px 16px; border-radius: 2px; }
    QMenu::item:selected { background: #3c4043; }
    QMenu::separator { height: 1px; background: #3c4043; margin: 4px 8px; }

    QPushButton { border: 1px solid transparent; border-radius: 2px; padding: 4px 10px; background: transparent; color: #c4c7c5; }
    QPushButton:hover { background: #3c4043; }
    QPushButton:pressed { background: #5f6368; }

    QComboBox { border: 1px solid transparent; border-radius: 2px; padding: 2px 4px 2px 6px; background: transparent; color: #c4c7c5; }
    QComboBox:hover { background: #3c4043; }
    QComboBox::drop-down { border: none; width: 16px; }
    QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
    QComboBox QAbstractItemView { border: 1px solid #5f6368; background: #28292c; color: #e8eaed; selection-background-color: #394457; selection-color: #8ab4f8; outline: none; }

    QStatusBar { background: #28292c; border-top: 1px solid #3c4043; color: #9aa0a6; }
    QStatusBar::item { border: none; }

    QLabel { color: #e8eaed; }
    QCheckBox { color: #e8eaed; }
    QRadioButton { color: #e8eaed; }
    QGroupBox { color: #e8eaed; border: 1px solid #3c4043; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
    QScrollArea { background: #23252a; border: none; }

    QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: #5f6368; border-radius: 3px; min-height: 30px; margin: 2px; }
    QScrollBar::handle:vertical:hover { background: #9aa0a6; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
    QScrollBar::handle:horizontal { background: #5f6368; border-radius: 3px; min-width: 30px; margin: 2px; }
    QScrollBar::handle:horizontal:hover { background: #9aa0a6; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""


def apply_theme(app, dark=False):
    app.setStyleSheet(DARK_STYLE if dark else LIGHT_STYLE)