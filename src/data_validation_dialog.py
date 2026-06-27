"""
Dialog for creating/editing data validation rules (dropdown lists).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QComboBox,
    QDialogButtonBox, QFormLayout, QGroupBox, QRadioButton, QButtonGroup
)


class DataValidationDialog(QDialog):
    def __init__(self, existing=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Validation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Type selector
        type_group = QGroupBox("Validation Type")
        type_layout = QFormLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItem("Drop-down list", 'list')
        self.type_combo.addItem("Whole number", 'whole')
        self.type_combo.addItem("Decimal", 'decimal')
        self.type_combo.addItem("Text length", 'textLength')
        self.type_combo.addItem("Any value", None)
        type_layout.addRow("Type:", self.type_combo)
        layout.addWidget(type_group)

        # Source values
        src_group = QGroupBox("Source (comma-separated for list)")
        src_layout = QVBoxLayout(src_group)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("e.g. Yes, No, Maybe")
        src_layout.addWidget(self.source_edit)
        layout.addWidget(src_group)

        # Options
        self.allow_blank = QCheckBox("Allow blank")
        self.allow_blank.setChecked(True)
        layout.addWidget(self.allow_blank)

        # Input message
        msg_group = QGroupBox("Input Message (optional)")
        msg_layout = QVBoxLayout(msg_group)
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("Shown when cell is selected")
        msg_layout.addWidget(self.prompt_edit)
        layout.addWidget(msg_group)

        # Populate from existing
        if existing:
            idx = self.type_combo.findData(existing.dv_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.source_edit.setText(existing.formula1)
            self.allow_blank.setChecked(existing.allow_blank)
            self.prompt_edit.setText(existing.prompt)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Discard)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Discard).clicked.connect(self._clear)
        layout.addWidget(buttons)

    def _clear(self):
        self.done(2)  # custom code for "clear"

    def get_params(self):
        dv_type = self.type_combo.currentData()
        if dv_type is None:
            return None
        return {
            'dv_type': dv_type,
            'formula1': self.source_edit.text(),
            'allow_blank': self.allow_blank.isChecked(),
            'prompt': self.prompt_edit.text(),
            'error': '',
        }