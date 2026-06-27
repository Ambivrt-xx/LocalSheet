"""
Page setup dialog — orientation, paper size, margins.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QGroupBox, QRadioButton,
    QButtonGroup, QComboBox, QDialogButtonBox
)
from PyQt6.QtPrintSupport import QPrinter


class PageSetupDialog(QDialog):
    def __init__(self, current_orientation=QPrinter.PageOrientation.Portrait, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Page Setup")
        self.setMinimumWidth(350)
        self._orientation = current_orientation

        layout = QVBoxLayout(self)

        # Orientation
        orient_group = QGroupBox("Orientation")
        orient_layout = QVBoxLayout(orient_group)
        self.btn_portrait = QRadioButton("Portrait")
        self.btn_landscape = QRadioButton("Landscape")
        self.orient_group = QButtonGroup(self)
        self.orient_group.addButton(self.btn_portrait)
        self.orient_group.addButton(self.btn_landscape)
        if current_orientation == QPrinter.PageOrientation.Landscape:
            self.btn_landscape.setChecked(True)
        else:
            self.btn_portrait.setChecked(True)
        orient_layout.addWidget(self.btn_portrait)
        orient_layout.addWidget(self.btn_landscape)
        layout.addWidget(orient_group)

        # Paper size
        paper_group = QGroupBox("Paper Size")
        paper_layout = QFormLayout(paper_group)
        self.paper_combo = QComboBox()
        self.paper_combo.addItem("Letter", QPrinter.PageSize.Letter)
        self.paper_combo.addItem("A4", QPrinter.PageSize.A4)
        self.paper_combo.addItem("Legal", QPrinter.PageSize.Legal)
        self.paper_combo.addItem("A3", QPrinter.PageSize.A3)
        paper_layout.addRow("Size:", self.paper_combo)
        layout.addWidget(paper_group)

        # Margins
        margin_group = QGroupBox("Margins")
        margin_layout = QFormLayout(margin_group)
        self.margin_combo = QComboBox()
        self.margin_combo.addItem("Normal", 'normal')
        self.margin_combo.addItem("Narrow", 'narrow')
        self.margin_combo.addItem("Wide", 'wide')
        margin_layout.addRow("Preset:", self.margin_combo)
        layout.addWidget(margin_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_orientation(self):
        return (QPrinter.PageOrientation.Landscape if self.btn_landscape.isChecked()
                else QPrinter.PageOrientation.Portrait)

    def get_paper_size(self):
        return self.paper_combo.currentData()