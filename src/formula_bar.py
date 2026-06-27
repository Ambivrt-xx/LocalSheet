"""
Formula bar — shows the active cell address and its raw value/formula.
Google Sheets style: narrow cell-ref box, "fx" indicator, wide input.
"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QFrame
from PyQt6.QtGui import QFont
from .formula_engine import col_index_to_letters


class FormulaBar(QWidget):
    commit = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cell address box — narrow, bordered like Google Sheets
        self.address_label = QLabel("A1")
        self.address_label.setFixedWidth(72)
        self.address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.address_label.setFont(font)
        self.address_label.setStyleSheet(
            "QLabel { border: none; border-right: 1px solid #e0e0e0; "
            "background: #ffffff; color: #202124; padding: 0px; }")

        # "fx" label
        fx_label = QLabel("fx")
        fx_label.setFixedWidth(36)
        fx_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fx_label.setStyleSheet(
            "QLabel { border: none; border-right: 1px solid #e0e0e0; "
            "background: #ffffff; color: #5f6368; font-style: italic; }")
        fx_font = QFont()
        fx_font.setPointSize(10)
        fx_font.setItalic(True)
        fx_label.setFont(fx_font)

        # Formula input — borderless, blends with toolbar
        self.input = QLineEdit()
        self.input.setPlaceholderText("")
        self.input.setStyleSheet(
            "QLineEdit { border: none; border-bottom: 1px solid #e0e0e0; "
            "border-radius: 0px; padding: 4px 8px; background: #ffffff; color: #202124; }"
            "QLineEdit:focus { border: none; border-bottom: 2px solid #1a73e8; padding: 4px 8px; }")
        self.input.returnPressed.connect(self._on_commit)

        layout.addWidget(self.address_label)
        layout.addWidget(fx_label)
        layout.addWidget(self.input, 1)

        self.setFixedHeight(28)

    def update_cell(self, row, col, raw_value):
        self._updating = True
        self.address_label.setText(col_index_to_letters(col) + str(row + 1))
        self.input.setText(raw_value or "")
        self._updating = False

    def keyPressEvent(self, event):
        """F4 cycles the cell reference under the cursor through absolute/relative."""
        if event.key() == Qt.Key.Key_F4 and self.input.hasFocus():
            self._cycle_reference()
            event.accept()
            return
        super().keyPressEvent(event)

    def _cycle_reference(self):
        """Cycle A1 -> \$A\$1 -> A\$1 -> \$A1 -> A1 for the reference under cursor."""
        import re
        text = self.input.text()
        cursor_pos = self.input.cursorPosition()

        # Find a cell reference near the cursor
        pattern = re.compile(r'(\$?)([A-Z]{1,3})(\$?)(\d+)')
        best_match = None
        for m in pattern.finditer(text):
            if m.start() <= cursor_pos <= m.end():
                best_match = m
                break
        if not best_match:
            return

        col_abs, col_letters, row_abs, row_num = best_match.groups()
        full = best_match.group(0)

        # Cycle: A1 -> \$A\$1 -> A\$1 -> \$A1 -> A1
        states = [
            (False, False),  # A1
            (True, True),    # \$A\$1
            (False, True),   # A\$1
            (True, False),   # \$A1
        ]
        current = (bool(col_abs), bool(row_abs))
        try:
            idx = states.index(current)
        except ValueError:
            idx = 0
        next_idx = (idx + 1) % len(states)
        new_col_abs, new_row_abs = states[next_idx]

        new_ref = f"{'\$' if new_col_abs else ''}{col_letters}{'\$' if new_row_abs else ''}{row_num}"

        new_text = text[:best_match.start()] + new_ref + text[best_match.end():]
        self.input.setText(new_text)
        self.input.setCursorPosition(best_match.start() + len(new_ref))

    def _on_commit(self):
        if self._updating:
            return
        self.commit.emit(self.input.text())