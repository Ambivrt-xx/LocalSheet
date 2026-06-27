"""
FilterDialog — modal dialog showing unique column values with checkboxes
for spreadsheet row filtering.
"""
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QCheckBox, QDialogButtonBox,
    QScrollArea
)


class FilterDialog(QDialog):
    """Dialog showing unique column values with checkboxes for filtering."""

    def __init__(self, values, current_filter, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter by Values")
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        container_layout = QVBoxLayout(container)

        self.checks = {}
        select_all = QCheckBox("(Select All)")
        select_all.setChecked(True)
        select_all.stateChanged.connect(self._toggle_all)
        container_layout.addWidget(select_all)
        self.select_all = select_all

        for v in values:
            cb = QCheckBox(str(v))
            cb.setChecked(True if not current_filter else v in current_filter)
            self.checks[v] = cb
            container_layout.addWidget(cb)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_all(self, state):
        checked = state != 0
        for cb in self.checks.values():
            cb.setChecked(checked)

    def selected_values(self):
        return {v for v, cb in self.checks.items() if cb.isChecked()}