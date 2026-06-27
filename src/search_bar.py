"""
Search bar — appears on Ctrl+F, highlights matching cells as the user types.
Google Sheets style: floating panel with flat buttons.
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox
)
from PyQt6.QtGui import QKeySequence


class SearchBar(QWidget):
    search_changed = pyqtSignal(str)
    next_match = pyqtSignal()
    prev_match = pyqtSignal()
    closed = pyqtSignal()
    replace_requested = pyqtSignal(str, str)
    replace_all_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._replace_visible = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in sheet")
        self.input.setClearButtonEnabled(True)
        self.input.setStyleSheet(
            "QLineEdit { border: 1px solid #c0c0c0; border-radius: 0px; padding: 3px 6px; "
            "background: #ffffff; color: #202124; }"
            "QLineEdit:focus { border: 2px solid #1a73e8; padding: 2px 5px; }")
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self._on_return)

        self.match_label = QLabel("")
        self.match_label.setStyleSheet("color: #5f6368; font-size: 12px;")
        self.match_label.setFixedWidth(90)
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # "Search in formulas" checkbox
        self.formula_search = QCheckBox("fx")
        self.formula_search.setToolTip("Search in formulas instead of values")
        self.formula_search.setStyleSheet("color: #5f6368; font-size: 11px;")
        self.formula_search.setFixedWidth(36)
        self.formula_search.toggled.connect(lambda: self._on_text_changed(self.input.text()))

        btn_prev = QPushButton("\u2191")
        btn_prev.setFixedSize(26, 26)
        btn_prev.setToolTip("Previous match (Shift+Enter)")
        btn_prev.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #5f6368; font-size: 14px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        btn_prev.clicked.connect(self.prev_match.emit)

        btn_next = QPushButton("\u2193")
        btn_next.setFixedSize(26, 26)
        btn_next.setToolTip("Next match (Enter)")
        btn_next.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #5f6368; font-size: 14px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        btn_next.clicked.connect(self.next_match.emit)

        self.btn_replace_toggle = QPushButton("...")
        self.btn_replace_toggle.setFixedSize(26, 26)
        self.btn_replace_toggle.setToolTip("Show / hide replace")
        self.btn_replace_toggle.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #5f6368; font-size: 12px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        self.btn_replace_toggle.setCheckable(True)
        self.btn_replace_toggle.toggled.connect(self._toggle_replace)

        btn_close = QPushButton("\u2715")
        btn_close.setFixedSize(26, 26)
        btn_close.setToolTip("Close search (Esc)")
        btn_close.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #5f6368; font-size: 12px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        btn_close.clicked.connect(self.closed.emit)

        # Replace row (hidden until toggled)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with")
        self.replace_input.setClearButtonEnabled(True)
        self.replace_input.setStyleSheet(self.input.styleSheet())
        self.replace_input.returnPressed.connect(self._on_replace_return)

        self.btn_replace = QPushButton("Replace")
        self.btn_replace.setFixedHeight(26)
        self.btn_replace.setToolTip("Replace current match")
        self.btn_replace.setStyleSheet(
            "QPushButton { border: 1px solid #dadce0; background: #ffffff; color: #3c4043; padding: 0 10px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        self.btn_replace.clicked.connect(self._on_replace_clicked)

        self.btn_replace_all = QPushButton("Replace All")
        self.btn_replace_all.setFixedHeight(26)
        self.btn_replace_all.setToolTip("Replace all matches")
        self.btn_replace_all.setStyleSheet(
            "QPushButton { border: 1px solid #dadce0; background: #ffffff; color: #3c4043; padding: 0 10px; }"
            "QPushButton:hover { background: #f1f3f4; }")
        self.btn_replace_all.clicked.connect(self._on_replace_all_clicked)

        self._replace_row = QWidget()
        rl = QHBoxLayout(self._replace_row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(4)
        rl.addWidget(self.replace_input)
        rl.addWidget(self.btn_replace)
        rl.addWidget(self.btn_replace_all)
        self._replace_row.hide()

        layout.addWidget(self.input)
        layout.addWidget(self.formula_search)
        layout.addWidget(self.match_label)
        layout.addWidget(btn_prev)
        layout.addWidget(btn_next)
        layout.addWidget(self.btn_replace_toggle)
        layout.addWidget(btn_close)
        layout.addWidget(self._replace_row)

        self.setFixedHeight(32)
        self.hide()

    def _toggle_replace(self, checked):
        self._replace_visible = checked
        self._replace_row.setVisible(checked)
        self.setFixedHeight(60 if checked else 32)
        if checked:
            self.replace_input.setFocus()

    def _on_replace_clicked(self):
        self.replace_requested.emit(self.input.text(), self.replace_input.text())

    def _on_replace_all_clicked(self):
        self.replace_all_requested.emit(self.input.text(), self.replace_input.text())

    def _on_replace_return(self):
        self._on_replace_clicked()

    def focus_input(self):
        self.show()
        self.input.setFocus()
        self.input.selectAll()

    def _on_text_changed(self, text):
        self.search_changed.emit(text)

    def _on_return(self):
        from PyQt6.QtWidgets import QApplication
        mods = QApplication.keyboardModifiers()
        if mods & Qt.KeyboardModifier.ShiftModifier:
            self.prev_match.emit()
        else:
            self.next_match.emit()

    def set_match_count(self, current, total):
        if total == 0:
            self.match_label.setText("No results")
        else:
            self.match_label.setText(f"{current} of {total}")

    def is_formula_search(self):
        return self.formula_search.isChecked()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            return
        super().keyPressEvent(event)