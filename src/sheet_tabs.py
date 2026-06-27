"""
Sheet tabs — bottom tab bar for managing multiple worksheets.
Google Sheets style: flat tabs, thin separators, "+" button on the right.
"""
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QTabBar, QPushButton, QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtGui import QAction, QFont, QColor
from . import qt_constants as C


class SheetTabs(QWidget):
    sheet_changed = pyqtSignal(int)
    sheet_added = pyqtSignal()
    sheet_deleted = pyqtSignal(int)
    sheet_renamed = pyqtSignal(int, str)
    sheet_duplicated = pyqtSignal(int)

    def __init__(self, workbook, parent=None):
        super().__init__(parent)
        self.workbook = workbook
        self._main_window = parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(False)
        self.tab_bar.setMovable(True)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabMoved.connect(self._on_tab_moved)
        self.tab_bar.tabBarDoubleClicked.connect(self._on_tab_double_clicked)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self._on_context_menu)

        # "All sheets" menu button (left of tabs, Google Sheets style)
        self.all_sheets_btn = QPushButton("\u2261")
        self.all_sheets_btn.setFixedSize(28, 28)
        self.all_sheets_btn.setToolTip("All sheets")
        self.all_sheets_btn.setStyleSheet(
            "QPushButton { border: none; border-right: 1px solid #e1e3e6; "
            "background: #f8f9fa; color: #5f6368; font-size: 14px; }"
            "QPushButton:hover { background: #f1f3f4; }")

        # Add button (right of tabs)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setToolTip("Add new sheet")
        add_btn.setStyleSheet(
            "QPushButton { border: none; background: #f8f9fa; color: #5f6368; font-size: 16px; }"
            "QPushButton:hover { background: #f1f3f4; color: #1a73e8; }")
        add_btn.clicked.connect(self.sheet_added.emit)

        layout.addWidget(self.all_sheets_btn)
        layout.addWidget(self.tab_bar, 1)
        layout.addWidget(add_btn)
        layout.addSpacing(2)

        self.setFixedHeight(30)
        self.refresh()

    def refresh(self):
        self.tab_bar.blockSignals(True)
        while self.tab_bar.count() > 0:
            self.tab_bar.removeTab(0)
        for i, sheet in enumerate(self.workbook.sheets):
            if sheet.sheet_hidden:
                continue
            self.tab_bar.addTab(sheet.name)
            # Apply tab color if set
            if sheet.tab_color:
                self.tab_bar.setTabTextColor(self.tab_bar.count() - 1, QColor(sheet.tab_color))
        # Map visible tab index back to sheet index
        visible_indices = [i for i, s in enumerate(self.workbook.sheets) if not s.sheet_hidden]
        active_visible = None
        if self.workbook.active_index in visible_indices:
            active_visible = visible_indices.index(self.workbook.active_index)
        if active_visible is not None and 0 <= active_visible < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(active_visible)
        self.tab_bar.blockSignals(False)

    def _on_tab_changed(self, index):
        # Map visible tab index back to actual sheet index (skipping hidden sheets)
        visible_indices = [i for i, s in enumerate(self.workbook.sheets) if not s.sheet_hidden]
        if 0 <= index < len(visible_indices):
            actual = visible_indices[index]
            self.workbook.active_index = actual
            self.sheet_changed.emit(actual)

    def _on_tab_close(self, index):
        if len(self.workbook.sheets) <= 1:
            QMessageBox.information(self, "Cannot Delete",
                                    "Cannot delete the last remaining sheet.")
            return
        self.sheet_deleted.emit(index)

    def _on_tab_moved(self, from_idx, to_idx):
        self.workbook.move_sheet(from_idx, to_idx)
        self.workbook.active_index = self.tab_bar.currentIndex()
        self.sheet_changed.emit(self.tab_bar.currentIndex())

    def _on_tab_double_clicked(self, index):
        self._rename_tab(index)

    def _rename_tab(self, index):
        if not (0 <= index < len(self.workbook.sheets)):
            return
        old_name = self.workbook.sheets[index].name
        name, ok = QInputDialog.getText(self, "Rename Sheet", "New name:", text=old_name)
        if ok and name.strip():
            self.sheet_renamed.emit(index, name.strip())

    def _on_context_menu(self, pos):
        index = self.tab_bar.tabAt(pos)
        if index < 0:
            return
        # Map visible tab index to actual sheet index
        visible_indices = [i for i, s in enumerate(self.workbook.sheets) if not s.sheet_hidden]
        if index >= len(visible_indices):
            return
        actual = visible_indices[index]
        menu = QMenu(self)
        act = QAction("Rename", self)
        act.triggered.connect(lambda: self._rename_tab(actual))
        menu.addAction(act)
        act = QAction("Duplicate", self)
        act.triggered.connect(lambda: self.sheet_duplicated.emit(actual))
        menu.addAction(act)
        menu.addSeparator()
        act = QAction("Tab Color...", self)
        act.triggered.connect(lambda: self._tab_color(actual))
        menu.addAction(act)
        act = QAction("Hide", self)
        act.triggered.connect(lambda: self._hide_tab(actual))
        menu.addAction(act)
        menu.addSeparator()
        act = QAction("Delete", self)
        act.triggered.connect(lambda: self._on_tab_close(actual))
        menu.addAction(act)
        menu.exec(self.tab_bar.mapToGlobal(pos))

    def _tab_color(self, index):
        if self._main_window:
            self._main_window.workbook.active_index = index
            self._main_window.set_tab_color()

    def _hide_tab(self, index):
        if self._main_window:
            self._main_window.workbook.active_index = index
            self._main_window.hide_sheet()