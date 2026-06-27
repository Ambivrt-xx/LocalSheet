"""
ProtectSheetDialog — dialog for enabling/disabling sheet protection.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QCheckBox, QDialogButtonBox, QLabel
)


class ProtectSheetDialog(QDialog):
    """Dialog for configuring sheet protection."""

    def __init__(self, is_protected=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Protect Sheet")
        self.setMinimumWidth(380)
        self._build_ui(is_protected)

    def _build_ui(self, is_protected):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "Protect the sheet to prevent accidental edits to cells.\n"
            "Locked cells cannot be edited while the sheet is protected."))

        form = QFormLayout()
        self.protect_cb = QCheckBox("Protect sheet and contents of locked cells")
        self.protect_cb.setChecked(is_protected)
        form.addRow(self.protect_cb)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Optional password")
        form.addRow("Password (optional):", self.password_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def should_protect(self):
        return self.protect_cb.isChecked()

    def get_password(self):
        return self.password_input.text().strip() or None