"""
MultiSortDialog — sort by up to 3 columns with ascending/descending per key.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QDialogButtonBox, QGroupBox, QGridLayout
)
from .formula_engine import col_index_to_letters


class SortKeyWidget(QGroupBox):
    """A single sort key: column + order + has header checkbox."""

    def __init__(self, title, cols, parent=None):
        super().__init__(title, parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)

        self.col_combo = QComboBox()
        for c in cols:
            self.col_combo.addItem(f"Column {col_index_to_letters(c)}", c)
        layout.addWidget(QLabel("Sort by:"), 0, 0)
        layout.addWidget(self.col_combo, 0, 1)

        self.order_combo = QComboBox()
        self.order_combo.addItem("A to Z (Ascending)", True)
        self.order_combo.addItem("Z to A (Descending)", False)
        layout.addWidget(QLabel("Order:"), 1, 0)
        layout.addWidget(self.order_combo, 1, 1)

    def get_sort_key(self):
        return (
            self.col_combo.currentData(),
            self.order_combo.currentData()
        )


class MultiSortDialog(QDialog):
    """Dialog for multi-column sorting."""

    def __init__(self, max_col, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sort")
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)

        self.has_header = QCheckBox("My data has headers")
        self.has_header.setChecked(True)
        layout.addWidget(self.has_header)

        cols = list(range(max_col + 1))

        self.keys = []
        for title in ("Sort by", "Then by", "Then by"):
            kw = SortKeyWidget(title, cols, self)
            self.keys.append(kw)
            layout.addWidget(kw)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_sort_keys(self):
        """Return list of (col, ascending) tuples, only for active keys."""
        results = []
        for kw in self.keys:
            col, asc = kw.get_sort_key()
            if col is not None:
                results.append((col, asc))
        return results

    def has_headers(self):
        return self.has_header.isChecked()