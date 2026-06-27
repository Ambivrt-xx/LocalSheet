"""
Dialog for managing named ranges — define names for cell ranges to use in formulas.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QDialogButtonBox, QInputDialog
)


class NamedRangesDialog(QDialog):
    def __init__(self, existing_ranges, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Named Ranges")
        self.setMinimumWidth(450)
        self._ranges = dict(existing_ranges)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self._refresh_list()
        layout.addWidget(QLabel("Defined names:"))
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add...")
        btn_add.clicked.connect(self._add)
        btn_edit = QPushButton("Edit...")
        btn_edit.clicked.connect(self._edit)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self._delete)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_list(self):
        self.list_widget.clear()
        for name, (r1, c1, r2, c2) in self._ranges.items():
            from .formula_engine import col_index_to_letters
            ref = f"{col_index_to_letters(c1)}{r1+1}:{col_index_to_letters(c2)}{r2+1}"
            self.list_widget.addItem(QListWidgetItem(f"{name} = {ref}"))

    def _add(self):
        name, ok = QInputDialog.getText(self, "Add Named Range", "Name:")
        if not ok or not name.strip():
            return
        ref, ok2 = QInputDialog.getText(self, "Add Named Range", "Range (e.g. A1:B10):")
        if not ok2 or not ref.strip():
            return
        parsed = self._parse_ref(ref.strip())
        if parsed:
            self._ranges[name.strip().upper()] = parsed
            self._refresh_list()

    def _edit(self):
        row = self.list_widget.currentRow()
        names = list(self._ranges.keys())
        if row < 0 or row >= len(names):
            return
        name = names[row]
        from .formula_engine import col_index_to_letters
        r1, c1, r2, c2 = self._ranges[name]
        current = f"{col_index_to_letters(c1)}{r1+1}:{col_index_to_letters(c2)}{r2+1}"
        ref, ok = QInputDialog.getText(self, "Edit Named Range", f"Range for {name}:", text=current)
        if ok and ref.strip():
            parsed = self._parse_ref(ref.strip())
            if parsed:
                self._ranges[name] = parsed
                self._refresh_list()

    def _delete(self):
        row = self.list_widget.currentRow()
        names = list(self._ranges.keys())
        if row < 0 or row >= len(names):
            return
        del self._ranges[names[row]]
        self._refresh_list()

    def _parse_ref(self, ref):
        """Parse 'A1:B2' or 'A1' into (r1, c1, r2, c2)."""
        import re
        from .formula_engine import col_letters_to_index
        m = re.match(r'^([A-Za-z]+)(\d+)(?::([A-Za-z]+)(\d+))?$', ref)
        if not m:
            return None
        c1 = col_letters_to_index(m.group(1))
        r1 = int(m.group(2)) - 1
        if m.group(3):
            c2 = col_letters_to_index(m.group(3))
            r2 = int(m.group(4)) - 1
        else:
            c2, r2 = c1, r1
        return (r1, c1, r2, c2)

    def get_ranges(self):
        return dict(self._ranges)